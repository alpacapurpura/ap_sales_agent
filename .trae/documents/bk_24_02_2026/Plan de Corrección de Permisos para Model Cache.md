# Solución Refinada: Inicialización de Caché con Docker Compose

## Respuesta a tus dudas
1.  **Entrypoint automático**: Sí, un servicio de inicialización (`init-cache`) en Docker Compose se ejecuta cada vez que levantas el stack (`up`). Si se configura con `restart: no`, se ejecuta una vez, realiza su tarea (corregir permisos) y se detiene, permitiendo que el servicio principal (`api`) arranque después con todo listo.
2.  **Gitignore**: Sí, la carpeta `./data/model_cache` (en el host) debe estar en `.gitignore` para no subir binarios pesados al repositorio.

## Plan Técnico Detallado

Implementaremos el patrón **Init Container** usando Docker Compose. Esto es estándar, limpio y no requiere scripts manuales en el host ni tocar el `Dockerfile` de la aplicación principal.

### 1. Modificar `docker-compose.yml`
Añadiremos un servicio ligero (`init_cache`) que prepara el terreno:

```yaml
  init_cache:
    image: alpine:latest
    command: sh -c "mkdir -p /app/model_cache && chmod 777 /app/model_cache"
    volumes:
      - ./data/model_cache:/app/model_cache
    profiles: ["development", "production"]
```

Luego, haremos que el servicio `api` espere a que este termine:
```yaml
  api:
    # ...
    depends_on:
      init_cache:
        condition: service_completed_successfully
      # ... otros depends
```

### 2. Verificar `.gitignore`
Aseguraremos que `data/model_cache` esté ignorado para mantener el repositorio limpio.

### 3. Ejecución
Al aplicar estos cambios y ejecutar `docker compose up`, el flujo será:
1.  Arranca `init_cache`.
2.  Crea/corrige permisos de la carpeta compartida.
3.  Termina exitosamente.
4.  Arranca `api` (visionarias_brain).
5.  La API descarga los modelos en la carpeta que ahora sí es escribible.

Esta solución es **portátil** (funciona en cualquier servidor nuevo) y **automática**.
