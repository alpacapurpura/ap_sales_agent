# Patrón de Diseño: Feature Flag con Enum (Type Safe)

Refinamos la estrategia para usar un **Enum** en `schema.py`, garantizando que solo se usen valores válidos y evitando "magic strings".

## Diseño Actualizado

### 1. Definición de Tipos (`src/core/schema.py`)
Crearemos un Enum para centralizar las opciones:

```python
class PromptSource(str, Enum):
    HYBRID = "hybrid"   # DB > File (Default)
    FILE = "file"       # Local File System only (Dev)
    DB = "db"           # DB Only (Strict Prod)
```

### 2. Configuración (`src/config.py`)
La configuración usará este Enum para validar la entrada del `.env`.

### 3. Lógica (`src/core/prompts/base.py`)
El `PromptLoader` importará `PromptSource` y comparará `settings.PROMPT_SOURCE` contra estos valores tipados.

## Plan de Ejecución

1.  **Actualizar `src/core/schema.py`**: Agregar la clase `PromptSource(str, Enum)`.
2.  **Actualizar `src/config.py`**:
    *   Importar `PromptSource`.
    *   Agregar `PROMPT_SOURCE: PromptSource = PromptSource.HYBRID`.
3.  **Refactorizar `src/core/prompts/base.py`**:
    *   Refactorizar método `render` para implementar el switch lógico.
    *   Extraer lógica de archivos a `_load_from_file` para limpieza.
4.  **Verificación**: Script de prueba que cambie `settings.PROMPT_SOURCE` a `PromptSource.FILE` y verifique el comportamiento.
