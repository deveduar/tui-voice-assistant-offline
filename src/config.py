import os
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(PROJECT_ROOT, "vosk-model-small-es-0.42")
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")
DEFAULT_MIC_INDEX = 1
DEFAULT_MODEL_NAME = "vosk-model-small-es-0.42"
DEFAULT_ASSISTANT_NAMES = ["flex"]
DEFAULT_REQUIRE_NAME = False
DEFAULT_THEME = "textual-dark"

def resolve_model_path(name: str) -> str:
    if os.path.isabs(name):
        return name
    return os.path.join(PROJECT_ROOT, name)

def scan_models():
    try:
        entries = os.listdir(PROJECT_ROOT)
        models = sorted(
            d for d in entries
            if d.startswith("vosk-model-") and os.path.isdir(os.path.join(PROJECT_ROOT, d))
        )
        return [os.path.join(PROJECT_ROOT, d) for d in models] if models else [resolve_model_path(DEFAULT_MODEL_NAME)]
    except OSError:
        return [resolve_model_path(DEFAULT_MODEL_NAME)]


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(config: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def get_config():
    cfg = load_config()
    changed = False
    if "assistant_name" in cfg and "assistant_names" not in cfg:
        old = cfg.pop("assistant_name")
        cfg["assistant_names"] = [old.strip().lower()] if old else list(DEFAULT_ASSISTANT_NAMES)
        changed = True

    defaults = {
        "mic_index": DEFAULT_MIC_INDEX,
        "model_name": DEFAULT_MODEL_NAME,
        "assistant_names": DEFAULT_ASSISTANT_NAMES,
        "require_name": DEFAULT_REQUIRE_NAME,
        "disabled_commands": [],
        "theme": DEFAULT_THEME,
    }
    for key, val in defaults.items():
        if key not in cfg:
            cfg[key] = val
            changed = True
    if changed:
        save_config(cfg)
    return cfg
