# Asistente de Voz — Offline con Vosk + Textual TUI

Asistente por voz en español, 100% offline, con interfaz TUI moderna (Textual).
Reconoce comandos de voz y ejecuta acciones en Windows.

## Requisitos

- Python 3.8+
- Windows 10/11 (recomendado Windows Terminal)
- Micrófono funcional

## Instalación

```cmd
pip install -r requirements.txt
```

Esto instala:
- `vosk` — reconocimiento offline de voz
- `pyaudio` — captura de audio del micrófono
- `textual` — interfaz TUI moderna

## Uso

```cmd
python asistente_voz.py
```

### Primera ejecución

1. El asistente carga el modelo de voz (∼40 MB).
2. Si no hay `config.json` o el micrófono guardado no es válido, se abre un menú TUI para seleccionar el micrófono.
3. La selección se guarda en `config.json` para usos posteriores.
4. Comienza la escucha continua.

## Interfaz TUI

```
┌─────────────────────────────────┐
│  Asistente de Voz               │  ← Header
├─────────────────────────────────┤
│  abrir bloc de notas            │  ← RichLog (historial)
│  Abriendo el bloc de notas.     │
│  abrir calculadora              │
│  Abriendo la calculadora.       │
├─────────────────────────────────┤
│  buscando google...             │  ← Static (texto parcial)
├─────────────────────────────────┤
│  Microfono [1] activo           │  ← Status bar
├─────────────────────────────────┤
│  [Q] Salir  [C] Microfono       │  ← Footer
└─────────────────────────────────┘
```

### Atajos de teclado

| Tecla | Acción |
|-------|--------|
| `Q` | Salir del asistente |
| `C` | Abrir menú de selección de micrófono |

## Comandos de voz

| Comando | Acción |
|---------|--------|
| "abrir bloc de notas" / "abrir notepad" | Abre el Bloc de Notas |
| "abrir calculadora" / "abrir calc" | Abre la Calculadora |
| "abrir navegador" / "abrir internet" | Abre Google Chrome en google.com |
| "buscar en google [consulta]" | Busca en Google |
| "cambiar micrófono" / "cambiar microfono" | Abre menú para cambiar micrófono |
| "salir" / "adiós" / "cerrar asistente" | Cierra el asistente |

Los comandos de apagado del sistema están comentados en el código por seguridad.
Para activarlos, descomenta las líneas correspondientes en `ejecutar_comando()`.

## Configuración

El archivo `config.json` se genera automáticamente:

```json
{
  "mic_index": 1
}
```

- `mic_index`: índice del dispositivo de entrada (micrófono) a usar.
- Si el índice guardado no es válido (el micrófono ya no existe), el asistente abre el menú TUI para seleccionar uno nuevo.

## Sin Textual (fallback)

Si `textual` no está instalado, el asistente funciona en modo texto simple (selección numérica de micrófono + salida por consola).

## Estructura del proyecto

```
audio-vosk/
├── asistente_voz.py              # Asistente de voz (Textual + fallback texto)
├── config.json                   # Configuración persistente (se crea solo)
├── requirements.txt              # Dependencias
├── README.md                     # Este archivo
├── vosk-model-small-es-0.42/     # Modelo de voz (no tocar)
└── .gitignore
```
