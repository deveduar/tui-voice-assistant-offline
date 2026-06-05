import sys
import json
import os
from functools import partial

import pytest

from src.commands import (
    Command, CommandRegistry, cargar_comandos,
    _accion_programa, _accion_url,
    ejecutar_comando,
    _log_failed_command,
)

# ── Windows 10 ──────────────────────────────────────
# Estas pruebas están diseñadas y verificadas en Windows 10.
# En Linux/macOS algunos tests pueden fallar por dependencias
# del sistema (shell=True, rutas, programas Windows).


class TestMatch:
    def test_match_basic(self, registry):
        cmd, query = registry.match("abrir notepad por favor")
        assert cmd is not None
        assert cmd.patterns[0] == "abrir notepad"
        assert query == ""

    def test_match_catchall(self, registry):
        cmd, query = registry.match("abrir chrome")
        assert cmd is not None
        assert cmd.patterns[0] == "abrir"
        assert query == "chrome"

    def test_match_case_insensitive(self, registry):
        cmd, _ = registry.match("ABRIR NOTEPAD")
        assert cmd is not None
        assert cmd.patterns[0] == "abrir notepad"

    def test_match_no_match(self, registry):
        result = registry.match("hacer cafe")
        assert result is None

    def test_match_empty_string(self, registry):
        result = registry.match("")
        assert result is None


class TestMatchDisabled:
    def test_disabled_not_matched(self, registry_disabled):
        result = registry_disabled.match("abrir notepad")
        assert result is None

    def test_disabled_returned_by_match_disabled(self, registry_disabled):
        cmd = registry_disabled.match_disabled("abrir notepad")
        assert cmd is not None
        assert cmd.patterns[0] == "abrir notepad"

    def test_enabled_not_returned_by_match_disabled(self, registry_disabled):
        cmd = registry_disabled.match_disabled("abrir calc")
        assert cmd is None


class TestMatchOrder:
    def test_specific_before_catchall(self, registry):
        cmd, _ = registry.match("abrir notepad")
        assert cmd.patterns[0] == "abrir notepad"

    def test_catchall_for_unknown(self, registry):
        cmd, _ = registry.match("abrir chrome")
        assert cmd.patterns[0] == "abrir"

    def test_notepad_with_suffix(self, registry):
        cmd, _ = registry.match("abrir notepad y algo mas")
        assert cmd.patterns[0] == "abrir notepad"


class TestMatchNeedsQuery:
    def test_query_extracted(self, registry_query):
        cmd, query = registry_query.match("buscar en google como hacer paella")
        assert cmd.patterns[0] == "buscar en google"
        assert query == "como hacer paella"

    def test_query_is_lowercased(self, registry_query):
        cmd, query = registry_query.match("buscar en google Python 3.12")
        # match() aplica text.lower() al inicio, el query hereda ese lowercase
        assert query == "python 3.12"

    def test_query_empty_when_exact(self, registry_query):
        cmd, query = registry_query.match("buscar en google")
        assert query == ""


class TestCargarComandos:
    def test_loads_commands_from_json(self, commands_json_path, monkeypatch):
        monkeypatch.setattr("src.commands._CONFIG_PATH", commands_json_path)
        reg = CommandRegistry()
        cargar_comandos(reg)
        assert len(reg.all()) > 0

    def test_creates_programa_action(self, commands_json_path, monkeypatch):
        monkeypatch.setattr("src.commands._CONFIG_PATH", commands_json_path)
        reg = CommandRegistry()
        cargar_comandos(reg)
        cmd = reg.all()[0]
        assert cmd.patterns[0] == "abrir notepad"
        assert cmd.action is not None

    def test_invalid_json_file(self):
        reg = CommandRegistry()
        cargar_comandos(reg, "/no/existe.json")
        assert len(reg.all()) == 0

    def test_disabled_commands_correctly_marked(self, commands_json_path, monkeypatch):
        monkeypatch.setattr("src.commands._CONFIG_PATH", commands_json_path)
        reg = CommandRegistry()
        cargar_comandos(reg)
        for cmd in reg.all():
            assert cmd.enabled is True


class TestAccionPrograma:
    @pytest.fixture(autouse=True)
    def _mock_popen(self, monkeypatch):
        monkeypatch.setattr(
            "src.commands.subprocess.Popen",
            lambda *a, **kw: None,
        )

    def test_no_program_returns_error(self):
        class FakeApp:
            pass
        result = _accion_programa(FakeApp(), "", program=None)
        assert "No se especifico" in result

    def test_returns_success_message(self):
        class FakeApp:
            pass
        result = _accion_programa(FakeApp(), "", program="notepad")
        assert "Abriendo" in result

    def test_expandvars_called(self, monkeypatch):
        calls = []
        monkeypatch.setattr(
            "src.commands.subprocess.Popen",
            lambda *a, **kw: calls.append(a[0]),
        )
        result = _accion_programa(None, "", program="notepad")
        assert len(calls) == 1
        assert "notepad" in calls[0]

    @pytest.mark.skipif(
        not sys.platform == "win32",
        reason="%COMSPEC% solo existe en Windows",
    )
    def test_expandvars_with_env_var(self, monkeypatch):
        calls = []
        monkeypatch.setattr(
            "src.commands.subprocess.Popen",
            lambda *a, **kw: calls.append(a[0]),
        )
        _accion_programa(None, "", program="%COMSPEC%")
        assert len(calls) == 1
        expanded = calls[0]
        assert expanded != "%COMSPEC%"
        assert expanded.endswith(".exe") or "cmd" in expanded.lower()


class TestAccionUrl:
    @pytest.fixture(autouse=True)
    def _mock_webbrowser(self, monkeypatch):
        monkeypatch.setattr("src.commands.webbrowser.open", lambda url: None)

    def test_opens_url(self, monkeypatch):
        opened = []
        monkeypatch.setattr("src.commands.webbrowser.open", lambda url: opened.append(url))
        _accion_url(None, "", url="https://example.com")
        assert len(opened) == 1
        assert opened[0] == "https://example.com"

    def test_no_url_returns_error(self):
        result = _accion_url(None, "", url=None)
        assert "No se especifico" in result

    def test_needs_query_returns_prompt_when_empty(self):
        result = _accion_url(None, "", url="https://example.com", needs_query=True)
        assert "No dijiste" in result

    def test_needs_query_with_query(self, monkeypatch):
        opened = []
        monkeypatch.setattr("src.commands.webbrowser.open", lambda url: opened.append(url))
        _accion_url(None, "python", url="https://example.com?q={query}", needs_query=True)
        assert opened[0] == "https://example.com?q=python"


class TestEjecutarComando:
    @pytest.fixture(autouse=True)
    def _mock_log(self, monkeypatch):
        monkeypatch.setattr("src.commands._log_failed_command", lambda *a, **kw: None)

    def test_empty_text_returns_empty(self):
        assert ejecutar_comando("") == ""

    def test_whitespace_text_returns_empty(self):
        assert ejecutar_comando("   ") == ""

    def test_unrecognized_returns_message(self):
        result = ejecutar_comando("hacer algo imposible")
        assert "no reconocido" in result

    def test_unrecognized_with_app(self):
        result = ejecutar_comando("xyzzy no existe")
        assert "no reconocido" in result
