import os
import json
import sys
import subprocess
import webbrowser
import threading
import queue

import vosk
import pyaudio

try:
    from textual.app import App, ComposeResult
    from textual.screen import Screen
    from textual.widgets import (
        Header, Footer, RichLog, Static,
        Button, Label, ListView, ListItem,
    )
    from textual.containers import Container
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

MODEL_PATH = "vosk-model-small-es-0.42"
CONFIG_PATH = "config.json"
DEFAULT_MIC_INDEX = 1


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def list_microphones():
    p = pyaudio.PyAudio()
    devices = []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            devices.append((i, info["name"]))
    p.terminate()
    return devices


def ejecutar_comando(texto, app=None):
    cmd = texto.lower().strip()

    if "abrir bloc de notas" in cmd or "abrir notepad" in cmd:
        os.system("notepad")
        return "Abriendo el bloc de notas."

    elif "abrir calculadora" in cmd or "abrir calc" in cmd:
        os.system("calc")
        return "Abriendo la calculadora."

    elif "abrir navegador" in cmd or "abrir internet" in cmd:
        webbrowser.open("https://www.google.com")
        return "Abriendo el navegador."

    elif "buscar en google" in cmd:
        query = cmd.replace("buscar en google", "").strip()
        if query:
            webbrowser.open(f"https://www.google.com/search?q={query}")
            return f"Buscando '{query}' en Google."
        else:
            return "No dijiste qué buscar."

    # Comandos de apagado (comentados para evitar riesgos)
    # elif "apagar pc" in cmd or "apagar el ordenador" in cmd:
    #     subprocess.run(["shutdown", "/s", "/t", "5"])
    #     return "El sistema se apagará en 5 segundos."
    # elif "cancelar apagado" in cmd:
    #     subprocess.run(["shutdown", "/a"])
    #     return "Apagado cancelado."

    elif "cambiar micrófono" in cmd or "cambiar microfono" in cmd:
        if app:
            app.action_cambiar_microfono()
        return "Abriendo selección de micrófono."

    elif "salir" in cmd or "adiós" in cmd or "cerrar asistente" in cmd:
        if app:
            app.action_salir()
        return "Cerrando asistente..."

    else:
        return f"Comando no reconocido: '{texto}'"


class AudioManager:
    def __init__(self, mic_index, model, output_queue):
        self.mic_index = mic_index
        self.model = model
        self.output_queue = output_queue
        self.running = False
        self.thread = None
        self.p = None
        self.stream = None
        self.recognizer = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
        if self.p:
            try:
                self.p.terminate()
            except Exception:
                pass
        if self.thread:
            self.thread.join(timeout=2)

    def _run(self):
        try:
            self.p = pyaudio.PyAudio()
            self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                input_device_index=self.mic_index,
                frames_per_buffer=4000,
            )
            self.stream.start_stream()
            self.output_queue.put({"type": "status", "text": "listening"})

            while self.running:
                data = self.stream.read(4000, exception_on_overflow=False)
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    texto = result.get("text", "")
                    if texto:
                        self.output_queue.put({"type": "result", "text": texto})
                else:
                    partial = json.loads(self.recognizer.PartialResult())
                    partial_text = partial.get("partial", "")
                    if partial_text:
                        self.output_queue.put(
                            {"type": "partial", "text": partial_text}
                        )

        except Exception as e:
            self.output_queue.put({"type": "error", "message": str(e)})


if TEXTUAL_AVAILABLE:

    class MicConfigScreen(Screen):
        def __init__(self, mics):
            super().__init__()
            self.mics = mics

        def compose(self):
            yield Header("Seleccionar Micrófono")
            yield Label("Elige un micrófono (flechas + Enter):", id="mic-label")
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
            lv = event.list_view
            if lv.index is not None and 0 <= lv.index < len(self.mics):
                self.dismiss(self.mics[lv.index][0])

        def on_button_pressed(self, event):
            if event.button.id == "confirm-btn":
                lv = self.query_one("#mic-list", ListView)
                if lv.index is not None and 0 <= lv.index < len(self.mics):
                    self.dismiss(self.mics[lv.index][0])

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
        MicConfigScreen {
            align: center middle;
        }
        #mic-list {
            height: 1fr;
            width: 80%;
            border: solid $primary;
            margin: 1;
        }
        #mic-label {
            margin: 1;
            text-style: bold;
        }
        """

        BINDINGS = [
            ("q", "salir", "Salir"),
            ("c", "cambiar_microfono", "Microfono"),
        ]

        def __init__(self):
            super().__init__()
            self.audio_manager = None
            self.audio_queue = queue.Queue()
            self.config = load_config()

            if not os.path.exists(MODEL_PATH):
                print(f"ERROR: Modelo no encontrado en '{MODEL_PATH}'")
                sys.exit(1)

            print("Cargando modelo de voz... (esto puede tardar unos segundos)")
            self.model = vosk.Model(MODEL_PATH)

        def compose(self):
            yield Header("Asistente de Voz")
            with Container():
                yield RichLog(id="log", highlight=True, wrap=True, max_lines=1000)
                yield Static("Esperando entrada de voz...", id="partial-text")
                yield Static("Iniciando...", id="status-bar")
            yield Footer()

        def on_mount(self):
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

        def _check_queue(self):
            log = self.query_one("#log", RichLog)
            partial_widget = self.query_one("#partial-text", Static)
            status_widget = self.query_one("#status-bar", Static)

            while not self.audio_queue.empty():
                msg = self.audio_queue.get_nowait()
                if msg["type"] == "partial":
                    partial_widget.update(msg["text"])
                elif msg["type"] == "result":
                    texto = msg["text"]
                    log.write(texto)
                    respuesta = ejecutar_comando(texto, self)
                    log.write(respuesta)
                    partial_widget.update("")
                elif msg["type"] == "status":
                    if msg["text"] == "listening":
                        status_widget.update("Escuchando...")
                    else:
                        status_widget.update(msg["text"])
                elif msg["type"] == "error":
                    log.write(f"ERROR: {msg['message']}")
                    status_widget.update("Error en microfono")

        def action_salir(self):
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

        def on_unmount(self):
            if self.audio_manager:
                self.audio_manager.stop()


def run_text_mode():
    print("Textual no esta instalado. Usando modo texto simple.")
    print("Instala 'textual' con: pip install textual\n")

    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: No se encuentra el modelo en '{MODEL_PATH}'")
        sys.exit(1)

    print("Cargando modelo de voz...")
    model = vosk.Model(MODEL_PATH)
    recognizer = vosk.KaldiRecognizer(model, 16000)

    mics = list_microphones()
    if not mics:
        print("No se encontro ningun microfono.")
        sys.exit(1)

    print("\n--- Microfonos disponibles ---")
    for idx, name in mics:
        print(f"  {idx}: {name}")

    while True:
        try:
            mic_index = int(input("\nSelecciona el numero del microfono: "))
            if any(mic_index == m[0] for m in mics):
                break
            print("Numero invalido.")
        except ValueError:
            print("Debes ingresar un numero.")

    print(f"\nInicializando microfono [{mic_index}]...")
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        input_device_index=mic_index,
        frames_per_buffer=4000,
    )
    stream.start_stream()

    print("\nAsistente activado. Habla (di 'salir' para terminar).\n")
    try:
        while True:
            data = stream.read(4000, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                texto = result.get("text", "")
                if texto:
                    respuesta = ejecutar_comando(texto)
                    print(texto)
                    print(f"{respuesta}\n")
            else:
                partial = json.loads(recognizer.PartialResult())
                partial_text = partial.get("partial", "")
                if partial_text:
                    print(f"\r{partial_text}", end="", flush=True)
    except KeyboardInterrupt:
        print("\n\nAsistente detenido.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


def main():
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: No se encuentra la carpeta del modelo en '{MODEL_PATH}'")
        sys.exit(1)

    if TEXTUAL_AVAILABLE:
        app = VoiceAssistantApp()
        app.run()
    else:
        run_text_mode()


if __name__ == "__main__":
    main()
