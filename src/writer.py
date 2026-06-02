import ctypes
import sys


def write_text(text):
    if sys.platform != "win32":
        return False

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    user32.OpenClipboard(None)
    user32.EmptyClipboard()

    text_bytes = (text + "\0").encode("utf-16-le")
    h = kernel32.GlobalAlloc(0x2000, len(text_bytes))
    p = kernel32.GlobalLock(h)
    ctypes.memmove(p, text_bytes, len(text_bytes))
    kernel32.GlobalUnlock(h)
    user32.SetClipboardData(13, h)
    user32.CloseClipboard()

    KEYEVENTF_KEYDOWN = 0
    KEYEVENTF_KEYUP = 2
    VK_CONTROL = 0x11
    VK_V = 0x56

    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYDOWN, 0)
    user32.keybd_event(VK_V, 0, KEYEVENTF_KEYDOWN, 0)
    user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

    return True
