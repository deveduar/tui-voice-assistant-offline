import os
import sys
import queue

import vosk

from ..config import (
    MODEL_PATH, DEFAULT_MIC_INDEX,
    DEFAULT_ASSISTANT_NAME, DEFAULT_REQUIRE_NAME,
    get_config, save_config,
)
from ..audio import AudioManager, list_microphones
from ..commands import ejecutar_comando, registry
from ..writer import write_text

try:
    from textual.app import App, ComposeResult
    from textual.widgets import Header, Footer, RichLog, Static
    from textual.containers import Container
    from .screens import MicConfigScreen, HelpScreen, CommandConfigScreen
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

_WRITE_ENTER_PATTERNS = ["modo escritura", "modo dictado", "empezar a escribir"]
_WRITE_EXIT_PATTERNS = ["modo comandos", "modo normal", "salir de escritura", "dejar de escribir"]


def run():
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: No se encuentra la carpeta del modelo en '{MODEL_PATH}'")
        sys.exit(1)

    if not TEXTUAL_AVAILABLE:
        from .fallback import run_text_mode
        print("Textual no esta instalado. Usando modo texto simple.")
        print("Instala 'textual' con: pip install textual\n")
        run_text_mode()
        return

    app = VoiceAssistantApp()
    app.run()


if TEXTUAL_AVAILABLE:

    class VoiceAssistantApp(App):
        CSS = """
        Screen {
            background: $surface;
        }
        #log {
            height: 1fr;
            border: solid $primary;
            margin: 1;
            padding: 1;
        }
        #partial-text {
            height: 3;
            border: solid $secondary;
            margin: 0 1;
            padding: 0 1;
            background: $boost;
        }
        #status-bar {
            height: 1;
            margin: 0 1;
            color: $text-muted;
        }
        """

        BINDINGS = [
            ("q", "salir", "Salir"),
            ("c", "cambiar_microfono", "Microfono"),
            ("h", "help", "Ayuda"),
            ("w", "despertar", "Despertar"),
            ("m", "config_comandos", "Comandos"),
            ("t", "toggle_escritura", "Escribir"),
        ]

        def __init__(self):
            self.config = get_config()
            super().__init__()
            self.theme = self.config.get("theme", "textual-dark")
            self.audio_manager = None
            self.audio_queue = queue.Queue()
            self.sleeping = False
            self.writing_mode = False

            cfg_name = self.config.get("assistant_name", DEFAULT_ASSISTANT_NAME)
            self.assistant_name = cfg_name.strip().lower()
            self.require_name = self.config.get("require_name", DEFAULT_REQUIRE_NAME)

            print("Cargando modelo de voz... (esto puede tardar unos segundos)")
            self.model = vosk.Model(MODEL_PATH)

        def watch_theme(self, theme_name: str):
            self.config["theme"] = theme_name
            save_config(self.config)

        def compose(self):
            yield Header("Asistente de Voz")
            with Container():
                yield RichLog(id="log", highlight=True, wrap=True, max_lines=1000)
                yield Static("Esperando entrada de voz...", id="partial-text")
                yield Static("Iniciando...", id="status-bar")
            yield Footer()

        def on_mount(self):
            self._load_disabled_state()

            mics = list_microphones()
            if not mics:
                self.query_one("#log", RichLog).write(
                    "ERROR: No se encontro ningun microfono."
                )
                return

            mic_index = self.config.get("mic_index", DEFAULT_MIC_INDEX)
            valid_indices = [m[0] for m in mics]

            if mic_index not in valid_indices:
                self.query_one("#log", RichLog).write(
                    "Microfono guardado no valido. Selecciona uno:"
                )
                self.push_screen(MicConfigScreen(mics), self._on_mic_selected)
            else:
                self._start_audio(mic_index)

            self.set_interval(0.1, self._check_queue)

        def _load_disabled_state(self):
            disabled = self.config.get("disabled_commands", [])
            for cmd in registry.all():
                for pattern in cmd.patterns:
                    if pattern in disabled:
                        cmd.enabled = False
                        break

        def _save_disabled_state(self):
            disabled = []
            for cmd in registry.all():
                if not cmd.enabled:
                    disabled.append(cmd.patterns[0])
            self.config["disabled_commands"] = disabled
            save_config(self.config)

        def _start_audio(self, mic_index):
            self.audio_manager = AudioManager(
                mic_index, self.model, self.audio_queue
            )
            self.audio_manager.start()
            self.query_one("#status-bar", Static).update(
                f"Microfono [{mic_index}] activo"
            )

        def _on_mic_selected(self, mic_index):
            save_config({"mic_index": mic_index})
            self.query_one("#log", RichLog).write(
                f"Microfono [{mic_index}] seleccionado."
            )
            self._start_audio(mic_index)

        def _update_status(self):
            status = self.query_one("#status-bar", Static)
            if self.sleeping:
                status.update("Dormido")
            elif self.writing_mode:
                status.update("Escribiendo...")
            else:
                status.update("Escuchando...")

        def _check_queue(self):
            log = self.query_one("#log", RichLog)
            partial_widget = self.query_one("#partial-text", Static)

            while not self.audio_queue.empty():
                msg = self.audio_queue.get_nowait()
                if msg["type"] == "partial":
                    partial_widget.update(msg["text"])
                elif msg["type"] == "result":
                    texto = msg["text"]
                    texto_lower = texto.lower().strip()
                    handled = False

                    if self.writing_mode:
                        if any(p in texto_lower for p in _WRITE_EXIT_PATTERNS):
                            self.writing_mode = False
                            self._update_status()
                            log.write(texto)
                            log.write("Modo escritura desactivado. Modo comandos.")
                            handled = True
                        else:
                            write_text(texto)
                            log.write(f"[Escritura] {texto}")
                            handled = True
                    else:
                        if any(p in texto_lower for p in _WRITE_ENTER_PATTERNS):
                            self.writing_mode = True
                            self._update_status()
                            log.write(texto)
                            log.write("Modo escritura activado. Todo lo que digas se escribira en la ventana activa.")
                            handled = True

                    if not handled:
                        respuesta = ejecutar_comando(texto, self)
                        if respuesta:
                            log.write(texto)
                            log.write(respuesta)

                    partial_widget.update("")
                elif msg["type"] == "status":
                    if msg["text"] == "listening":
                        self._update_status()
                    else:
                        self.query_one("#status-bar", Static).update(msg["text"])
                elif msg["type"] == "error":
                    log.write(f"ERROR: {msg['message']}")
                    self.query_one("#status-bar", Static).update("Error en microfono")

        def action_salir(self):
            self._save_disabled_state()
            if self.audio_manager:
                self.audio_manager.stop()
            self.exit()

        def action_cambiar_microfono(self):
            if self.audio_manager:
                self.audio_manager.stop()
                self.audio_manager = None
            mics = list_microphones()
            if mics:
                self.push_screen(MicConfigScreen(mics), self._on_mic_selected)

        def action_help(self):
            self.push_screen(HelpScreen())

        def action_dormir(self):
            self.sleeping = True
            self._update_status()
            self.query_one("#partial-text", Static).update(
                f"Di '{self.assistant_name} despierta' para activar"
            )

        def action_despertar(self):
            self.sleeping = False
            self._update_status()
            self.query_one("#partial-text", Static).update("")

        def action_toggle_escritura(self):
            self.writing_mode = not self.writing_mode
            self._update_status()
            log = self.query_one("#log", RichLog)
            if self.writing_mode:
                log.write("Modo escritura activado por teclado.")
            else:
                log.write("Modo escritura desactivado.")

        def action_config_comandos(self):
            self.push_screen(CommandConfigScreen(), self._on_config_closed)

        def _on_config_closed(self, _result=None):
            self._save_disabled_state()
            self.query_one("#log", RichLog).write("Configuracion de comandos guardada.")

        def on_unmount(self):
            self._save_disabled_state()
            if self.audio_manager:
                self.audio_manager.stop()
