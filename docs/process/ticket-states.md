# Ticket State Machine

> Owner: `/architect` (escribe), `/dev-team` (transitions), `/auditor` (verdict).
> SSoT estados ticket. Cualquier cambio de estado debe loguear transition en `04-tickets.yaml::tickets[].transitions[]`.

## Estados (12)

```
                ┌──────────┐
                │  draft   │  /architect crea ticket
                └────┬─────┘
                     │ deps OK + handoff completo
                     ▼
                ┌──────────┐
                │  ready   │  en queue, esperando dev
                └────┬─────┘
                     │ /dev-team toma
                     ▼
                ┌──────────┐
                │ assigned │  owner asignado
                └────┬─────┘
                     │ dev empieza
                     ▼
                ┌──────────┐
                │ building │  TDD en curso
                └────┬─────┘
                     │
       ┌─────────────┴───────────────┐
       │                             │
       ▼                             ▼
┌──────────────┐               ┌──────────────┐
│tests-failing │               │tests-passing │
└──────┬───────┘               └──────┬───────┘
       │ retry building              │ git push
       │ (cap 5 → blocked)           ▼
       │                       ┌──────────┐
       └──────────────────────►│  pushed  │
                               └────┬─────┘
                                    │ /auditor toma
                                    ▼
                               ┌──────────┐
                               │ auditing │
                               └────┬─────┘
                                    │
                       ┌────────────┴───────────┐
                       │                        │
                       ▼                        ▼
              ┌──────────────────┐     ┌──────────────┐
              │changes-requested │     │ audit-passed │
              └────────┬─────────┘     └──────┬───────┘
                       │ back to building     │ /pm aplica
                       │ (cap 2 → escala)     ▼
                       │                ┌──────────┐
                       │                │  merged  │
                       │                └────┬─────┘
                       │                     │
                       │                     ▼
                       │                ┌──────────┐
                       │                │  closed  │
                       │                └──────────┘
                       │
                       └──────► [building]

           ┌──────────┐
           │ blocked  │  cualquier estado → blocked si bloqueo externo
           └──────────┘  Resuelve Chris → vuelve a estado anterior
```

## Definiciones por estado

| State | Quien transitiona desde | Quien transitiona a | Reglas |
|---|---|---|---|
| `draft` | (initial) | `/architect` → `ready` | Architect creando ticket. Aún no tiene handoff completo. |
| `ready` | `/architect` | `/dev-team` → `assigned` | Handoff completo, dependencies cumplidas (depends_on todos audit-passed). En queue. |
| `assigned` | `/dev-team` | dev → `building` | Owner concreto asignado (qwen-opencode | claude-opus | claude-sonnet). |
| `building` | dev | dev → `tests-failing` o `tests-passing` | TDD activo. Bitácora viva en `T-{n}-impl-log.md`. |
| `tests-failing` | dev | dev → `building` | Local quality gates rojo. Cap 5 iteraciones → escala blocked. |
| `tests-passing` | dev | dev → `pushed` | Local 100% verde. git push pendiente. |
| `pushed` | dev | `/auditor` → `auditing` | Commit pusheado a development. /auditor puede tomar. |
| `auditing` | `/auditor` | `/auditor` → `audit-passed` o `changes-requested` | Auditor corre tests + review. |
| `changes-requested` | `/auditor` | dev → `building` | Iteración. Cap 2 → escala. |
| `audit-passed` | `/auditor` | `/pm` → `merged` | Listo para merge a producto. |
| `merged` | `/pm` | (auto) → `closed` | Diff aplicado a `product/`. Story status updated. |
| `closed` | (terminal) | — | Ticket histórico. No más cambios. |
| `blocked` | any | resolución Chris → estado anterior | Bloqueo externo (env, dependencia, decision). |

## Cap iterations + escala

- `building → tests-failing → building` cap **5** intentos. Después → `blocked` con `blocker` field rellenado.
- `auditing → changes-requested → building → ... → auditing` cap **2** iteraciones de auditor. Después → `escalated` (manual Chris review).

## Owner eligibility por surface

| Surface | qwen-opencode | claude-sonnet | claude-opus |
|---|---|---|---|
| BE (no agentic) | ✅ | ✅ | ✅ |
| FE (no agentic) | ✅ | ✅ | ✅ |
| AGENTIC | ⛔ PROHIBIDO | ⛔ PROHIBIDO | ✅ OBLIGATORIO |
| INFRA / migration | ✅ | ✅ | ✅ |

> Razón qwen ban en AGENTIC: skills `sales-agent-expert`/`copilot-expert` + brand-voice + protected surfaces requieren Opus 4.7 con prompt eng. específico.

## Transiciones — quién las escribe

Cada transition append-only en `04-tickets.yaml::tickets[].transitions[]`:

```yaml
transitions:
  - { state: draft, at: "2026-05-04T15:00Z", by: "/architect" }
  - { state: ready, at: "2026-05-04T15:30Z", by: "/architect", note: "deps OK" }
  - { state: assigned, at: "2026-05-04T16:00Z", by: "/dev-team", to: "qwen-opencode" }
  - { state: building, at: "2026-05-04T16:05Z", by: "qwen-opencode" }
  - { state: tests-passing, at: "2026-05-04T17:00Z", by: "qwen-opencode" }
  - { state: pushed, at: "2026-05-04T17:05Z", by: "qwen-opencode", commit: "abc1234" }
  - { state: auditing, at: "2026-05-04T17:30Z", by: "/auditor" }
  - { state: audit-passed, at: "2026-05-04T18:00Z", by: "/auditor" }
  - { state: merged, at: "2026-05-04T18:30Z", by: "/pm" }
```

## Hooks

`/architect`, `/dev-team`, `/auditor`, `/pm` actualizan transitions manualmente al ejecutar acciones (escriben `checkpoint.md` durante el handoff).

Hook automático `post-edit-checkpoint.sh` fue removido 2026-05-06 — su lógica `find -mmin -5` no detectaba la edición real, sólo archivos modificados recientemente por otros procesos. La actualización del `last_modified` queda como responsabilidad explícita del skill que cierra el handoff.
