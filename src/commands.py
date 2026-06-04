import json
import os
import shutil
import subprocess
import webbrowser
from dataclasses import dataclass
from functools import partial
from typing import Callable, Optional

from .config import PROJECT_ROOT


@dataclass
class Command:
    patterns: list[str]
    description: str
    action: Callable[..., str]
    needs_query: bool = False
    enabled: bool = True
    category: str = "general"
    always_requires_name: bool = False


class CommandRegistry:
    def __init__(self):
        self._commands: list[Command] = []

    def add(self, command: Command):
        self._commands.append(command)

    def match(self, text: str) -> Optional[tuple[Command, str]]:
        text = text.lower().strip()
        for cmd in self._commands:
            if not cmd.enabled:
                continue
            for pattern in cmd.patterns:
                idx = text.find(pattern)
                if idx != -1:
                    query = ""
                    if cmd.needs_query:
                        query = text[idx + len(pattern):].strip()
                    return cmd, query
        return None

    def match_disabled(self, text: str) -> Optional[Command]:
        text = text.lower().strip()
        for cmd in self._commands:
            if cmd.enabled:
                continue
            for pattern in cmd.patterns:
                if pattern in text:
                    return cmd
        return None

    def all(self) -> list[Command]:
        return list(self._commands)


# --- GlazeWM helper ---

def gwm(*args):
    try:
        result = subprocess.run(
            ["glazewm", "command", *args],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


# --- Generic action factories (map 1:1 from JSON) ---

def _accion_programa(app, query, program=None, program_args=None, **kwargs):
    if not program:
        return "No se especifico programa."
    full = f"{program} {program_args}" if program_args else program
    subprocess.Popen(full, shell=True)
    return f"Abriendo {os.path.basename(program)}."

def _accion_url(app, query, url=None, needs_query=False, **kwargs):
    if not url:
        return "No se especifico URL."
    target = url.replace("{query}", query) if needs_query and query else url
    webbrowser.open(target)
    if needs_query and not query:
        return "No dijiste que buscar."
    return f"Abriendo enlace."

def _accion_teclas(app, query, keys=None, **kwargs):
    if not keys:
        return "No se especificaron teclas."
    return f"Tecla {keys} no implementada."

def _accion_shell(app, query, shell=None, confirm=False, **kwargs):
    if not shell:
        return "No se especifico comando."
    subprocess.Popen(shell, shell=True)
    return "Comando ejecutado."

def _accion_teclear(app, query, text=None, **kwargs):
    if not text:
        return "No se especifico texto."
    try:
        from .writer import write_text
        write_text(text)
        return f"Texto escrito: {text[:30]}..."
    except Exception:
        return "Error al escribir texto."

def _accion_gwm(app, query, gwm_args=None, **kwargs):
    if not gwm_args:
        return "Comando GlazeWM no especificado."
    if gwm(*gwm_args):
        desc = _describe_gwm(gwm_args)
        return desc
    return "Error: gwm no disponible."

def _accion_abrir_catchall(app, query, **kwargs):
    q = query.strip().lower()
    if not q:
        return "Di que programa quieres abrir."
    if shutil.which(q):
        subprocess.Popen(q, shell=True)
        return f"Abriendo {q}."
    return f"No se encontro el programa '{q}'."


def _describe_gwm(args):
    actions = {
        "close": "Cerrando ventana.",
        "--next-active-workspace": "Siguiente escritorio.",
        "--prev-active-workspace": "Anterior escritorio.",
        "--recent-workspace": "Volviendo al ultimo escritorio.",
        "toggle-fullscreen": "Maximizando ventana.",
        "toggle-minimized": "Minimizando ventana.",
        "toggle-floating": "Ventana en modo flotante.",
        "toggle-tiling": "Ventana en modo fijo.",
        "reload-config": "Configuracion recargada.",
        "wm-cycle-focus": "Ciclando foco.",
        "toggle-tiling-direction": "Direccion de tiling cambiada.",
        "wm-redraw": "Ventanas redibujadas.",
        "wm-toggle-pause": "GlazeWM pausado/reanudado.",
    }
    for arg in args:
        if arg in actions:
            return actions[arg]
    if "--direction" in args:
        idx = args.index("--direction")
        if idx + 1 < len(args):
            dirs = {"left": "izquierda", "right": "derecha", "up": "arriba", "down": "abajo"}
            d = dirs.get(args[idx + 1], args[idx + 1])
            if "focus" in args:
                return f"Enfocando ventana a la {d}."
            return f"Moviendo ventana a la {d}."
    if "--workspace" in args:
        idx = args.index("--workspace")
        if idx + 1 < len(args):
            n = args[idx + 1]
            if "move" in args:
                return f"Ventana movida al escritorio {n}."
            return f"Yendo al escritorio {n}."
    return "Comando GlazeWM ejecutado."


# --- Internal app actions (require app reference) ---

def _salir(app, q, **kwargs):
    if app:
        app.action_salir()
    return "Cerrando asistente..."

def _duerme(app, q, **kwargs):
    if app:
        app.action_dormir()
    return "Asistente en reposo."

def _despierta(app, q, **kwargs):
    if app:
        app.action_despertar()
    return "Asistente activo."

def _modo_escritura(app, q, **kwargs):
    if app:
        app.writing_mode = True
        app._update_status()
    return "Modo escritura activado."

def _modo_comandos(app, q, **kwargs):
    if app:
        app.writing_mode = False
        app._update_status()
    return "Modo escritura desactivado."

def _configurar_comandos(app, q, **kwargs):
    if app:
        app.action_config_comandos()
    return "Abriendo configuracion de comandos."

def _cambiar_microfono(app, q, **kwargs):
    if app:
        app.action_palette_mic_open()
    return "Abriendo seleccion de microfono."


# --- Action ID mapping ---

_ACTION_MAP = {
    "programa": _accion_programa,
    "url": _accion_url,
    "teclas": _accion_teclas,
    "shell": _accion_shell,
    "teclear": _accion_teclear,
    "gwm": _accion_gwm,
    "abrir_catchall": _accion_abrir_catchall,
    "salir": _salir,
    "dormir": _duerme,
    "despertar": _despierta,
    "modo_escritura": _modo_escritura,
    "modo_comandos": _modo_comandos,
    "config_comandos": _configurar_comandos,
    "cambiar_micro": _cambiar_microfono,
}

_CONFIG_PATH = os.path.join(PROJECT_ROOT, "commands_config.json")


def cargar_comandos(registry: CommandRegistry, path: str = None):
    path = path or _CONFIG_PATH
    try:
        with open(path, encoding="utf-8") as f:
            items = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return



    _KW_KEYS = ("program", "program_args", "url", "keys", "shell", "confirm",
                "text", "gwm_args")

    for item in items:
        action_id = item.get("action")
        action_fn = _ACTION_MAP.get(action_id)
        if not action_fn:
            continue

        needs_query = item.get("needs_query", False)
        always_name = item.get("always_requires_name", False)

        kwargs = {k: item[k] for k in _KW_KEYS if k in item}
        if needs_query:
            kwargs["needs_query"] = True
        fn = partial(action_fn, **kwargs) if kwargs else action_fn

        registry.add(Command(
            patterns=item["patterns"],
            description=item.get("description", ""),
            category=item.get("category", "general"),
            action=fn,
            needs_query=needs_query,
            always_requires_name=always_name,
        ))




# --- Module-level registry and loader ---

registry = CommandRegistry()
cargar_comandos(registry)


def ejecutar_comando(text: str, app=None) -> str:
    text = text.lower().strip()
    if not text:
        return ""

    assistant_name = ""
    require_name = False
    sleeping = False
    if app:
        assistant_name = getattr(app, "assistant_name", "flex")
        require_name = getattr(app, "require_name", False)
        sleeping = getattr(app, "sleeping", False)

    has_prefix = False
    if assistant_name:
        if text == assistant_name:
            return f"Di '{assistant_name} ayuda' para ver comandos."
        if text.startswith(assistant_name + " "):
            text = text[len(assistant_name) + 1:].strip()
            has_prefix = True

    disabled_cmd = registry.match_disabled(text)
    if disabled_cmd:
        if sleeping:
            return ""
        if require_name and not has_prefix:
            return ""
        return f"Comando deshabilitado: {disabled_cmd.description}"

    match = registry.match(text)
    if not match:
        if sleeping:
            return ""
        if require_name and not has_prefix:
            return ""
        return f"Comando no reconocido: '{text}'"

    cmd, query = match

    if cmd.category == "sistema" and any(
        p in cmd.patterns[0] for p in ["duerme", "dormir", "reposo",
                                        "despierta", "despertar", "activo"]
    ):
        if not has_prefix:
            if sleeping:
                return ""
            return f"Usa '{assistant_name} {cmd.patterns[0]}' para {cmd.description.lower().replace(' (requiere nombre)', '')}."
        return cmd.action(app, query)

    if sleeping:
        return ""

    if cmd.always_requires_name:
        if not has_prefix:
            if sleeping:
                return ""
            name = assistant_name or "flex"
            return f"Di '{name} {cmd.patterns[0]}' para {cmd.description.lower()}."

    if require_name and not has_prefix:
        return ""

    return cmd.action(app, query)
