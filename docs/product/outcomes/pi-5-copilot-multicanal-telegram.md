---
id: pi-5-copilot-multicanal-telegram
state: done
title: Copilot multicanal — Telegram MVP (V1 only)
why_now: |
  Dueño usa más Telegram que web fuera de horario laboral. Mobile-first
  consulta del copilot = ganancia productividad real. HITL Telegram baja
  churn de leads alto ticket (hoy se enfrían cuando dueño tarda en responder
  edge case sales_agent).
target_end: 2026-05-01
closed_at: 2026-05-06
priority: 1
created: 2026-04-30
last_modified: 2026-05-06
migrated_from: docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/
story_ids:
  - copilot-telegram-magic-link
  - copilot-telegram-orchestrator-respond
success_metrics:
  - "Bot global @nicolify_copilot_bot vinculado vía magic link 15min single-use HMAC funcional end-to-end"
  - "Orchestrator real responde DMs Telegram con channel format MarkdownV2 + tool subset filter + memory cost-aware"
  - "Tests passing: 86 copilot telegram tests + 9 arch fitness telegram_separation tests"
  - "Latencia <3s p95 turn no-streaming (objetivo S2 — verificable post-deploy con observability S5 deferred)"
tags:
  - module:copilot
  - type:feature
  - channel:telegram
  - scope:v1-only
---

# Copilot multicanal — Telegram MVP (V1)

Extender copilot al canal Telegram con bot global Nicolify (`@nicolify_copilot_bot`).
Pattern multicanal extensible (WhatsApp + IG DM = futuros outcomes separados).

**V1 scope (shipped):** magic link linking + orchestrator real responde DMs.
**Deferred (NOT shipped):** notificaciones proactivas, HITL escalation sales_agent,
arch fitness completo + observability — ver § Closure note abajo.

## Migration note
This outcome was migrated from legacy paradigm (`docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/`)
on 2026-05-05 as part of Wave 2 PM redesign. Full original content archived at
`docs/archive/2026/legacy-pis/PI-5-copilot-multicanal-telegram/`.

## Original content summary

JTBD: "Cuando estoy fuera de la laptop (celular, reunión, calle), quiero
consultar el estado de mi negocio o dejar encargos a mi copilot, para no
perder tiempo ni momentum mientras estoy lejos del escritorio."

In-scope original PI-5 (5 sprints planeados):
- S1 — Telegram bot global + magic link linking (SHIPPED)
- S2 — Orchestrator hookup + memory + cache + tool subset filter (SHIPPED)
- S3 — HITL escalation sales_agent (LangGraph interrupt pattern) (DEFERRED)
- S4 — Notificaciones proactivas + `copilot_owner_todos` (DEFERRED)
- S5 — Arch fitness completo + observability/telemetría (DEFERRED)

Out (siempre): WhatsApp / IG DM (futuros outcomes separados). Bots per-tenant.

Surface live post-S2:
- `CopilotOrchestrator.invoke_text(channel, ..., context)` non-streaming entrypoint
- `ContextWindowBuilder.for_channel()` + `RollingSummarizer.for_channel()` classmethods
- `PromptFragment.TELEGRAM_CHANNEL_CONTEXT` cache fragment (~2200 tokens stable)
- Tool registry runtime filter via `ToolGroupMeta.available_channels`
- `ConversationRepository.get_or_create_by_channel()` tenant-scoped

## Closure note (2026-05-06) — V1 scope only

**Decisión Chris:** cerrar V1 honestamente. Outcome legacy paradigma permitía
rolling sin force-close → S3-S5 quedaron en limbo. Paradigma nuevo (post
pm-redesign 2026-05) exige finite outcomes con merge event-driven. Cerramos
PI-5 con lo que efectivamente shipea valor (S1+S2) y diferimos S3-S5 a un
outcome fresh si/cuando retomemos.

### Shipped (V1)
- **S1 — copilot-telegram-magic-link** (story `live`, commit `c1fa2909` 2026-04-30)
  - Path: [docs/product/stories/copilot/copilot-telegram-magic-link.yaml](../stories/copilot/copilot-telegram-magic-link.yaml)
  - Bot global + magic link 15min HMAC single-use + webhook non-blocking ARQ
- **S2 — copilot-telegram-orchestrator-respond** (story `live`, commit `d09799b9` 2026-05-01, close `6bad657b`)
  - Path: [docs/product/stories/copilot/copilot-telegram-orchestrator-respond.yaml](../stories/copilot/copilot-telegram-orchestrator-respond.yaml)
  - `invoke_text()` orchestrator + memory cost-aware + cache prefix Telegram + tool subset filter + MarkdownV2

### Tests verification (2026-05-06)
- `pytest tests/modules/copilot/ -k telegram`: **86 passed, 0 failed**
- `pytest tests/architecture/test_copilot_telegram_separation.py`: **9 passed, 0 failed**

### Deferred to future outcome (paradigma nuevo, NOT done)

Si futuro retomar, crear outcome fresh con story_ids ad-hoc. NO reabrir este.

- **S3 — HITL escalation sales_agent** (LangGraph interrupt pattern: pause
  → notify dueño Telegram → wait response → resume con respuesta inyectada)
- **S4 — Notificaciones proactivas + `copilot_owner_todos`** (alerts
  métricas críticas + reminders + tabla owner_todos)
- **S5 — Arch fitness completo + observability/telemetría** (DTO cache
  token fields wire-up + UNIQUE constraint conversations multi-channel +
  eval suite Telegram-specific + prompt injection adversarial coverage)

### Known capability gaps (5) — capability `copilot-telegram-channel`
Documentadas en [capabilities/copilot/copilot-telegram-channel.yaml](../capabilities/copilot/copilot-telegram-channel.yaml)
con `defer_reason: pi-5-v1-scope-only`. Resumen verbatim:

- DTO cache token fields hardcoded 0 (S5 wire-up pendiente) — invoke_text outer except defensive set_turn_error
- UNIQUE constraint conversations multi-channel deferred S5 PR-5 — race posible en SELECT-then-INSERT
- BotFather setWebhook prod `@nicolify_bot` post-deploy = operación pendiente Chris
- No eval suite Telegram-specific (memory windowing + cache prefix con persona simulated)
- Adversarial: prompt injection via Telegram caption — no testeado

### Lessons learned

- **Scope honesty > rolling momentum.** Paradigma legacy permitía outcome
  vivo indefinido; sprints quedaban "pendientes" sin pressure de cerrar.
  Resultado: capability live con 5 gaps no atacados + success_metrics con
  números (≥3 encargos, ≥70% adopción) que nunca se midieron por falta de S4.
- **Paradigma nuevo (finite outcomes, event-driven merge) previene este
  drift.** Si futuro retomamos Telegram → outcome fresh con scope explícito,
  no reabrir éste.
