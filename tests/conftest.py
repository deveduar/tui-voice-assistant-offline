import os
import sys
import json
import tempfile
from pathlib import Path

import pytest

from src.commands import CommandRegistry, Command, cargar_comandos


SAMPLE_COMMANDS_JSON = [
    {
        "patterns": ["abrir notepad", "abrir bloc de notas"],
        "description": "Abre el Bloc de Notas",
        "category": "general",
        "action": "programa",
        "program": "notepad",
    },
    {
        "patterns": ["siguiente escritorio", "siguiente"],
        "description": "Siguiente escritorio virtual",
        "category": "glazewm",
        "action": "gwm",
        "gwm_args": ["focus", "--next-active-workspace"],
    },
    {
        "patterns": ["modo escritura", "modo dictado"],
        "description": "Activa el modo escritura",
        "category": "sistema",
        "action": "modo_escritura",
    },
    {
        "patterns": ["salir", "adios"],
        "description": "Cierra el asistente",
        "category": "sistema",
        "action": "salir",
    },
]

SAMPLE_COMMANDS_ORDERED = [
    Command(["abrir notepad"], "Abre Bloc de Notas", lambda app, q: "ok"),
    Command(["abrir"], "Catch-all", lambda app, q: "catchall", needs_query=True),
]

SAMPLE_COMMANDS_DISABLED = [
    Command(["abrir notepad"], "Abre Bloc de Notas", lambda app, q: "ok", enabled=False),
    Command(["abrir calc"], "Abre Calculadora", lambda app, q: "ok"),
]

SAMPLE_COMMANDS_QUERY = [
    Command(["buscar en google"], "Buscar en Google",
            lambda app, q: f"buscando {q}", needs_query=True),
    Command(["buscar en youtube"], "Buscar en YouTube",
            lambda app, q: f"youtube {q}", needs_query=True),
]


@pytest.fixture
def registry():
    reg = CommandRegistry()
    for c in SAMPLE_COMMANDS_ORDERED:
        reg.add(c)
    return reg


@pytest.fixture
def registry_disabled():
    reg = CommandRegistry()
    for c in SAMPLE_COMMANDS_DISABLED:
        reg.add(c)
    return reg


@pytest.fixture
def registry_query():
    reg = CommandRegistry()
    for c in SAMPLE_COMMANDS_QUERY:
        reg.add(c)
    return reg


@pytest.fixture
def commands_json_path():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(SAMPLE_COMMANDS_JSON, f, ensure_ascii=False)
        path = f.name
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def temp_config_path():
    old_path = None
    import src.config as cfg
    old_path = cfg.CONFIG_PATH
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump({}, f)
        cfg.CONFIG_PATH = f.name
        yield f.name
    cfg.CONFIG_PATH = old_path
    try:
        os.unlink(f.name)
    except OSError:
        pass
