# Sprint S3 — MVP 1 Telegram Outbound

## Meta

| Campo | Valor |
|---|---|
| Sprint ID | S3-mvp-telegram |
| PI padre | PI-1-campaigns-module |
| Estado | not-started (bloqueado por S2) |
| Inicio | TBD post-S2 cierre |
| Cierre estimado | +1-2 semanas después S2 cierre |
| Cierre real | — |
| Owner PM | /pm |

## Objetivo (1 línea)

Primer end-to-end visible: Chris envía campaña Telegram a 5+ contactos reales desde UI (S4) → Sales Agent OutboundOrchestrator personaliza outbound → leads que responden vuelven a Inbox con tag campaign_id → analytics endpoint sirve métricas básicas (SENT/RESPONDED/CONVERTED).

**PI-1 cierra acá si S3 + S4 mergean.**

## Pre-handoff (input desde S2)

- **Decisiones tomadas S2:** link a `../S2-orchestrator/handoff.md`
- **Surface disponible:**
  - CampaignOrchestrator.launch() + 3 ARQ workers operables
  - ChannelRouter v1 Telegram select_channel
  - BudgetGuard + ComplianceService wired (cutover S2)
  - Circuit breaker + audit log
- **Riesgos abiertos:**
  - sales_agent voice fidelity en outbound (no probado tonadas largas)
  - Inbound reply recognition cross-conversation (matching CampaignTask)

## Plan PRs (folders) — DESCOMPONER POST-S2 HANDOFF

> S3 es cross-stack (BE sales_agent + FE Inbox + E2E). Posiblemente 2-3 PRs.

| PR (tentativo) | Scope | Stack | Esfuerzo | Estado |
|---|---|---|---|---|
| PR-7-outbound-orchestrator | sales_agent: OutboundOrchestrator paralelo a ChatOrchestrator + AgentState campaign_id/instructions/outbound_mode + slot CAMPAIGN_CONTEXT en compose.py + supervisor routing (skip qualifier para score≥40 si outbound_mode=True) + sales_agent_adapter (CampaignTask → OutboundOrchestrator) | BE | L | not-started |
| PR-8-inbound-recognition-and-inbox-tag | Inbound reply recognition (ChatOrchestrator busca CampaignTask SENT últimas 24h → inyecta campaign_id) + Inbox UI tag "campaña: {name}" + Campaign analytics endpoint GET `/campaigns/{id}/stats` (SENT/RESPONDED/CONVERTED) | BE+FE | M | not-started |
| PR-9-e2e-and-manual-test | E2E test Playwright (crear campaign → launch → verify Telegram sent) + Chris manual test 5+ contactos reales (proceso documentado, no entregable code) | E2E | S | not-started |

**Cohesión:**
- PR-7 = sales_agent surface extension. BE-only.
- PR-8 = recognition + visibility. Cross-stack thin.
- PR-9 = validación final. Mínimo code (test E2E + checklist manual).

**Paralelo a S4-crm-hub-lite** (Sprint paralelo separado, mismo PI). S4 entrega `/sales/contactos` UI necesaria para que Chris pueda crear segmento manual + lanzar campaña → consume PR-7/PR-8.

## Criterio éxito sprint (PI-1 cierre criteria)

- [ ] PR-7 + PR-8 + PR-9 shipped con RESULT.md
- [ ] `/test-backend` + `/test-frontend` 21 gates verde
- [ ] Chris envía campaña Telegram real a 5+ contactos desde UI S4
- [ ] 0 mensajes duplicados (verificar via `domain_event_outbox` query)
- [ ] 0 leak cross-tenant (test arch verde)
- [ ] ≥3 trace events por campaign launch (`launch / task_created / task_sent`)
- [ ] Inbound reply de lead → conversación tagged `campaign_id` correcto
- [ ] Analytics endpoint sirve stats correctos (1 SENT verified, 1 RESPONDED si lead respondió)
- [ ] `current-state/{campaigns,sales_agent}.md` con capabilities lineage

## Out of scope (a PI-2/3)

| Item | PI futuro |
|---|---|
| Copilot Marketing/Commercial Director subagent (NL → campaign creation) | PI-2 |
| ManyChat bridge (WhatsApp via ManyChat) | PI-2 |
| MailerLite EMAIL_DRIP | PI-2 |
| EVENT_TRIGGER (webinar/launch multi-step) | PI-3 |
| Retargeting Meta Ads | PI-3 |
| CRM Hub completo (Segment Builder Visual + Campaign Dashboard + página detail) | PI-3 |

## Decisiones a tomar durante sprint

| Fecha | Decisión | PR |
|---|---|---|
| TBD | Voice fidelity grader threshold para outbound (≥0.7 prod)? | PR-7 |
| TBD | Inbound recognition window (24h conservador? expandir 48h?) | PR-8 |
| TBD | Analytics live (DB query) vs cached MV refresh 5min | PR-8 |

## Riesgos

| Riesgo | Mitigación | Owner |
|---|---|---|
| sales_agent suena robótico en outbound (falta context inicial) | Voice fidelity grader test obligatorio. Sample 20 outbounds → manual review Chris | builder |
| Telegram rate-limit (Bot API 30 msgs/sec) | OutboundRateLimiter S0 + chunking + backoff | architect |
| Lead responde campaña 3 días después → CampaignTask SENT timestamp ya old | Window 48h configurable + fallback "no campaign context" si miss | architect |
| Falsos positivos en inbound recognition (lead responde no relacionado) | Score similarity contenido + threshold | architect |
| E2E test flaky (Telegram API real) | Mock Telegram API en CI. Manual test = staging real | builder |

## Cierre (PI-1 cierre potencial)

1. Llenar `learnings.md`
2. Llenar `handoff.md` para PI-2 (multi-canal expansion) — surface ChannelRouter + OutboundOrchestrator extension points
3. Marcar `done`
4. Verificar `RESULT.md` PRs
5. **Si último sprint PI-1** (S3 + S4 ambos shipped):
   - Escribir `pis/active/PI-1-campaigns-module/retro.md`
   - Mover folder completo a `pis/archive/PI-1-campaigns-module/`
   - Update roadmap.md: PI-1 → Done section
   - Open PI-2-campaigns-multi-canal en Now (placeholder ya en Next)
