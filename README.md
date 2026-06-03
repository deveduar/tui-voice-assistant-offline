# Asistente de Voz — Offline con Vosk + Textual TUI

Asistente por voz en español, 100% offline, con interfaz TUI moderna (Textual).
Reconoce comandos de voz y ejecuta acciones en Windows.

## Requisitos

- Python 3.8+
- Windows 10/11 (recomendado Windows Terminal)
- Microfono funcional
- Opcional: [GlazeWM](https://github.com/glazerdesktop/GlazeWM) para comandos de ventanas

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

## Doble modo de funcionamiento

El asistente tiene **dos modos** segun si `textual` esta instalado:

| Modo | Cuando | Interfaz |
|------|--------|----------|
| **TUI** (recomendado) | `textual` instalado | Interfaz grafica en terminal con Header, RichLog, atajos de teclado |
| **Texto simple** (fallback) | `textual` no instalado | Seleccion numerica de microfono, salida por consola con prints |

No necesitas decidir nada: si `textual` esta disponible se usa la TUI,
si no, cae automaticamente al modo texto.

## Interfaz TUI

```
+------------------------------------------+
|  Asistente de Voz                        |  <- Header
+------------------------------------------+
|  flex abre notepad                       |  <- RichLog (historial)
|  Abriendo el bloc de notas.              |
|  [Escritura] esto es un texto dictado    |
+------------------------------------------+
|  texto parcial de voz...                 |  <- Static (texto parcial)
+------------------------------------------+
|  Escuchando... [small-es-0.42]            |  <- Status bar (incluye modelo)
+------------------------------------------+
|  [Q] Salir  [M] Menu Comandos            |  <- Footer
+------------------------------------------+
```

### Atajos de teclado

| Tecla | Accion |
|-------|--------|
| `Q` | Salir del asistente |
| `M` | Abrir Menu Comandos (activar/desactivar comandos) |
| `M` | Abrir Menu Comandos (activar/desactivar comandos) |
| `Ctrl+P` | Abrir paleta de comandos (micro, modelo, dormir, escritura, ...) |
| `Enter` | (en Menu Comandos) Activar/desactivar comando |
| `Escape` | Salir del Menu Comandos (guarda cambios) |

## Nombre del asistente (wake word)

Puedes anteceder cualquier comando con el nombre del asistente (configurable en `config.json`):

> "**flex** abre notepad"
> "**flex** siguiente escritorio"
> "**flex** ayuda"

Si `require_name` esta en `true` en `config.json`, el nombre es **obligatorio**
para todos los comandos. Por defecto esta en `false` (el nombre es opcional).

Los comandos de dormir/despertar **siempre requieren** el nombre del asistente.

## Modo escritura (dictado)

Activa el modo escritura con **"modo escritura"** / **"modo dictado"**.
En este modo, todo lo que digas se escribe automaticamente en la ventana activa
(usa portapapeles + Ctrl+V). Ideal para tomar notas, escribir documentos, etc.

- Entrar: "modo escritura", "modo dictado", o desde `Ctrl+P`
- Salir: "modo comandos", "modo normal", o desde `Ctrl+P`
- La barra de estado muestra "Escribiendo..." cuando esta activo
- Cada frase dictada se registra en el log con el prefijo `[Escritura]`

## Modo dormir / despertar

- **"[nombre] duerme"** — el asistente deja de procesar comandos (sigue escuchando).
  Muestra "Dormido" en la barra de estado.
- **"[nombre] despierta"** — vuelve al modo normal.
- Tambien se puede desde `Ctrl+P` en la paleta de comandos.
- Siempre requieren el nombre del asistente (ej: "flex duerme").

## Paleta de comandos (Ctrl+P)

La paleta de comandos permite acceder rapidamente a funciones sin usar teclas dedicadas:

- **Microfono**: cambiar microfono activo
- **Modelo**: cambiar modelo de voz (grande/pequeno)
- **Dormir / Despertar**: poner en reposo o activar
- **Modo escritura / Modo comandos**: activar/desactivar dictado
- **Configurar comandos**: abrir Menu Comandos

Al abrirla con `Ctrl+P` muestra un placeholder con las opciones disponibles. Escribe para filtrar.

## Seleccion de modelo de voz

El asistente detecta automaticamente las carpetas `vosk-model-*` en la raiz del proyecto.
Puedes cambiar entre modelos desde la paleta de comandos (`Ctrl+P`, escribe "modelo").
El nombre del modelo activo se muestra en la barra de estado.

Modelos disponibles:
- `vosk-model-small-es-0.42` (~40 MB, rapido, defecto)
- `vosk-model-es-0.42` (~1.5 GB, mas preciso)

El cambio de modelo ocurre en caliente: para el audio, carga el nuevo modelo y reanuda.

## Comandos de voz

### Generales

| Comando | Accion |
|---------|--------|
| "abrir bloc de notas" / "abrir notepad" | Abre el Bloc de Notas |
| "abrir calculadora" / "abrir calc" | Abre la Calculadora |
| "abrir navegador" / "abrir internet" | Abre el navegador en google.com |
| "buscar en google [consulta]" | Busca en Google |
| "abrir [programa]" | Abre un programa configurado (codigo, lapce, notepad plus, explorador, ...) |
| "cambiar microfono" / "cambiar microfono" | Cambia de microfono |
| "salir" / "adios" / "cerrar asistente" | Cierra el asistente |
| "configurar comandos" / "gestionar comandos" | Abre el Menu Comandos |

### GlazeWM (ventanas y escritorios)

Requiere [GlazeWM](https://github.com/glazerdesktop/GlazeWM) instalado y `glazewm.exe` en PATH.

| Comando | Accion |
|---------|--------|
| "abrir terminal" / "abrir cmd" | Abre Windows Terminal |
| "cerrar ventana" | Cierra la ventana activa |
| "siguiente escritorio" / "siguiente" | Siguiente escritorio virtual |
| "anterior escritorio" / "anterior" | Anterior escritorio virtual |
| "ultimo escritorio" / "volver" | Vuelve al ultimo escritorio activo |
| "ir al escritorio [1-9]" / "escritorio [uno-nueve]" | Ir al escritorio N |
| "mover ventana al escritorio [1-9]" | Mueve la ventana activa al escritorio N |
| "maximizar ventana" / "maximizar" | Pantalla completa |
| "minimizar ventana" / "minimizar" | Minimiza la ventana |
| "hacer flotante" / "flotar ventana" | Cambia a modo flotante |
| "hacer fija" / "fijar ventana" | Cambia a modo fijo (tiling) |
| "enfocar izquierda/derecha/arriba/abajo" | Enfoca ventana en esa direccion |
| "mover izquierda/derecha/arriba/abajo" | Mueve la ventana activa en esa direccion |
| "ciclar foco" / "siguiente ventana" | Cambia el foco entre ventanas flotantes/ancladas |
| "cambiar direccion" / "cambiar direccion tiling" | Cambia la direccion de insercion de ventanas |
| "redibujar" / "refrescar ventanas" | Redibuja todas las ventanas |
| "pausar glaze" / "reanudar glaze" | Pausa/reanuda la gestion de ventanas |
| "recargar config" / "recargar configuracion" | Recarga config de GlazeWM |

### Lanzadores personalizados

Los programas se configuran en `config.json` bajo `custom_launchers`. Valores por defecto:

| Voz | Comando |
|-----|---------|
| "abrir codigo" / "abrir visual studio" | `code` (VS Code) |
| "abrir lapce" | `lapce` |
| "abrir notepad plus" / "abrir notepad plus plus" | `notepad++` |
| "abrir explorador" / "abrir archivos" | `explorer` |
| "abrir powershell" | `pwsh` (PowerShell 7) |
| "abrir terminal" | `wt` (Windows Terminal) |
| "abrir ubuntu" / "abrir wsl" | `wt -p Ubuntu` |
| "abrir vst" | `wt -p VST` (perfil SSH) |
| "abrir zed" | `zed` |

Puedes anadir o modificar entradas editando `config.json`.

### Desactivar comandos

Cada comando tiene un campo `enabled`. Los comandos desactivados no
se ejecutan y se muestran en el Menu Comandos con la marca "✘".

El estado de los comandos desactivados se guarda en `config.json`
(disabled_commands) y persiste entre sesiones.

## Configuracion

El archivo `config.json` se genera automaticamente en la raiz del proyecto:

```json
{
  "mic_index": 1,
  "assistant_name": "flex",
  "require_name": false,
  "theme": "textual-dark",
  "model_name": "vosk-model-small-es-0.42",
  "disabled_commands": [],
  "custom_launchers": {
    "codigo": "code",
    "visual studio": "code",
    "lapce": "lapce",
    "notepad plus": "notepad++",
    "notepad plus plus": "notepad++",
    "explorador": "explorer",
    "archivos": "explorer",
    "powershell": "pwsh",
    "terminal": "wt",
    "vst": "wt -p VST",
    "ubuntu": "wt -p Ubuntu",
    "wsl": "wt -p Ubuntu",
    "zed": "zed"
  }
}
```

| Campo | Descripcion |
|-------|-------------|
| `mic_index` | Indice del microfono a usar |
| `assistant_name` | Nombre del asistente (wake word) |
| `require_name` | Si es true, todos los comandos requieren el nombre |
| `theme` | Tema de Textual ("textual-dark", "monokai", "dracula", "gruvbox", etc.) |
| `model_name` | Ruta del modelo Vosk (ej: "vosk-model-small-es-0.42") |
| `disabled_commands` | Lista de patrones de comandos desactivados |
| `custom_launchers` | Mapa de voz → comando para "abrir [programa]" |

Si el microfono guardado no es valido, el asistente abre el menu TUI
para seleccionar uno nuevo.

Para cambiar el tema, edita el campo `theme` en `config.json`. Temas comunes:
`textual-dark`, `monokai`, `dracula`, `gruvbox`, `catppuccin`, `nord`.

## Sin Textual (fallback)

Si `textual` no esta instalado, el asistente funciona en modo texto simple
(seleccion numerica de microfono + salida por consola).
Los comandos de voz funcionan igual, solo cambia la interfaz.

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
    +-- writer.py                  # Portapapeles + Ctrl+V para modo escritura
    +-- ui/
        +-- __init__.py
        +-- app.py                 # VoiceAssistantApp (Textual) + run()
        +-- screens.py             # CommandConfigScreen
        +-- fallback.py            # Modo texto sin Textual
```

## Notas

- Los comandos de apagado del sistema estan comentados en `src/commands.py`
por seguridad. Descomentalos si los necesitas.
- Los comandos de GlazeWM requieren que `glazewm.exe` este en el PATH del sistema.
- Los archivos `__init__.py` permiten que Python trate `src/` y `src/ui/`
como paquetes, habilitando los imports relativos (ej: `from ..audio import ...`).
- El modo escritura usa solo `ctypes` (biblioteca estandar de Python) —
no necesita librerias adicionales.
