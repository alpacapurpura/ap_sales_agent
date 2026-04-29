# Knowledge Base: Campaign System — Nicolify PM
**Estado:** En construcción activa (desde 2026-04-29)
**Propósito:** Acumular conocimiento de mercado + decisiones de producto sobre el sistema de campañas de Nicolify, antes de pasar a ejecución.

---

## Cómo usar esta carpeta

Esta carpeta es el "cuaderno de equipo" donde vamos construyendo conocimiento juntos. **Todo sigue siendo PM-level** hasta que decidamos explícitamente abrir una carpeta de ejecución técnica.

### Estructura

| Carpeta | Contenido |
|---|---|
| `00-framework/` | Taxonomía de tipos de campaña + arquitectura general + patrones de diseño |
| `01-conversacional/` | Canales de mensajería (WhatsApp, Telegram, IG DM, TikTok DM, etc.) |
| `02-email-marketing/` | MailerLite, Mailchimp, Kit, ActiveCampaign, automatizaciones vs campañas |
| `03-otros-tipos/` | Push, retargeting, webinars, referral, voz AI, video AI, community |
| `04-integracion-nicolify/` | Cómo todo esto conecta con CRM Hub, Sales Agent, Copilot, agentes futuros |

### Flujo de decisiones

```
Investigación → Decisiones preliminares → Priorización → Plan de ejecución
(esta carpeta)                                             (carpeta nueva cuando sea momento)
```

---

## Status decisiones

| Tema | Estado |
|---|---|
| Arquitectura general (patrón Strategy) | ✅ Decidido — ver `00-framework/architecture.md` |
| Tipos de campaña a soportar | ⚠️ En análisis |
| Canal prioritario para outbound conversacional | ❓ Pendiente decisión |
| Modelo Email (propio vs. MailerLite) | ⚠️ En análisis |
| Automatizaciones vs campañas one-shot | ⚠️ En análisis |
| Retargeting a plataformas de ads | ✅ Prioridad decidida (Tier 1) |
| Webinar campaign orchestration | ✅ Prioridad decidida (Tier 1) |
| SMS | ✅ Descartado — WhatsApp domina LATAM |
| AI Voice | ⚠️ Interesante, diferir |
| TikTok DM | ✅ Tier 1 (ManyChat ya conectado, LATAM abierto) |

---

## Preguntas abiertas a responder (con Chris)

1. Canal prioritario para campañas outbound: ¿WhatsApp primero o TikTok DM?
2. Modelo email: integración con MailerLite del tenant vs. propio SMTP para los flows del agente
3. ¿Cuándo es el momento de abrir la carpeta de ejecución?
4. ¿El emprendedor escribe templates o el agente siempre personaliza?
5. Prioridad entre webinar orchestration y retargeting — ¿cuál va primero?

---

## Log de conversaciones

| Fecha | Tema | Decisiones |
|---|---|---|
| 2026-04-29 | Kickoff: CRM Hub + taxonomía inicial + research | Ver `00-framework/campaign-types.md` |
