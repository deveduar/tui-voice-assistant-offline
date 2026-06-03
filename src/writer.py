import ctypes
import logging
import sys
import time
from ctypes import wintypes

logger = logging.getLogger("writer")
handler = logging.FileHandler("writer_debug.log", mode="w", encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

WM_CHAR = 0x0102
VK_CONTROL = 0x11
VK_V = 0x56
KEYEVENTF_KEYDOWN = 0
KEYEVENTF_KEYUP = 2
INPUT_KEYBOARD = 1
CF_UNICODETEXT = 13
GMEM_MOVABLE = 0x0002
GMEM_ZEROINIT = 0x0040


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", _INPUT_UNION),
    ]


user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

user32.SendInput.argtypes = [wintypes.UINT, ctypes.c_void_p, ctypes.c_int]
user32.SendInput.restype = wintypes.UINT
user32.GetForegroundWindow.argtypes = []
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetWindowTextW.argtypes = [wintypes.HWND, ctypes.c_wchar_p, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.GetClassNameW.argtypes = [wintypes.HWND, ctypes.c_wchar_p, ctypes.c_int]
user32.GetClassNameW.restype = ctypes.c_int
user32.SendMessageW.argtypes = [wintypes.HANDLE, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.SendMessageW.restype = ctypes.c_ssize_t
kernel32.GetLastError.argtypes = []
kernel32.GetLastError.restype = wintypes.DWORD

user32.OpenClipboard.argtypes = [wintypes.HANDLE]
user32.OpenClipboard.restype = wintypes.BOOL
user32.EmptyClipboard.argtypes = []
user32.EmptyClipboard.restype = wintypes.BOOL
user32.CloseClipboard.argtypes = []
user32.CloseClipboard.restype = wintypes.BOOL
user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
user32.SetClipboardData.restype = wintypes.HANDLE

kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = wintypes.HANDLE
kernel32.GlobalLock.argtypes = [wintypes.HANDLE]
kernel32.GlobalLock.restype = wintypes.LPVOID
kernel32.GlobalUnlock.argtypes = [wintypes.HANDLE]
kernel32.GlobalUnlock.restype = wintypes.BOOL
kernel32.GlobalFree.argtypes = [wintypes.HANDLE]
kernel32.GlobalFree.restype = wintypes.HANDLE


def _debug_foreground():
    hwnd = user32.GetForegroundWindow()
    title = ctypes.c_wchar_p(" " * 256)
    cls = ctypes.c_wchar_p(" " * 256)
    user32.GetWindowTextW(hwnd, title, 256)
    user32.GetClassNameW(hwnd, cls, 256)
    logger.debug("foreground hwnd=%s class=%s title=%s", hwnd, cls.value, title.value)
    return hwnd


def _send_input(inp):
    ret = user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
    err = kernel32.GetLastError()
    if ret == 0:
        logger.debug("SendInput FAILED ret=%d err=%d", ret, err)
    else:
        logger.debug("SendInput OK ret=%d err=%d", ret, err)
    return ret


def _paste_clipboard():
    inp_down_ctl = INPUT(INPUT_KEYBOARD, _INPUT_UNION(ki=KEYBDINPUT(VK_CONTROL, 0, KEYEVENTF_KEYDOWN, 0, 0)))
    inp_down_v = INPUT(INPUT_KEYBOARD, _INPUT_UNION(ki=KEYBDINPUT(VK_V, 0, KEYEVENTF_KEYDOWN, 0, 0)))
    inp_up_v = INPUT(INPUT_KEYBOARD, _INPUT_UNION(ki=KEYBDINPUT(VK_V, 0, KEYEVENTF_KEYUP, 0, 0)))
    inp_up_ctl = INPUT(INPUT_KEYBOARD, _INPUT_UNION(ki=KEYBDINPUT(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0, 0)))
    for inp in (inp_down_ctl, inp_down_v, inp_up_v, inp_up_ctl):
        _send_input(inp)


def _set_clipboard(text):
    for attempt in range(3):
        if user32.OpenClipboard(None):
            break
        time.sleep(0.05)
    else:
        logger.debug("clipboard OpenClipboard failed after 3 attempts")
        return False
    try:
        user32.EmptyClipboard()
        text_bytes = (text + "\0").encode("utf-16-le")
        h = kernel32.GlobalAlloc(GMEM_MOVABLE | GMEM_ZEROINIT, len(text_bytes))
        if not h:
            logger.debug("clipboard GlobalAlloc failed")
            return False
        p = kernel32.GlobalLock(h)
        if not p:
            logger.debug("clipboard GlobalLock failed")
            kernel32.GlobalFree(h)
            return False
        ctypes.memmove(p, text_bytes, len(text_bytes))
        kernel32.GlobalUnlock(h)
        user32.SetClipboardData(CF_UNICODETEXT, h)
        logger.debug("clipboard OK wrote %d chars", len(text))
    finally:
        user32.CloseClipboard()
    return True


def _write_via_message(hwnd, text):
    for i, ch in enumerate(text):
        ret = user32.SendMessageW(hwnd, WM_CHAR, ord(ch), 0)
        if ret == 0:
            logger.debug("SendMessageW WM_CHAR returned 0 at char %d '%s'", i, ch)
            return False
        if i == 0:
            logger.debug("SendMessageW first char OK")
    logger.debug("SendMessageW sent %d chars OK", len(text))
    return True


def _write_via_paste(text):
    if not _set_clipboard(text):
        return False
    _paste_clipboard()
    logger.debug("clipboard paste sent %d chars", len(text))
    return True


def write_text(text):
    if sys.platform != "win32":
        logger.debug("write_text not win32, skip")
        return False

    logger.debug("write_text text='%s' len=%d", text[:50], len(text))

    hwnd = _debug_foreground()
    if not hwnd:
        logger.debug("write_text no foreground window, skip")
        return False

    if _write_via_message(hwnd, text):
        logger.debug("write_text done via SendMessageW")
        return True

    logger.debug("write_text SendMessageW failed, falling back to clipboard paste")
    return _write_via_paste(text)
