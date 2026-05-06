---
id: pi-5-copilot-multicanal-telegram
state: building
title: Copilot multicanal — Telegram MVP
why_now: |
  Dueño usa más Telegram que web fuera de horario laboral. Mobile-first
  consulta del copilot = ganancia productividad real. HITL Telegram baja
  churn de leads alto ticket (hoy se enfrían cuando dueño tarda en responder
  edge case sales_agent).
target_end: null
priority: 1
created: 2026-04-30
last_modified: 2026-05-05
migrated_from: docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/
story_ids: []
success_metrics:
  - ">=10 capacidades clave consultables desde Telegram + >=3 tipos encargo, latencia <3s p95"
  - ">=70% adopción Telegram link entre tenants activos a 30 días post-launch"
  - "Cualitativo: 'el copilot me responde como mi account manager — le pregunto desde el celular'"
tags:
  - module:copilot
  - type:feature
  - channel:telegram
---

# Copilot multicanal — Telegram MVP

Extender copilot al canal Telegram con bot global Nicolify (`@nicolify_copilot_bot`).
Pattern multicanal extensible (WhatsApp + IG DM = futuros outcomes separados).
Incluye HITL escalation para que sales_agent pause y consulte al dueño en
Telegram cuando hay decisión sensible en lead alto ticket.

## Migration note
This outcome was migrated from legacy paradigm (`docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/`)
on 2026-05-05 as part of Wave 2 PM redesign. Full original content archived at
`docs/archive/2026/legacy-pis/PI-5-copilot-multicanal-telegram/`.

Estado en migración: S1-foundation-telegram-bot shipped (commit `c1fa2909`).
S2-telegram-orchestrator-memory-cache shipped (commit `d09799b9` PR-2 +
`6bad657b` close 2026-05-01). Sprints S3+ pendientes (notificaciones
proactivas, HITL escalation, etc).

## Original content summary

JTBD: "Cuando estoy fuera de la laptop (celular, reunión, calle), quiero
consultar el estado de mi negocio o dejar encargos a mi copilot, para no
perder tiempo ni momentum mientras estoy lejos del escritorio."

In-scope (PI-5):
- Telegram bot global (1 token env var, único, NO per-tenant). DMs only
- Linking chat_id ↔ tenant via magic link in-app + deep link `t.me/bot?start=TOKEN`
- Tool subset map SSoT (`available_in_channels: ["web","telegram"]`)
- Conversation memory cost-aware (hybrid: recent N + summary older + vector retrieval)
- Notificaciones proactivas (alerts métricas críticas + sales_agent HITL + reminders)
- HITL sales_agent escalation (LangGraph interrupt pattern: pause → notify
  copilot Telegram → wait owner response → resume con respuesta inyectada)

Out: WhatsApp / IG DM (futuros outcomes separados). Bots per-tenant (escala
mata).

Surface live post-S2 (per handoff.md):
- `CopilotOrchestrator.invoke_text(channel, ..., context)` non-streaming entrypoint
- `ContextWindowBuilder.for_channel()` + `RollingSummarizer.for_channel()` classmethods
- `PromptFragment.TELEGRAM_CHANNEL_CONTEXT` cache fragment (~2200 tokens stable)
- Tool registry runtime filter via `ToolGroupMeta.available_channels`
- `ConversationRepository.get_or_create_by_channel()` tenant-scoped

Pendiente S3+: notificaciones proactivas implementación + HITL interrupt.
