"""Paste into a freshly verified WeChat input box. Never sends a message."""
import ctypes
from ctypes import wintypes as w
import time

from app.winapi import libraries, process_name, window_title


def set_clipboard(text):
    u, k, _ = libraries()
    data = str(text).encode("utf-16-le") + b"\0\0"
    for _ in range(10):
        if not u.OpenClipboard(None):
            time.sleep(.03)
            continue
        try:
            if not u.EmptyClipboard():
                raise RuntimeError("无法写入剪贴板")
            handle = k.GlobalAlloc(0x2, len(data))
            if not handle:
                raise RuntimeError("剪贴板内存分配失败")
            pointer = k.GlobalLock(handle)
            if not pointer:
                k.GlobalFree(handle)
                raise RuntimeError("剪贴板内存锁定失败")
            ctypes.memmove(pointer, data, len(data))
            k.GlobalUnlock(handle)
            if not u.SetClipboardData(13, handle):
                k.GlobalFree(handle)
                raise RuntimeError("无法设置剪贴板文本")
            return
        finally:
            u.CloseClipboard()
    raise RuntimeError("剪贴板正在被占用，请稍后重试")


LOCKED_MESSAGE = "电脑处于锁屏状态，无法操作微信窗口"


def _user32():
    """额外用到的几个 user32 函数，单独声明参数类型（句柄按指针传，x64 安全）。"""
    u = ctypes.WinDLL("user32", use_last_error=True)
    u.OpenInputDesktop.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    u.OpenInputDesktop.restype = ctypes.c_void_p
    u.SwitchDesktop.argtypes = [ctypes.c_void_p]
    u.SwitchDesktop.restype = w.BOOL
    u.CloseDesktop.argtypes = [ctypes.c_void_p]
    u.CloseDesktop.restype = w.BOOL
    u.WindowFromPoint.argtypes = [w.POINT]
    u.WindowFromPoint.restype = ctypes.c_void_p
    u.GetAncestor.argtypes = [ctypes.c_void_p, w.UINT]
    u.GetAncestor.restype = ctypes.c_void_p
    u.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                               ctypes.c_int, ctypes.c_int, w.UINT]
    u.SetWindowPos.restype = w.BOOL
    u.SwitchToThisWindow.argtypes = [ctypes.c_void_p, w.BOOL]
    u.SwitchToThisWindow.restype = None
    return u


def session_locked():
    """锁屏/安全桌面时，当前输入桌面无法切换；此时任何窗口操作和按键都到不了微信。"""
    try:
        u = _user32()
        desk = u.OpenInputDesktop(0, False, 0x0100)  # DESKTOP_SWITCHDESKTOP
        if not desk:
            return True
        try:
            return not u.SwitchDesktop(desk)
        finally:
            u.CloseDesktop(desk)
    except (AttributeError, OSError):
        return False


def focus_window(hwnd):
    """把窗口切到前台；返回是否成功。锁屏时直接报错（之后的点击和按键都无效）。"""
    u, k, _ = libraries()
    if u.GetForegroundWindow() == hwnd:
        return True
    if session_locked():
        raise RuntimeError(LOCKED_MESSAGE)
    fg = u.GetForegroundWindow()
    thread_id = u.GetWindowThreadProcessId(fg, None) if fg else 0
    own = k.GetCurrentThreadId()
    attached = bool(thread_id and u.AttachThreadInput(own, thread_id, True))
    try:
        u.SetForegroundWindow(hwnd)
    finally:
        if attached:
            u.AttachThreadInput(own, thread_id, False)
    time.sleep(.15)
    if u.GetForegroundWindow() != hwnd:
        # 后台进程受前台锁限制：模拟一次 Alt 按键可获得切换前台的许可。
        u.keybd_event(0x12, 0, 0, 0)
        u.keybd_event(0x12, 0, 2, 0)
        u.BringWindowToTop(hwnd)
        u.SetForegroundWindow(hwnd)
        time.sleep(.2)
    if u.GetForegroundWindow() != hwnd:
        try:
            _user32().SwitchToThisWindow(hwnd, True)
            time.sleep(.25)
        except (AttributeError, OSError):
            pass
    return u.GetForegroundWindow() == hwnd


def safe_click(hwnd, sx, sy):
    """在屏幕坐标点一下，但只在这一点确实落在 hwnd 上时才点。

    先把微信临时置顶（不抢焦点），用 WindowFromPoint 核对落点属于微信，再发真实鼠标点击——
    由真实输入激活窗口不受前台锁限制。点完立即取消置顶。落点被别的窗口挡住就拒绝点击。
    """
    u, _, _ = libraries()
    x32 = _user32()
    flags = 0x0001 | 0x0002 | 0x0010  # NOSIZE | NOMOVE | NOACTIVATE
    x32.SetWindowPos(hwnd, ctypes.c_void_p(-1), 0, 0, 0, 0, flags)  # HWND_TOPMOST
    try:
        time.sleep(.08)
        hit = x32.WindowFromPoint(w.POINT(int(sx), int(sy)))
        root = x32.GetAncestor(hit, 2) if hit else None  # GA_ROOT
        if not root or int(root) != int(hwnd):
            raise RuntimeError("微信窗口被其他窗口挡住，已取消点击")
        old = w.POINT()
        u.GetCursorPos(ctypes.byref(old))
        try:
            u.SetCursorPos(int(sx), int(sy))
            u.mouse_event(0x2, 0, 0, 0, 0)
            u.mouse_event(0x4, 0, 0, 0, 0)
        finally:
            u.SetCursorPos(old.x, old.y)
    finally:
        x32.SetWindowPos(hwnd, ctypes.c_void_p(-2), 0, 0, 0, 0, flags)  # HWND_NOTOPMOST
    time.sleep(.15)


def _chord(*keys):
    """按下组合键（依序按下、逆序抬起）。"""
    u, _, _ = libraries()
    for key in keys:
        u.keybd_event(key, 0, 0, 0)
    for key in reversed(keys):
        u.keybd_event(key, 0, 2, 0)


def click_chat_row(hwnd, x, y):
    """点击左侧会话列表中的一点（截图像素坐标）以打开该会话；不输入任何文字。

    微信 4.x 的搜索结果是独立浮层，原先「Ctrl+F 搜索后回车」打不开会话，还可能弹出搜一搜。
    调用方必须在点击后重新用 OCR 严格核验会话标题。
    """
    u, _, d = libraries()
    focus_window(hwnd)  # 失败也继续：下面的真实点击本身会激活微信；锁屏会在这里报错
    rect = w.RECT()
    if d.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(rect), ctypes.sizeof(rect)) != 0:
        if not u.GetWindowRect(hwnd, ctypes.byref(rect)):
            raise RuntimeError("无法定位微信会话列表")
    sx, sy = rect.left + int(x), rect.top + int(y)
    if not (rect.left < sx < rect.right and rect.top < sy < rect.bottom):
        raise RuntimeError("会话列表位置无法确认")
    safe_click(hwnd, sx, sy)
    time.sleep(.45)


def fill(hwnd, area, text, verify=None, expected_window_title=None):
    """verify must OCR a recent frame and raise on any changed conversation."""
    if not callable(verify):
        raise RuntimeError("缺少最新会话核验，已拒绝填入")
    if not str(text).strip():
        raise RuntimeError("回复内容为空")
    u, k, d = libraries()
    expected_window_title = expected_window_title or window_title(hwnd)

    def check():
        if not u.IsWindow(hwnd) or not u.IsWindowVisible(hwnd) or u.IsIconic(hwnd):
            raise RuntimeError("微信窗口不可用，请打开目标聊天后重试")
        if process_name(hwnd) not in ("wechat.exe", "weixin.exe"):
            raise RuntimeError("窗口已改变，已拒绝填入")
        if window_title(hwnd) != expected_window_title:
            raise RuntimeError("微信窗口标题已改变，已拒绝填入")
        return verify()

    check()
    # 切前台失败也继续：下面点输入框是真实点击，会激活微信（只在落点确属微信时才点）。
    focus_window(hwnd)
    fresh_area = check()
    area = fresh_area or area
    rect = w.RECT()
    if d.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(rect), ctypes.sizeof(rect)) != 0:
        if not u.GetWindowRect(hwnd, ctypes.byref(rect)):
            raise RuntimeError("无法定位微信输入框")
    x0, _, x1, y1 = area[:4]
    if x1 - x0 < 160 or rect.bottom - rect.top - y1 < 85:
        raise RuntimeError("输入区域过小，已拒绝填入；请放大微信窗口")
    x, y = rect.left + x0 + 60, rect.top + y1 + 40
    if not (rect.left < x < rect.right and rect.top < y < rect.bottom - 35):
        raise RuntimeError("输入框位置无法确认")
    check()
    set_clipboard(text)
    safe_click(hwnd, x, y)
    check()
    if u.GetForegroundWindow() != hwnd:
        raise RuntimeError("焦点已离开微信，已取消填入")
    for key in (0x23, 0x56):
        u.keybd_event(0x11, 0, 0, 0)
        try:
            u.keybd_event(key, 0, 0, 0)
            u.keybd_event(key, 0, 2, 0)
        finally:
            u.keybd_event(0x11, 0, 2, 0)
    return {"success": True, "message": "已填入微信输入框，请检查后手动发送"}
