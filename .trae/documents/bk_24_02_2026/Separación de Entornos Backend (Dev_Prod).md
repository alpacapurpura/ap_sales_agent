Analizando tu backend, la situación es diferente al frontend. Tu `backend/Dockerfile` **ya implementa Multi-Stage Builds** correctamente (separando `builder` de `final`), lo cual es excelente.

Sin embargo, al igual que en el frontend, el `docker-compose.yml` actual mezcla configuraciones de desarrollo y producción en un solo servicio.

### El Problema
Actualmente, el servicio `api` monta `./backend:/app`. Esto es ideal para desarrollo (hot-reload), pero en producción:
1.  **Sobrescribe el código de la imagen**: Ignora el código "congelado" en la imagen Docker y usa los archivos del host.
2.  **Riesgo de seguridad/estabilidad**: Cambios accidentales en el servidor en vivo afectarían inmediatamente al contenedor.
3.  **Comando de Dev**: Usa `uvicorn` directo. En producción, a menudo se prefiere `gunicorn` con workers para mayor concurrencia (aunque Uvicorn puro es aceptable en muchos casos, Gunicorn es más robusto).

### La Solución Propuesta
Voy a aplicar la misma lógica de "Separación de Servicios" que hicimos en el frontend para garantizar un entorno de producción inmutable y performante.

1.  **Refactorizar `docker-compose.yml`**:
    *   **`api_dev`**:
        *   Profile: `development`
        *   Volúmenes: `./backend:/app` (Hot reload activado).
        *   Comando: `uvicorn ... --reload` (Explícitamente con reload).
    *   **`api_prod`**:
        *   Profile: `production`
        *   Volúmenes: **Ninguno** (Usa el código copiado en el Dockerfile).
        *   Comando: `gunicorn -k uvicorn.workers.UvicornWorker src.main:app` (Servidor de producción robusto) o `uvicorn` sin reload.
    *   **`admin_dashboard`**: Aplicar lógica similar si deseas separar dev/prod para el panel de administración, o mantenerlo simple si es interno. (Sugerencia: Separarlo también para consistencia).

2.  **Ajuste en `backend/Dockerfile`**:
    *   Actualmente es correcto, pero verificaré que `gunicorn` esté en `requirements.txt` si decidimos usarlo para producción.

¿Procedemos a separar los servicios Backend en `dev` y `prod` en el `docker-compose.yml`?
