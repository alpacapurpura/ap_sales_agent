# Canales Conversacionales — Research
**Fecha:** 2026-04-29
**Fuente:** Research sobre ManyChat, Respond.io, Intercom, Brevo, Wati, Landbot, Klaviyo

---

## Hallazgo central: el patrón "Campaign IS the Conversation" (Landbot)

El insight más importante de todo el research: en canales conversacionales, **la campaña y la conversación de seguimiento son la misma entidad**. No son dos cosas separadas.

```
MO INCORRECTO (email thinking):
Campaña broadcast ──→ [termina aquí]
                       ↓ alguien responde
                       Conversación separada

MODELO CORRECTO (Landbot, respond.io):
Mensaje inicial (broadcast) ──→ Conversación continúa automáticamente
                                  ↓
                               Calificación
                                  ↓
                               Sales Agent toma el hilo
```

**Implicación para Nicolify:** Una "campaña conversacional" no termina cuando se envía el mensaje. Termina cuando el contacto convierte o cierra la conversación. El `campaign_id` debe vivir en el `AgentState` del Sales Agent para attribution correcta.

---

## ManyChat — Funcionalidad clave

### Entry point system (source-aware treatment)

ManyChat tiene 6 mecanismos de entrada, cada uno puede llevar a un flow diferente:

| Entry Point | Cómo funciona | Variable disponible |
|---|---|---|
| Keyword | Usuario escribe palabra específica → flow | `{last_input_text}` |
| Comment trigger | Comenta en post/reel → auto-DM | `{comment.post_id}` |
| CTWA / CTDM Ad | Click en ad Meta → DM con ad_id | `{entry_point}` contiene ad_id |
| Ref parameter | Landing page → link con `?ref=webinar_enero` | `{ref}` |
| Story reply/mention | Responde story → flow específico | story_id |
| API trigger | Nicolify llama API → entra en flow | custom payload |

**El más importante para Nicolify:** El `ref` parameter. Cuando un tenant crea una landing page en Nicolify y pone un botón "Escríbeme por WhatsApp", ese botón puede llevar a `wa.me/5XXXXXX?ref=lp_webinar_enero`. ManyChat captura el `ref` → Nicolify lo recibe en el webhook → lo guarda en `CustomerProfile.source_ref`.

**Lo que falta en Nicolify hoy:**
- `source_ref: str` no existe en `CustomerProfile`
- `source_ad_id: str` no existe en `CustomerProfile`
- Los webhooks de ManyChat (`flow.triggered`) no están leyendo estos campos

### Segmentación en ManyChat

ManyChat filtra por:
- **Tags:** strings libres aplicados manual o automáticamente
- **Custom Fields:** key-value tipados (texto, número, fecha, boolean)
- **Engagement:** "ha visto flow X", "ha clickeado botón Y", "está subscrito a secuencia Z"
- **Tiempo:** `last_interaction` time-based, `first_seen`

La granularidad es per-subscriber, no per-segment (no hay un "segment builder" sofisticado como HubSpot). La segmentación está implícita en los tags y custom fields.

**Implicación para Nicolify:** Los tags de ManyChat deben sincronizarse con las `traits` del `CustomerProfile`. El webhook de `tag.applied` ya existe — falta una capa de sincronización bidireccional.

### Diferencia: Broadcast vs Automation en ManyChat

| | Broadcast | Automation Flow |
|---|---|---|
| Trigger | Manual (tenant lo ejecuta) | Automático (evento dispara) |
| Audiencia | Snapshot del segmento en ese momento | Individual cuando cumple condición |
| Timing | Inmediato o programado | En tiempo real |
| Ventana WhatsApp | 24h (o HSM template) | 24h rule applies |
| Conversación continúa | No | Sí |

**Regla de oro WhatsApp (WABA):**
- Dentro de 24h desde última interacción → puedes enviar cualquier mensaje
- Después de 24h → solo puedes enviar "HSM templates" (plantillas aprobadas por Meta)
- Esto aplica a TODOS los canales WABA, incluyendo lo que Nicolify enviaría a través del Sales Agent

---

## Respond.io — Multi-canal best-in-class

### Por qué es la referencia más relevante

Respond.io es el único tool que:
1. Maneja WhatsApp + Telegram + IG + TikTok DM + Facebook Messenger en una sola inbox
2. Tiene routing inteligente por "canal preferido del contacto"
3. Tiene CTWA attribution (captura el `ad_id` de Meta cuando alguien llega de un ad de WhatsApp)
4. Tiene el concepto de "first contact source" persistido en el perfil

### Multi-channel routing model (lo que debemos replicar)

```
Contacto: { 
  whatsapp: "+51 999 888 777",
  telegram: "@juanperez",
  instagram: "juanperez_oficial",
  preferred_channel: "whatsapp",  // el que más usa
  last_active_channel: "telegram"  // por donde llegó último
}

Campaign.send(contacto):
  1. Verificar disponibilidad de canales
  2. Aplicar compliance rules (WABA 24h)
  3. Elegir según: preferred → last_active → campaign default
  4. Enviar por canal elegido
  5. Registrar canal_usado en CampaignTask
```

**El dato clave que falta en Nicolify:** `preferred_channel` y `last_active_channel` no existen como campos explícitos en `CustomerProfile`. Se puede inferir de `CustomerIdentity` + `last_interaction_date` por canal.

---

## Inbound Treatment — Cómo los mejores lo resuelven

### HubSpot: Original Source + UTM persistence

HubSpot guarda el `utm_source`, `utm_medium`, `utm_campaign` del PRIMER toque del contacto. Nunca lo sobreescribe. Esto se llama "Original Source" y es la base para la atribución de campañas.

Los workflows pueden hacer branching basado en estos valores: "IF `utm_campaign` = 'webinar_enero' THEN enroll in secuencia especial".

**Para Nicolify:** `lead_source` en `CustomerProfile` es demasiado genérico. Necesitamos preservar el primer toque con granularidad de campaña.

### ManyChat: entry_point + ref = source-aware routing

Cuando un lead llega desde un ad específico (CTWA ad → WhatsApp), `entry_point` tiene el `ad_id`. El flow puede branchar: "IF entry_point contains 'ad_webinar_enero' THEN set tag webinar_lead AND go to webinar_treatment_flow".

**El resultado:** El mismo WhatsApp bot trata diferente a alguien que llegó por un ad que a alguien orgánico. El tratamiento es contextual al origen.

### Respond.io: contact source attribute

Cada contacto tiene un `source` attribute inmutable — por qué canal y qué campaña los creó. Siempre disponible para workflow branching.

---

## Patrones de Broadcast Conversacional

### Outbound desde Nicolify (lo que queremos construir)

El flujo completo que debemos poder ejecutar:

```
Emprendedor en Nicolify:
1. Crea campaña "Seguimiento precio - Semana 1"
2. Selecciona segmento "Leads hot sin respuesta > 3 días"
3. Elige canal: WhatsApp (primero) | Telegram (fallback)
4. Decide: "Dejar que Sales Agent personalice con el contexto del lead"
5. Programa: Lunes 10am

[Execution time]

Por cada contacto en el segmento:
  → CampaignTask creado
  → Sales Agent recibe: { contact_id, campaign_id, instructions: "seguimiento precio" }
  → Agent carga: profile, historial de objeciones, last_interaction, preferred_channel
  → Agent genera mensaje: "Hola [nombre], el otro día preguntaste sobre [oferta]..."
  → Agent envía por WhatsApp (o Telegram como fallback)
  → Si responde → conversación vive en Studio > Inbox con tag "campaña: seguimiento precio"
  → Si convierte → Enrollment atribuido a "campaña: seguimiento precio"
```

### Compliance rules importantes

| Canal | Ventana libre | Fuera de ventana |
|---|---|---|
| WhatsApp WABA | 24h desde última interacción | Solo templates aprobados por Meta |
| Instagram DM | 24h desde última interacción | No se puede iniciar, debe venir del usuario |
| Telegram Bot | No hay ventana — siempre permitido | N/A |
| Email | No hay ventana — siempre permitido | Solo con opt-in y unsubscribe |

**Implicación crítica:** Para campañas outbound de WhatsApp a leads fríos (sin interacción reciente), **siempre necesitaremos HSM templates aprobados por Meta**. El Sales Agent no puede enviar mensajes "libres" fuera de la ventana de 24h.

**Opción arquitectónica:** Cuando el ChannelRouter detecta que el contacto está fuera de ventana → usar template HSM en lugar del mensaje generado por el agente.

---

## TikTok DM via ManyChat — Detalle 2025

### Estado actual en LATAM

- Disponible en todos los países LATAM (México, Colombia, Perú, Argentina, Chile, Ecuador, etc.)
- NO disponible en US, UK, EU (restricciones regulatorias)
- Ventana: 48 horas desde la última interacción, máximo 10 mensajes automatizados por conversación
- Se requiere cuenta TikTok Business + ManyChat Business Plan

### Flujo completo comment-to-DM

```
Creator: "Comenta 'QUIERO' para recibir el PDF gratis"
    ↓
Follower comenta "QUIERO" en el video
    ↓
ManyChat detecta el comentario (necesita TikTok Business API access)
    ↓
Auto-DM enviado al followery que comentó
    ↓
Flow: "Hola! Aquí tienes el PDF: [link] ¿Por cierto, cuál es tu mayor desafío con [tema]?"
    ↓
Si responde → calificación conversacional
    ↓
Si da su WhatsApp → Sales Agent lo toma para conversación más profunda
    ↓
CRM: lead con source_ref = "tiktok_video_202503_pdf" + source_campaign_id
```

### Por qué es Tier 1 para LATAM

- Los creators LATAM ya están en TikTok y ya usan comment-to-DM manualmente
- ManyChat lo automatiza sin necesidad de infraestructura nueva
- Los leads de TikTok son warm (vieron el video, lo compartieron) — alta intención

### Limitación importante

TikTok no tiene CTWA equivalent. No hay ad → DM tracking nativo como Meta tiene. El `source_ref` debe venir del enlace del bio o del keyword comentado — less granular que Meta.

---

## Decisiones pendientes (conversacional)

1. **WhatsApp templates HSM:** ¿Tenemos un proceso para que el tenant cree y someta templates a aprobación de Meta? ¿O usamos el Sales Agent solo para contactos en ventana de 24h?

2. **TikTok DM activation:** ¿Qué tan difícil es para el tenant conectar su TikTok Business a ManyChat desde el módulo `connections/`? ¿Ya está mapeado?

3. **Source-ref capture:** ¿El webhook de ManyChat que ya tenemos captura `ref` y `entry_point`? Si no, ese es un cambio small en el parser del webhook.

4. **Channel priority configuration:** ¿Dejamos que el tenant configure el orden de prioridad de canales (WhatsApp > Telegram > email), o lo hacemos automático basado en el historial del contacto?
