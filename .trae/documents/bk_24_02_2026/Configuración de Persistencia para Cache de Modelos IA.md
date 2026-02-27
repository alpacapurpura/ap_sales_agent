## Análisis

Actualmente, tu configuración de Docker Compose para el servicio `api` **no tiene configurado un volumen persistente explícito para** **`model_cache`**.

1. **Situación Actual**:

   * En `docker-compose.yml`, el servicio `api` monta `./backend:/app`.

   * En el código (`semantic_router.py` y `vector_store.py`), la ruta de caché está hardcodeada a `/app/model_cache`.

   * Al estar mapeado todo `./backend` a `/app`, la carpeta `model_cache` se creará dentro de tu carpeta `backend` en el host la primera vez que se descarguen los modelos.

2. **Comportamiento en Producción**:

   * **SÍ se generará automáticamente**: Cuando la aplicación arranque e intente cargar los modelos (al usar `TextEmbedding` o `Ranker`), si no los encuentra, las librerías subyacentes (como `huggingface_hub` o `fastembed`) intentarán descargarlos.

   * **Persistencia**: Dado que `./backend` está montado como volumen, los modelos descargados se guardarán en tu disco en `backend/model_cache`. Esto es bueno para evitar re-descargas, pero puede "ensuciar" tu directorio de código en el servidor.

## Recomendación (Plan)

Para producción, es una mejor práctica usar un **volumen nombrado de Docker** o una ruta de datos específica (`./data/model_cache`) en lugar de mezclar caché con código fuente.

1. Modificar `docker-compose.yml` para montar `model_cache` desde una carpeta dedicada en `./data`.
2. Asegurar que `.gitignore` siga ignorando `backend/model_cache` (ya lo hace, lo cual es correcto).

### Pasos a ejecutar:

1. Editar `docker-compose.yml` para añadir un volumen específico para la caché de modelos, apuntando a `./data/model_cache` en el host y `/app/model_cache` en el contenedor.
2. Esto garantiza que si actualizas el código o cambias la estrategia de montaje, tus modelos de 2GB+ no se pierdan ni se mezclen con el repo.

