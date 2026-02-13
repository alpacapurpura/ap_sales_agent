# Guía de Despliegue a Producción

Este documento detalla los pasos críticos para desplegar la solución en el servidor de producción.

## 1. Prerrequisitos de Red
Antes de iniciar los contenedores, asegúrate de que la red externa para Traefik exista.
El nombre de la red debe coincidir con la variable `TRAEFIK_NETWORK` en tu `.env`.

```bash
# Ejemplo (ajusta el nombre si es diferente en tu .env):
docker network create web_gateway
```

## 2. Variables de Entorno (.env)
Asegúrate de que tu archivo `.env` en producción tenga definidas las siguientes variables críticas para el build del frontend:

```ini
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
NEXT_PUBLIC_API_URL=https://api.tudominio.com
INTERNAL_API_URL=http://api_prod:8000
TRAEFIK_NETWORK=web_gateway
```

## 3. Despliegue Inicial
Para iniciar en modo producción:

```bash
docker compose --profile production up -d --build
```
*Nota: El build del frontend puede tardar unos minutos.*

## 4. Migraciones de Base de Datos
La API en producción no corre migraciones automáticamente. Ejecuta esto tras el despliegue:

```bash
docker exec visionarias_brain alembic upgrade head
```

## 5. Verificación de Evolution API (WhatsApp)
Estás usando la versión `v2.2.2` en producción (con Postgres).
Si vienes de la `v1.8.2` (dev), ten en cuenta que las sesiones antiguas NO se migrarán automáticamente. Tendrás que volver a escanear el QR.

## 6. Backups
Configura un cronjob para respaldar la base de datos diariamente:

```bash
docker exec visionarias_postgres pg_dump -U postgres visionarias > backup_$(date +%F).sql
```
