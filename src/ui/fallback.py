import os
import sys
import json

import vosk
import pyaudio

from ..config import MODEL_PATH
from ..audio import list_microphones
from ..commands import ejecutar_comando


def run_text_mode():
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
