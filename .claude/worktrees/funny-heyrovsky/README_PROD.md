# Guía de Despliegue a Producción

Este documento detalla los pasos críticos para desplegar la solución en el servidor de producción.

## 1. Prerrequisitos de Red
Antes de iniciar los contenedores, asegúrate de que la red externa para Traefik exista.
El nombre de la red debe coincidir con la variable `TRAEFIK_NETWORK` en tu `.env.prod`.

```bash
# Ejemplo (ajusta el nombre si es diferente en tu .env):
docker network create web_gateway
```

## 2. Variables de Entorno (.env.prod)
Asegúrate de que tu archivo `.env.prod` en producción tenga definidas las siguientes variables críticas para frontend/backend y carril Shopify:

```ini
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
NEXT_PUBLIC_API_URL=https://api.tudominio.com
NEXT_PUBLIC_APP_URL=https://app.tudominio.com
INTERNAL_API_URL=http://backend:8000
SHOPIFY_API_KEY=...
SHOPIFY_API_SECRET=...
SHOPIFY_APP_URL=https://api.tudominio.com
TRAEFIK_NETWORK=web_gateway
```

## 3. Despliegue Inicial
Para iniciar en modo producción:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
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

## 7. Promoción controlada a App Store
Antes de publicar cambios al canal de distribución, ejecuta este flujo:

1. Completar gate dev: smoke tests, validación en `visionarias.lat`, OAuth/compliance en verde.
2. Activar carril productivo:
   ```bash
   make shopify-config-prod
   make shopify-config-status
   ```
3. Publicar la configuración productiva en Shopify Partner:
   ```bash
   cd shopify_app
   npx shopify app config push
   ```
4. Ejecutar despliegue productivo y validar instalación/reautorización en tienda de producción.
5. Enviar/publicar actualización en App Store solo con evidencia de checks aprobados.

## 8. Rollback operativo (Shopify + despliegue)
Si un release genera fallos de OAuth, callback o compliance:

1. Detener promoción y comunicar incidente.
2. Reaplicar configuración prod estable:
   ```bash
   make shopify-config-prod
   make shopify-config-status
   cd shopify_app
   npx shopify app config push
   ```
3. Volver al build/commit estable previo en infraestructura productiva.
4. Verificar recuperación con 4 checks mínimos:
   - App embebida carga correctamente.
   - Callback OAuth finaliza sin loop.
   - Endpoints `customers/data_request`, `customers/redact` y `shop/redact` responden 2xx.
   - Logs backend sin 401/403/500 en handshake.
5. Mover investigación y fix al carril dev antes de intentar una nueva promoción.
