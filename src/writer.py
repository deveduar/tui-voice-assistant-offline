import ctypes
import logging
import sys
from ctypes import wintypes

logger = logging.getLogger("writer")
handler = logging.FileHandler("writer_debug.log", mode="w", encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

WM_CHAR = 0x0102


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
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


user32 = ctypes.windll.user32

user32.SendInput.argtypes = [wintypes.UINT, ctypes.c_void_p, ctypes.c_int]
user32.SendInput.restype = wintypes.UINT
user32.GetForegroundWindow.argtypes = []
user32.GetForegroundWindow.restype = wintypes.HWND
user32.SendMessageW.argtypes = [wintypes.HANDLE, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.SendMessageW.restype = ctypes.c_ssize_t


def _write_via_message(hwnd, text):
    for ch in text:
        user32.SendMessageW(hwnd, WM_CHAR, ord(ch), 0)
    logger.debug("sendmessage sent %d chars", len(text))


def write_text(text):
    if sys.platform != "win32":
        return False

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        logger.debug("write_text no foreground window")
        return False

    logger.debug("write_text text='%s'", text[:50])
    _write_via_message(hwnd, text)
    return True
