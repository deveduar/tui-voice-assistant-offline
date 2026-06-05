import sys

import pytest

# ── Windows 10 ──────────────────────────────────────
# writer.py usa ctypes.windll.user32, exclusivo de Windows.
# Estos tests se saltan automáticamente en otros sistemas.
pytestmark = pytest.mark.skipif(
    sys.platform != "win32",
    reason="writer.py requiere Windows (ctypes.windll.user32)",
)


class TestWriteText:
    def test_import_writer(self):
        from src.writer import write_text, _write_via_message
        assert callable(write_text)
        assert callable(_write_via_message)

    def test_write_text_no_foreground_returns_false(self, monkeypatch):
        from src.writer import write_text
        monkeypatch.setattr(
            "src.writer.user32.GetForegroundWindow",
            lambda: 0,
        )
        result = write_text("hola")
        assert result is False

    def test_write_text_calls_sendmessage(self, monkeypatch):
        from src.writer import write_text
        sent = []

        monkeypatch.setattr(
            "src.writer.user32.GetForegroundWindow",
            lambda: 12345,
        )
        monkeypatch.setattr(
            "src.writer.user32.SendMessageW",
            lambda hwnd, msg, wparam, lparam: sent.append(chr(wparam)),
        )

        result = write_text("abc")
        assert result is True
        assert sent == ["a", "b", "c"]

    def test_write_text_handles_empty_string(self, monkeypatch):
        from src.writer import write_text
        sent = []

        monkeypatch.setattr(
            "src.writer.user32.GetForegroundWindow",
            lambda: 12345,
        )
        monkeypatch.setattr(
            "src.writer.user32.SendMessageW",
            lambda hwnd, msg, wparam, lparam: sent.append(chr(wparam)),
        )

        result = write_text("")
        assert result is True
        assert sent == []


class TestWriteTextNotWindows:
    def test_returns_false_on_linux(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "linux")
        from src.writer import write_text
        result = write_text("hola")
        assert result is False
