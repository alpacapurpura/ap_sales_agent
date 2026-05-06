---
id: pi-3-sales-agent-improvement
state: validated
title: Mejorar Sales Agent post redesign 2026-04
why_now: |
  Redesign 2026-04 dejó base sólida (voz marca, tools, observabilidad). Próxima
  etapa es profundizar en cierre real (vs solo conversar bien) y completar
  multi-canal (WhatsApp pendiente).
target_end: null
priority: 2
created: 2026-04-29
last_modified: 2026-05-05
migrated_from: docs/pm-nico/pis/active/PI-3-sales-agent-improvement/
story_ids: []
success_metrics:
  - "Cuantitativo TBD (% leads → cita, % citas → cliente)"
  - "Cualitativo: 'el agente cierra solo, ya no necesito tomar las riendas'"
---

# Mejorar Sales Agent post redesign 2026-04

Mejoras al sales_agent post redesign 2026-04. Hipótesis preliminar: la base
conversacional + voz marca + observabilidad están sólidas; lo que falta es
profundizar en cierre real (closer studio recién entró) + completar
multi-canal (WhatsApp pendiente) + follow-up engine más inteligente.

## Migration note
This outcome was migrated from legacy paradigm (`docs/pm-nico/pis/active/PI-3-sales-agent-improvement/`)
on 2026-05-05 as part of Wave 2 PM redesign. Full original content archived at
`docs/archive/2026/legacy-pis/PI-3-sales-agent-improvement/`.

Estado en migración: discovery placeholder — no kickoff ni stories formales aún.

## Original content summary

PI-3 fue creado 2026-04-29 como placeholder para tracking de mejoras
incrementales al sales_agent. Hipótesis driver:

- H1: Agente conversa bien pero cierre podría estar débil
- H2: Multi-canal sigue gap (WhatsApp pendiente, otros canales)
- H3: Follow-up engine podría ser más inteligente (timing, contenido)
- H4: Voz marca podría tener anchors RAG per-tenant cuando >50 mensajes reales aprobados

Discovery tasks pendientes (per archived PI.md):
1. Entrevistar Chris: ¿agente cierra? ¿en qué falla? ¿qué reportan tenants?
2. Captura métricas reales (cost per conversation, close rate por tenant)
3. Decisión: WhatsApp como next-channel, o closer studio refinement primero
4. Research SDR AI 2026 landscape

Restricciones heredadas: voz marca SSoT en `personality_profiles.system_instruction`;
subagent isolation invariants intactas; 8 tests obligatorios brand-voice;
golden tests para detectar drift.
