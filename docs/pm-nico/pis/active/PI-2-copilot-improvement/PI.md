# PI-2-copilot-improvement — Mejorar Copilot

## Meta

| Campo | Valor |
|---|---|
| PI ID | PI-2-copilot-improvement |
| Estado | discovery (placeholder — pendiente kickoff) |
| Tema | Mejoras al copilot — interfaz primaria Nicolify |
| Owner PM | /pm |
| Inicio | 2026-04-29 (placeholder) |
| Cierre estimado | TBD según scope refinado |
| Cierre real | — |

## Outcome esperado

_Pendiente discovery formal._ Hipótesis preliminar: aumentar % de operaciones Nicolify que ocurren via copilot vs UI directa. Mejora consistencia + descubrimiento + autoadopción.

- Cuantitativo: TBD (¿% acciones via copilot? ¿retención day-7?)
- Cualitativo: User dice "siempre uso copilot, la UI es solo cuando necesito ver algo visual"

## Hipótesis

Pendientes discovery. Posibles:
- H1: Hay gaps de capacidades operables conversacionalmente entre módulos (algunos rich, otros pobres) → user inconsistente
- H2: Conversaciones largas pierden contexto (Lost-in-the-Middle) → frustración
- H3: User no descubre lo que copilot puede hacer → infrautiliza
- H4: Cards visuales podrían ser más ricas / interactivas

## Scope

### In (preliminar)

- TBD via discovery

### Out (preliminar)

- TBD

## PRs candidatos

_Vacío. Se llenarán post-discovery._

## Opportunities atendidas

_Pendiente captura._

## Restricciones / Riesgos

- Restricción: cost/turn (Kimi K2.5 / DeepSeek V3 / GPT-4o tier routing) — cualquier mejora debe respetar budget
- Riesgo técnico: subagent isolation invariants ya tienen tests — no romper
- Riesgo: LangGraph + deepagents en producción — cambios estructurales con cuidado

## Decisiones clave

_Pendientes._

## Métricas seguimiento

_Pendientes._

## Discovery tasks pendientes

1. Entrevistar Chris: ¿qué dolor copilot reporta hoy? ¿qué le gustaría mejorar?
2. Lookup current-state copilot.md para gaps documentados
3. Research patrones agentic copilot 2026 (Replit Agent, Cursor, Claude Projects, custom GPTs en SaaS)
4. Captura señales analytics copilot (cost per conversation, success rate, drop-off)
5. Decidir scope (¿bug general o feature gigante? Probablemente un mix)

## Cierre / Retro

Pendiente.
