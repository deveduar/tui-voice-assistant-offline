import os
import json
import sys

import pytest

from src.config import (
    load_config, save_config, get_config,
    scan_models, resolve_model_path,
    PROJECT_ROOT, CONFIG_PATH,
)

# ── Windows 10 ──────────────────────────────────────
# Estas pruebas están diseñadas y verificadas en Windows 10.
# En Linux/macOS las rutas y modelos pueden diferir.


class TestLoadConfig:
    def test_load_returns_dict(self, temp_config_path):
        cfg = load_config()
        assert isinstance(cfg, dict)

    def test_load_nonexistent_returns_empty(self):
        old = CONFIG_PATH
        import src.config as cfg_mod
        cfg_mod.CONFIG_PATH = "/no/existe/config.json"
        try:
            cfg = load_config()
            assert cfg == {}
        finally:
            cfg_mod.CONFIG_PATH = old

    def test_load_invalid_json_returns_empty(self):
        old = CONFIG_PATH
        import src.config as cfg_mod
        invalid = os.path.join(os.path.dirname(CONFIG_PATH), "_test_invalid.json")
        cfg_mod.CONFIG_PATH = invalid
        try:
            with open(invalid, "w") as f:
                f.write("{not json}")
            cfg = load_config()
            assert cfg == {}
        finally:
            cfg_mod.CONFIG_PATH = old
            try:
                os.unlink(invalid)
            except OSError:
                pass


class TestSaveConfig:
    def test_save_and_reload(self, temp_config_path):
        data = {"mic_index": 5, "theme": "dracula"}
        save_config(data)
        loaded = load_config()
        assert loaded["mic_index"] == 5
        assert loaded["theme"] == "dracula"

    def test_save_preserves_all_keys(self, temp_config_path):
        data = {"a": 1, "b": "two", "c": [3, 4]}
        save_config(data)
        loaded = load_config()
        assert loaded == data


class TestGetConfig:
    def test_returns_defaults_for_missing_keys(self, temp_config_path):
        cfg = get_config()
        assert "mic_index" in cfg
        assert "model_name" in cfg
        assert "assistant_name" in cfg
        assert "require_name" in cfg
        assert "disabled_commands" in cfg
        assert "theme" in cfg

    def test_preserves_existing_values(self, temp_config_path):
        save_config({"mic_index": 99})
        cfg = get_config()
        assert cfg["mic_index"] == 99

    def test_default_assistant_name(self, temp_config_path):
        cfg = get_config()
        assert cfg["assistant_name"] == "flex"


class TestResolveModelPath:
    def test_absolute_path_unchanged(self):
        abspath = os.path.abspath(".")
        result = resolve_model_path(abspath)
        assert result == abspath

    def test_relative_path_prepended(self):
        result = resolve_model_path("vosk-model-small-es-0.42")
        assert result == os.path.join(
            PROJECT_ROOT, "vosk-model-small-es-0.42"
        )


class TestScanModels:
    def test_returns_list(self, monkeypatch):
        monkeypatch.setattr("src.config.os.listdir", lambda _: [
            "vosk-model-small-es-0.42",
            "vosk-model-es-0.42",
            "main.py",
            "README.md",
        ])
        monkeypatch.setattr("src.config.os.path.isdir", lambda p: "vosk-model" in p)
        models = scan_models()
        assert isinstance(models, list)
        assert len(models) == 2

    def test_returns_absolute_paths(self, monkeypatch):
        monkeypatch.setattr("src.config.os.listdir", lambda _: [
            "vosk-model-small-es-0.42",
        ])
        monkeypatch.setattr("src.config.os.path.isdir", lambda p: True)
        models = scan_models()
        assert len(models) == 1
        assert os.path.isabs(models[0])

    def test_fallback_when_oserror(self, monkeypatch):
        monkeypatch.setattr("src.config.os.listdir", lambda _: (_ for _ in ()).throw(OSError))
        models = scan_models()
        assert isinstance(models, list)
        assert len(models) >= 1


class TestModelNameComparison:
    def test_relative_and_absolute_resolve_same(self):
        from src.config import PROJECT_ROOT
        relative = "vosk-model-small-es-0.42"
        absolute = os.path.join(PROJECT_ROOT, relative)
        assert os.path.abspath(relative) == os.path.abspath(absolute)

    def test_os_path_abspath_matches_stored_absolute(self, monkeypatch):
        from src.config import PROJECT_ROOT
        stored = "vosk-model-small-es-0.42"
        scanned = os.path.join(PROJECT_ROOT, stored)
        monkeypatch.setattr("src.config.os.listdir", lambda _: [stored])
        monkeypatch.setattr("src.config.os.path.isdir", lambda p: True)
        models = scan_models()
        assert len(models) == 1
        assert os.path.abspath(stored) == os.path.abspath(models[0])

    def test_resolve_model_path_matches_scan(self, monkeypatch):
        from src.config import resolve_model_path, PROJECT_ROOT
        model_names = ["vosk-model-small-es-0.42", "vosk-model-es-0.42"]
        monkeypatch.setattr("src.config.os.listdir", lambda _: model_names)
        monkeypatch.setattr("src.config.os.path.isdir", lambda p: True)
        scanned = scan_models()
        target = "vosk-model-small-es-0.42"
        resolved = resolve_model_path(target)
        for sm in scanned:
            if sm.endswith(target):
                assert os.path.abspath(resolved) == os.path.abspath(sm)
                return
        pytest.fail(f"'{target}' not found in scanned models: {scanned}")
