## 📌 Plan para el agente (mejora del asistente de voz)

### 🎯 Objetivo
Refactorizar `asistente_voz.py` para:
- Usar un micrófono por defecto (índice `1`) sin preguntar cada vez, pero permitir cambiarlo mediante un **menú TUI interactivo** (solo para configuración).
- Guardar la configuración (micrófono, y futuros parámetros) en `config.json`.
- Añadir una librería TUI ligera (ej. `pick`, `simple-term-menu`, o `questionary`) para seleccionar el micrófono de forma visual, sin depender de `fzf` ni de entrada numérica manual.
- Mantener el asistente **exclusivamente por voz** para los comandos; el menú TUI solo aparece explícitamente para modificar la configuración (por ejemplo, si el usuario lo solicita mediante un comando de voz como "cambiar micrófono", o si el micrófono guardado no es válido).
- El agente **no ejecutará ningún comando** (entorno WSL). Solo entregará el código modificado como texto.

### 📁 Estructura esperada
```
audio-vosk/
├── asistente_voz.py
├── config.json
├── vosk-model-small-es-0.42/ YA ESTA EN EL DIRECTORIO NO TOCAR
└── requirements.txt (opcional, incluye la librería TUI elegida)
```

### 🧩 Pasos de implementación FASE 1 

#### 1. Elección de la librería TUI ligera
El agente deberá elegir una de estas (la más simple y sin dependencias pesadas):
- `pick` (muy ligera, solo menú de selección con flechas)
- `simple-term-menu` (similar)
- `questionary` (un poco más completa, pero aún ligera)
- **No se permite** `fzf`, `prompt_toolkit` completo, `tkinter`, etc.
El agente debe justificar la elección en la respuesta.

#### 2. Estructura modular del script
Organizar el código en secciones:
- **Configuración** (constantes, rutas, valores por defecto)
- **Funciones de persistencia** (`cargar_config`, `guardar_config`)
- **Funciones de audio** (`listar_microfonos`, `validar_microfono`, `inicializar_stream`)
- **Funciones TUI** (`menu_seleccion_microfono`) → muestra la lista de micrófonos usando la librería elegida y devuelve el índice seleccionado.
- **Funciones de comandos** (`ejecutar_comando`)
- **Bucle principal** (escucha y reconocimiento)

#### 3. Implementar configuración persistente (JSON)
- Crear `config.json` con clave `mic_index` (por defecto `1`).
- Al iniciar, cargar configuración. Si no existe, permitira seleccionarla a traves de la tui.
- Validar que el `mic_index` guardado sigue siendo válido (existe y tiene canales de entrada). Si no:
  - Mostrar un mensaje de error y lanzar el menú TUI para seleccionar uno nuevo.
  - Guardar la nueva selección.

#### 4. Añadir el menú TUI para configuración
- Crear una función `menu_configuracion()` que:
  - Obtenga la lista actual de micrófonos (nombre e índice).
  - Presente al usuario un menú interactivo (con flechas/enter) para elegir uno.
  - Devuelva el índice seleccionado.
- Este menú se usará en dos casos:
  - Durante el inicio, si el micrófono guardado no es válido.
  - mostrar los comandos en un recuadro, a medida que los digo en tiempo real, esto lo hace, pero tiene que estar en la tui con buena estica de TUI

#### 5. Refactorizar el bucle principal
- Eliminar la actual selección manual con `input()`.
- Sustituir por:
  - Cargar configuración.
  - Si el micrófono guardado es válido, usarlo directamente.
  - Si no, llamar al menú TUI para seleccionar uno nuevo, guardarlo y usarlo.
- Inicializar el stream de audio con el índice elegido.

#### 6. Manejo de errores y robustez
- Capturar excepciones al leer del micrófono (por si se desconecta). Si ocurre, mostrar mensaje y salir con código de error.
- Si la librería TUI no está instalada, mostrar un mensaje claro y usar el método de selección numérica como fallback (sin depender de la TUI).

#### 7. Mantener todos los comandos de voz originales
- No eliminar ni modificar la lógica de `ejecutar_comando`.
- Los comandos de apagado siguen comentados (o se pueden eliminar si el usuario lo prefiere).

### ⚠️ Reglas de oro (para el agente) – VERSIÓN CORREGIDA

1. **No ejecutar ningún comando** – El agente trabaja en un entorno WSL o de solo lectura. Solo debe entregar el código modificado como texto. No ejecutará `pip`, `python`, ni ningún binario.

2. **No añadir dependencias pesadas** – Está permitido añadir **una librería TUI ligera** (`pick`, `simple-term-menu` o `questionary`). Cualquier otra dependencia debe ser justificada y muy ligera. Nada de `fzf`, `keyboard`, `prompt_toolkit` completo, `pyqt`, `tkinter`, etc.

3. **El menú TUI es solo para configuración** – No se implementarán menús para lanzar comandos de voz. El asistente sigue siendo 100% controlado por voz para sus acciones principales. El menú TUI solo aparecerá para cambiar ajustes (por ahora, el micrófono).

4. **Mantener la compatibilidad con Windows** – Los comandos del sistema (`notepad`, `calc`, `shutdown`) son para Windows. No cambiar a rutas de Linux. Los paths deben usar `os.path` o barras invertidas dobles.

5. **Estructura clara y funciones pequeñas** – Cada función debe tener una única responsabilidad. El código debe estar comentado en ingles.

6. **Manejo de errores básico** – Si el modelo no existe, el micrófono falla, la librería TUI no está instalada o el `config.json` está corrupto, el programa debe informar claramente y salir con un código de error (no explotar silenciosamente). En caso de falta de la librería TUI, usar un menú numérico simple (como el actual).

7. **No borrar funcionalidad existente** – Todos los comandos de voz actuales deben seguir funcionando igual. Solo se añade la persistencia y el menú TUI para configuración.

8. **El agente no debe asumir que el código se ejecutará en WSL** – Aunque el entorno actual sea WSL, el script está pensado para Windows (por los comandos). El agente no debe incluir instrucciones de ejecución en la entrega; solo el código.

### 📦 Entregables esperados

- Archivo `asistente_voz.py` actualizado.
- Archivo `requirements.txt` (con `vosk`, `pyaudio` y la librería TUI elegida).
- Breve lista de cambios (1-2 líneas) indicando qué se modificó y por qué se eligió esa librería TUI.
- El agente no debe generar `config.json` (se creará al ejecutar).

---