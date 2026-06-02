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
|  flex escritorio 3                       |
|  Yendo al escritorio 3.                  |
+------------------------------------------+
|  buscando inteligencia artificial...     |  <- Static (texto parcial)
+------------------------------------------+
|  Escuchando... / Dormido                 |  <- Status bar
+------------------------------------------+
|  [Q] Salir  [C] Micro  [H] Ayuda         |
|  [W] Despertar  [D] Desactivados         |  <- Footer
+------------------------------------------+
```

### Atajos de teclado

| Tecla | Accion |
|-------|--------|
| `Q` | Salir del asistente |
| `C` | Abrir menu de seleccion de microfono |
| `H` | Abrir pantalla de ayuda con todos los comandos |
| `W` | Despertar al asistente (si esta dormido) |
| `D` | Alternar vista de comandos desactivados en ayuda |

## Nombre del asistente (wake word)

Puedes anteceder cualquier comando con el nombre del asistente (configurable en `config.json`):

> "**flex** abre notepad"
> "**flex** siguiente escritorio"
> "**flex** ayuda"

Si `require_name` esta en `true` en `config.json`, el nombre es **obligatorio**
para todos los comandos. Por defecto esta en `false` (el nombre es opcional).

Los comandos de dormir/despertar **siempre requieren** el nombre del asistente.

## Modo dormir / despertar

- **"flex duerme"** — el asistente deja de procesar comandos (sigue escuchando).
  Muestra "Dormido" en la barra de estado.
- **"flex despierta"** — vuelve al modo normal.
- Tambien puedes usar la tecla `W` para despertar.

## Comandos de voz

### Generales

| Comando | Accion |
|---------|--------|
| "abrir bloc de notas" / "abrir notepad" | Abre el Bloc de Notas |
| "abrir calculadora" / "abrir calc" | Abre la Calculadora |
| "abrir navegador" / "abrir internet" | Abre el navegador en google.com |
| "buscar en google [consulta]" | Busca en Google |
| "cambiar microfono" / "cambiar microfono" | Abre menu para cambiar microfono |
| "ayuda" / "comandos" / "que puedes hacer" | Muestra la pantalla de ayuda |
| "salir" / "adios" / "cerrar asistente" | Cierra el asistente |
| "[nombre] duerme" | Pone el asistente en reposo |
| "[nombre] despierta" | Activa el asistente |

### GlazeWM (ventanas y escritorios)

Requiere [GlazeWM](https://github.com/glazerdesktop/GlazeWM) instalado y `gwm.exe` en PATH.

| Comando | Accion |
|---------|--------|
| "abrir terminal" / "abrir cmd" | Abre Windows Terminal |
| "cerrar ventana" | Cierra la ventana activa |
| "siguiente escritorio" / "siguiente" | Siguiente escritorio virtual |
| "anterior escritorio" / "anterior" | Anterior escritorio virtual |
| "ir al escritorio [1-9]" / "escritorio [uno-nueve]" | Ir al escritorio N |
| "mover ventana al escritorio [1-9]" | Mueve la ventana activa al escritorio N |
| "maximizar ventana" / "maximizar" | Pantalla completa |
| "minimizar ventana" / "minimizar" | Minimiza la ventana |
| "hacer flotante" / "flotar ventana" | Cambia a modo flotante |
| "hacer fija" / "fijar ventana" | Cambia a modo fijo (tiling) |
| "recargar config" / "recargar configuracion" | Recarga config de GlazeWM |

### Desactivar comandos

Cada comando tiene un campo `enabled` en `src/commands.py`. Los comandos
desactivados no se ejecutan pero pueden mostrarse en la ayuda con la etiqueta
"(desactivado)" segun la configuracion de `show_disabled_commands`.

El estado de los comandos desactivados se guarda en `config.json`
(disabled_commands) y persiste entre sesiones.

## Configuracion

El archivo `config.json` se genera automaticamente en la raiz del proyecto:

```json
{
  "mic_index": 1,
  "assistant_name": "flex",
  "require_name": false,
  "show_disabled_commands": true,
  "disabled_commands": []
}
```

| Campo | Descripcion |
|-------|-------------|
| `mic_index` | Indice del microfono a usar |
| `assistant_name` | Nombre del asistente (wake word) |
| `require_name` | Si es true, todos los comandos requieren el nombre |
| `show_disabled_commands` | Muestra comandos desactivados en la ayuda |
| `disabled_commands` | Lista de patrones de comandos desactivados |

Si el microfono guardado no es valido, el asistente abre el menu TUI
para seleccionar uno nuevo.

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
    +-- ui/
        +-- __init__.py
        +-- app.py                 # VoiceAssistantApp (Textual) + run()
        +-- screens.py             # MicConfigScreen + HelpScreen
        +-- fallback.py            # Modo texto sin Textual
```

## Notas

- Los comandos de apagado del sistema estan comentados en `src/commands.py`
por seguridad. Descomentalos si los necesitas.
- Los comandos de GlazeWM requieren que `gwm.exe` este en el PATH del sistema.
- Los archivos `__init__.py` permiten que Python trate `src/` y `src/ui/`
como paquetes, habilitando los imports relativos (ej: `from ..audio import ...`).
