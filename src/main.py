"""ChatBot — native Windows shell, offline UI, local capture and configurable model API."""
from __future__ import annotations

import argparse
import multiprocessing
import os
import sys
from pathlib import Path


def locations():
    if getattr(sys, 'frozen', False):
        root = Path(sys.executable).parent
        assets = Path(sys._MEIPASS)
    else:
        root = Path(__file__).resolve().parents[1]
        assets = root
    return root, assets


def main():
    multiprocessing.freeze_support()
    parser = argparse.ArgumentParser(description='ChatBot 实时微信对话助手')
    parser.add_argument('--demo', action='store_true', help='明确标记的合成数据界面预览，不读取微信，不调用模型')
    parser.add_argument('--screenshot', help='Save the rendered application UI then exit (demo only).')
    parser.add_argument('--quit-after', type=int, default=0, help='Exit after N seconds for startup smoke testing.')
    parser.add_argument('--data-dir', help='Override portable data directory.')
    parser.add_argument('--compact', action='store_true')
    parser.add_argument('--self-test-report', help='Run synthetic, offline portable diagnostics and write a JSON report.')
    parser.add_argument('--start-capture', action='store_true', help='Start capture immediately after opening the configured app.')
    parser.add_argument('--status-report', help='Write aggregate status only, without messages, titles or keys.')
    parser.add_argument('--safe-start', action='store_true', help='Open with automatic analysis and sending disabled for this launch only.')
    args = parser.parse_args()
    if args.self_test_report:
        from desk.selftest import run_self_test
        return run_self_test(args.self_test_report)
    if args.screenshot and not args.demo:
        parser.error('--screenshot requires --demo to avoid saving private conversation screenshots.')
    root, assets = locations()
    from desk.platforms import data_directory, keep_responsive_in_background
    keep_responsive_in_background()
    data = Path(args.data_dir) if args.data_dir else data_directory(root, args.demo)
    data.mkdir(parents=True, exist_ok=True)
    os.environ['CHATBOT_DATA_DIR'] = str(data.resolve())
    os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS', '--disable-logging')

    from PySide6.QtCore import QTimer, QUrl, Qt
    from PySide6.QtGui import QAction, QIcon, QDesktopServices
    from PySide6.QtWidgets import QApplication, QMainWindow, QMenu, QSystemTrayIcon
    from PySide6.QtWebChannel import QWebChannel
    from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from desk.controller import Controller
    from desk.bridge import Bridge
    from desk.frameless import WindowShell, make_frameless, native_frame_event, restore_frame_styles

    app = QApplication(sys.argv[:1])
    from desk.instance import SingleInstance
    instance = SingleInstance(data)
    if not instance.acquire():
        return 0
    app.aboutToQuit.connect(instance.close)
    from desk.version import VERSION
    app.setApplicationName('ChatBot')
    app.setOrganizationName('ChatBot')
    app.setApplicationVersion(VERSION)
    icon = QIcon(str(assets / 'ui' / 'icon.ico'))
    app.setWindowIcon(icon)
    controller = Controller(data)
    if args.safe_start or args.demo:
        controller.auto_resume_on_launch = False
        controller.store.config['auto_analyze'] = False
        controller.store.config['stickers_auto'] = False
    if args.status_report:
        def record_status(snapshot):
            session = snapshot.get('current_session') or {}
            analysis = snapshot.get('analysis') or {}
            messages = session.get('messages') or []
            summary = {'capture': snapshot['status']['capture'], 'analysis': snapshot['status']['analysis'],
                       'detail': snapshot['status']['detail'],
                       'message_count': len(messages), 'sides': sorted({m.get('side', '') for m in messages}),
                       'candidate_count': len(analysis.get('candidates') or []),
                       'judgment_count': len(analysis.get('answers') or {}),
                       'latency_ms': analysis.get('latency_ms'), 'warning': analysis.get('warning'),
                       'error': snapshot['status']['last_error']}
            import json
            Path(args.status_report).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
        controller.stateChanged.connect(record_status)

    class LocalPage(QWebEnginePage):
        def acceptNavigationRequest(self, url, navtype, is_main_frame):
            if is_main_frame and url.scheme() not in ('file', 'qrc', 'about'):
                if navtype == QWebEnginePage.NavigationType.NavigationTypeLinkClicked and url.scheme() in ('https', 'http'):
                    QDesktopServices.openUrl(url)
                return False
            return super().acceptNavigationRequest(url, navtype, is_main_frame)

        def javaScriptConsoleMessage(self, level, message, line, source):
            # UI exceptions omit full message to avoid accidental user content in console logs.
            if level == QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel:
                print(f'UI error at line {line}', file=sys.stderr)

    class Window(QMainWindow):
        def closeEvent(self, event):
            controller.close()
            event.accept()

        def nativeEvent(self, event_type, message):
            handled, result = native_frame_event(self, event_type, message)
            return (True, result) if handled else super().nativeEvent(event_type, message)

        def changeEvent(self, event):
            super().changeEvent(event)
            if event.type() == event.Type.WindowStateChange and getattr(self, '_shell', None):
                self._shell.maximizedChanged.emit(self.isMaximized())

    window = Window()
    def activate_window():
        if window.isMinimized():
            window.showNormal()
        else:
            window.show()
        window.raise_()
        window.activateWindow()
    instance.activated.connect(activate_window)
    window.setWindowTitle('ChatBot')
    window.setWindowIcon(icon)
    window.resize(1280, 850)
    window.setMinimumSize(500, 640)
    window.setStyleSheet('QMainWindow { background: #f2ece0; }')
    shell = window._shell = WindowShell(window)
    frameless = make_frameless(window)
    view = QWebEngineView(window)
    # Off-the-record profile: no browser credentials, cookies or chat cache on disk.
    profile = QWebEngineProfile(view)
    profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
    profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
    page = LocalPage(profile, view)
    page.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)
    page.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, False)
    view.setPage(page)
    view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
    bridge = Bridge(controller)
    channel = QWebChannel(page)
    channel.registerObject('bridge', bridge)
    if frameless:
        channel.registerObject('shell', shell)
    page.setWebChannel(channel)
    window.setCentralWidget(view)

    tray = QSystemTrayIcon(icon, window)
    menu = QMenu()
    for label, fn in [('打开 ChatBot', activate_window),
                      ('暂停采集', lambda: controller.handle('pause_capture', {})),
                      ('退出', app.quit)]:
        action = QAction(label, menu)
        action.triggered.connect(fn)
        menu.addAction(action)
    tray.setContextMenu(menu)
    tray.setToolTip('ChatBot · 发送由你决定')
    tray.activated.connect(lambda reason: activate_window() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
    tray.show()

    def window_action(kind, value):
        if kind == 'compact':
            if window.isMaximized():
                window.showNormal()
            window.resize(520, 780) if value else window.resize(1280, 850)
            window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, bool(value) or controller.store.config['always_on_top'])
            window.show()
            restore_frame_styles(window)
        elif kind == 'always_on_top':
            window.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, bool(value))
            window.show()
            restore_frame_styles(window)
        elif kind == 'quit':
            app.quit()
    controller.windowAction.connect(window_action)
    app.aboutToQuit.connect(controller.close)
    app.aboutToQuit.connect(tray.hide)

    url = QUrl.fromLocalFile(str(assets / 'ui' / 'index.html'))
    if args.demo:
        # Screenshot mode targets the actual workspace; normal demo launch
        # still plays the complete cinematic introduction.
        url.setQuery('demo=1&intro=0' if args.screenshot else 'demo=1')
    view.load(url)
    window.show()
    restore_frame_styles(window)
    if args.start_capture and not args.demo:
        QTimer.singleShot(1200, lambda: controller.handle('start_capture', {}))
    if not args.demo and not args.safe_start:
        def check_release():
            if not controller.closed and controller.store.config.get('updates_auto', True):
                controller.check_updates()
        QTimer.singleShot(12000, check_release)
        release_timer = QTimer(window)
        release_timer.setInterval(6 * 60 * 60 * 1000)
        release_timer.timeout.connect(check_release)
        release_timer.start()
    if args.compact:
        window_action('compact', True)
    elif controller.store.config['always_on_top']:
        window_action('always_on_top', True)
    if args.screenshot:
        def save_screen(ok):
            if not ok:
                app.exit(2)
                return
            def save():
                target = Path(args.screenshot)
                target.parent.mkdir(parents=True, exist_ok=True)
                success = view.grab().save(str(target))
                print('UI screenshot saved' if success else 'UI screenshot failed')
                app.exit(0 if success else 3)
            QTimer.singleShot(2000, save)
        view.loadFinished.connect(save_screen)
    if args.quit_after:
        QTimer.singleShot(args.quit_after * 1000, app.quit)
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
