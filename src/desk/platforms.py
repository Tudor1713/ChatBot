"""Desktop capabilities and writable application locations."""
from pathlib import Path
import sys


def capabilities(platform=None):
    platform = platform or sys.platform
    windows = platform == 'win32'
    return {'platform': platform, 'name': 'macOS' if platform == 'darwin' else 'Windows' if windows else 'Linux',
            'native_capture': windows, 'native_database': windows or platform == 'darwin', 'send': windows,
            'imports': True, 'media': True, 'moments': True,
            'credentials': 'Keychain' if platform == 'darwin' else 'DPAPI' if windows else 'session'}


def keep_responsive_in_background(platform=None):
    """Windows：退出后台节能降频，并把「低于正常/空闲」优先级恢复为正常。

    计划任务启动的程序默认是「低于正常」优先级，叠加后台节能降频后，发送前的输入框
    OCR 会从约 0.05 秒变成 3 秒以上，核验画面因此判为过期而拒发。只调整本进程自身。
    返回实际做了哪些调整，失败时静默跳过。
    """
    if (platform or sys.platform) != 'win32':
        return {}
    import ctypes

    class _Throttling(ctypes.Structure):
        _fields_ = [('Version', ctypes.c_ulong), ('ControlMask', ctypes.c_ulong), ('StateMask', ctypes.c_ulong)]

    done = {}
    try:
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        handle = ctypes.c_void_p(kernel.GetCurrentProcess())
        # ProcessPowerThrottling=4；ControlMask=EXECUTION_SPEED、StateMask=0 表示不要降频。
        state = _Throttling(1, 0x1, 0x0)
        done['throttling_off'] = bool(kernel.SetProcessInformation(handle, 4, ctypes.byref(state), ctypes.sizeof(state)))
        if kernel.GetPriorityClass(handle) in (0x40, 0x4000):  # IDLE / BELOW_NORMAL
            done['priority_normal'] = bool(kernel.SetPriorityClass(handle, 0x20))
    except (AttributeError, OSError):
        pass
    return done


def data_directory(root, demo=False):
    if demo:
        if sys.platform == 'darwin':
            return Path.home() / 'Library/Caches/ChatBot/demo'
        return Path(root) / 'work/demo-data'
    if sys.platform == 'darwin':
        return Path.home() / 'Library/Application Support/ChatBot'
    return Path(root) / 'data'


def keychain_service(directory):
    import hashlib
    identity = str(Path(directory).resolve()).encode('utf-8')
    return 'ai.chatbot.desktop.' + hashlib.sha256(identity).hexdigest()[:32]


def keychain_get(directory):
    from keyring.backends.macOS import Keyring
    return Keyring().get_password(keychain_service(directory), 'credentials') or '{}'


def keychain_set(directory, value):
    from keyring.backends.macOS import Keyring
    Keyring().set_password(keychain_service(directory), 'credentials', value)
