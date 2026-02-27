# Corrección de Ruta de Caché

Tienes toda la razón, la carpeta `model_cache` ya existe y de hecho **ya se usa correctamente en `vector_store.py`**, pero **se olvidó configurar en `router_service.py`**.

El diagnóstico es:
1. `vector_store.py` -> Usa `/app/model_cache` (Correcto).
2. `router_service.py` -> No especifica ruta -> **Descarga en `/tmp` cada vez** (Incorrecto).

## Plan de Ejecución
1. **Modificar `src/services/router_service.py`**:
   - Agregar el parámetro `cache_dir="/app/model_cache"` al inicializar `TextEmbedding`.

Esto forzará al Router a usar los modelos que ya tienes descargados, eliminando el tiempo de espera y el timeout de Telegram inmediatamente.

¿Procedo con esta corrección?