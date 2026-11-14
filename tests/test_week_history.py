import sys
from pathlib import Path
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from desk.week_history import read_week_context

class WeekHistoryTests(unittest.TestCase):
    def test_native_session_reads_every_page_from_same_session(self):
        now=1800000000;called=[]
        def page(cfg,sid,cursor,limit):
            self.assertEqual(sid,'chosen');called.append(cursor)
            return {'items':[{'id':str(cursor),'side':'other','text':'合成','timestamp':now-10}],
                'has_more':cursor is None,'next_cursor':'older' if cursor is None else None}
        messages,meta=read_week_context({'id':'chosen','source':'wechat_db'}, {},page,now=now)
        self.assertEqual(len(messages),2);self.assertTrue(meta['complete']);self.assertEqual(called[:2],[None,'older'])

    def test_ocr_matches_unique_native_contact_not_other_people(self):
        class Native:
            def sessions(self,limit,offset):return [{'id':'one','name':'合成联系人'}] if offset==0 else []
            def messages(self,sid,limit,before=None,**window):
                self.asserted=sid
                self.windows=getattr(self,'windows',[])+[window]
                return [{'id':'real','side':'me','text':'完整记录','timestamp':1800000000,'_cursor':(1,1,1,'shard')}]
        n=Native()
        msgs,meta=read_week_context({'id':'ocr:hash','title':'合成联系人','source':'ocr'}, {},None,native_factory=lambda:n,now=1800000000)
        self.assertEqual(n.asserted,'one');self.assertEqual(meta['message_count'],1);self.assertTrue(meta['complete'])
        self.assertEqual(n.windows[0],{'start_time':1800000000-7*86400,'end_time':1800000000})

    def test_thin_week_falls_back_to_latest_200_messages(self):
        now=1800000000
        class Native:
            def messages(self,sid,limit,before=None,**window):
                if window:  # 近 7 天只有 30 条
                    return [{'id':f'w{j}','side':'other','text':'近','timestamp':now-j,'_cursor':(j,)} for j in range(30)]
                self.latest_limit=limit
                return [{'id':f'l{j}','side':'me' if j%2 else 'other','text':'旧','timestamp':now-j*3600,'_cursor':(j,)} for j in range(limit)]
        n=Native()
        messages,meta=read_week_context({'id':'chosen','source':'wechat_db'},{},None,native_factory=lambda:n,now=now)
        self.assertEqual(n.latest_limit,200);self.assertEqual(len(messages),200)
        self.assertEqual(meta['mode'],'latest');self.assertEqual(meta['week_count'],30);self.assertIsNone(meta['days'])
        self.assertTrue(all('_cursor' not in m for m in messages))
        self.assertLess(messages[0]['timestamp'],messages[-1]['timestamp'])  # 正序

    def test_full_week_keeps_seven_day_window(self):
        now=1800000000
        class Native:
            def messages(self,sid,limit,before=None,**window):
                if not window:raise AssertionError('Enough recent messages: no fallback read')
                i=before or 0
                return [{'id':str(j),'side':'other','text':'近','timestamp':now-j,'_cursor':j+1} for j in range(i,min(i+limit,160))]
        messages,meta=read_week_context({'id':'chosen','source':'wechat_db'},{},None,native_factory=lambda:Native(),now=now)
        self.assertEqual(meta['days'],7);self.assertEqual(len(messages),160)

    def test_collected_only_session_uses_latest_200(self):
        now=1800000000
        rows=[{'id':str(j),'side':'other','text':'旧','timestamp':now-30*86400+j} for j in range(300)]
        messages,meta=read_week_context({'id':'ocr:x','source':'ocr','messages':rows},{},None,now=now)
        self.assertEqual(len(messages),200);self.assertEqual(meta['mode'],'latest');self.assertEqual(messages[-1]['id'],'299')

    def test_native_reads_filtered_pages_without_assuming_sort_sequence_is_time(self):
        class Native:
            def messages(self,sid,limit,before=None,**window):
                self.asserted=(sid,window)
                i=before or 0
                return [{'id':str(j),'side':'other','text':'合成','timestamp':1800000000-j,
                         '_cursor':j+1} for j in range(i,min(i+limit,650))]
        n=Native()
        def wrong_page(*a):raise AssertionError('Should use native SQL time bounds')
        messages,meta=read_week_context({'id':'chosen','source':'wechat_db'}, {},wrong_page,native_factory=lambda:n,now=1800000000)
        self.assertEqual(len(messages),650);self.assertTrue(meta['complete'])
        self.assertEqual(n.asserted,('chosen',{'start_time':1800000000-7*86400,'end_time':1800000000}))

    def test_ambiguous_names_are_not_merged(self):
        class Native:
            def sessions(self,limit,offset):return [{'id':'a','name':'同名'},{'id':'b','name':'同名'}]
        with self.assertRaises(ValueError):
            read_week_context({'id':'ocr:x','title':'同名','source':'ocr'}, {},None,native_factory=Native,now=1800000000)

    def test_unavailable_ocr_history_is_explicitly_partial(self):
        def unavailable():raise ValueError('未配置')
        msgs,meta=read_week_context({'id':'ocr:x','source':'ocr','messages':[{'side':'me','text':'可见'}]}, {},None,native_factory=unavailable,now=1800000000)
        self.assertFalse(meta['complete']);self.assertEqual(len(msgs),1)

if __name__=='__main__':unittest.main()
