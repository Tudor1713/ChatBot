"""Offline rendered new-message regression. All WeChat actions are mocked."""
import json,sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))

def main():
    from PySide6.QtCore import QTimer,QUrl
    from PySide6.QtWidgets import QApplication
    from PySide6.QtWebChannel import QWebChannel
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from desk.controller import Controller
    from desk.bridge import Bridge
    app=QApplication([]);temp=tempfile.TemporaryDirectory(dir=ROOT/'work',prefix='fill-ui-')
    native=patch('desk.capture_service.CaptureService');capture=native.start().return_value
    capture.fill_db.return_value={'success':True}
    c=Controller(Path(temp.name));c.store.config.update(source='wechat_db',auto_analyze=False,
        base_url='http://127.0.0.1:1/v1',model_name='synthetic-only')
    c.store.secrets['api_key']='synthetic-only'
    sid='synthetic-contact'
    def incoming(mid):
        c._on_capture('messages',{'session_id':sid,'title':'合成容错会话','source':'wechat_db',
            'messages':[{'id':mid,'side':'other','text':'本地合成新消息','timestamp':time.time()}]})
    incoming('first');fingerprint=c.fingerprint(c.sessions[sid]);incoming('during-generation')
    result={'session_id':sid,'judgment_available':False,'updated_at':time.time(),
        'candidates':[{'text':f'本地合成建议{i}'} for i in range(5)],
        'topics':{k:[] for k in ('missed','their','mine')}}
    c._on_analysis(sid,c.revision,fingerprint,result,None)
    # A different chat's notification must not disable the selected draft.
    c.live_id='other-notification';c.follow_live=False;c.current_id=sid
    v=QWebEngineView();v.resize(1320,900);channel=QWebChannel(v.page());bridge=Bridge(c)
    channel.registerObject('bridge',bridge);v.page().setWebChannel(channel)
    u=QUrl.fromLocalFile(str(ROOT/'ui/index.html'));u.setQuery('intro=0')
    stage=[0];deadline=time.monotonic()+20;report={'success':False}
    def inspect(raw):
        state=json.loads(raw or '{}')
        if stage[0]==0 and state.get('replies')==5:
            report.update(state)
            if not state.get('updated') or state.get('enabled')!=5:app.exit(1);return
            stage[0]=1
            v.grab().save(str(ROOT/'work/manual-fill-ui.png'))
            v.page().runJavaScript("[...document.querySelectorAll('.reply-card button')].find(b=>b.textContent.trim()==='填入微信').click()")
        elif stage[0]==1 and capture.fill_db.called:
            report['filled']=capture.fill_db.call_args.args==('本地合成建议0',sid,'合成容错会话')
            report['sent']=capture.send.called or capture.send_db.called
            stage[0]=2
            v.page().runJavaScript("[...document.querySelectorAll('nav button')].find(b=>b.textContent.includes('自动回复')).click()")
        elif stage[0]==2 and state.get('autoPage'):
            report['disclosureRemoved']=not state.get('disclosure')
            report['autoOff']=not c.snapshot()['auto_reply']['enabled']
            report['success']=report['filled'] and not report['sent'] and report['disclosureRemoved'] and report['autoOff']
            app.exit(0 if report['success'] else 2);return
        if time.monotonic()>deadline:
            report.update(lastState=state,stage=stage[0],controllerReplies=len(c.results.get(sid,{}).get('candidates',[])))
            v.grab().save(str(ROOT/'work/manual-fill-ui.png'));app.exit(3);return
        QTimer.singleShot(120,tick)
    def tick():
        v.page().runJavaScript("JSON.stringify({replies:document.querySelectorAll('.reply-card').length,enabled:[...document.querySelectorAll('.reply-card button')].filter(b=>b.textContent.trim()==='填入微信'&&!b.disabled).length,updated:document.body.textContent.includes('已保留原来的建议'),autoPage:!!document.querySelector('.auto-reply-page'),disclosure:document.body.textContent.includes('ChatBot生成')})",inspect)
    v.loadFinished.connect(lambda ok:QTimer.singleShot(500,tick) if ok else app.exit(4));v.load(u);v.show()
    code=app.exec();c.close();v.close();native.stop();temp.cleanup()
    print(json.dumps(report,ensure_ascii=False));return code

if __name__=='__main__':raise SystemExit(main())
