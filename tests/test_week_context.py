"""Local synthetic tests: no personal records or remote model requests."""
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from core import week_context
from core.draft import parse_bundle
from core.questions import build_rank_question
from desk.local_account import save_account, load_account
from desk.wechat_sqlcipher import ReadOnlyWechatCipher

NOW = 1800000000

class WeekContextTests(unittest.TestCase):
    def test_rolling_week_includes_boundary_and_preserves_over_200_messages(self):
        items = [{'id':str(i),'side':'me' if i%2 else 'other','text':f'内容{i}',
                  'timestamp':NOW-i*10,'kind':'text'} for i in range(450)]
        items += [{'id':'edge','side':'other','text':'边界','timestamp':NOW-7*86400},
                  {'id':'old','side':'other','text':'太早','timestamp':NOW-7*86400-1},
                  {'id':'future','side':'other','text':'未来','timestamp':NOW+1}]
        selected, meta = week_context.select_week(items, NOW, complete=True)
        self.assertEqual(len(selected),451)
        self.assertEqual(selected[0]['id'],'edge')
        self.assertEqual(selected[-1]['id'],'0')
        self.assertTrue(meta['complete'])
        self.assertEqual(meta['message_count'],451)

    def test_unknown_dates_are_disclosed_and_media_not_misrepresented(self):
        selected, meta=week_context.select_week([
            {'id':'u','side':'other','text':'可见消息','timestamp':None},
            {'id':'p','side':'other','text':'[图片]','kind':'image','timestamp':NOW}],NOW,complete=False)
        self.assertFalse(meta['complete']);self.assertEqual(meta['unknown_time_count'],1)
        self.assertEqual(meta['media_count'],1)
        state=week_context.build_week_state(selected,{},meta)
        self.assertIn('图片',json.dumps(state,ensure_ascii=False))

    def test_pagination_loads_entire_week_without_200_limit(self):
        rows=[{'id':str(i),'side':'other','text':str(i),'timestamp':NOW-i} for i in range(650)]
        calls=[]
        def fetch(cursor):
            i=cursor or 0; calls.append(i)
            return {'items':list(reversed(rows[i:i+100])), 'has_more':i+100<len(rows),
                    'next_cursor':i+100 if i+100<len(rows) else None}
        selected,meta=week_context.collect_week(fetch,NOW)
        self.assertEqual(len(selected),650);self.assertEqual(len(calls),7);self.assertTrue(meta['complete'])
        state=week_context.build_week_state(selected,{'my_interests':'摄影'},meta)
        self.assertEqual(len(state['chat']['messages']),650)
        self.assertEqual(state['my_interests'],'摄影')

    def test_repeated_cursor_and_oversize_fail_without_silent_loss(self):
        def fetch(cursor):
            return {'items':[{'id':'a','side':'other','text':'a','timestamp':NOW}],
                    'has_more':True,'next_cursor':'same'}
        with self.assertRaises(ValueError):week_context.collect_week(fetch,NOW)
        with self.assertRaises(ValueError):
            week_context.build_week_state([{'id':'a','side':'other','text':'a'*400001}],{}, {})

    def test_pagination_stops_at_old_boundary_and_deduplicates(self):
        def fetch(cursor):
            if cursor is None:return {'items':[{'id':'a','side':'other','text':'a','timestamp':NOW}], 'has_more':True,'next_cursor':'b'}
            return {'items':[{'id':'old','side':'other','text':'old','timestamp':NOW-8*86400},
                {'id':'a','side':'other','text':'a','timestamp':NOW}], 'has_more':True,'next_cursor':'c'}
        selected,meta=week_context.collect_week(fetch,NOW)
        self.assertEqual(len(selected),1);self.assertTrue(meta['complete'])

class ReplyBundleTests(unittest.TestCase):
    def test_five_replies_and_three_evidence_backed_directions(self):
        value={'candidates':['回复'+str(i) for i in range(5)],'topics':{
            k:[{'title':'聊摄影','opener':'周末想出去拍照吗？','reason':'之前提过摄影',
                'evidence_ids':['m1','nonexistent']}] for k in ('missed','their','mine')}}
        response={'choices':[{'message':{'content':json.dumps(value)}}]}
        candidates,topics=parse_bundle(response, {'m1'})
        self.assertEqual(len(candidates),5)
        self.assertEqual(set(topics),{'missed','their','mine'})
        self.assertEqual(topics['their'][0]['evidence_ids'],['m1'])
        rank=build_rank_question(candidates)
        self.assertEqual(list(rank['best_reply']['criteria']),['reply_a','reply_b','reply_c','reply_d','reply_e'])

    def test_legacy_response_remains_valid_and_no_topics_are_fabricated(self):
        response={'choices':[{'message':{'content':'["一","二","三","四","五","六"]'}}]}
        candidates,topics=parse_bundle(response,set())
        self.assertEqual(candidates,['一','二','三','四','五']);self.assertFalse(any(topics.values()))

class ProtectedAccountTests(unittest.TestCase):
    def test_account_is_dpapi_encrypted_and_reads_raw_key_without_writes(self):
        if sys.platform!='win32':self.skipTest('Windows DPAPI')
        import sqlcipher3
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/'db_storage';root.mkdir();db=root/'sample.db';key='a1'*32
            c=sqlcipher3.connect(str(db));c.execute('PRAGMA key="x\''+key+'\'"')
            c.execute('create table sample(value text)');c.execute('insert into sample values (?)',('合成',));c.commit();c.close()
            salt=db.read_bytes()[:16].hex();record=Path(t)/'account.json'
            save_account(record,root,'synthetic_owner',{salt:key})
            self.assertNotIn(key,record.read_text());self.assertNotIn(str(root),record.read_text())
            info=load_account(record);self.assertEqual(info['keys'][salt],key)
            factory=ReadOnlyWechatCipher(root,key,raw_keys=info['keys'])
            c=factory(db)
            try:
                self.assertEqual(c.execute('select value from sample').fetchone()[0],'合成')
                with self.assertRaises(sqlcipher3.DatabaseError):c.execute('delete from sample')
            finally:c.close()
            with self.assertRaises(Exception):factory(Path(t)/'outside.db')

    def test_invalid_key_or_path_is_rejected_before_storage(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):save_account(Path(t)/'account.json',Path(t),'x',{'bad':'secret'})

if __name__=='__main__':unittest.main()
