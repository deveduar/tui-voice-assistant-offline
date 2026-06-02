import os
import json

MODEL_PATH = "vosk-model-small-es-0.42"
CONFIG_PATH = "config.json"
DEFAULT_MIC_INDEX = 1
DEFAULT_ASSISTANT_NAME = "flex"
DEFAULT_REQUIRE_NAME = False
DEFAULT_THEME = "textual-dark"

DEFAULT_LAUNCHERS = {
    "codigo": "code",
    "visual studio": "code",
    "lapce": "lapce",
    "notepad plus": "notepad++",
    "notepad plus plus": "notepad++",
    "explorador": "explorer",
    "archivos": "explorer",
    "powershell": "pwsh",
    "terminal": "wt",
    "vst": "wt -p VST",
    "ubuntu": "wt -p Ubuntu",
    "wsl": "wt -p Ubuntu",
    "zed": "zed",
}


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
    defaults = {
        "mic_index": DEFAULT_MIC_INDEX,
        "assistant_name": DEFAULT_ASSISTANT_NAME,
        "require_name": DEFAULT_REQUIRE_NAME,
        "disabled_commands": [],
        "theme": DEFAULT_THEME,
        "custom_launchers": dict(DEFAULT_LAUNCHERS),
    }
    for key, val in defaults.items():
        if key not in cfg:
            cfg[key] = val
            changed = True
    if changed:
        save_config(cfg)
    return cfg
