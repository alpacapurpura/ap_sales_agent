# Solución: Inyección de Variables Vía `env_file`

Tienes toda la razón. Para evitar cualquier riesgo de "hardcoding" y mantener el `docker-compose.yml` limpio, la mejor práctica es usar la directiva `env_file`. Esto instruye a Docker a leer las variables directamente del archivo `.env` e inyectarlas en el contenedor, sin tener que declararlas una por una en el YAML.

## Pasos de Ejecución

1.  **Actualizar `docker-compose.yml`**:
    *   En el servicio `client_dashboard`, agregar la directiva `env_file: - .env`.
    *   Esto asegurará que `CLERK_SECRET_KEY` (y cualquier otra config futura) pase del archivo `.env` al entorno de ejecución de Node.js automáticamente.

    ```yaml
    client_dashboard:
      # ...
      env_file:
        - .env  <-- Esto carga todo el archivo .env en el contenedor
      # ...
    ```

2.  **Aplicar Cambios**:
    *   Reconstruir el contenedor: `docker compose --profile development up -d --build client_dashboard`.

3.  **Verificación**:
    *   Comprobar en los logs que el error `Missing secretKey` ha desaparecido.
    *   Confirmar que el login funciona en `http://localhost:3000`.

Esta solución cumple estrictamente con tu regla: el archivo `.env` es la única fuente de verdad y no hay claves expuestas en el código del orquestador.
