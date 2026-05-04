# Taxonomía de Tipos de Campaña
**Estado:** Investigación completada (2026-04-29)
**Decisiones pendientes:** Ver tabla al final

---

## Universo completo de tipos de campaña

### TIER 1 — Construir en los próximos 12 meses

#### A. Conversacional Outbound (Sales Agent)
**Qué es:** El Sales Agent inicia conversaciones con un segmento del CRM.
**Canales:** WhatsApp, Telegram, Instagram DM, TikTok DM
**Cuándo usarlo:** Leads calientes sin respuesta, seguimiento post-interés, upsell a clientes existentes
**Referencia del mercado:** Artisan, 11x, AiSDR — todos los SDR agents siguen este patrón
**Lo que ya tenemos:** Sales Agent completo. Falta solo el outbound entry point.
**Decisión pendiente:** ¿WhatsApp primero o multi-canal desde el inicio?

#### B. Conversacional Inbound con Tratamiento Diferenciado (Source-Aware)
**Qué es:** NO es una campaña outbound. Es una instrucción de tratamiento que el Sales Agent usa CUANDO alguien entra desde una fuente específica.
**Ejemplo:** Personas que llegaron por el anuncio "Webinar de Enero" → el agente sabe esto y abre con "Vi que te interesó el masterclass de enero..."
**Canales:** Cualquiera (donde el lead nos habla primero)
**Lo que ya tenemos:** `source_channel` en `Enrollment`. Falta: `source_campaign_id` en `CustomerProfile` + lógica de override en el agente.
**Valor:** Muy alto. Los leads "warm" de una campaña específica convierten 2–3x más cuando son tratados con contexto del origen.

#### C. Email — Campaña One-Shot (Broadcast)
**Qué es:** Un email a un segmento en un momento dado. Newsletter, anuncio, promo.
**Herramienta:** MailerLite (ya integrado)
**Cuándo usarlo:** Lanzamientos, novedades, recuperación de clientes inactivos
**Lo que ya tenemos:** MailerLite API completa (ETL + connections). Falta: UI para crear/enviar desde Nicolify.
**Decisión pendiente:** ¿Exponemos la UI de MailerLite directamente, o construimos una capa propia?

#### D. Email — Automatización / Secuencia (Drip)
**Qué es:** Serie de emails disparados automáticamente por un trigger (suscripción, compra, etapa de lifecycle).
**Herramienta:** MailerLite Automations (ya integrado a nivel ETL). Falta el control desde Nicolify.
**El patrón:** Un trigger crea/actualiza al suscriptor en un grupo de MailerLite → MailerLite dispara la automation → emailsequence corre.
**Los tipos principales:**
  - Welcome sequence (6 emails en 10 días para nuevos suscriptores)
  - Post-compra (confirmación + onboarding + upsell)
  - Re-engagement (leads inactivos > 30 días)
  - Pre-evento (5 reminders antes de webinar)
  - Post-webinar (replay + offer close)
**Lo que ya tenemos:** MailerLite group API. Falta: lógica de "cuándo agregar a qué grupo" + plantillas de secuencias recomendadas.

#### E. Event Campaign / Launch Orchestration (Webinar + Launch)
**Qué es:** Campaña multi-canal anclada a una fecha. Coordina emails + WhatsApp + push alrededor de un evento (webinar, lanzamiento de programa, oferta de 48h).
**Por qué Tier 1:** El infoproductor promedio hace 1–4 lanzamientos al año, cada uno generando 60–80% del ingreso anual. Automatizar esto tiene ROI directo e inmediato.
**Anatomía:**
```
D-7  → Email "Se viene algo grande" + WhatsApp broadcast
D-3  → Email detallado + página de registro
D-1  → Email urgencia + WhatsApp recordatorio
D-0 -1h → WhatsApp/SMS "En una hora empieza"
D-0 +2h → Email "¿Cómo te fue?" + replay
D+1  → Email "El replay estará disponible hasta mañana" (urgencia)
D+2  → Email "Última oportunidad" + oferta + WhatsApp follow-up
D+3  → Close (último email + WhatsApp)
```
**Lo que ya tenemos:** `scheduling/`, MailerLite, WhatsApp/Telegram adapters. Falta: `CampaignStep[]` con offsets + motor de ejecución temporal.

#### F. Retargeting (CRM → Plataformas de Ads)
**Qué es:** Exportar un segmento del CRM (MQLs que no compraron, clientes de alto LTV) a Meta/Google Ads como Custom Audience.
**Por qué Tier 1:** Los tenants ya pagan en ads. Multiplicar el ROI de esos ads con audiencias de CRM es ganancia directa.
**ROI data:** 29% mejor ROI vs audiencias frías. Hasta 73% mejor ROAS con listas de alta calidad.
**Flujo:**
```
CRM Segment ("SQLs sin conversión > 30 días")
  → hash emails/phones
  → Meta Marketing API: POST /customaudiences
  → Audiencia disponible en Ads Manager
  → Opción: crear Lookalike desde top customers
```
**Lo que ya tenemos:** `advertising/` module (placeholder) + `ad_offer_associations` model. Falta: Meta Marketing API integration + "Exportar a Meta" UI en CRM Hub.

#### G. TikTok DM Automation
**Qué es:** Flujos de DM en TikTok disparados por comentarios en videos (Comment-to-DM).
**Por qué Tier 1:** ManyChat ya conectado. TikTok disponible en LATAM (no bloqueado como en UK/US). Creator economy en TikTok crece más rápido que Instagram en 2025.
**Flujo:**
```
Creator publica video en TikTok
→ Comentario con keyword ("QUIERO")
→ ManyChat captura → auto-DM al comentarista
→ Lead qualification flow
→ Handoff a Sales Agent vía WhatsApp (lead da su número)
→ CRM: lead con source_campaign_id = "tiktok-video-marzo-25"
```
**Lo que ya tenemos:** ManyChat integration. Falta: configuración TikTok Business en `connections/` + tratamiento de estos leads en CRM.

---

### TIER 2 — 6–12 meses

#### H. Web Push Notifications
**Qué es:** Notificaciones push a suscriptores del browser del tenant (personas en la landing page que dieron permiso).
**Cuándo:** Post-landing page opt-in. Launches, nuevo contenido, carrito abandonado.
**Herramienta:** OneSignal (free tier generoso, REST API simple).
**LATAM relevance:** Alta. Android domina LATAM (80%+). iOS 16.4+ ya soporta web push.
**Opt-in rates:** 5–15%. No reemplaza email/WhatsApp, es additive.
**Prerequisito:** El módulo `landing/` debe tener el snippet de OneSignal y manejar opt-ins.

#### I. Referral / Afiliados
**Qué es:** Código de referido por cliente/estudiante. Tracking de conversiones y comisiones.
**Por qué:** Leads referidos convierten 5x más. Para creators LATAM, el boca a boca es el canal #1 no explotado.
**Implementación v1:** Sin herramienta externa. `referral_code` en `CustomerProfile`, `journey_event` tipo "referral_converted", comisiones trackadas manualmente.
**Prerequisito:** `Sale` model ya existe + `Enrollment` ya existe.

#### J. AI Voice Follow-up (Sales Agent → Canal de Voz)
**Qué es:** El Sales Agent llama por teléfono a leads que no respondieron por WhatsApp en 48-72h.
**Herramienta:** Vapi + ElevenLabs.
**Cuándo tiene sentido:** Solo para warm leads (temperature=HOT, score > 70) + deals > $200 USD.
**Por qué no Tier 1:** Culturalmente risky en LATAM para cold outreach. Funciona bien para warm follow-up opt-in.
**Arquitectura:** Un `VoiceAdapter` en la capa de `connections/` + `sales_agent`. El agente ya sabe qué decir (tiene el perfil CRM).

---

### TIER 3 — No en el roadmap de 12 meses

| Canal | Por qué diferir |
|---|---|
| SMS | WhatsApp domina LATAM. No tiene ROI incremental. Compliance complejo. |
| Twitter/X DMs | API $5K/mes para automation. Audiencia migrando. |
| LinkedIn DMs | Gray-area. Solo para nicho B2B coaching. |
| Pendo/Appcues | Caro para uso interno de Nicolify. Mejor construir nativo. |
| Discord | Muy niche para el segmento core LATAM. |
| AI video personalizado (Tavus/HeyGen) | Solo tiene ROI en high-ticket > $1K USD. |
| Skool/Circle community | Poco adoption LATAM en 2025. |

---

## Matriz de decisión

| Tipo | ¿Necesita nuevo módulo BE? | ¿Necesita nueva integración? | ¿Usa Sales Agent? | ¿Usa MailerLite? | ¿Primer canal? |
|---|---|---|---|---|---|
| Conversacional Outbound | Sí (`campaigns/`) | No | SÍ (outbound entry point) | No | WhatsApp / TikTok DM |
| Source-Aware Treatment | No (campos en CRM) | No | SÍ (override flow) | No | N/A |
| Email Broadcast | Parcial (campaign orchestrator) | No (MailerLite existe) | No | SÍ | Email |
| Email Drip/Automation | Parcial (trigger logic) | No (MailerLite existe) | No | SÍ | Email |
| Event Campaign | SÍ (`CampaignStep[]`) | No | SÍ (parcial) | SÍ | Multi-canal |
| Retargeting Ads | Sí (en `advertising/`) | SÍ (Meta Marketing API) | No | No | Meta Ads |
| TikTok DM | Parcial (CRM source tracking) | Parcial (ManyChat TikTok config) | SÍ (handoff) | No | TikTok → WhatsApp |
| Web Push | No (OneSignal simple) | SÍ (OneSignal) | No | No | Browser push |
| Referral | Mínimo (2 campos en CRM) | No | No | No | N/A |
| AI Voice | SÍ (VoiceAdapter) | SÍ (Vapi) | SÍ (extends agent) | No | Llamada telefónica |

---

## ¿Qué construir primero? — Preguntas abiertas

**Pregunta 1:** El Email Drip/Automation puede implementarse casi sin código nuevo (solo trigger logic: "cuando lead llega a MQL → agregar a grupo X en MailerLite"). ¿Lo priorizamos como quick win antes que los otros?

**Pregunta 2:** Event Campaign (webinar/launch) es el mayor ROI pero también el más complejo. ¿Empezamos con un subconjunto simple (solo reminders de WhatsApp para evento)?

**Pregunta 3:** Retargeting a Meta Ads. ¿El tenant ya tiene Meta Ads conectado desde el módulo `connections/`? Si sí, esto está más cerca de lo que parece.

**Pregunta 4:** Para Source-Aware Treatment, el primer paso es capturar `source_ref` y `source_ad_id` desde los webhooks de ManyChat (ya existen). ¿Lo priorizamos como dato de alto valor?
