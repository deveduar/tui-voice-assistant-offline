import os
import json
import sys
import subprocess
import webbrowser
import vosk
import pyaudio

# ------------------------------------------------------------
# CONFIGURACIÓN
# ------------------------------------------------------------
# Ruta al modelo (carpeta que ya tienes)
MODEL_PATH = "vosk-model-small-es-0.42"

# ------------------------------------------------------------
# FUNCIONES AUXILIARES
# ------------------------------------------------------------
def listar_microfonos():
    """Muestra los índices y nombres de los dispositivos de entrada disponibles."""
    p = pyaudio.PyAudio()
    print("\n--- Micrófonos disponibles ---")
    dispositivos = []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            dispositivos.append((i, info['name']))
            print(f"  {i}: {info['name']}")
    p.terminate()
    if not dispositivos:
        print("No se encontró ningún micrófono.")
        sys.exit(1)
    return dispositivos

def seleccionar_microfono(dispositivos):
    """Pregunta al usuario qué micrófono usar."""
    while True:
        try:
            idx = int(input("\nSelecciona el número del micrófono a usar: "))
            if any(idx == d[0] for d in dispositivos):
                return idx
            else:
                print("Número inválido, elige uno de la lista.")
        except ValueError:
            print("Debes ingresar un número.")

def ejecutar_comando(texto):
    """
    Ejecuta acciones según el texto reconocido.
    Añade aquí todos los comandos que quieras.
    """
    cmd = texto.lower().strip()
    print(f"\n[Comando interpretado]: {cmd}")

    # --- Comandos de ejemplo (modifícalos a tu gusto) ---
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

    # COMANDOS DE APAGADO (comentados para evitar riesgos)
    # elif "apagar pc" in cmd or "apagar el ordenador" in cmd:
    #     subprocess.run(["shutdown", "/s", "/t", "5"])
    #     return "El sistema se apagará en 5 segundos."

    # elif "cancelar apagado" in cmd:
    #     subprocess.run(["shutdown", "/a"])
    #     return "Apagado cancelado."

    elif "salir" in cmd or "adiós" in cmd or "cerrar asistente" in cmd:
        print("Cerrando asistente...")
        sys.exit(0)

    else:
        return f"Comando no reconocido: '{texto}'"

# ------------------------------------------------------------
# PROGRAMA PRINCIPAL
# ------------------------------------------------------------
def main():
    # 1. Verificar que el modelo existe
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: No se encuentra la carpeta del modelo en '{MODEL_PATH}'")
        print("Asegúrate de tener descargado y descomprimido el modelo.")
        sys.exit(1)

    # 2. Cargar modelo Vosk
    print("Cargando modelo de voz... (esto puede tardar unos segundos)")
    model = vosk.Model(MODEL_PATH)
    recognizer = vosk.KaldiRecognizer(model, 16000)

    # 3. Selección de micrófono
    dispositivos = listar_microfonos()
    mic_index = seleccionar_microfono(dispositivos)

    # 4. Inicializar PyAudio con el micrófono elegido
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        input_device_index=mic_index,
        frames_per_buffer=4000
    )
    stream.start_stream()

    print("\n✅ Asistente activado. Habla (di 'salir' para terminar).\n")

    # 5. Bucle de escucha continua
    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            texto = result.get("text", "")
            if texto:
                respuesta = ejecutar_comando(texto)
                print(f"🤖 Asistente: {respuesta}\n")
        else:
            partial = json.loads(recognizer.PartialResult())
            partial_text = partial.get("partial", "")
            if partial_text:
                print(f"\r[Escuchando...] {partial_text}", end="", flush=True)

if __name__ == "__main__":
    main()