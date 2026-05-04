# Process — Reglas transversales del harness

**Qué es:** reglas de proceso que aplican a cualquier PI/sprint/story. Bound contract entre Chris + Claude + sub-agents.

## Archivos

| Archivo | Owner | Cuándo leer |
|---|---|---|
| `migration-plan.md` | `/pm` | Resume migración SDD; consultar si phase incompleta |
| `ticket-states.md` | `/architect` + `/dev-team` + `/auditor` | Antes mover ticket de estado |
| `checkpoint-protocol.md` | todos | Resume cualquier sesión |
| `parallel-sessions-protocol.md` | todos | Multi-instancia Claude (M1-M8) |
| `learnings.md` | `/pm` | Append-only post-incident |

## Reglas globales

- **Anti-teléfono-descompuesto.** Subagents devuelven `done -> path/to/artifact.md`. NO payload en chat.
- **Tool subtraction (Vercel).** Cada subagent tiene tools mínimas. Documentación > tooling.
- **Resume protocol.** Cada nivel (PI/sprint/story) tiene `checkpoint.md`. Cualquier sesión retoma desde `next_action`.
- **Ticket state transitions** son explícitas (ver `ticket-states.md`).
- **Single owner por artefacto.** Si 2 agents tocan mismo archivo → conflict → escalate Chris.
- **Self-evaluation prohibida.** Builder no aprueba su propio trabajo. Auditor separado.
- **Auditor con autoridad limitada.** Fixea triviales (lint/typo). Diseño/security/arch → escala.
- **Spanish neutro UI strings.** No voseo (excepto sales_agent voz tenant).
