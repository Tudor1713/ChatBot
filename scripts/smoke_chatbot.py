"""Native QtWebEngine UI checks with synthetic data and no external requests."""
import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    from PySide6.QtCore import QEventLoop, QTimer, QUrl
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
    from PySide6.QtWebChannel import QWebChannel
    from PySide6.QtWebEngineCore import QWebEnginePage
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from desk.controller import Controller
    from desk.bridge import Bridge
    app = QApplication([])
    temporary = tempfile.TemporaryDirectory(prefix='chatbot-ui-')
    ctrl = Controller(Path(temporary.name))
    ctrl.store.secrets['api_key'] = 'synthetic-smoke-only'
    ctrl.store.config.update(source='archive', auto_analyze=False, stickers_auto=False, intro_enabled=False)
    messages = [{'id': str(i), 'side': 'me' if i % 3 == 0 else 'other', 'kind': 'text',
                 'text': f'合成消息 {i + 1}：这是一段用于验证界面流畅度的测试记录。',
                 'timestamp': 1794400000 + i} for i in range(1000)]
    ctrl.sessions['synthetic'] = {'id': 'synthetic', 'title': '合成演示会话', 'source': 'manual',
                                 'messages': messages, 'updated': 1}
    ctrl.current_id = 'synthetic'
    ctrl.results['synthetic'] = {'session_id': 'synthetic', 'candidates': [
        {'text': text, 'reason': '合成建议'} for text in (
            '好呀，我先整理一下，晚点发给你。', '收到，明天上午一起确认。',
            '可以，我们按刚才的安排来。', '我再核对一下细节，有进展就告诉你。', '明白了，谢谢提醒。')],
        'best_index': 0, 'answers': {}, 'context_window': {'mode': 'latest', 'message_count': 1000}}
    errors = []

    class Page(QWebEnginePage):
        def javaScriptConsoleMessage(self, level, message, line, source):
            if level == self.JavaScriptConsoleMessageLevel.ErrorMessageLevel:
                errors.append({'line': line, 'message': message[:240]})

    view = QWebEngineView()
    page = Page(view)
    view.setPage(page)
    view.resize(1280, 850)
    channel = QWebChannel(page)
    bridge = Bridge(ctrl)
    channel.registerObject('bridge', bridge)
    page.setWebChannel(channel)
    report = {'success': False, 'checks': [], 'uses_external_api': False, 'uses_real_wechat': False}

    def js(code):
        loop, result = QEventLoop(), []
        def done(value):
            result.append(value)
            loop.quit()
        page.runJavaScript(code, done)
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        if not result:
            raise AssertionError('JavaScript callback timed out')
        return result[0]

    def wait(condition, seconds=8):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if js(condition):
                return
            QTest.qWait(25)
        raise AssertionError('UI condition timed out: ' + condition)

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        report['checks'].append(name)

    try:
        view.load(QUrl.fromLocalFile(str(ROOT / 'ui/index.html')))
        view.show()
        wait("document.querySelectorAll('.message').length > 0")
        wait("lateImage.complete && lateImage.naturalWidth > 0 && (()=>{const t=document.querySelector('.timeline');return t.scrollHeight-t.scrollTop-t.clientHeight<45})()")
        check('page_identity', js('document.title') == 'ChatBot')
        report['initial_message_nodes'] = js("document.querySelectorAll('.message').length")
        check('bounded_initial_render_200_of_1000', report['initial_message_nodes'] == 200)
        js("window.savedTimeline=document.querySelector('.timeline'); window.savedMessage=document.querySelector('.message'); window.savedLast=document.querySelector('.message:last-child');")
        js("const draft=document.querySelector('.regen-row input'); draft.value='测试输入保持'; draft.dispatchEvent(new Event('input')); draft.focus(); draft.setSelectionRange(2,4);")
        ctrl.status['analysis'] = 'running'
        ctrl.emit()
        wait("document.querySelector('.judgment-strip.busy') !== null")
        report['preservation_detail'] = js("JSON.stringify({sameTimeline:savedTimeline===document.querySelector('.timeline'),sameMessage:savedMessage===document.querySelector('.message'),oldId:savedMessage.dataset.messageId,newId:document.querySelector('.message').dataset.messageId,count:document.querySelectorAll('.message').length})")
        check('status_update_preserves_message_nodes', js("savedTimeline===document.querySelector('.timeline') && savedMessage===document.querySelector('.message')"))
        report['draft_focus'] = js("JSON.stringify({active:document.activeElement.tagName,value:document.activeElement.value,start:document.activeElement.selectionStart,end:document.activeElement.selectionEnd,draft:document.querySelector('.regen-row input').value})")
        check('status_update_preserves_draft_focus', js("document.activeElement===document.querySelector('.regen-row input') && document.activeElement.value==='测试输入保持' && document.activeElement.selectionStart===2 && document.activeElement.selectionEnd===4"))
        ctrl.status['analysis'] = 'idle'
        messages.append({'id': '1000', 'side': 'other', 'kind': 'text', 'text': '新增的合成消息', 'timestamp': 1794401001})
        ctrl.emit()
        wait("document.querySelector('.timeline').textContent.includes('新增的合成消息')")
        check('append_preserves_existing_last_message', js("savedLast === document.querySelector('[data-message-id=\"999\"]')"))
        js("document.querySelector('.timeline').scrollTop=document.querySelector('.timeline').scrollHeight")
        QTest.qWait(50)
        js("window.lateImage=new Image(); lateImage.src='data:image/svg+xml,'+encodeURIComponent('<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"320\" height=\"240\"><rect width=\"320\" height=\"240\" fill=\"gray\"/></svg>'); document.querySelector('.message:last-child').append(lateImage)")
        QTest.qWait(150)
        check('late_media_keeps_latest_message_visible', js("(()=>{const t=document.querySelector('.timeline');return t.scrollHeight-t.scrollTop-t.clientHeight<45})()"))
        js('lateImage.remove()')
        QTest.qWait(50)
        js("document.querySelector('.timeline').scrollTop=100")
        QTest.qWait(50)
        js("document.querySelector('.message:last-child').append(lateImage)")
        QTest.qWait(100)
        check('late_media_does_not_move_history_reader', js("Math.abs(document.querySelector('.timeline').scrollTop-100)<2"))
        js("lateImage.remove(); document.querySelector('.timeline').scrollTop=document.querySelector('.timeline').scrollHeight")
        QTest.qWait(50)
        js("document.querySelector('.timeline-more').click()")
        wait("document.querySelectorAll('.message').length === 400")
        check('older_messages_load_on_demand', True)
        ctrl.sessions['synthetic']['highlight_message_id'] = '5'
        ctrl.emit()
        wait("document.querySelector('[data-message-id=\"5\"].message-hit') !== null")
        check('highlight_can_reveal_old_message', True)
        ctrl.sessions['synthetic'].pop('highlight_message_id')
        ctrl.emit()
        QTest.qWait(80)
        js("document.querySelector('.timeline').scrollTop=document.querySelector('.timeline').scrollHeight")
        QTest.qWait(250)
        view.grab().save(str(args.output / 'ChatBot-workspace.png'))
        js("document.querySelector('#settings-button').focus(); document.querySelector('#settings-button').click()")
        wait("document.querySelector('#drawer').classList.contains('open')")
        QTest.qWait(300)
        check('drawer_moves_keyboard_focus', js("document.querySelector('#drawer').contains(document.activeElement)"))
        view.grab().save(str(args.output / 'ChatBot-settings.png'))
        from unittest.mock import patch
        update_fixture = {'status': 'available', 'version': '2.7.0', 'message': '发现 ChatBot 2.7.0，合成发布说明。',
                          'notes': '合成更新内容：改善连接与使用体验。',
                          'url': 'https://github.com/Tudor1713/ChatBot/releases/tag/v2.7.0'}
        with patch('desk.updates.check_updates', return_value=update_fixture):
            js("document.querySelector('#check-updates').click()")
            wait("document.querySelector('#editor').textContent.includes('合成更新内容')")
        check('update_dialog_has_release_notes_and_download', js("document.querySelector('#editor').textContent.includes('前往 GitHub 下载')"))
        QTest.qWait(300)
        view.grab().save(str(args.output / 'ChatBot-update.png'))
        js("document.querySelector('#editor').close()")
        js("document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}))")
        QTest.qWait(300)
        check('escape_returns_focus', js("document.activeElement===document.querySelector('#settings-button')"))
        view.resize(520, 780)
        QTest.qWait(350)
        check('compact_layout_has_no_horizontal_overflow', js('document.documentElement.scrollWidth <= innerWidth'))
        view.grab().save(str(args.output / 'ChatBot-compact.png'))
        check('no_javascript_errors', not errors)
        report['success'] = True
    except Exception as exc:
        report['error'] = str(exc)
        view.grab().save(str(args.output / 'ChatBot-failure.png'))
    finally:
        report['console_errors'] = errors
        (args.output / 'ChatBot-ui-checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        ctrl.close()
        view.close()
        temporary.cleanup()
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
