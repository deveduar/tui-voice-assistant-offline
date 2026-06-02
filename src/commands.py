import os
import webbrowser
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class Command:
    patterns: list[str]
    description: str
    action: Callable[..., str]
    needs_query: bool = False


class CommandRegistry:
    def __init__(self):
        self._commands: list[Command] = []

    def add(self, command: Command):
        self._commands.append(command)

    def match(self, text: str) -> Optional[tuple[Command, str]]:
        text = text.lower().strip()
        for cmd in self._commands:
            for pattern in cmd.patterns:
                idx = text.find(pattern)
                if idx != -1:
                    query = ""
                    if cmd.needs_query:
                        query = text[idx + len(pattern):].strip()
                    return cmd, query
        return None

    def all(self) -> list[Command]:
        return list(self._commands)


# --- Action functions ---

def _abrir_notepad(app, q):
    os.system("notepad")
    return "Abriendo el bloc de notas."

def _abrir_calc(app, q):
    os.system("calc")
    return "Abriendo la calculadora."

def _abrir_navegador(app, q):
    webbrowser.open("https://www.google.com")
    return "Abriendo el navegador."

def _buscar_google(app, q):
    if q:
        webbrowser.open(f"https://www.google.com/search?q={q}")
        return f"Buscando '{q}' en Google."
    return "No dijiste qué buscar."

def _cambiar_microfono(app, q):
    if app:
        app.action_cambiar_microfono()
    return "Abriendo seleccion de microfono."

def _salir(app, q):
    if app:
        app.action_salir()
    return "Cerrando asistente..."

def _ayuda(app, q):
    if app:
        app.action_help()
    return "Abriendo ayuda..."

# Shutdown commands (commented out for safety)
# import subprocess
# def _apagar(app, q):
#     subprocess.run(["shutdown", "/s", "/t", "5"])
#     return "El sistema se apagara en 5 segundos."
# def _cancelar_apagado(app, q):
#     subprocess.run(["shutdown", "/a"])
#     return "Apagado cancelado."


# --- Command registry ---

registry = CommandRegistry()

registry.add(Command(
    patterns=["abrir bloc de notas", "abrir notepad"],
    description="Abre el Bloc de Notas de Windows",
    action=_abrir_notepad,
))

registry.add(Command(
    patterns=["abrir calculadora", "abrir calc"],
    description="Abre la Calculadora de Windows",
    action=_abrir_calc,
))

registry.add(Command(
    patterns=["abrir navegador", "abrir internet"],
    description="Abre el navegador en Google",
    action=_abrir_navegador,
))

registry.add(Command(
    patterns=["buscar en google"],
    description="Busca un termino en Google",
    needs_query=True,
    action=_buscar_google,
))

registry.add(Command(
    patterns=["cambiar microfono", "cambiar micrófono"],
    description="Cambia el microfono activo",
    action=_cambiar_microfono,
))

registry.add(Command(
    patterns=["salir", "adiós", "cerrar asistente"],
    description="Cierra el asistente de voz",
    action=_salir,
))

registry.add(Command(
    patterns=["ayuda", "comandos", "que puedes hacer"],
    description="Muestra la pantalla de ayuda con todos los comandos",
    action=_ayuda,
))

# registry.add(Command(
#     patterns=["apagar pc", "apagar el ordenador"],
#     description="Apaga el equipo en 5 segundos",
#     action=_apagar,
# ))
# registry.add(Command(
#     patterns=["cancelar apagado"],
#     description="Cancela el apagado programado",
#     action=_cancelar_apagado,
# ))


def ejecutar_comando(text: str, app=None) -> str:
    text = text.lower().strip()
    if not text:
        return ""
    match = registry.match(text)
    if match:
        cmd, query = match
        return cmd.action(app, query)
    return f"Comando no reconocido: '{text}'"
