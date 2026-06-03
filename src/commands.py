import os
import webbrowser
import subprocess
import shutil
from dataclasses import dataclass
from typing import Callable, Optional

from .config import get_config


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


# --- Action functions ---

def _abrir_notepad(app, q):
    subprocess.Popen("notepad", shell=True)
    return "Abriendo el bloc de notas."

def _abrir_calc(app, q):
    subprocess.Popen("calc", shell=True)
    return "Abriendo la calculadora."

def _abrir_navegador(app, q):
    webbrowser.open("https://www.google.com")
    return "Abriendo el navegador."

def _buscar_google(app, q):
    if q:
        webbrowser.open(f"https://www.google.com/search?q={q}")
        return f"Buscando '{q}' en Google."
    return "No dijiste que buscar."

def _cambiar_microfono(app, q):
    if app:
        app.action_palette_mic_open()
    return "Abriendo seleccion de microfono."

def _salir(app, q):
    if app:
        app.action_salir()
    return "Cerrando asistente..."

def _configurar_comandos(app, q):
    if app:
        app.action_config_comandos()
    return "Abriendo configuracion de comandos."

def _abrir_terminal(app, q):
    subprocess.Popen("wt", shell=True)
    return "Abriendo terminal."

def _cerrar_ventana(app, q):
    if gwm("close"):
        return "Cerrando ventana."
    return "Error: gwm no disponible."

def _siguiente_escritorio(app, q):
    if gwm("focus", "--next-active-workspace"):
        return "Siguiente escritorio."
    return "Error: gwm no disponible."

def _anterior_escritorio(app, q):
    if gwm("focus", "--prev-active-workspace"):
        return "Anterior escritorio."
    return "Error: gwm no disponible."

def _ultimo_escritorio(app, q):
    if gwm("focus", "--recent-workspace"):
        return "Ultimo escritorio."
    return "Error: gwm no disponible."

def _maximizar_ventana(app, q):
    if gwm("toggle-fullscreen"):
        return "Ventana maximizada."
    return "Error: gwm no disponible."

def _minimizar_ventana(app, q):
    if gwm("toggle-minimized"):
        return "Ventana minimizada."
    return "Error: gwm no disponible."

def _hacer_flotante(app, q):
    if gwm("toggle-floating", "--centered"):
        return "Ventana en modo flotante."
    return "Error: gwm no disponible."

def _hacer_fija(app, q):
    if gwm("toggle-tiling"):
        return "Ventana en modo fijo."
    return "Error: gwm no disponible."

def _recargar_config(app, q):
    if gwm("reload-config"):
        return "Configuracion recargada."
    return "Error: gwm no disponible."

def _ciclar_foco(app, q):
    if gwm("wm-cycle-focus"):
        return "Ciclando foco entre ventanas."
    return "Error: gwm no disponible."

def _cambiar_direccion_tiling(app, q):
    if gwm("toggle-tiling-direction"):
        return "Direccion de tiling cambiada."
    return "Error: gwm no disponible."

def _redibujar(app, q):
    if gwm("wm-redraw"):
        return "Ventanas redibujadas."
    return "Error: gwm no disponible."

def _pausar_glaze(app, q):
    if gwm("wm-toggle-pause"):
        return "GlazeWM pausado/reanudado."
    return "Error: gwm no disponible."

def _focus_direction(direction):
    def action(app, q):
        if gwm("focus", "--direction", direction):
            return f"Enfocando ventana a la {'izquierda' if direction == 'left' else 'derecha' if direction == 'right' else 'arriba' if direction == 'up' else 'abajo'}."
        return "Error: gwm no disponible."
    return action

def _move_direction(direction):
    def action(app, q):
        if gwm("move", "--direction", direction):
            return f"Moviendo ventana a la {'izquierda' if direction == 'left' else 'derecha' if direction == 'right' else 'arriba' if direction == 'up' else 'abajo'}."
        return "Error: gwm no disponible."
    return action

def _abrir_programa(app, q):
    q = q.strip().lower()
    if not q:
        return "Di que programa quieres abrir."
    config = get_config()
    launchers = config.get("custom_launchers", {})
    if q in launchers:
        subprocess.Popen(launchers[q], shell=True)
        return f"Abriendo {q}."
    if not shutil.which(q):
        return f"No se encontro el programa '{q}'."
    subprocess.Popen(q, shell=True)
    return f"Abriendo {q}."

def _duerme(app, q):
    if app:
        app.action_dormir()
    return "Asistente en reposo."

def _despierta(app, q):
    if app:
        app.action_despertar()
    return "Asistente activo."

def _modo_escritura(app, q):
    if app:
        app.writing_mode = True
        app._update_status()
    return "Modo escritura activado."

def _modo_comandos(app, q):
    if app:
        app.writing_mode = False
        app._update_status()
    return "Modo escritura desactivado."

def _focus_workspace(n):
    def action(app, q):
        if gwm("focus", "--workspace", str(n)):
            return f"Yendo al escritorio {n}."
        return "Error: gwm no disponible."
    return action

def _move_to_workspace(n):
    def action(app, q):
        gwm("move", "--workspace", str(n))
        gwm("focus", "--workspace", str(n))
        return f"Ventana movida al escritorio {n}."
    return action


# --- Command registry ---

registry = CommandRegistry()

# --- General ---

registry.add(Command(
    patterns=["abrir bloc de notas", "abrir notepad"],
    description="Abre el Bloc de Notas de Windows",
    category="general",
    action=_abrir_notepad,
))

registry.add(Command(
    patterns=["abrir calculadora", "abrir calc"],
    description="Abre la Calculadora de Windows",
    category="general",
    action=_abrir_calc,
))

registry.add(Command(
    patterns=["abrir navegador", "abrir internet"],
    description="Abre el navegador en Google",
    category="general",
    action=_abrir_navegador,
))

registry.add(Command(
    patterns=["buscar en google"],
    description="Busca un termino en Google",
    category="general",
    needs_query=True,
    action=_buscar_google,
))

registry.add(Command(
    patterns=["cambiar microfono", "cambiar micrófono"],
    description="Cambia el microfono activo",
    category="general",
    action=_cambiar_microfono,
))

registry.add(Command(
    patterns=["salir", "adios", "adiós", "cerrar asistente"],
    description="Cierra el asistente de voz",
    category="general",
    action=_salir,
    always_requires_name=True,
))

registry.add(Command(
    patterns=["configurar comandos", "gestionar comandos", "personalizar comandos"],
    description="Abre la pantalla para activar/desactivar comandos",
    category="general",
    action=_configurar_comandos,
))

# --- GlazeWM ---

registry.add(Command(
    patterns=["abrir terminal", "abrir cmd"],
    description="Abre la terminal de Windows",
    category="glazewm",
    action=_abrir_terminal,
))

registry.add(Command(
    patterns=["cerrar ventana"],
    description="Cierra la ventana activa en GlazeWM",
    category="glazewm",
    action=_cerrar_ventana,
))

registry.add(Command(
    patterns=["siguiente escritorio", "siguiente"],
    description="Va al siguiente escritorio virtual",
    category="glazewm",
    action=_siguiente_escritorio,
))

registry.add(Command(
    patterns=["anterior escritorio", "anterior"],
    description="Va al anterior escritorio virtual",
    category="glazewm",
    action=_anterior_escritorio,
))

registry.add(Command(
    patterns=["ultimo escritorio", "volver", "escritorio anterior"],
    description="Vuelve al ultimo escritorio activo",
    category="glazewm",
    action=_ultimo_escritorio,
))

registry.add(Command(
    patterns=["maximizar ventana", "maximizar"],
    description="Pone la ventana activa en pantalla completa",
    category="glazewm",
    action=_maximizar_ventana,
))

registry.add(Command(
    patterns=["minimizar ventana", "minimizar"],
    description="Minimiza la ventana activa",
    category="glazewm",
    action=_minimizar_ventana,
))

registry.add(Command(
    patterns=["hacer flotante", "flotar ventana"],
    description="Cambia la ventana activa a modo flotante",
    category="glazewm",
    action=_hacer_flotante,
))

registry.add(Command(
    patterns=["hacer fija", "fijar ventana", "hacer tiling"],
    description="Cambia la ventana activa a modo fijo (tiling)",
    category="glazewm",
    action=_hacer_fija,
))

registry.add(Command(
    patterns=["recargar config", "recargar configuracion"],
    description="Recarga la configuracion de GlazeWM",
    category="glazewm",
    action=_recargar_config,
))

registry.add(Command(
    patterns=["ciclar foco", "siguiente ventana", "ciclar ventana"],
    description="Cambia el foco entre ventanas flotantes y ancladas",
    category="glazewm",
    action=_ciclar_foco,
))

registry.add(Command(
    patterns=["cambiar direccion", "cambiar direccion tiling"],
    description="Cambia la direccion de insercion de nuevas ventanas",
    category="glazewm",
    action=_cambiar_direccion_tiling,
))

registry.add(Command(
    patterns=["redibujar", "refrescar ventanas"],
    description="Redibuja todas las ventanas en GlazeWM",
    category="glazewm",
    action=_redibujar,
))

registry.add(Command(
    patterns=["pausar glaze", "pausar ventanas", "reanudar glaze"],
    description="Pausa o reanuda la gestion de ventanas de GlazeWM",
    category="glazewm",
    action=_pausar_glaze,
))

_DIR_NAMES = {
    "left": ("izquierda", "izquierdo"),
    "right": ("derecha", "derecho"),
    "up": ("arriba", "superior"),
    "down": ("abajo", "inferior"),
}
for direction, (es_name, _) in _DIR_NAMES.items():
    registry.add(Command(
        patterns=[f"enfocar {es_name}", f"enfoque {es_name}"],
        description=f"Enfoca la ventana a la {es_name}",
        category="glazewm",
        action=_focus_direction(direction),
    ))

for direction, (es_name, _) in _DIR_NAMES.items():
    registry.add(Command(
        patterns=[f"mover {es_name}", f"desplazar {es_name}"],
        description=f"Mueve la ventana activa a la {es_name}",
        category="glazewm",
        action=_move_direction(direction),
    ))

_NUM_WORDS = ["", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"]

for i in range(1, 10):
    registry.add(Command(
        patterns=[
            f"ir al escritorio {i}",
            f"escritorio {i}",
            f"ir al escritorio {_NUM_WORDS[i]}",
            f"escritorio {_NUM_WORDS[i]}",
        ],
        description=f"Ir al escritorio virtual {i}",
        category="glazewm",
        action=_focus_workspace(i),
    ))

for i in range(1, 10):
    registry.add(Command(
        patterns=[
            f"mover ventana al escritorio {i}",
            f"mover al escritorio {i}",
            f"mover ventana al escritorio {_NUM_WORDS[i]}",
            f"mover al escritorio {_NUM_WORDS[i]}",
        ],
        description=f"Mueve la ventana activa al escritorio virtual {i}",
        category="glazewm",
        action=_move_to_workspace(i),
    ))

# --- Sistema ---

registry.add(Command(
    patterns=["duerme", "dormir", "reposo"],
    description="Pone el asistente en reposo (requiere nombre)",
    category="sistema",
    action=_duerme,
))

registry.add(Command(
    patterns=["despierta", "despertar", "activo"],
    description="Activa el asistente del reposo (requiere nombre)",
    category="sistema",
    action=_despierta,
))

registry.add(Command(
    patterns=["modo escritura", "modo dictado", "empezar a escribir"],
    description="Activa el modo dictado (escribe lo que digas)",
    category="sistema",
    action=_modo_escritura,
))

registry.add(Command(
    patterns=["modo comandos", "modo normal", "salir de escritura", "dejar de escribir"],
    description="Desactiva el modo dictado",
    category="sistema",
    action=_modo_comandos,
))

# Custom launcher (must be last to let specific "abrir" commands match first)
registry.add(Command(
    patterns=["abrir"],
    description="Abre un programa configurado (codigo, lapce, notepad plus, explorador, ...)",
    needs_query=True,
    category="general",
    action=_abrir_programa,
))


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
