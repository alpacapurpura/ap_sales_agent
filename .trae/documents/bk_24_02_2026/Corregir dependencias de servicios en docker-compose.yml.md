# Corrección de Dependencias en Docker Compose

El error ocurre porque el servicio `client_dashboard_prod` intenta depender de un servicio llamado `api`, pero en tu archivo `docker-compose.yml`, los servicios de API se llaman `api_dev` y `api_prod`.

## Cambios Propuestos

Voy a corregir las referencias en `docker-compose.yml` para que coincidan con los nombres reales de los servicios:

1.  **En `client_dashboard_prod`**:
    *   Cambiar `depends_on: - api` por `depends_on: - api_prod`.

2.  **En `client_dashboard_dev`** (para prevenir el mismo error en desarrollo):
    *   Cambiar `depends_on: - api` por `depends_on: - api_dev`.

Esto resolverá el error `depends on undefined service "api"` y permitirá que `make prod` (o tu comando de docker compose) funcione correctamente.
