# campaigns — Estado funcional

## Meta

| Campo | Valor |
|---|---|
| Studio padre | Sales / Growth (TBD via PI-1 — probablemente Sales con hooks Growth) |
| Estado | nuevo (PI-1 en discovery → planning, S0 in-progress) |
| Última actualización | 2026-04-29 (PR-0 saneamiento research) |
| Doc técnico | _no existe aún — módulo nuevo en construcción_ |

## Qué hace por el user

**No existe aún como módulo dedicado.** Hoy hay piezas dispersas:
- Sales Agent puede mensajear leads inbound (no es "campaña" estructurada).
- Connections tiene MailerLite / Manychat conectados (canales, sin orquestación).
- Assets genera copies (sin enviarlos).

PI-1 unifica esto en módulo `campaigns/` que orquesta multi-canal con primitivas robustas (outbox, idempotency, plan tiers + budget guard, compliance, observability ext).

## Capacidades actuales

**Cero como módulo.** Capacidades fragmentadas hoy:

| Capacidad fragmentada | Dónde vive | Limitación |
|---|---|---|
| Mensaje individual lead Telegram/WhatsApp | sales_agent (inbound only) | No outbound, no segmento, no template |
| Email send via MailerLite | connections (ETL lectura) | No automation trigger desde Nicolify |
| Lifecycle scoring | crm | Sin trigger a action |
| Source attribution UTM | landing parcial | No persiste a CustomerProfile |

## Capacidades operables desde copilot (hoy / proyectadas)

| Capacidad | Hoy | PI-N | Tool |
|---|---|---|---|
| Lanzar campaña outbound | ❌ | PI-2 (Marketing Campaign Subagent) | `campaign_create` + `campaign_launch` |
| Consultar status campaña | ❌ | PI-1 S3 | `campaign_get_status` |
| Pausar/activar | ❌ | PI-1 S3 | `campaign_pause` / `campaign_launch` |
| Crear segmento NL | ❌ | PI-2 | `segment_create` |
| Performance queries | ❌ | PI-2 | `campaign_roi` |
| Export segment Meta Ads | ❌ | PI-3 | `export_segment_to_meta` |

## UI capabilities (PI-1 S4 lite + PI-3 completo)

| Capacidad UI | Hoy | PI-1 S4 (lite) | PI-3 (completo) |
|---|---|---|---|
| Vista lista contactos con filtros básicos | ❌ (stub) | ✅ tabla + lifecycle/score/channel/search | ✅ + filtros avanzados (traits, ranges) |
| Detail contacto | ❌ | ✅ drawer (identidades, score, source, link Inbox) | ✅ página completa + timeline rico |
| Segment manual (selección múltiple) | ❌ | ✅ POST STATIC | ✅ + bulk actions |
| Segment Builder Visual (drag-drop filters) | ❌ | ❌ | ✅ POST DYNAMIC |
| Campaign Dashboard (performance) | ❌ | ❌ | ✅ |
| Lanzar campaña Telegram desde segment | ❌ | ✅ botón básico | ✅ + multi-canal |
| Export segment Meta Ads | ❌ | ❌ | ✅ |

## Estado calidad funcional

| Capacidad | Estado | Notas |
|---|---|---|
| Módulo campaigns/ en sí | inexistente | Crea PI-1 |
| Outbound conversational | inexistente | PI-1 S3 (MVP 1 Telegram) |
| Source-aware treatment | inexistente | PI-1 Sprint 1 (campos CRM) + Sprint 3 (override flow) |
| Email drip MailerLite bridge | parcial (ETL lectura) | PI-2 completa write side |
| Event campaign / launch | inexistente | PI-3 |
| Retargeting Meta Ads | inexistente (placeholder advertising/) | PI-3 |
| TikTok DM automation | inexistente | PI-2/3 |

## Conexiones cross-módulo (proyectado)

- **Leerá de:** crm (segmentos, customer profiles), connections (canales, MailerLite/ManyChat/Meta), offer (qué se promociona), assets (copy/asset opcional), commercial_calendar (timing futuro), brand (voz para Sales Agent outbound).
- **Lo leerá:** copilot (Marketing Campaign Subagent), sales_agent (OutboundOrchestrator extension), analytics (campaign performance), advertising (retargeting export).

## Oportunidades capturadas

| Slug | Tier | PI |
|---|---|---|
| [outbound-conversational](../opportunities/outbound-conversational.md) | Tier 1A | PI-1 S3 |
| [source-aware-treatment](../opportunities/source-aware-treatment.md) | Tier 1B | PI-1 S1+S3 |
| [email-drip-mailerlite](../opportunities/email-drip-mailerlite.md) | Tier 1C+1D | PI-2 |
| [event-campaign-orchestration](../opportunities/event-campaign-orchestration.md) | Tier 1E | PI-3 |
| [retargeting-meta-ads](../opportunities/retargeting-meta-ads.md) | Tier 1F | PI-3 |
| [tiktok-dm-automation](../opportunities/tiktok-dm-automation.md) | Tier 1G | PI-2/3 |

## Dolor user / oportunidades detectadas

Capturadas en opportunities/ arriba. Driver común: **emprendedor no quiere aprender 3 herramientas separadas (Mailchimp + ManyChat + HubSpot). Quiere "todo desde Nicolify".**

## PIs históricos / activos

| PI | Estado | Tema |
|---|---|---|
| PI-1 | discovery → planning, S0 in-progress | campaigns module (foundation + MVP 1 Telegram) |
| PI-2 | Next (placeholder) | Multi-canal (ManyChat bridge) + Copilot subagent + EMAIL_DRIP |
| PI-3 | Later (placeholder) | Event campaigns + CRM Hub Frontend + Retargeting |
| PI-4 | Later (placeholder) | Push (OneSignal) + Referral / Afiliados |

## Decisiones producto vinculadas

Ver [`pis/PI-1-campaigns-module/decisions.md`](../pis/PI-1-campaigns-module/decisions.md). Resumen:
- D1-D9: heredadas legacy (multi-canal, no templates, foundation-first, Commercial Director = Copilot subagent, B2C only, módulo independiente, Copilot único contacto, ManyChat bridge transitorio, Telegram tests).
- D10: Sprint 0 = Robustez + Escalabilidad cross-cutting.
- D11: PI-1 cierra con MVP 1 Telegram. Multi-canal/email/event a PI-2/3.
- D12: Primitivas S0 viven en `shared/`.
- D13: 5 planes tarifarios con tope LLM mensual ($5/$15/$30/$45/$95).
- D14: Reservación 50% sales_agent (BudgetGuard invariante).
- D15: Outbox global (no solo campaigns).
- D16: Reusa `shared/agent_observability/` (no módulo nuevo).
- D17: Sprint 0 cortado a 5 sub-sprints.

## Input históricos (legacy)

`docs/pm/campaigns/` — research original (5 carpetas + FOUNDATION + MASTER_TODO). Sintetizado en [`research/2026-04-29-campaigns-foundation-synthesis.md`](../research/2026-04-29-campaigns-foundation-synthesis.md). Decisión de archivado al cierre PI-1.
