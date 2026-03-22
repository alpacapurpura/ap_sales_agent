# Cambios Propuestos para docker-compose.yml

Actualmente los servicios usan la sintaxis antigua (`mem_limit`, `cpus`) y en total suman más de **10.5 GB** de memoria límite, lo que causa cuellos de botella en WSL 2. 

Se propone migrar **todos** los servicios a la nueva sintaxis `deploy.resources.limits` y ajustar los valores para reducir el consumo total a **~7.2 GB**.

## Detalles por Servicio:

1. **api_dev** (FastAPI)
   - *Actual:* 1.2GB / 1.5 CPUs
   - *Nuevo:* 1024M / 1.0 CPUs
2. **client_dashboard_dev** (Next.js)
   - *Actual:* 1.7GB / 1.75 CPUs
   - *Nuevo:* 1024M / 1.0 CPUs (Next.js requiere un poco más que 512M para compilar rápido)
3. **whatsapp_engine**
   - *Actual:* 1.2GB / 1.0 CPUs
   - *Nuevo:* 1024M / 0.50 CPUs
4. **admin_dashboard_dev, frontend_tooling, backend_tooling, qdrant, postgres, scheduler, worker**
   - *Nuevo:* 512M / 0.50 CPUs (Valor por defecto solicitado)
5. **redis, tunnel**
   - *Nuevo:* 256M / 0.25 CPUs
6. **init_cache**
   - *Nuevo:* 128M / 0.25 CPUs (Antes no tenía límites)

## Estructura a aplicar (Ejemplo):
```yaml
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 512M
        reservations:
          memory: 256M
```
*(Se eliminarán las claves antiguas `mem_limit`, `mem_reservation`, `cpus` de la raíz de cada servicio).*