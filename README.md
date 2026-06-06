# Asistente de Voz Offline

Asistente por voz en español, 100% offline (Vosk), con interfaz TUI moderna (Textual) y comandos configurables vía JSON.

## Requisitos

- Python 3.10+
- Windows 10/11 (recomendado Windows Terminal)
- Micrófono funcional
- Opcional: [GlazeWM](https://github.com/glazerdesktop/GlazeWM) para comandos de ventanas

## Instalación

```cmd
pip install -r requirements.txt
```

Esto instala: `vosk`, `pyaudio`, `textual`.

Descarga un modelo Vosk en español y extráelo en la raíz del proyecto:

- **Modelo pequeño** (~40 MB, rápido): `vosk-model-small-es-0.42`
- **Modelo grande** (~1.5 GB, más preciso): `vosk-model-es-0.42`

## Uso

```cmd
python main.py
```

En la primera ejecución:
1. Se detectan automáticamente los modelos Vosk disponibles.
2. Si no hay `config.json` o el micrófono guardado no es válido, se abre un menú TUI para seleccionar el micrófono.
3. El asistente carga el modelo de forma asíncrona (no bloquea la TUI).
4. Comienza la escucha continua.

## Cómos rápidos

| Pregunta | Respuesta |
|----------|-----------|
| Cómo abro la paleta de comandos | `Ctrl+P` |
| Cómo cierro el asistente | `Q` o voz: *"flex salir"* |
| Cómo activo el dictado | Voz: *"modo escritura"* |
| Cómo desactivo el dictado | Voz: *"modo comandos"* |
| Cómo duermo al asistente | Voz: *"flex duerme"* (cualquier nombre de la lista sirve) |
| Cómo veo/desactivo comandos | `M` o voz: *"configurar comandos"* |
| Cómo cambio de tema | `Ctrl+P` → escribe "tema" |
| Cómo cambio de micrófono | `Ctrl+P` → escribe "micro" |
| Cómo cambio de modelo | `Ctrl+P` → escribe "modelo" |

## Widgets y atajos

```
┌─────────────────────────────────────────────┐
│  Flex — Asistente de Voz                    │  Header
├─────────────────────────────────────────────┤
│  flex abre notepad                          │  RichLog (historial)
│  Abriendo el bloc de notas.                 │
│  [Escritura] esto es texto dictado          │
├─────────────────────────────────────────────┤
│  texto parcial de voz...                    │  Static (texto parcial)
├─────────────────────────────────────────────┤
│  💤 Dormido · modelo-small-es-0.42 · Mic 1  │  Status bar
├─────────────────────────────────────────────┤
│  [Q] Salir  [M] Comandos  [Ctrl+P] Paleta   │  Footer
└─────────────────────────────────────────────┘
```

| Tecla | Acción |
|-------|--------|
| `Q` | Salir |
| `M` | Menú de comandos (activar/desactivar) |
| `Ctrl+P` | Paleta de comandos |
| `Enter` | (en menú comandos) Alternar comando |
| `Esc` | (en menú comandos) Guardar y cerrar |

En la paleta (`Ctrl+P`) escribe palabras clave para filtrar:

- **micro** — cambiar micrófono
- **modelo** — cambiar modelo de voz
- **modo** — dormir / despertar / escritura / comandos
- **tema** — cambiar tema de la interfaz
- **comandos** — abrir configuración de comandos
- **asistente** — salir

## Comandos de voz

Los comandos se definen en `commands_config.json`. Cada entrada tiene:

```json
{
  "patterns": ["abrir bloc de notas", "abrir notepad"],
  "description": "Abre el Bloc de Notas",
  "category": "general",
  "action": "programa",
  "program": "notepad"
}
```

### Tipos de acción

| Tipo | Qué hace | Parámetros |
|------|----------|------------|
| `programa` | Ejecuta un programa | `program`, `program_args` |
| `url` | Abre una URL en el navegador | `url`, `needs_query` |
| `teclear` | Envía teclas a la ventana activa | `keys` |
| `gwm` | Comando para GlazeWM | `gwm_args` |
| `shell` | Ejecuta un comando shell | `shell_cmd` |
| `abrir_catchall` | Busca un programa por nombre | (usa `query` directamente) |

`needs_query: true` indica que el comando espera texto adicional (ej: *"buscar en youtube cómo hacer paella"` → busca el query).

## Modo escritura (dictado)

Actívalo con *"modo escritura"* o *"modo dictado"*. Todo lo que digas se inyecta en la ventana activa.

- **Entrar**: voz *"modo escritura"*, *"modo dictado"* o `Ctrl+P` → escritura
- **Salir**: voz *"modo comandos"*, *"modo normal"*, *"salir de escritura"* o `Ctrl+P` → comandos
- **Método**: `SendMessageW(WM_CHAR)` — inyección directa en la cola de mensajes de la ventana, sin portapapeles ni `SendInput`

## Nombre del asistente (wake word)

En `config.json`:

```json
{
  "assistant_names": ["flex"],
  "require_name": false
}
```

- `assistant_names` — lista de palabras para anteceder comandos (ej: *"flex abre notepad"*, *"talón abre notepad"*)
- `require_name` — si es `true`, **todos** los comandos requieren algún nombre de la lista
- El primer nombre de la lista se usa en mensajes de ayuda y display

Los comandos de dormir/despertar siempre requieren el nombre.

> La versión anterior usaba `assistant_name` (string). La migración a `assistant_names` (lista) es automática en el primer arranque.

## Gestión de comandos

### Desactivar comandos

Desde el menú (`M` o voz *"configurar comandos"*):
- Los comandos desactivados se marcan con ✘
- Al hablar un comando desactivado: *"Comando deshabilitado: ..."*
- El estado persiste entre sesiones en `config.json > disabled_commands`
- El menú no se apila si ya está abierto

### Comandos fallidos

Los comandos que no se reconocen se registran en `failed_commands.jsonl` con timestamp. Útil para detectar patrones que faltan y añadirlos a `commands_config.json`.

## Configuración

`config.json` se genera automáticamente:

```json
{
  "mic_index": 1,
  "assistant_names": ["flex"],
  "require_name": false,
  "theme": "catppuccin-mocha",
  "model_name": "vosk-model-small-es-0.42",
  "disabled_commands": []
}
```

| Campo | Descripción |
|-------|-------------|
| `mic_index` | Índice del micrófono |
| `assistant_names` | Lista de nombres del asistente (wake words) |
| `require_name` | Si es `true`, nombre obligatorio para todo |
| `theme` | Tema Textual (`catppuccin-mocha`, `dracula`, `gruvbox`, `monokai`, etc.) |
| `model_name` | Carpeta del modelo Vosk |
| `disabled_commands` | IDs de comandos desactivados |

Se puede cambiar el tema desde la paleta (`Ctrl+P` → tema) y se guarda automáticamente.

## Estructura

```
audio-vosk/
├── main.py                        # Punto de entrada
├── config.json                    # Configuración persistente (se crea solo)
├── commands_config.json           # Comandos de voz editables por el usuario
├── failed_commands.jsonl          # Comandos no reconocidos (se crea solo)
├── requirements.txt
├── vosk-model-small-es-0.42/      # Modelo de voz
├── src/
│   ├── config.py                  # Carga/guarda config.json
│   ├── audio.py                   # AudioManager (hilo + cola)
│   ├── commands.py                # CommandRegistry + acciones genéricas
│   ├── writer.py                  # SendMessageW(WM_CHAR) para dictado
│   └── ui/
│       ├── app.py                 # VoiceAssistantApp (Textual)
│       ├── screens.py             # CommandConfigScreen
│       └── fallback.py            # Modo texto sin Textual
```

## Notas técnicas

- **Salida limpia**: flag `_exiting` + restauración manual de mouse tracking del terminal (`\x1b[?1000l\x1b[?1002l\x1b[?1006l`)
- **Robustez**: `_check_queue` envuelto en `try/except`; reinicio automático del hilo de audio si falla
- **No bloqueante**: `subprocess.Popen()` en todos los lanzadores
- **Validación**: `shutil.which()` antes de ejecutar programas
- **Dictado**: solo `ctypes` (sin librerías de terceros); `SendMessageW(WM_CHAR)` inyección carácter por carácter
- **Rutas absolutas**: resueltas contra `PROJECT_ROOT` mediante `os.path.join`
