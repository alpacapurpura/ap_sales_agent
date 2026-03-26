# ManyChat Flow Configuration Guide

> **Objetivo:** Configurar "External Request" blocks en los flows de ManyChat para enviar eventos al webhook de Nicolify, alimentando el Growth Studio con métricas reales.

---

## 1. URL del Webhook

### Producción
```
POST https://api.nicolify.com/api/v1/connections/marketing-webhooks/manychat/{TENANT_ID}
```

### Desarrollo (ngrok)
```bash
ngrok http 8000
# URL: https://{subdomain}.ngrok.io/api/v1/connections/marketing-webhooks/manychat/{TENANT_ID}
```

Reemplazar `{TENANT_ID}` con el UUID del tenant (visible en la configuración de la cuenta o en la tabla `tenants`).

---

## 2. Configuración del External Request Block

En cada flow de ManyChat donde quieras trackear un evento:

1. Agregar un bloque **"External Request"** (Action → External Request)
2. Método: **POST**
3. URL: la URL del webhook (ver arriba)
4. Headers:
   ```
   Content-Type: application/json
   ```
5. Body: JSON con los campos del evento (ver plantillas abajo)
6. Response Mapping: no es necesario (fire-and-forget)

---

## 3. Plantillas JSON por Tipo de Evento

### 3.1 `subscriber.new` — Nuevo suscriptor capturado

**Cuándo usar:** Primer paso de flows de bienvenida o Default Reply.

```json
{
  "event_type": "subscriber.new",
  "subscriber_id": "{{user_id}}",
  "channel": "instagram",
  "first_name": "{{first_name}}",
  "last_name": "{{last_name}}",
  "email": "{{email}}",
  "phone": "{{phone}}",
  "ig_username": "{{ig_username}}"
}
```

**Notas:**
- `channel`: usar `"instagram"` o `"whatsapp"` según el canal del flow
- Los campos `email`, `phone`, `ig_username` son opcionales — enviar lo que esté disponible
- Se mapea a etapa **Captura** → canal `manychat-ig` o `manychat-wa`

---

### 3.2 `comment.trigger` — Comment trigger activado

**Cuándo usar:** Primer paso de flows activados por comentarios en posts.

```json
{
  "event_type": "comment.trigger",
  "subscriber_id": "{{user_id}}",
  "channel": "instagram",
  "first_name": "{{first_name}}",
  "ig_username": "{{ig_username}}"
}
```

**Notas:**
- Se mapea a etapa **Atracción** → canal `manychat-comments`
- Métrica: `comment_triggers`

---

### 3.3 `tag.applied` — Tag asignado al suscriptor

**Cuándo usar:** Inmediatamente después de un bloque "Add Tag" en cualquier flow.

```json
{
  "event_type": "tag.applied",
  "subscriber_id": "{{user_id}}",
  "channel": "instagram",
  "tag_name": "NOMBRE_DEL_TAG",
  "first_name": "{{first_name}}",
  "email": "{{email}}",
  "ig_username": "{{ig_username}}"
}
```

**Tags con mapeo especial:**

| Tag | Métrica | Etapa |
|:----|:--------|:------|
| `Solicito_reunion` | `meetings_requested` | Oportunidad |
| `link_clicked` | `link_clicks` | Nutrición |
| `quiz_started` | `qualified_leads` | Nutrición |
| `Estrategia`, `Orden`, `Bienestar`, `Liderazgo`, `Claridad` | `qualified_leads` | Nutrición |
| Cualquier otro tag | `tag_applied` | Nutrición |

---

### 3.4 `flow.triggered` — Flow de automatización activado

**Cuándo usar:** Primer paso de flows de nurturing, BOFU, o secuencias.

```json
{
  "event_type": "flow.triggered",
  "subscriber_id": "{{user_id}}",
  "channel": "instagram",
  "flow_ns": "NAMESPACE_DEL_FLOW",
  "flow_name": "NOMBRE_LEGIBLE_DEL_FLOW",
  "first_name": "{{first_name}}",
  "email": "{{email}}"
}
```

**Mapeo por nombre de flow:**

| Patrón en `flow_name` | Métrica | Etapa |
|:-----------------------|:--------|:------|
| Contiene "BOFU" | `bofu_flows_triggered` | Oportunidad |
| Contiene "FollowUp" o "Sequence" | `sequences_sent` | Nutrición |
| Cualquier otro | `flows_triggered` | Nutrición |

---

### 3.5 `field.updated` — Custom field actualizado

**Cuándo usar:** Después de un bloque "Set Custom Field" para campos clave.

```json
{
  "event_type": "field.updated",
  "subscriber_id": "{{user_id}}",
  "channel": "instagram",
  "custom_field_name": "NOMBRE_DEL_CAMPO",
  "custom_field_value": "{{VALOR_DEL_CAMPO}}",
  "email": "{{email}}"
}
```

**Campos con mapeo:**

| Campo | Métrica | Etapa |
|:------|:--------|:------|
| `Consultas` | `consultations` | Oportunidad |
| Cualquier otro | (no se trackea) | — |

---

## 4. Flows a Configurar (Cuenta Visionarias)

| Flow | Event Type | Ubicación del External Request |
|:-----|:-----------|:-------------------------------|
| `Instagram Default Reply` | `subscriber.new` | Primer paso del flow |
| `Saludá a tus nuevos seguidores` | `subscriber.new` | Primer paso |
| `Quick Automation ES` (comment trigger) | `comment.trigger` | Primer paso |
| `Auto-DM de links desde comentarios` | `comment.trigger` | Primer paso |
| `IG-BOFU-01-FIXA-Programa-Visionarias-Gatillo` | `flow.triggered` | Primer paso (`flow_name` = nombre del flow) |
| `WS-BOFU-01A-FIX-Programa-Visionarias-Gatillo` | `flow.triggered` | Primer paso |
| `Proposito-Instagram-FollowUp-48h` | `flow.triggered` | Primer paso |
| `Sequence Message 1` | `flow.triggered` | Primer paso |
| Flows que aplican tag `Solicito_reunion` | `tag.applied` | Después del "Add Tag" action |
| Flows que aplican tag `quiz_started` | `tag.applied` | Después del "Add Tag" action |
| Flows que actualizan campo `Consultas` | `field.updated` | Después del "Set Custom Field" action |

---

## 5. Testing con ngrok

### Setup
```bash
# 1. Instalar ngrok si no lo tienes
# https://ngrok.com/download

# 2. Levantar el backend
docker compose up -d

# 3. Exponer el puerto
ngrok http 8000

# 4. Copiar la URL HTTPS de ngrok
# Ejemplo: https://abc123.ngrok.io
```

### Test manual con curl
```bash
# Simular un evento subscriber.new
curl -X POST https://abc123.ngrok.io/api/v1/connections/marketing-webhooks/manychat/{TENANT_ID} \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "subscriber.new",
    "subscriber_id": "12345",
    "channel": "instagram",
    "first_name": "Test",
    "ig_username": "testuser"
  }'

# Respuesta esperada:
# {"status": "processed", "event": "subscriber.new"}
```

### Verificar en la base de datos
```bash
# Verificar journey_events
docker exec -t visionarias_postgres psql -U postgres -d visionarias_logs -c \
  "SELECT event_name, properties->>'source' as source FROM journey_events WHERE event_name LIKE 'manychat_%' ORDER BY occurred_at DESC LIMIT 5;"

# Verificar official_metrics
docker exec -t visionarias_postgres psql -U postgres -d visionarias_logs -c \
  "SELECT channel_slug, metric_name, value, metric_date FROM official_metrics WHERE provider='manychat' ORDER BY created_at DESC LIMIT 10;"
```

---

## 6. Troubleshooting

| Problema | Causa probable | Solución |
|:---------|:---------------|:---------|
| `{"status": "ignored", "reason": "no_manychat_connection"}` | Tenant no tiene ManyChat conectado | Ir a Configuración → ManyChat → Conectar con API key |
| `{"status": "ignored", "reason": "missing_event_type_or_subscriber_id"}` | JSON body incorrecto | Verificar que `event_type` y `subscriber_id` están presentes |
| Error 400 "Invalid JSON payload" | Body no es JSON válido | Revisar comillas y formato del JSON en ManyChat |
| Evento procesado pero no aparece en dashboard | Cache activo (5 min TTL) | Esperar 5 minutos o invalidar cache manualmente |
| Métricas no incrementan | `metric_name` o `stage_slug` no resolvieron | Verificar que el `event_type` y `tag_name`/`flow_name` matchean los mapeos |

---

## 7. Arquitectura del Pipeline

```
ManyChat Flow
    └─ External Request (POST)
        └─ /api/v1/connections/marketing-webhooks/manychat/{tenant_id}
            ├─ Identity Resolution (CRM)
            │   └─ CustomerService.identify() → CustomerProfile
            ├─ Journey Event (CRM)
            │   └─ JourneyEventModel → lifecycle score recalculation
            └─ Metric Promotion (Analytics)
                └─ ManyChatMetricsPromoter.promote_event()
                    └─ official_metrics (upsert_increment)
                        └─ Growth Studio Dashboard
```
