# Diagnóstico de Incidente en Backend

He revisado los logs del contenedor `visionarias_brain` y he identificado la causa raíz de la falla que impide el inicio del servicio.

## 🔍 Hallazgos

* **Error Crítico:** `ModuleNotFoundError: No module named 'src.services.models'`

* **Ubicación:** Archivo `/app/src/core/prompts/base.py`, línea 9.

* **Causa:** Se está intentando importar `PromptVersion` desde una ruta incorrecta (`src.services.models`).

* **Contexto Arquitectónico:** Según las reglas de arquitectura y la estructura actual de archivos, los modelos de base de datos residen en `src.services.db.models`, no en `src.services.models`.

## 🛠️ Plan de Solución

### 1. Corregir Importación en el Core

Modificaré `backend/src/core/prompts/base.py` para apuntar a la ubicación correcta del modelo.

**Cambio propuesto:**

```python
# Antes
from src.services.models import PromptVersion

# Después
from src.services.db.models import PromptVersion
```

### 2. Limpieza de Scripts (Mantenimiento)

He detectado que el mismo error de importación existe en varios scripts de utilidad. Aunque no afectan el servicio principal, es profesional corregirlos para evitar futuros errores en tareas de mantenimiento.

* `backend/scripts/seed_prompts.py`

* `backend/scripts/update_db_prompts.py`

### 3. Verificación

Una vez aplicado el parche:

1. Reiniciaré el contenedor afectado si es necesario (Docker suele recargar cambios en python automáticamente con hot-reload, pero dada la falla de inicio, el contenedor se reiniciará solo).
2. Verificaré el estado del contenedor con `docker ps` para confirmar que está `Up`.
3. Revisaré los logs nuevamente para asegurar que el servicio arrancó correctamente.

