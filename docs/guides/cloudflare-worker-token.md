# Fix: Cloudflare Worker API Token

## Contexto

El job `☁️ Deploy Cloudflare Worker` del pipeline de producción falla con:

```
Authentication error [code: 10000]
A request to the Cloudflare API (/memberships) failed.
Unable to retrieve email for this user.
Are you missing the User->User Details->Read permission?
```

**Este job tiene `continue-on-error: true` — no bloquea el deploy.** Pero hay que corregirlo para que el worker `sentry-slack-alerts` se actualice automáticamente en cada release.

---

## Paso 1 — Crear nuevo token en Cloudflare

1. Abrí: `https://dash.cloudflare.com/profile/api-tokens`
2. Click **"Create Token"**
3. Buscá el template **"Edit Cloudflare Workers"** → click **"Use template"**

> Usar el template garantiza que todos los permisos requeridos por `wrangler deploy` estén incluidos.

Los permisos que se cargan automáticamente son:
- `Account > Workers Scripts > Edit`
- `Account > Workers KV Storage > Edit`
- `User > User Details > Read` ← el que faltaba

4. En **"Account Resources"** → seleccioná `All accounts` (o `Contact@nicolify.com's Account`)
5. Click **"Continue to summary"** → **"Create Token"**
6. **Copiá el token — solo se muestra una vez**

---

## Paso 2 — Actualizar el secret en GitHub

1. Abrí: `https://github.com/alpacapurpura/ap_sales_agent/settings/secrets/actions`
2. Buscá `CLOUDFLARE_API_TOKEN`
3. Click en el ícono de editar (lápiz)
4. Pegá el nuevo token
5. Click **"Update secret"**

---

## Paso 3 — Verificar el token (opcional)

Antes de hacer push, verificá que el token funcione localmente:

```bash
cd workers/sentry-slack-alerts
CLOUDFLARE_API_TOKEN=<tu-nuevo-token> npx wrangler whoami
```

Debe mostrar `Contact@nicolify.com's Account` sin errores.

---

## Paso 4 — Confirmar en el próximo deploy

En el siguiente push a `main`, el job `☁️ Deploy Cloudflare Worker` debe mostrar:

```
✓ Deploy sentry-slack-alerts worker
```

---

## Por qué falla el token actual

El error `code: 10000` indica que el token existe y está activo, pero le falta el permiso `User: User Details: Read`. Wrangler necesita este permiso para llamar a `/memberships` y determinar a qué cuenta hacer el deploy. Si el token fue creado con "Custom token" en lugar del template "Edit Cloudflare Workers", ese permiso no se agrega por defecto.

---

## Worker afectado

- **Nombre:** `sentry-slack-alerts`
- **Ubicación:** `workers/sentry-slack-alerts/`
- **Account ID:** `8bf41e35bb65044b2cf5e471bd456fc0`
- **Workflow step:** `.github/workflows/deploy-prod.yml` → job `deploy-worker`
