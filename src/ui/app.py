import os
import sys
import queue
from functools import partial

import vosk

from ..config import (
    MODEL_PATH, DEFAULT_MIC_INDEX,
    DEFAULT_ASSISTANT_NAME, DEFAULT_REQUIRE_NAME,
    get_config, save_config, scan_models,
    PROJECT_ROOT, resolve_model_path,
)
from ..audio import AudioManager, list_microphones
from ..commands import ejecutar_comando, registry
from ..writer import write_text

try:
    from textual.app import App, ComposeResult
    from textual.widgets import Header, Footer, RichLog, Static
    from textual.containers import Container
    try:
        from textual.command import Provider, Hit, CommandPalette
    except ImportError:
        Provider = None
        CommandPalette = None
    from .screens import CommandConfigScreen
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False


def run():
    models = scan_models()
    raw = get_config().get("model_name", MODEL_PATH)
    model_name = resolve_model_path(raw)
    if model_name not in models:
        model_name = models[0] if models else resolve_model_path(MODEL_PATH)
    if not os.path.exists(model_name):
        print(f"ERROR: No se encuentra la carpeta del modelo en '{model_name}'")
        print("Modelos disponibles:", ", ".join(models))
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

    class VoiceAssistantCommands(Provider):
        async def search(self, query: str):
            app = self.app
            q = query.lower()

            if not q or "micro" in q or "mic" in q:
                mics = list_microphones()
                for idx, name in mics:
                    yield Hit(
                        10,
                        f"[{idx}] {name}",
                        partial(app.action_palette_mic, idx),
                        "Seleccionar este microfono",
                    )

            if not q or "modelo" in q or "model" in q:
                models = scan_models()
                for mname in models:
                    short = os.path.basename(mname)
                    yield Hit(
                        20,
                        short,
                        partial(app.action_palette_model, mname),
                        "Usar este modelo de voz",
                    )

            if not q or "dormir" in q or "suspen" in q or "reposo" in q:
                yield Hit(30, "Dormir asistente", app.action_dormir, "Poner en reposo")

            if not q or "despertar" in q or "activar" in q:
                yield Hit(31, "Despertar asistente", app.action_despertar, "Activar del reposo")

            if not q or "escritura" in q or "dictado" in q:
                yield Hit(
                    40, "Modo escritura",
                    partial(app._toggle_writing_from_palette, True),
                    "Activar dictado",
                )

            if not q or "comandos" in q or "normal" in q:
                yield Hit(
                    41, "Modo comandos",
                    partial(app._toggle_writing_from_palette, False),
                    "Desactivar dictado",
                )

            if not q or "config" in q or "comandos" in q:
                yield Hit(50, "Configurar comandos", app.action_config_comandos, "Abrir configuracion de comandos")


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

        COMMANDS = {VoiceAssistantCommands} if Provider else {}

        BINDINGS = [
            ("q", "salir", "Salir"),
            ("m", "config_comandos", "Menu Comandos"),
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
            raw = self.config.get("model_name", MODEL_PATH)
            self._model_name = resolve_model_path(raw)

            vosk.SetLogLevel(-1)
            print("Cargando modelo de voz... (esto puede tardar unos segundos)")
            self.model = vosk.Model(self._model_name)

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
                    "Microfono guardado no valido. Usa Ctrl+P para seleccionar uno:"
                )
                self.action_palette_mic_open()
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
            if self.audio_manager:
                self.audio_manager.stop()
            self.audio_manager = AudioManager(
                mic_index, self.model, self.audio_queue
            )
            self.audio_manager.start()
            model_short = os.path.basename(self._model_name).replace("vosk-model-", "").replace("-es-", "-")
            self.query_one("#status-bar", Static).update(
                f"Microfono [{mic_index}] activo [{model_short}]"
            )

        def _update_status(self):
            try:
                status = self.query_one("#status-bar", Static)
                model_short = os.path.basename(self._model_name).replace("vosk-model-", "").replace("-es-", "-")
                if self.sleeping:
                    status.update(f"Dormido [{model_short}]")
                elif self.writing_mode:
                    status.update(f"Escribiendo... [{model_short}]")
                else:
                    status.update(f"Escuchando... [{model_short}]")
            except Exception:
                pass

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

                    if self.sleeping:
                        respuesta = ejecutar_comando(texto, self)
                        if respuesta:
                            log.write(texto)
                            log.write(respuesta)
                    elif self.writing_mode:
                        match = registry.match(texto_lower)
                        if match and match[0].category == "sistema" and \
                           any(p in match[0].patterns[0] for p in
                               ["modo comandos", "modo normal", "salir de escritura"]):
                            match[0].action(self, "")
                            log.write(texto)
                            log.write("Modo escritura desactivado.")
                        else:
                            write_text(texto)
                            log.write(f"[Escritura] {texto}")
                    else:
                        match = registry.match(texto_lower)
                        if match and match[0].category == "sistema" and \
                           any(p in match[0].patterns[0] for p in ["modo escritura", "modo dictado"]):
                            match[0].action(self, "")
                            log.write(texto)
                            log.write("Modo escritura activado.")
                        else:
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

        def action_command_palette(self) -> None:
            if self.use_command_palette and not CommandPalette.is_open(self):
                self.push_screen(
                    CommandPalette(
                        id="--command-palette",
                        placeholder="micro, modelo, dormir, escritura, comandos...",
                    )
                )

        def action_config_comandos(self):
            self.push_screen(CommandConfigScreen(), self._on_config_closed)

        def _on_config_closed(self, dirty: bool = False):
            if dirty:
                self._save_disabled_state()
                self.query_one("#log", RichLog).write("Configuracion de comandos guardada.")

        def action_palette_mic(self, mic_index: int):
            current = self.config.get("mic_index")
            if mic_index == current:
                return
            if self.audio_manager:
                self.audio_manager.stop()
                self.audio_manager = None
            self.config["mic_index"] = mic_index
            save_config(self.config)
            self._start_audio(mic_index)
            self.query_one("#log", RichLog).write(
                f"Microfono cambiado a [{mic_index}]."
            )

        def action_palette_mic_open(self):
            mics = list_microphones()
            if mics:
                from textual.screen import Screen
                from textual.widgets import Header, Footer, ListView, ListItem, Label, Button
                class MicPicker(Screen):
                    def __init__(self, mics):
                        super().__init__()
                        self.mics = mics
                    def compose(self):
                        yield Header("Seleccionar Microfono")
                        yield Label("Elige un microfono:")
                        yield ListView(id="mic-list")
                        yield Button("Confirmar", variant="primary", id="confirm-btn")
                        yield Footer()
                    def on_mount(self):
                        lv = self.query_one("#mic-list", ListView)
                        for idx, name in self.mics:
                            lv.append(ListItem(Label(f"  [{idx}] {name}")))
                        if self.mics:
                            lv.index = 0
                    def on_list_view_selected(self, event):
                        idx = event.list_view.index
                        if idx is not None and 0 <= idx < len(self.mics):
                            self.dismiss(self.mics[idx][0])
                    def on_button_pressed(self, event):
                        if event.button.id == "confirm-btn":
                            lv = self.query_one("#mic-list", ListView)
                            if lv.index is not None and 0 <= lv.index < len(self.mics):
                                self.dismiss(self.mics[lv.index][0])
                self.push_screen(MicPicker(mics), self._on_mic_picked)

        def _on_mic_picked(self, mic_index):
            if mic_index is not None:
                self.action_palette_mic(mic_index)

        def action_palette_model(self, model_name: str):
            abs_path = os.path.abspath(model_name)
            current = self.config.get("model_name")
            if abs_path == current:
                return
            if self.audio_manager:
                self.audio_manager.stop()
                self.audio_manager = None
            self.config["model_name"] = abs_path
            save_config(self.config)
            self._model_name = abs_path
            self.query_one("#status-bar", Static).update(
                f"Cargando {os.path.basename(abs_path)}..."
            )
            self.call_later(self._finish_model_load, abs_path)

        def _finish_model_load(self, model_path: str):
            try:
                vosk.SetLogLevel(-1)
                new_model = vosk.Model(model_path)
            except Exception as e:
                log = self.query_one("#log", RichLog)
                log.write(f"ERROR: No se pudo cargar '{model_path}': {e}")
                mic_index = self.config.get("mic_index", DEFAULT_MIC_INDEX)
                self._start_audio(mic_index)
                return
            self.model = new_model
            mic_index = self.config.get("mic_index", DEFAULT_MIC_INDEX)
            self._start_audio(mic_index)
            self.query_one("#log", RichLog).write(
                f"Modelo cambiado a {os.path.basename(model_path)}."
            )

        def _toggle_writing_from_palette(self, on: bool):
            self.writing_mode = on
            self._update_status()
            log = self.query_one("#log", RichLog)
            if on:
                log.write("Modo escritura activado desde paleta.")
            else:
                log.write("Modo escritura desactivado.")

        def on_unmount(self):
            self._save_disabled_state()
            if self.audio_manager:
                self.audio_manager.stop()
