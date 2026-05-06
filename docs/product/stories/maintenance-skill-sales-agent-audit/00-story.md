---
story_id: maintenance-skill-sales-agent-audit
type: service-story
subtype: maintenance
module: sales_agent
capability: null  # cross-cutting maintenance
estimate: 1d
priority: 1  # PRE-REQUISITE absoluto
links:
  outcome: "../../outcomes/pi-12-sales-agent-eval-foundation.md"
  skill_target: "../../../../.claude/skills/sales-agent-expert/"
---

# Story — Maintenance: audit + actualizar `sales-agent-expert` skill

## Job-To-Be-Done

**Como** /architect y /dev-team que van a leer el skill `sales-agent-expert` para diseñar/construir las stories eval-foundation-*
**Quiero** que el skill SSoT refleje la realidad actual del módulo sales_agent post homologación con copilot (observability, callback handler, cost tracking, etc.)
**Para** que las decisiones arquitectónicas downstream (tenant seed, simulator, personas, goldens, graders) se basen en hechos del código vivo y no en documentación vieja que mienta

## Por qué importa

Discovery con Chris (2026-05-06) reveló:
- Hay homologación reciente entre `sales_agent` y `copilot` (observability + arquitectura base similar)
- Skill `sales-agent-expert/SKILL.md` + `references/` puede tener claims obsoletos
- Si `/architect` lee skill mintiendo → diseña arq incorrecta → `/dev-team` construye sobre base falsa → audit detecta tarde → roundtrip caro

Esta story es PRE-REQUISITO ABSOLUTO. 1d de audit ahora < 5d de re-trabajo después.

## Outcome esperado

- Diff aplicado a `.claude/skills/sales-agent-expert/SKILL.md` con realidad post 2026-05-06:
  - Estado actual del módulo (paths/responsabilidades reales)
  - Surfaces homologadas con copilot (`shared/agent_observability/*` consumers list)
  - Anti-patterns post-cambios (qué NO hacer en el módulo hoy)
  - Decisiones cardinales de los últimos 30 días (PI-12 Stories shipped, LiteLLM canonicalization, etc.)
- `references/` files actualizadas:
  - `sales-agent-brand-voice.md` (verificar SSoT system_instruction sigue siendo `personality_profiles`)
  - `tool-patterns.md` (scheduler/payment/closer specialist tools actuales)
  - `humanization-rules.md` (verificar voseo exception sigue, audio personalizado future flag)
  - `conversation-stages.md` (verificar stages enum actuales)
- Diff documentado en `T-1-impl-log.md` con secciones: "Claims removed", "Claims updated", "Claims added"
- Test de regresión: invocar el skill manualmente y verificar que ejemplos citados existen (`grep` files mencionados → 100% match)

## Antecedentes / Contexto

- **Origen:** discovery 2026-05-06 — Chris explicitó "hemos hecho varios cambios y homologación con copilot, audita como lo tenemos actualmente"
- **Skill target:** `.claude/skills/sales-agent-expert/`
- **Stack:** read-only sobre `backend/src/modules/sales_agent/` + `backend/src/shared/agent_observability/` + `docs/process/learnings.md` últimos 60d
- **Stakeholder primario:** /architect y /dev-team (consumidores del skill) + Chris (oracle)
- **Skills que cargar para audit:** ninguno externo (el audit ES sobre el skill)

## Out of scope (explícito)

- NO refactorizar el módulo `sales_agent` — sólo auditar + documentar
- NO tocar `copilot-expert` skill (puede merecer audit aparte futuro)
- NO actualizar otros skills del repo
- NO crear nueva documentación arquitectónica fuera del skill

## Riesgos / Asunciones

- **Riesgo:** skill cita LOC/paths que ya cambiaron → falsos positivos en audit. **Mitigación:** grep cada path citado, marcar OBSOLETO en lugar de borrar (preserva trazabilidad).
- **Riesgo:** audit revela inconsistencias profundas (módulo viola anti-patterns ahora documentados) → escala scope. **Mitigación:** documentar findings en `T-1-impl-log.md` sección "Surface drift" + escalar a Chris si requiere story aparte de refactor.
- **Asunción:** skill estructura `SKILL.md + references/*.md` se mantiene (no rediseño completo). Solo content update.

## Próximo paso

`→ /po lee este archivo + redacta 01-spec.md service-story con scenarios:
  happy (skill audit completo, diff aplicado, tests pass),
  negative (path citado no existe → OBSOLETO marker),
  edge (homologación con copilot detecta surface compartida nueva no documentada),
  adversarial (skill self-contradicts entre SKILL.md y reference file → flag prioridad alta)`
