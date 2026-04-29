# Email Marketing — Research
**Fecha:** 2026-04-29
**Fuente:** Research sobre MailerLite, Mailchimp, Kit/ConvertKit, ActiveCampaign, Brevo, Klaviyo, Beehiiv

---

## El stack actual de Nicolify con MailerLite

Nicolify ya tiene MailerLite profundamente integrado:
- ETL extraction de campaigns, automations, forms, subscribers (analytics module)
- Webhook listener en `connections/api/marketing_webhooks.py`
- `sync_contacts` y `sync_events` (stubs — no implementado aún)
- Credencial del tenant guardada en `connections/`

**Punto de partida:** No necesitamos cambiar de plataforma. MailerLite ya es la herramienta del tenant. Lo que necesitamos es:
1. Poder **triggerear** actions en MailerLite desde Nicolify (añadir a grupo, iniciar automation)
2. Poder **ver y crear** campañas/automations simples desde Nicolify
3. Que las acciones del Sales Agent generen journey_events que MailerLite puede usar como triggers

---

## Modelo Mental Correcto: Campañas vs. Automatizaciones

Este es el malentendido más común. Son objetos COMPLETAMENTE diferentes:

```
CAMPAÑA (one-shot)
├── El emprendedor la crea en un momento
├── Elige audiencia (snapshot en ese momento)
├── Programa envío
├── Se envía → FIN
└── Tiene stats: opens, clicks, unsubscribes

AUTOMATIZACIÓN (always-on)
├── Está activa continuamente
├── Cada contacto que cumple el trigger → entra individualmente
├── Recorre los pasos a su propio ritmo
├── Puede estar en múltiples automations simultáneamente
├── Tiene exit conditions (se fue, compró, se unsuscribió)
└── Stats: por automation + por step
```

**Analogía:** Una campaña es un evento presencial (todos van el mismo día). Una automatización es un curso online (cada quien lo empieza cuando se inscribe y avanza a su ritmo).

---

## El modelo de MailerLite (el que usamos)

### Grupos vs Segmentos

| Concepto | MailerLite Groups | MailerLite Segments |
|---|---|---|
| Tipo | Estático (se asigna manualmente o por automation) | Dinámico (se recalcula automáticamente) |
| Uso como trigger | SÍ — "cuando alguien se une al grupo X" | SÍ — "cuando alguien entra al segmento X" |
| Ejemplo | "Leads webinar enero 2025" | "Suscriptores activos que abrieron en 90 días" |
| API | `POST /subscribers/{id}/groups` | Solo se crea en UI, no asignación por API |

**La acción clave del Sales Agent:** Cuando un lead completa la calificación o llega a cierta etapa → `POST /api/mailerlite/subscribers` con el email + `groups: ["MQL-calificados"]` → esto dispara automáticamente la automation de MailerLite que tiene trigger "Joins group: MQL-calificados".

Este es el bridge entre el CRM/Sales Agent de Nicolify y las automations de MailerLite del tenant.

### Automation Steps disponibles

```
Email → envía un email (plantilla del tenant)
Delay → espera X días/horas/minutos
Condition → IF/ELSE basado en:
  - ¿Abrió el email anterior?
  - ¿Clickeó link X?
  - ¿Está en grupo Y?
  - ¿Campo Z tiene valor W?
Action →
  - Agregar a grupo
  - Quitar de grupo
  - Actualizar campo
  - Webhook (!!!!) → llama a Nicolify con info del subscriber
  - Copiar a otra automation
```

**El Webhook step es el puente bidireccional:** Una automation de MailerLite puede notificar a Nicolify cuando un lead abre un email → Nicolify actualiza su CRM → si el lead era "frío" se convierte en "tibio".

---

## El modelo mental que debemos exponer al tenant: inspirado en Kit

A pesar de que usamos MailerLite internamente, la UX que le mostramos al tenant debe ser más simple. Kit/ConvertKit es la referencia:

### Kit approach (por qué es la UX correcta para microempresarios)

**Un solo "directorio" de suscriptores** — no múltiples listas. Un suscriptor es un suscriptor. Si está en tu base, lo tienes.

**Tags como organizadores** — en Kit son tags, en MailerLite son grupos. Mismo concepto. Libres, muchos por suscriptor, son la unidad de segmentación.

**Sequences como el corazón** — una sequence es una serie de emails que corren cuando alguien "entra" a ella. Kit separa el contenido (la sequence) de la lógica (la automation). Nicolify debería exponer esto así:

```
Tenant ve en Nicolify:
  "Secuencias" (lista de sequences/automations activas)
  → Welcome (6 emails, 500 subscribers activos)
  → Post-compra (3 emails, 89 subscribers activos)
  → Re-enganche (2 emails, 23 subscribers activos)

NO ve la complejidad de "triggers + conditions + actions" internamente
```

El tenant solo configura:
1. El nombre y objetivo de la secuencia
2. Los emails (en MailerLite, que ya sabe usar)
3. Cuándo entrar (qué acción de Nicolify lo dispara)

Nicolify maneja el "cuándo entrar" automáticamente.

---

## Triggers de automatización: cuándo Nicolify dispara MailerLite

| Acción en Nicolify | Grupo que se activa en MailerLite | Automation que se dispara |
|---|---|---|
| Lead da su email por primera vez | `nuevos-suscriptores` | Welcome sequence |
| Lead llega a MQL (score ≥ 40) | `leads-calificados` | Nurture sequence con ofertas |
| Lead completa compra | `clientes` + `compra-[oferta_slug]` | Post-compra onboarding |
| Lead inactivo > 14 días (score decay) | `reenganche-necesario` | Re-engagement sequence |
| Lead asiste a webinar | `asistio-webinar-[slug]` | Post-webinar close sequence |
| Lead no asistió a webinar (registrado) | `no-asistio-webinar-[slug]` | "Mira el replay" sequence |
| Lead hace click en link del email | Webhook → Nicolify journey_event | Lead score +3 |

**Estos son los 7 triggers más importantes.** Con estos 7, un infoproductor ya tiene un sistema de email marketing completo.

---

## Landing Page → Email capture → Automation (el flujo completo)

Este es el flujo que DEBE funcionar desde Nicolify:

```
1. Tenant crea landing page en Nicolify (módulo landing/)
   → define call-to-action: "Suscríbete y recibe el PDF gratis"
   → conecta formulario a MailerLite (ya existe conexión)

2. Visitante llena el formulario en la landing page
   → Nicolify crea/actualiza suscriptor en MailerLite vía API
   → Asigna grupo "nuevos-suscriptores" (si tiene automation de bienvenida)
   → Asigna grupo "landing-[slug]" para attribution
   → Crea CustomerProfile en CRM con:
       source_ref = "landing_pdf_gratis"
       lead_source = "landing_page"
       primary_email = email_capturado

3. MailerLite automation "Joins group: nuevos-suscriptores" se dispara
   → Email 1: bienvenida + PDF prometido (inmediato)
   → Email 2: D+2 historia personal
   → ... (6 emails en 10 días)

4. Si el suscriptor hace click en un link → MailerLite webhook → Nicolify
   → JourneyEvent("email_clicked", +3 score)
   → CustomerProfile.lead_score actualizado
   → Si lead_score ≥ 40 → cambia a MQL → agrega a grupo "leads-calificados"
```

**Lo que falta hoy:**
- El form de la landing page ya puede capturar email, pero ¿lo envía a MailerLite con los grupos correctos?
- ¿El `sync_contacts` stub maneja la creación bidireccional?
- ¿El webhook de MailerLite → Nicolify está procesando clicks para journey_events?

---

## Automatizaciones de alto impacto para infoproductores

Basado en benchmarks de la industria:

### 1. Welcome Sequence (ROI: 51% average open rate — el más alto de cualquier email)

```
Email 1 (inmediato): "Aquí está lo que prometí" + deliver lead magnet
Email 2 (D+2):       Tu historia. Por qué haces esto.
Email 3 (D+4):       Tu mejor contenido gratuito
Email 4 (D+6):       Testimonios de clientes
Email 5 (D+8):       "Mucha gente me pregunta sobre [programa]..."
Email 6 (D+10):      Call-to-action directo con oferta
```

**Branching inteligente:**
- Si abrió Email 3 → skip Email 4, ir directo a Email 5 (ya está enganchado)
- Si compró en cualquier punto → exit sequence, entrar a post-purchase

### 2. Post-Webinar Close Sequence (D0 hasta D+3)

```
D0 +2h:  "¿Cómo te fue?" + replay disponible + resumen de lo que vimos
D+1:     "Estas son las preguntas más frecuentes que recibí..."
D+2:     "El replay estará disponible hasta mañana" + última oportunidad
D+3:     "Cerramos hoy" + urgencia real + oferta final
```

### 3. Re-engagement (para inactivos > 30 días)

```
Email 1: "¿Sigues ahí?" — tono casual, nada de vender
Email 2 (D+3): "Quizás esto te interese..." — contenido de valor
Email 3 (D+7): "Si no abres esto, te quito de la lista" — honestidad
Si no abrió ninguno → marcar como inactivo, quitar de envíos regulares (proteger deliverability)
```

### 4. Abandono de carrito / Payment link no completado

```
D0 +1h:  "Parece que te quedaste a medias..."
D0 +24h: "¿Pasó algo?"
D+3:     "Tu lugar sigue disponible... por ahora"
```

MailerLite soporta esto via webhook desde Nicolify cuando `Enrollment.status = PAYMENT_PENDING` y no cambia en 1h.

---

## Transaccional vs Marketing — separación crítica

Esta distinción es non-negotiable en producción:

| | Transaccional | Marketing |
|---|---|---|
| Ejemplos en Nicolify | Confirmación de pago, recordatorio de cita, contraseña | Newsletter, secuencia de bienvenida, campaña de lanzamiento |
| Herramienta | Brevo SMTP / Postmark / Resend (sistema Nicolify) | MailerLite (cuenta del tenant) |
| Requiere opt-in | No (relación de servicio) | Sí |
| Puede llevar unsubscribe | No | Obligatorio |
| Open rate esperado | 80-95% | 20-40% |
| Riesgo deliverability | Bajo | Medio (afecta reputación del dominio) |

**Regla:** Todo email que sale de Nicolify como plataforma (sistema) → Brevo/Postmark. Todo email que sale en nombre del tenant para su audiencia → MailerLite del tenant.

**Nunca mezclar los dos.** Un hard bounce en una campaña de marketing puede contaminar la reputación del dominio y mandar los emails transaccionales a spam.

---

## Deliverability checklist para onboarding de nuevo tenant

Cuando un tenant conecta MailerLite, Nicolify debe verificar/guiar:

1. ✅ Dominio custom autenticado en MailerLite (SPF + DKIM)
2. ✅ DMARC configurado (al menos `p=none` con `rua` report)
3. ✅ Double opt-in habilitado (recomendado fuertemente)
4. ✅ Welcome automation creada (o usar template de Nicolify)
5. ✅ Unsubscribe link activo en todos los emails
6. ✅ Sender address real (no generic)

**Estos 6 puntos pueden verificarse via MailerLite API** y mostrarse como un "deliverability score" en el dashboard de connections.

---

## Decisiones pendientes (email marketing)

1. **UI propia vs. abrir MailerLite:** ¿Construimos una interfaz de campaigns/automations dentro de Nicolify, o el tenant va directamente a MailerLite para editar? Recomendación: Nicolify orquesta los triggers y muestra métricas, el tenant edita el contenido en MailerLite (ya sabe usarlo).

2. **Template de welcome sequence preinstalada:** ¿Al conectar MailerLite, Nicolify crea automáticamente la automation de bienvenida en la cuenta del tenant? Sería un onboarding killer feature.

3. **Bidirectional sync:** ¿Cuándo implementamos `sync_contacts` (lead en Nicolify CRM → suscriptor en MailerLite)? Este es el bridge fundamental.

4. **Click/open events → CRM:** ¿Cuándo activamos el webhook de MailerLite → Nicolify para capturar clicks/opens como journey_events? Esto actualizaría el lead_score automáticamente.

5. **Propio SMTP (Brevo):** ¿Qué emails transaccionales necesita enviar Nicolify YA? ¿Están usando Brevo o están sin configurar?
