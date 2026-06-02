import json
import threading
import queue

import vosk
import pyaudio


def list_microphones():
    p = pyaudio.PyAudio()
    devices = []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            devices.append((i, info["name"]))
    p.terminate()
    return devices


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
