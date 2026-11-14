"""Rendered offline desktop UI test using only built-in synthetic demo data."""
import json,os,sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl,QTimer
root=Path(__file__).resolve().parents[1]
app=QApplication([]);view=QWebEngineView();view.resize(1320,900)
url=QUrl.fromLocalFile(str(root/'ui/index.html'));url.setQuery('demo=1&intro=0')
result={}
def done(value):
    result.update(json.loads(value or '{}'))
    good=result.get('replies')==5 and result.get('tabs')==3 and result.get('week')
    if not good:
        print(json.dumps(result));app.exit(1);return
    view.page().runJavaScript("document.querySelector('[data-topic-direction=their]').click(); document.querySelector('.topic-card h3')?.textContent",switched)
def switched(value):
    result['switched']=value
    if not value or '兴趣' not in value:print(json.dumps(result,ensure_ascii=False));app.exit(2);return
    def capture():
        target=root/'work/week-ui.png';target.parent.mkdir(exist_ok=True)
        view.grab().save(str(target))
        print(json.dumps(result,ensure_ascii=False));app.exit(0)
    QTimer.singleShot(300,capture)
def inspect():
    view.page().runJavaScript("JSON.stringify({replies:document.querySelectorAll('.reply-card').length,tabs:document.querySelectorAll('[data-topic-direction]').length,week:!!document.querySelector('.week-context')?.textContent.includes('7天')})",done)
view.loadFinished.connect(lambda ok:QTimer.singleShot(2400,inspect) if ok else app.exit(3))
view.load(url);view.show();QTimer.singleShot(12000,lambda:app.exit(4));sys.exit(app.exec())
