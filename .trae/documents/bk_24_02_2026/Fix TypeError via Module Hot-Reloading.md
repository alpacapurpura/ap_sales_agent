# Solución: Forzar Recarga de Módulos (Hot-Reload)

El error `TypeError: KnowledgeService.search() got an unexpected keyword argument 'return_raw'` confirma que, aunque el código en disco (`knowledge_service.py`) es correcto y tiene el nuevo argumento, **la aplicación en ejecución (Streamlit) sigue usando la versión antigua de la clase cargada en memoria**.

Esto ocurre porque Streamlit detecta cambios en el archivo principal (`app.py`), pero a veces no recarga profundamente las dependencias importadas (`src.services.*`) si estas ya están cacheadas por Python (`sys.modules`).

## Plan de Acción

Para solucionar esto de raíz y mejorar la experiencia de desarrollo (evitando tener que reiniciar el contenedor Docker con cada cambio en el backend), implementaré una **recarga forzada de módulos** al inicio de `src/admin/app.py`.

1.  **Modificar `src/admin/app.py`**:
    *   Importar `importlib`.
    *   Importar los módulos de servicio (`src.services.vector_store` y `src.services.knowledge_service`).
    *   Ejecutar `importlib.reload()` en ese orden específico antes de importar la clase `KnowledgeService`.

Esto asegurará que cada vez que interactúes con el Admin Panel, este utilice la versión más reciente de tu lógica de negocio.

### Código a Insertar

```python
import importlib
import src.services.vector_store
import src.services.knowledge_service

# Force reload logic modules to apply changes immediately
importlib.reload(src.services.vector_store)
importlib.reload(src.services.knowledge_service)

from src.services.knowledge_service import KnowledgeService
```