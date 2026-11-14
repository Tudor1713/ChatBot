"""Offline rendered failure isolation: local mock HTTP and real model worker."""
import json,multiprocessing,sys,tempfile,threading,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
class Mock(BaseHTTPRequestHandler):
    count=0
    def do_POST(self):
        type(self).count+=1
        p=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        if '判断引擎' in p['messages'][0]['content']:
            value={'choices':[{'finish_reason':'length','message':{'content':None,'reasoning_content':'synthetic only'}}]}
        else:
            value={'choices':[{'message':{'content':json.dumps({'candidates':[f'合成回应{i}' for i in range(5)],
                'topics':{k:[{'title':'合成话题','opener':'要聊聊吗？','reason':'待确认','evidence_ids':[]}] for k in ('missed','their','mine')}})}}]}
        data=json.dumps(value).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def log_message(self,*a):pass

def main():
    from PySide6.QtCore import QTimer,QUrl
    from PySide6.QtWidgets import QApplication
    from PySide6.QtWebChannel import QWebChannel
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from desk.controller import Controller
    from desk.bridge import Bridge
    app=QApplication([]);server=ThreadingHTTPServer(('127.0.0.1',0),Mock)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    temp=tempfile.TemporaryDirectory(dir=ROOT/'work',prefix='resilience-')
    c=Controller(Path(temp.name))
    c.store.save_config({'api_key':'<local-mock-only>','base_url':f'http://127.0.0.1:{server.server_port}/v1',
        'model_name':'deepseek-v4.1-flash','auto_analyze':False})
    c.handle('manual_context',{'title':'合成容错会话','text':'我：周末去拍照\n对方：去哪里呢？'})
    v=QWebEngineView();v.resize(1280,850);channel=QWebChannel(v.page());bridge=Bridge(c)
    channel.registerObject('bridge',bridge);v.page().setWebChannel(channel)
    u=QUrl.fromLocalFile(str(ROOT/'ui/index.html'));u.setQuery('intro=0')
    started=[False];deadline=time.monotonic()+35
    result={'success':False}
    def inspect(raw):
        if not raw:return QTimer.singleShot(150,tick)
        dom=json.loads(raw)
        if not started[0] and dom.get('ready'):
            started[0]=True;v.page().runJavaScript("[...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='分析当前').click()")
        elif c.results and dom.get('replies')==5:
            result.update(dom,requests=Mock.count)
            result['success']=dom.get('degraded') and dom.get('tabs')==3 and Mock.count==3
            QTimer.singleShot(200,lambda:(v.grab().save(str(ROOT/'work/resilience-ui.png')),app.exit(0 if result['success'] else 1)))
            return
        if time.monotonic()>deadline:app.exit(2);return
        QTimer.singleShot(150,tick)
    def tick():
        v.page().runJavaScript("JSON.stringify({ready:[...document.querySelectorAll('button')].some(b=>b.textContent.trim()==='分析当前'),replies:document.querySelectorAll('.reply-card').length,tabs:document.querySelectorAll('[data-topic-direction]').length,degraded:document.querySelector('.analysis-panel')?.textContent.includes('判断暂不可用，回复已保留')})",inspect)
    v.loadFinished.connect(lambda ok:QTimer.singleShot(500,tick) if ok else app.exit(3));v.load(u);v.show()
    code=app.exec();c.close();v.close();server.shutdown();server.server_close();temp.cleanup()
    print(json.dumps(result,ensure_ascii=False));return code

if __name__=='__main__':
    multiprocessing.freeze_support();raise SystemExit(main())
