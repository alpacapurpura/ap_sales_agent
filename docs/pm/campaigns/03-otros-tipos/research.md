# Otros Tipos de Campaña — Research
**Fecha:** 2026-04-29
**Fuente:** Research sobre web push, retargeting, webinars, referral, voice AI, video AI, community

---

## Resumen ejecutivo: ¿Qué más importa para LATAM?

Más allá de conversacional y email, el orden de prioridad real para el segmento de Nicolify (creators, coaches, infoproductores LATAM):

| # | Tipo | Por qué importa | Dificultad | Decisión |
|---|---|---|---|---|
| 1 | Webinar/Launch Orchestration | 60–80% del ingreso anual para infoproductores | Media | Tier 1 |
| 2 | Retargeting (CRM → Meta/Google Ads) | 29-73% mejor ROAS con audiencias CRM | Media | Tier 1 |
| 3 | TikTok DM (ya en conversacional) | Canal más rápido en LATAM 2025 | Baja | Tier 1 |
| 4 | Web Push | Additive, first-party data | Baja | Tier 2 |
| 5 | Referral/Afiliados | Leads referidos convierten 5x más | Baja | Tier 2 |
| 6 | AI Voice Follow-up | ROI para high-ticket, culturalmente risky | Media | Tier 2 (experimental) |
| SMS, LinkedIn, Discord, AI Video | Bajo ROI incremental o complejidad alta | | Descartado |

---

## 1. Webinar / Launch Orchestration

### Por qué es Tier 1

El "lanzamiento" es la forma más común de vender programas en LATAM. Cada infoproductor hace 1-4 por año. Cada lanzamiento puede representar 50-80% del ingreso anual. **Si Nicolify automatiza los launches, está en el corazón del negocio del tenant.**

### La anatomía de un lanzamiento (el "launch sequence" típico)

```
FASE 1: Pre-lanzamiento (D-14 a D-1)
→ Email: "Se viene algo grande" (genera curiosidad)
→ WhatsApp broadcast: teaser
→ Landing page: registro de interés / waitlist
→ Retargeting ad: para quienes visitaron la landing pero no se registraron

FASE 2: Lanzamiento (D0)
→ Email: "Ya está abierto" con CTA directo
→ WhatsApp: "Acaba de abrir"
→ Push: notificación a suscriptores del browser

FASE 3: Urgencia (D+1 a D+2)
→ Email: testimonios + FAQ
→ WhatsApp: "Quedan X lugares" (genuino, basado en enrollment count)
→ Sales Agent: contacta activamente a leads hot sin respuesta

FASE 4: Cierre (D+3)
→ Email: "Última oportunidad - cierra hoy a las 11:59pm"
→ WhatsApp: "Esto cierra en X horas"
→ Sales Agent: seguimiento a PAYMENT_PENDING que no pagaron

POST-VENTA
→ Email: onboarding bienvenida
→ WhatsApp: acceso + primeros pasos
→ Enrollments promovidos a PAID, acceso al programa
```

### El patrón EVENT_TRIGGER

Una campaña de lanzamiento es un `Campaign` de tipo `EVENT_TRIGGER` con:
- `anchor_event_date` = fecha de apertura del carrito (D0)
- `steps` = lista de CampaignStep con `offset_hours` negativos (pre) y positivos (post)
- Multi-canal por step: cada step puede ser email + WhatsApp + push

```
CampaignStep[]
  [offset: -336, channel: EMAIL,     template: "se_viene_algo_grande"]  # D-14
  [offset: -336, channel: WHATSAPP,  template: "teaser_broadcast"]      # D-14
  [offset: -24,  channel: EMAIL,     template: "manana_abre"]           # D-1
  [offset: -24,  channel: WHATSAPP,  template: "manana_ultimo_dia"]     # D-1
  [offset: 0,    channel: EMAIL,     template: "ya_esta_abierto"]       # D0
  [offset: 0,    channel: PUSH,      template: "abre_carrito"]          # D0
  [offset: 48,   channel: EMAIL,     template: "testimonios_faq"]       # D+2
  [offset: 72,   channel: EMAIL,     template: "ultima_oportunidad"]    # D+3
  [offset: 72,   channel: WHATSAPP,  template: "cierra_hoy"]            # D+3
```

### Webinar (sub-tipo de EVENT_TRIGGER)

El webinar es un launch con fecha del evento = la sesión en vivo.

```
CampaignStep[]
  [offset: -72,  channel: EMAIL,     template: "webinar_3_dias"]       # D-3
  [offset: -24,  channel: EMAIL,     template: "webinar_manana"]       # D-1
  [offset: -1,   channel: WHATSAPP,  template: "webinar_en_1h"]        # -1h
  [offset: +2,   channel: EMAIL,     template: "replay_disponible"]    # +2h post webinar
  [offset: +26,  channel: EMAIL,     template: "replay_mañana_cierra"] # +2h del D+1
  [offset: +50,  channel: WHATSAPP,  template: "oferta_cierra_hoy"]    # +2h del D+2
```

### Métricas que importan

- Asistencia real vs. registrados (registration → show-up rate, benchmark: 25-35%)
- Conversión post-webinar (show-up → purchase, benchmark: 5-15%)
- Revenue por asistente
- Qué step del drip tuvo más conversiones (attribution por step)

---

## 2. Retargeting (CRM → Meta/Google Ads)

### El gap actual

Nicolify ya captura leads (con email, teléfono, Instagram handle). El `advertising/` module existe como placeholder. Los tenants ya pagan en Meta Ads sin aprovechar esta data.

**La oportunidad:** Con hashed email/phone, Meta puede hacer match contra sus usuarios (~50-70% match rate). Una audiencia de "mis SQLs que no compraron" en Meta Ads convierte a 3-5x el costo de una audiencia fría.

### Tipos de audiencias útiles para infoproductores

| Audiencia CRM | ¿Para qué ads? |
|---|---|
| SQLs que no compraron (lifetime) | Retargeting directo del programa |
| MQLs (calificados sin convertir) | Awareness del programa + testimonios |
| Clientes (CUSTOMER stage) | Upsell a programa next level |
| Evangelist (EVANGELIST stage) | Lookalike seed — el más valioso |
| Inactivos > 30 días | Re-engagement con oferta especial |
| Asistentes a webinar sin compra | Retargeting post-webinar |

### Lookalike Audiences — el caso más valioso

```
"Mis mejores 200 clientes (top LTV)" 
→ hash emails
→ Meta Custom Audience
→ "Crear Lookalike al 1%" 
→ Meta encuentra 500K personas similares en LATAM
→ Mejor ROI que cualquier targeting demográfico/por intereses
```

Esto es lo que usan los infoproductores exitosos y es completamente manual hoy. Nicolify puede automatizarlo.

### Implementación técnica (Meta Marketing API)

```
1. Export: GET /api/v1/crm/segments/{id}/members → { emails[], phones[] }
2. Hash: SHA256 cada email y teléfono (Meta requirement)
3. Create: POST https://graph.facebook.com/v18.0/act_{ad_account_id}/customaudiences
   { name, subtype: "CUSTOM", retention_days: 180, customer_file_source: "USER_PROVIDED_ONLY" }
4. Upload: POST /customaudiences/{id}/users
   { payload: { schema: ["EMAIL_SHA256", "PHONE_SHA256"], data: [[hash_email, hash_phone], ...] } }
5. Optional: POST /act_{id}/customaudiences
   { name: "Lookalike from Evangelists", subtype: "LOOKALIKE", origin_audience_id, lookalike_spec: { country: "MX,CO,PE,AR", ratio: 0.01 } }
```

**Prerequisito:** El tenant ya tiene Meta Business Account conectado en `connections/` (para advertising module). Si sí, solo falta la UI "Exportar segmento a Meta" + el API call.

### Google Customer Match (segundo en importancia)

```
Similar a Meta pero para Google Ads
Upload: lista de emails hasheados
Match: Google encuentra usuarios en su red (Gmail, YouTube, Search)
Use case: remarketing en YouTube (video ads para creators)
```

---

## 3. Web Push Notifications

### Por qué ahora tiene sentido

Hasta 2023, iOS Safari no soportaba web push. Desde iOS 16.4 (2023), ya funciona. En LATAM Android domina (80%+ de smartphones), que siempre tuvo web push.

**Opt-in rates:** 5-15% en landing pages con buen copy. Mucho menor que email (70-80% de opt-in cuando es un lead magnet). Pero es un canal adicional sin costo adicional por mensaje.

**Open rates:** 14.4% CTR para notificaciones contextuales vs 4.19% genéricas. Mucho más alto que email (20-30% open, 2-3% CTR).

### Cuándo push > email

- Anuncios de tiempo real (carrito abierto, webinar comenzando en 1h)
- Contenido nuevo disponible ("Tu clase de hoy está lista")
- Flash sales cortas (24h max — push tiene urgencia natural)

### Arquitectura simplificada (OneSignal)

```
1. Tenant activa push en su landing page
2. Nicolify embeds OneSignal JS snippet en todas las landing pages
   → Visitante ve prompt "¿Quieres recibir notificaciones?"
   → OneSignal genera player_id por dispositivo
3. Nicolify guarda player_id en CustomerProfile.traits["onesignal_player_id"]
4. Campaign de tipo PUSH:
   → Nicolify llama POST /notifications con player_ids del segmento
   → Message + action URL
5. Push enviado instantáneamente
```

**Costo:** OneSignal free tier: 10,000 subscribers, ilimitadas notificaciones. Paid plans desde $9/mes para más subscribers. Muy accesible.

---

## 4. Referral / Afiliados

### El modelo más simple con mayor leverage

Los leads referidos convierten 5x más. Para creators LATAM, el boca a boca es el canal más poderoso y el menos explotado tecnológicamente.

### Implementación v1 (sin herramienta externa)

```
CustomerProfile:
  referral_code: str  # "JUAN25" — único por usuario
  referred_by_code: str | None  # si el usuario llegó referido

Cuando alguien hace compra:
  Si Enrollment.contact.referred_by_code → buscar el referrer
  Crear Commission record: { referrer_id, referred_id, sale_id, amount, status: PENDING }
  
Dashboard del emprendedor:
  Mis afiliados activos (personas que tienen su código)
  Conversiones este mes
  Comisiones pendientes de pago
  
No procesamos pagos — solo tracking
```

### Para programas con comunidad

Un referral simple: si te refieren 3 personas, accedes al "módulo premium" de forma gratuita. El backend solo necesita contar `referred_by_code` usages y disparar un `JourneyEvent("referral_milestone_3")` → automation de MailerLite da acceso.

---

## 5. AI Voice Follow-up

### El caso de uso correcto

**NO** llamadas en frío a extraños. **SÍ** seguimiento a leads warm que ya tuvieron contacto:

```
Lead Carlos (temperature: HOT, score: 78)
→ Pidió precio hace 3 días
→ No respondió WhatsApp en 48h
→ Campaign outbound intenta por WhatsApp → sin respuesta
→ Trigger AI Voice:
   Vapi llama al número de Carlos
   ElevenLabs voice (clona o usa preset de la voz del tenant)
   Script: "Hola Carlos, soy el asistente de [Marca]. 
            Vi que preguntaste sobre [programa] hace unos días.
            ¿Tienes 2 minutos para resolver alguna duda?"
   
   Si responde → conversation flow
   Si no → voicemail con callback link
```

### Datos técnicos

- **Vapi:** $0.05/min orquestación. Latencia < 500ms. REST API bien documentada.
- **ElevenLabs:** Síntesis de voz < 100ms. 70+ idiomas. Clonación de voz con 1 min de audio.
- **Costo por llamada:** ~$0.15/min. Llamada de 2 min = $0.30. Si convierte 1 de 20 high-ticket ($500+) → ROI claro.

### Por qué es Tier 2 y no Tier 1

1. **LATAM cultural fit:** Las llamadas telefónicas no solicitadas son vistas como spam. Funciona mejor en contexto opt-in ("en caso de que no puedas responder por WhatsApp, te podemos llamar").
2. **Compliance:** LGPD (Brasil), LFPDPPP (México) requieren consentimiento previo para llamadas de marketing.
3. **Arquitecturalmente complejo:** Requiere un nuevo `VoiceAdapter` + manejo de estados de llamada.

**Propuesta:** Implementar como feature opt-in. El tenant activa "AI Follow-up Voice" y el tenant's leads ven en el formulario inicial "¿Podemos llamarte en caso de no poder responder por WhatsApp? Sí/No". Solo llamar a los que dijeron Sí.

---

## 6. Tipos descartados — por qué

### SMS
- WhatsApp: 93-99% penetración LATAM, gratis, interactivo
- SMS: más caro, menos interactivo, mismo número de teléfono
- No hay caso de uso donde SMS gana a WhatsApp en este segmento
- Compliance: misma carga que WhatsApp pero sin las ventajas

### AI Personalized Video (Tavus/HeyGen)
- ROI comprobado: solo para deals > $1,000 USD (high-ticket coaching/consulting)
- Costo: $0.50-$2.00 por video personalizado. Para broadcasts de 200 personas = $100-400 por campaña.
- El segmento core de Nicolify vende programas $50-300 USD → no tiene sentido
- Para nichos de high-ticket consulting: interesante como feature premium en 18+ meses

### Twitter/X DMs
- API de automatización: $5,000/mes (Basic tier). Prohibitivo.
- Audiencia LATAM migrando a TikTok/Instagram
- No hay caso de negocio

### Discord
- Fuerte en gaming, crypto, tech
- Débil en: coaching, cursos online, fitness, negocios, que son el core de Nicolify LATAM
- El creator promedio de Nicolify no usa Discord como canal de ventas

---

## Preguntas abiertas (otros tipos)

1. **Webinar Orchestration MVP:** ¿El primer caso de uso es "lanzamiento de programa" o "webinar de 1 día"? El webinar es más simple (un solo evento, no una ventana de carrito abierto).

2. **Retargeting:** ¿Cuántos tenants de Nicolify ya tienen Meta Business conectado en `connections/`? Eso determina si esto es fácil (solo la UI de export) o necesita setup nuevo.

3. **Web Push:** ¿Las landing pages de Nicolify ya están bajo un dominio/subdominio que el tenant controla? El push requiere HTTPS en dominio propio para el permission prompt.

4. **Referral:** ¿Los tenants actuales piden esta feature? ¿O es algo a lanzar proactivamente?

5. **AI Voice:** ¿Vapi tiene API en español (con ElevenLabs para síntesis)? ¿Hay algún tenant que pueda ser beta tester?
