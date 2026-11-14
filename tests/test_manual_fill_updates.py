"""No real WeChat writes: explicit fill is separated from automatic sending."""
import contextlib,sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from PySide6.QtWidgets import QApplication
from desk.controller import Controller,AUTO_DISCLOSURE
from desk.capture_service import CaptureService
APP=QApplication.instance() or QApplication([])

class ManualFillTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.native=patch('desk.capture_service.CaptureService');self.native.start()
        self.c=Controller(Path(self.temp.name));self.c.store.config['auto_analyze']=False
        self.incoming('one');self.fingerprint=self.c.fingerprint(self.c.sessions['chat:a'])
        self.c.results['chat:a']={'session_id':'chat:a','candidates':[{'text':'已经选好的建议'}]}
        self.c.result_fingerprints['chat:a']=self.fingerprint
    def tearDown(self):self.c.close();self.native.stop();self.temp.cleanup()
    def incoming(self,mid):
        self.c._on_capture('messages',{'session_id':'chat:a','title':'合成联系人','source':'ocr',
            'messages':[{'id':mid,'text':'合成来信','side':'other','timestamp':time.time()}]})
    def test_new_message_keeps_existing_draft_fillable_without_sending(self):
        self.incoming('two')
        self.assertTrue(self.c.snapshot()['analysis']['context_changed'])
        future=self.c.handle('fill_reply',{'session_id':'chat:a','index':0,'text':'已经选好的建议'})
        future.result(timeout=2)
        self.c.capture.fill.assert_called_once_with('已经选好的建议','合成联系人')
        self.c.capture.send.assert_not_called()
    def test_generation_completing_after_new_message_preserves_manual_draft(self):
        self.incoming('two');result={'session_id':'chat:a','candidates':[{'text':'刚完成的建议'}]}
        self.c._on_analysis('chat:a',self.c.revision,self.fingerprint,result,None)
        self.assertEqual(self.c.results['chat:a']['candidates'][0]['text'],'刚完成的建议')
        self.assertTrue(self.c.snapshot()['analysis']['context_changed'])
    def test_wrong_conversation_and_replaced_candidate_are_still_blocked(self):
        with self.assertRaises(ValueError):self.c.handle('fill_reply',{'session_id':'chat:b','index':0})
        with self.assertRaises(ValueError):self.c.handle('fill_reply',{'session_id':'chat:a','index':0,'text':'已经被替换的另一条'})
        self.c.capture.fill.assert_not_called()
    def test_native_fill_is_independent_of_another_chats_latest_notification(self):
        self.c.sessions['chat:a']['source']='wechat_db';self.c.store.config['source']='wechat_db'
        self.c.live_id='other-chat';self.c.current_id='chat:a'
        self.assertTrue(self.c.snapshot()['current_session']['active'])
        self.c.handle('fill_reply',{'session_id':'chat:a','index':0}).result(timeout=2)
        self.c.capture.fill_db.assert_called_once_with('已经选好的建议','chat:a','合成联系人')

    def test_week_history_is_not_cut_to_500_when_new_messages_arrive(self):
        now=time.time();session=self.c.sessions['chat:a']
        session['messages']=[{'id':str(i),'text':'合成','side':'other','timestamp':now-i} for i in range(650)]
        session['context_window']={'days':7,'complete':True,'message_count':650}
        self.incoming('after-week-load')
        self.assertEqual(len(session['messages']),651)
        self.assertEqual(session['context_window']['message_count'],651)

    def test_week_load_preserves_new_message_arriving_during_read(self):
        now=time.time();self.incoming('arrived-during-read')
        session={**self.c.sessions['chat:a'],'messages':[{'id':'loaded','text':'合成历史','side':'other','timestamp':now-10}],
                 'context_window':{'days':7,'complete':True,'message_count':1,'end':now}}
        self.c._on_session_loaded('chat:a',{'kind':'select','result':{'session':session}},None)
        ids={m['id'] for m in self.c.sessions['chat:a']['messages']}
        self.assertEqual(ids,{'loaded','one','arrived-during-read'})

class CaptureFillAndDisclosureTests(unittest.TestCase):
    def test_native_fill_queues_verification_without_enter_or_send(self):
        service=CaptureService(lambda *a:None);service._config={'source':'wechat_db'}
        with patch.object(service,'_fill_db_worker',return_value={'success':True}) as fill,patch.object(service,'_send_db_worker') as send,patch.object(service,'_ensure_thread',side_effect=service._drain_requests):
            result=service.fill_db('合成建议','synthetic-id','合成联系人')
        self.assertTrue(result['success']);self.assertEqual(fill.call_args.args[0]['text'],'合成建议');send.assert_not_called()
    def test_native_fill_restores_window_and_reuses_fresh_target_verification(self):
        class Source:
            def sessions(self,limit,offset):return [{'id':'s','name':'合成联系人'}]
        service=CaptureService(lambda *a:None)
        task={'text':'合成','session_id':'s','title':'合成联系人'}
        with patch.object(service,'_new_wechat_db_source',return_value=Source()),patch.object(service,'_temporary_db_send_window',return_value=contextlib.nullcontext(123)),patch.object(service,'_fill_worker',return_value={'success':True}) as fill:
            self.assertTrue(service._fill_db_worker(task)['success'])
        self.assertEqual(fill.call_args.args[0]['title'],'合成联系人')
    def test_database_auto_reply_does_not_append_ai_signature(self):
        service=CaptureService(lambda *a:None);service._config={'source':'wechat_db'};service._wanted.set()
        with patch.object(service,'_send_db_worker',return_value={'success':True}) as send,patch.object(service,'_ensure_thread',side_effect=service._drain_requests):
            service.send_db('合成回复'+AUTO_DISCLOSURE,'s','m')
        self.assertEqual(send.call_args.args[0]['text'],'合成回复')
    def test_minimized_ocr_window_is_waiting_not_read_failure(self):
        events=[];service=None
        def callback(kind,data):
            events.append((kind,data))
            if kind=='status' and data.get('capture') in ('waiting','error'):service._stop.set()
        service=CaptureService(callback);service._config={'source':'ocr'};service._wanted.set()
        with patch.object(service,'_ensure_capture',side_effect=RuntimeError('请还原微信窗口并打开目标聊天')):service._run()
        self.assertEqual([d['capture'] for k,d in events if k=='status'][-1],'waiting')

if __name__=='__main__':unittest.main()
