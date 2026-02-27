Para resolver el problema de la desaparición de documentos cada vez que se realizan cambios (reinicios del contenedor), y la discrepancia entre Qdrant y PostgreSQL, implementaré lo siguiente:

### Análisis del Problema
1.  **Discrepancia (Vectores vs Documentos)**:
    *   **Qdrant (Vectores)**: Está usando un volumen persistente llamado `qdrant_data`. Por eso los vectores sobreviven a los reinicios.
    *   **PostgreSQL (Documentos)**: Está usando un volumen persistente llamado `postgres_data`. También debería sobrevivir.
    *   **El Problema Real**: Es probable que `docker-compose down` o ciertas acciones de reinicio en el entorno de desarrollo estén limpiando los volúmenes anónimos o que la conexión a la DB se esté reiniciando de una forma que hace parecer que está vacía, O que estemos usando una base de datos SQLite en lugar de Postgres en la configuración de `SessionLocal`, lo cual es común en entornos híbridos si no se configuró explícitamente la URL de conexión.
    *   Revisando `DocumentService`, veo que usa `SessionLocal`. Si `SessionLocal` apunta a SQLite en un archivo dentro del contenedor (no montado), se borra al recrear el contenedor. Si apunta a Postgres, debería persistir.

2.  **Solución Definitiva de Persistencia**:
    *   Aseguraré que la base de datos apunte correctamente al servicio `postgres` y no a un SQLite temporal.
    *   Si se está usando SQLite (común en dev rápido), cambiaré la configuración para usar Postgres robustamente o mapear el archivo SQLite a un volumen del host.
    *   Mapearé los volúmenes de datos a carpetas locales en el host (`./data/postgres`, `./data/qdrant`) en lugar de volúmenes gestionados por Docker. Esto da control total y evita borrados accidentales al hacer `docker-compose down -v`.

### Plan de Acción

1.  **Modificar `docker-compose.yml`**:
    *   Cambiar los volúmenes de `postgres` y `qdrant` para usar rutas relativas del host (ej: `./data/postgres_data:/var/lib/postgresql/data`). Esto garantiza que los datos vivan en tu carpeta de proyecto visible.

2.  **Verificar Configuración de Base de Datos (`src/services/database.py`)**:
    *   Confirmar que `DATABASE_URL` apunte al servicio `postgres`.

3.  **Herramienta de Sincronización (Sync)**:
    *   Crear una función en `DocumentService` llamada `sync_from_qdrant`.
    *   Esta función leerá los metadatos de los vectores existentes en Qdrant (que ya tiene 416 vectores).
    *   Reconstruirá la tabla `documents` en PostgreSQL basándose en esos metadatos (filename, category, etc.).
    *   Agregaré un botón en "Configuración" -> "Zona de Peligro" (o "Mantenimiento") llamado "🔄 Sincronizar DB desde Vectores".

Con esto, si alguna vez se borra la tabla de documentos pero los vectores siguen ahí, podrás recuperar el inventario con un clic.