# Instagram DM — Setup Checklist para Visionarias

**Fecha:** 2026-03-30
**Estado:** ManyChat conectado en Settings. Pendiente: configurar flows + Meta webhooks.

---

## 1. Configurar ManyChat External Requests (OBLIGATORIO)

ManyChat ya esta conectado en Nicolify, pero los flows de ManyChat todavia no envian eventos a nuestro webhook. Sin esto, no llegan datos.

### Webhook URL

```
POST https://<tu-dominio>/api/webhooks/manychat/d68f4af3-3871-4f09-9cbd-a9856235025f
```

> Reemplaza `<tu-dominio>` con el dominio de produccion (o usa ngrok para pruebas locales).

### Paso 1: Flow "Default Reply" (captura inicial)

1. Abre ManyChat → **Automation** → **Default Reply** (o tu flow principal de IG)
2. En el primer paso del flow, agrega un bloque **External Request**
3. Configura:
   - **Request Type:** POST
   - **URL:** `https://<tu-dominio>/api/webhooks/manychat/d68f4af3-3871-4f09-9cbd-a9856235025f`
   - **Headers:** `Content-Type: application/json`
   - **Body → Custom (JSON):**

```json
{
  "event_type": "subscriber.new",
  "subscriber_id": "{{subscriber_id}}",
  "channel": "instagram",
  "first_name": "{{first_name}}",
  "last_name": "{{last_name}}",
  "email": "{{email}}",
  "phone": "{{phone}}",
  "ig_username": "{{ig_username}}"
}
```

4. Click **Test Request** (con un subscriber de prueba)
5. Verifica que responde `{"status": "processed", "event": "subscriber.new"}`

### Paso 2: Comment Triggers (atraccion)

Si tienes flows que se activan por comentarios en posts:

1. Abre el flow de Comment Trigger
2. Agrega **External Request** al inicio:

```json
{
  "event_type": "comment.trigger",
  "subscriber_id": "{{subscriber_id}}",
  "channel": "instagram",
  "ig_username": "{{ig_username}}"
}
```

### Paso 3: Tags de Calificacion (nurture/oportunidad)

Para cada flow que aplique tags clave:

```json
{
  "event_type": "tag.applied",
  "subscriber_id": "{{subscriber_id}}",
  "channel": "instagram",
  "tag_name": "{{last_applied_tag}}",
  "ig_username": "{{ig_username}}"
}
```

**Tags que rastreamos:**
| Tag | Stage | Metrica |
|---|---|---|
| `Solicito_reunion` | Opportunity | meetings_requested |
| `quiz_started` | Nurture | qualified_leads |
| `Estrategia` | Nurture | qualified_leads |
| `link_clicked` | Nurture | link_clicks |

### Paso 4: Flows BOFU (oportunidad)

Para flows de fondo de embudo (ventas, consultas):

```json
{
  "event_type": "flow.triggered",
  "subscriber_id": "{{subscriber_id}}",
  "channel": "instagram",
  "flow_ns": "{{flow_ns}}",
  "flow_name": "{{flow_name}}",
  "ig_username": "{{ig_username}}"
}
```

> El nombre del flow debe contener "BOFU" para clasificar como oportunidad.

### Verificacion

Despues de configurar, envia un DM de prueba a @visionarias.lat y ejecuta:

```bash
docker logs visionarias_brain_dev --tail 30 2>&1 | grep manychat
```

Debe aparecer: `manychat_webhook_processed tenant_id=d68f4af3... event=manychat_subscriber_created`

---

## 2. Suscribir Meta IG Messaging Webhook (RECOMENDADO)

Esto activa la ruta directa: cuando alguien envia un DM a @visionarias.lat, Meta envia un webhook → el sales_agent procesa el mensaje → se crea un journey_event con `message_received`. Es la forma mas completa de rastrear conversaciones.

### Paso 1: Ir al Meta App Dashboard

1. Abre https://developers.facebook.com/apps/
2. Selecciona la app **Nicolify** (o el nombre que tenga)
3. Ve a **Webhooks** en el menu lateral

### Paso 2: Configurar Instagram Webhooks

1. En la seccion **Instagram**, haz click en **Subscribe to this object**
2. Agrega el campo `messages`
3. **Callback URL:** `https://<tu-dominio>/api/connections/meta/webhook`
4. **Verify Token:** (busca `META_WEBHOOK_VERIFY_TOKEN` en tu `.env`)
5. Click **Verify and Save**

### Paso 3: Verificar suscripcion

1. Envia un DM a @visionarias.lat desde otra cuenta
2. Verifica en logs:

```bash
docker logs visionarias_brain_dev --tail 50 2>&1 | grep -i "incoming_message\|message_received\|ig_dm"
```

### Paso 4: Verificar datos en DB

```bash
docker exec -t visionarias_postgres psql -U postgres -d visionarias_logs -c \
  "SELECT event_name, properties->>'channel_slug', COUNT(*) FROM journey_events WHERE tenant_id = 'd68f4af3-3871-4f09-9cbd-a9856235025f' AND event_name = 'message_received' GROUP BY 1, 2;"
```

---

## 3. Solicitar Advanced Access para instagram_manage_messages (NECESARIO para backfill)

### Error actual de Meta

Al intentar extraer conversaciones historicas via la Conversations API, Meta devuelve:

```
HTTP 400 — Error code: -2, Subcode: 2534084
Tipo: OAuthException

"Tiempo de espera de la solicitud agotado"

"Se agoto el tiempo de espera de tu consulta porque tienes demasiadas
conversaciones con usuarios que no tienen un rol en la app. Solicita
acceso avanzado al permiso instagram_manage_messages o reduce el numero
de conversaciones existentes en tu cuenta de Instagram para empresas
con usuarios que no tienen un rol en la app."
```

**Causa:** La app Nicolify tiene `instagram_manage_messages` en **Standard Access**. Con Standard Access, la API intenta filtrar conversaciones para mostrar solo las de usuarios que son testers/admins de la app, pero cuando hay muchas conversaciones con usuarios reales, la query hace timeout ANTES de poder filtrar.

**Impacto:** La ruta de backfill historico (Conversations API) esta completamente bloqueada. El boton "Sincronizar" no puede extraer DMs historicos.

**Nota:** El codigo ya fue corregido (URL, token, integracion). Solo falta el permiso de Meta.

### Pasos para solicitar Advanced Access

1. Abre https://developers.facebook.com/apps/ → tu app
2. Ve a **App Review** → **Permissions and Features**
3. Busca `instagram_manage_messages`
4. Click **Request Advanced Access**
5. Completa el formulario:
   - **Uso:** "We use the Instagram Messaging API to sync historical DM conversations into our CRM for lead tracking and analytics. Our app helps businesses automate their sales pipeline by tracking Instagram DM conversations as part of their marketing funnel."
   - **Screencast:** Graba un video corto mostrando el Growth Studio dashboard y explica como los DMs se muestran en las metricas de captura
6. Envia para review
7. Tiempo estimado: **1-5 dias habiles**

### Verificacion post-aprobacion

Una vez aprobado, el backfill automaticamente funcionara al clickear "Sincronizar" en Growth Studio (el fix ya esta integrado en `run_sync_all()`).

Para probar manualmente:

```bash
docker exec -t visionarias_brain_dev bash -c 'cd /app && python -c "
import asyncio
from uuid import UUID
async def test():
    from src.core.config import settings
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    engine = create_engine(str(settings.DATABASE_URL))
    with Session(engine) as db:
        from src.modules.connections.application.services.connection_port_impl import ConnectionPortImpl
        from src.modules.analytics.application.services.ig_dm_sync_service import InstagramDMSyncService
        cp = ConnectionPortImpl(db)
        svc = InstagramDMSyncService(db, connection_port=cp)
        result = await svc.sync(UUID(\"d68f4af3-3871-4f09-9cbd-a9856235025f\"))
        print(result)
asyncio.run(test())
"'
```

Esperado: `{"synced_messages": N, "new_leads": M, "skipped": K}` con N > 0.

---

## Resumen de prioridades

| # | Accion | Quien | Impacto | Urgencia |
|---|---|---|---|---|
| 1 | Configurar External Requests en ManyChat | Tu | Leads + conversaciones en dashboard | ALTA |
| 2 | Suscribir Meta IG messaging webhook | Tu | Conversaciones reales via sales_agent | ALTA |
| 3 | Solicitar Advanced Access | Tu | Backfill historico de DMs | MEDIA |
| 4 | Ejecutar plan de codigo (Task 3 + Task 6) | Claude | Bridge subscriber.new → message_received | ALTA (siguiente sesion) |
