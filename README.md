# Asistente de Voz — Offline con Vosk + Textual TUI

Asistente por voz en español, 100% offline, con interfaz TUI moderna (Textual).
Reconoce comandos de voz y ejecuta acciones en Windows.

## Requisitos

- Python 3.8+
- Windows 10/11 (recomendado Windows Terminal)
- Microfono funcional

## Instalacion

```cmd
pip install -r requirements.txt
```

Esto instala:
- `vosk` — reconocimiento offline de voz
- `pyaudio` — captura de audio del microfono
- `textual` — interfaz TUI moderna

## Uso

```cmd
python main.py
```

### Primera ejecucion

1. El asistente carga el modelo de voz (~40 MB).
2. Si no hay `config.json` o el microfono guardado no es valido, se abre un menu TUI para seleccionar el microfono.
3. La seleccion se guarda en `config.json` para usos posteriores.
4. Comienza la escucha continua.

## Interfaz TUI

```
+----------------------------------+
|  Asistente de Voz                |  <- Header
+----------------------------------+
|  abrir bloc de notas             |  <- RichLog (historial)
|  Abriendo el bloc de notas.      |
|  abrir calculadora               |
|  Abriendo la calculadora.        |
+----------------------------------+
|  buscando google...              |  <- Static (texto parcial)
+----------------------------------+
|  Microfono [1] activo            |  <- Status bar
+----------------------------------+
|  [Q] Salir  [C] Microfono  [H] Ayuda  |  <- Footer
+----------------------------------+
```

### Atajos de teclado

| Tecla | Accion |
|-------|--------|
| `Q` | Salir del asistente |
| `C` | Abrir menu de seleccion de microfono |
| `H` | Abrir pantalla de ayuda con todos los comandos |

## Comandos de voz

| Comando | Accion |
|---------|--------|
| "abrir bloc de notas" / "abrir notepad" | Abre el Bloc de Notas |
| "abrir calculadora" / "abrir calc" | Abre la Calculadora |
| "abrir navegador" / "abrir internet" | Abre el navegador en google.com |
| "buscar en google [consulta]" | Busca en Google |
| "cambiar microfono" / "cambiar microfono" | Abre menu para cambiar microfono |
| "ayuda" / "comandos" / "que puedes hacer" | Muestra la pantalla de ayuda |
| "salir" / "adios" / "cerrar asistente" | Cierra el asistente |

Los comandos de apagado del sistema estan comentados en el codigo por seguridad.
Para activarlos, descomenta las lineas en `src/commands.py`.

## Configuracion

El archivo `config.json` se genera automaticamente:

```json
{
  "mic_index": 1
}
```

- `mic_index`: indice del dispositivo de entrada (microfono) a usar.
- Si el indice guardado no es valido (el microfono ya no existe), el asistente abre el menu TUI para seleccionar uno nuevo.

## Sin Textual (fallback)

Si `textual` no esta instalado, el asistente funciona en modo texto simple
(seleccion numerica de microfono + salida por consola).

## Estructura del proyecto

```
audio-vosk/
+-- main.py                        # Punto de entrada
+-- config.json                    # Configuracion persistente (se crea solo)
+-- requirements.txt               # Dependencias
+-- README.md                      # Este archivo
+-- vosk-model-small-es-0.42/      # Modelo de voz (no tocar)
+-- .gitignore
+-- src/
    +-- __init__.py
    +-- config.py                  # Carga/guarda config.json
    +-- audio.py                   # AudioManager (hilo + cola) + listar microfonos
    +-- commands.py                # CommandRegistry + definicion de comandos
    +-- ui/
        +-- __init__.py
        +-- app.py                 # VoiceAssistantApp (Textual) + run()
        +-- screens.py             # MicConfigScreen + HelpScreen
        +-- fallback.py            # Modo texto sin Textual
```
