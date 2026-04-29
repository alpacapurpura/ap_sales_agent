# PI-3-sales-agent-improvement — Mejorar Sales Agent

## Meta

| Campo | Valor |
|---|---|
| PI ID | PI-3-sales-agent-improvement |
| Estado | discovery (placeholder — pendiente kickoff) |
| Tema | Mejoras al Sales Agent post redesign 2026-04 |
| Owner PM | /pm |
| Inicio | 2026-04-29 (placeholder) |
| Cierre estimado | TBD según scope refinado |
| Cierre real | — |

## Outcome esperado

_Pendiente discovery formal._ Hipótesis preliminar: el redesign 2026-04 dejó base sólida; siguiente etapa = profundizar en cierre real (vs solo conversar bien). Voz marca + tools + observabilidad están sólidos. ¿Qué falta para que cierre más?

- Cuantitativo: TBD (¿% leads → cita? ¿% citas → cliente?)
- Cualitativo: User dice "el agente cierra solo, ya no necesito tomar las riendas"

## Hipótesis

- H1: Agente conversa bien pero cierre podría estar débil (closer studio recién entró)
- H2: Multi-canal sigue gap (WhatsApp pendiente, otros canales)
- H3: Follow-up engine podría ser más inteligente (timing, contenido)
- H4: Voz marca está sólida pero podría tener anchors RAG per-tenant cuando >50 mensajes reales aprobados (Slot 5 placeholder hoy)

## Scope

### In (preliminar)

- TBD via discovery

### Out (preliminar)

- Voz marca foundation (ya está sólida — solo evolución incremental)
- Cost optimization (ya están con tier routing)
- Observabilidad (ya está sólida post rebuild 2026-04)

## PRs candidatos

_Vacío._

## Opportunities atendidas

_Pendiente captura._

## Restricciones / Riesgos

- Restricción: voz marca SSoT en `personality_profiles.system_instruction` — cualquier change respeta rule `sales-agent-brand-voice.md`
- Restricción: subagent isolation invariants — no romper
- Restricción: 8 tests obligatorios brand-voice (ver rule)
- Riesgo: golden tests requeridos para detectar drift con cambios modelo (ya rebuild planeado en rule)

## Decisiones clave

_Pendientes._

## Métricas seguimiento

_Pendientes._

## Discovery tasks pendientes

1. Entrevistar Chris: ¿agente cierra? ¿en qué falla? ¿qué reportan tenants?
2. Lookup current-state sales-agent.md
3. Research SDR AI 2026 (11x AI, AISDR, Regie.ai, Outreach Pulse, Salesforce Agentforce 3)
4. Captura métricas reales (cost per conversation, close rate por tenant)
5. Decisión: WhatsApp como next-channel? O closer studio refinement primero?

## Cierre / Retro

Pendiente.
