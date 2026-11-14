"""Frameless main window: the page draws the title bar, Windows keeps the frame behaviour.

On Windows the native caption is removed through WM_NCCALCSIZE while the window
keeps WS_CAPTION/WS_THICKFRAME, so snapping, the minimise animation, the DWM
shadow and edge resizing still come from the OS. The page asks for moves,
minimise, maximise and close through the ``shell`` web-channel object.
Other platforms keep their native title bar and no ``shell`` object is exposed.
"""
from __future__ import annotations

import sys

from PySide6.QtCore import QObject, Qt, Signal, Slot

IS_WINDOWS = sys.platform == 'win32'

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL('user32', use_last_error=True)
    dwmapi = ctypes.WinDLL('dwmapi')

    GWL_STYLE = -16
    WS_CAPTION, WS_THICKFRAME, WS_SYSMENU = 0x00C00000, 0x00040000, 0x00080000
    WS_MINIMIZEBOX, WS_MAXIMIZEBOX = 0x00020000, 0x00010000
    SWP_FRAMECHANGED_FLAGS = 0x0001 | 0x0002 | 0x0004 | 0x0010 | 0x0020  # NOSIZE|NOMOVE|NOZORDER|NOACTIVATE|FRAMECHANGED
    WM_NCCALCSIZE, WM_NCHITTEST = 0x0083, 0x0084
    HTLEFT, HTRIGHT, HTTOP, HTTOPLEFT, HTTOPRIGHT, HTBOTTOM, HTBOTTOMLEFT, HTBOTTOMRIGHT = 10, 11, 12, 13, 14, 15, 16, 17
    MONITOR_DEFAULTTONEAREST = 2

    class MARGINS(ctypes.Structure):
        _fields_ = [('left', ctypes.c_int), ('right', ctypes.c_int), ('top', ctypes.c_int), ('bottom', ctypes.c_int)]

    class NCCALCSIZE_PARAMS(ctypes.Structure):
        _fields_ = [('rgrc', wintypes.RECT * 3), ('lppos', ctypes.c_void_p)]

    class MONITORINFO(ctypes.Structure):
        _fields_ = [('cbSize', wintypes.DWORD), ('rcMonitor', wintypes.RECT), ('rcWork', wintypes.RECT), ('dwFlags', wintypes.DWORD)]

    user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
    user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
    user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
    user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.IsZoomed.argtypes = [wintypes.HWND]
    user32.MonitorFromWindow.restype = wintypes.HMONITOR
    user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
    user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFO)]
    dwmapi.DwmExtendFrameIntoClientArea.argtypes = [wintypes.HWND, ctypes.POINTER(MARGINS)]


def make_frameless(window) -> bool:
    """Hide the native caption of a QWidget window. Returns False where unsupported."""
    if not IS_WINDOWS:
        return False
    window.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
    window._frameless = True
    return True


def restore_frame_styles(window) -> None:
    """Give a frameless window back the styles that make it behave like a normal window.

    Qt rewrites GWL_STYLE whenever window flags change (for example "always on top"),
    so call this after every flag change as well as after the first show().
    """
    if not (IS_WINDOWS and getattr(window, '_frameless', False)):
        return
    hwnd = int(window.winId())
    style = user32.GetWindowLongPtrW(hwnd, GWL_STYLE)
    user32.SetWindowLongPtrW(hwnd, GWL_STYLE, style | WS_CAPTION | WS_THICKFRAME | WS_SYSMENU | WS_MINIMIZEBOX | WS_MAXIMIZEBOX)
    # A one-pixel sheet of DWM frame keeps the system shadow around the borderless window.
    dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(MARGINS(0, 0, 0, 1)))
    user32.SetWindowPos(hwnd, None, 0, 0, 0, 0, SWP_FRAMECHANGED_FLAGS)


def native_frame_event(window, event_type, message, border: int = 6):
    """Handle the two messages that turn the client area into the whole window.

    Returns ``(handled, result)``; ``handled`` is False when Qt should process the message.
    """
    if not (IS_WINDOWS and getattr(window, '_frameless', False)):
        return False, 0
    if bytes(event_type) != b'windows_generic_MSG':
        return False, 0
    msg = wintypes.MSG.from_address(int(message))
    if msg.message == WM_NCCALCSIZE and msg.wParam:
        if user32.IsZoomed(msg.hWnd):
            # A maximised captioned window overhangs the monitor by its frame; clamp it to the work area.
            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(MONITORINFO)
            monitor = user32.MonitorFromWindow(msg.hWnd, MONITOR_DEFAULTTONEAREST)
            if monitor and user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
                params = NCCALCSIZE_PARAMS.from_address(msg.lParam)
                params.rgrc[0] = info.rcWork
        return True, 0
    if msg.message == WM_NCHITTEST:
        if window.isMaximized() or window.isFullScreen():
            return False, 0
        x = ctypes.c_short(msg.lParam & 0xFFFF).value
        y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value
        rect = wintypes.RECT()
        user32.GetWindowRect(msg.hWnd, ctypes.byref(rect))
        edge = max(4, round(border * window.devicePixelRatioF()))
        left, right = x < rect.left + edge, x >= rect.right - edge
        top, bottom = y < rect.top + edge, y >= rect.bottom - edge
        hit = (HTTOPLEFT if top and left else HTTOPRIGHT if top and right else
               HTBOTTOMLEFT if bottom and left else HTBOTTOMRIGHT if bottom and right else
               HTLEFT if left else HTRIGHT if right else HTTOP if top else HTBOTTOM if bottom else 0)
        if hit:
            return True, hit
    return False, 0


class WindowShell(QObject):
    """Window commands for the page-drawn title bar (registered as ``shell``)."""

    maximizedChanged = Signal(bool)

    def __init__(self, window):
        super().__init__(window)
        self._window = window

    @Slot()
    def minimize(self):
        self._window.showMinimized()

    @Slot()
    def toggleMaximize(self):
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            self._window.showMaximized()

    @Slot()
    def close(self):
        self._window.close()

    @Slot()
    def startMove(self):
        handle = self._window.windowHandle()
        if handle is not None:
            handle.startSystemMove()

    @Slot(result=bool)
    def isMaximized(self):
        return self._window.isMaximized()
