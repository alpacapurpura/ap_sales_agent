# Agent Routing Matrix

> PM usa esta tabla para decidir qué agente/skill cargar por PR. Default: ningún agente; PM hace solo. Cargar agente solo si PR requiere builder/auditor/UX.

## Por tipo de trabajo

| Trabajo | Pre-design | Implementation | UX | Audit | Notas |
|---|---|---|---|---|---|
| Pure backend infra (outbox, idempotency, rate limiter) | `nicolify-architect` | `nicolify-backend` | — | `nicolify-backend-auditor` | Architect escribe CONTRACT.md (schema + interface + retry). Backend implementa TDD. |
| Backend + DB schema (planes, tablas nuevas) | `nicolify-architect` | `nicolify-backend` | — | `nicolify-backend-auditor` | Migration idempotente obligatoria (regla `backend-migrations.md`). |
| Backend + LangGraph/AI (subagent, RAG, Qdrant) | `nicolify-architect` | `nicolify-agentic` | — | `nicolify-backend-auditor` | LangGraph workflows van a `nicolify-agentic` específicamente. |
| Frontend con UI nueva | — | `nicolify-frontend` | `ux-flow-architect` | — | UX **antes** de implementación. UI-SPEC.md → frontend. |
| Frontend con UX exploratorio (concepto visual nuevo) | — | `nicolify-frontend` | `ux-disruptivo` → `ux-flow-architect` | — | Disruptivo genera concepto, flow-architect lo aterriza con flujo+spec. |
| Cross-stack feature (BE+FE+DB) | `nicolify-architect` | `nicolify-backend` + `nicolify-frontend` | `ux-flow-architect` | both auditors | Architect produce CONTRACT.md ÚNICO consumido por ambos. Paralelo BE/FE solo si CONTRACT ready. |
| Investigación cross-codebase | `Explore` o `general-purpose` | — | — | — | Read-only. PM transcribe brief a `research/{date}-{slug}.md`. |
| Migración research/docs (PR-0 saneamiento) | — | — | — | — | PM solo. No requiere agentes. |
| Bug fix backend | — | `nicolify-backend` | — | `nicolify-backend-auditor` | TDD: regression test ANTES fix. |
| Bug fix frontend | — | `nicolify-frontend` | — | — | E2E si aplica. |
| Documentación / current-state update | — | — | — | — | PM solo. |

## Por tipo de módulo Nicolify

Skills específicos por dominio (cargar JUNTO al builder genérico):

| Módulo | Skill experto | Cuándo cargar |
|---|---|---|
| Brand Studio | `brand-expert` | Modificar fields/schemas/buyer personas/voice tone |
| Offer Studio | `offer-expert` | Fields/secciones/expertise/presets/relaciones |
| Offer Type Presets | `offer-type-preset-expert` | Agregar preset, conditional questions |
| Sales Agent | `sales-agent-expert` | Voz marca, tools scheduler/payment, observabilidad, callback |
| Copilot | `copilot-expert` | Bugs, loops, cards, extracción, tools, costs, providers |
| Growth Studio metrics | `metrics-expert` | Channels, metrics, stages, groups |
| ManyChat | `manychat-expert` | Flows, subscribers, webhooks, tags |
| Auditoría brand+offer | `brand-offer-auditor` | Frameworks marketing coverage |
| ETL/analytics | (ver regla `etl-extraction-contract.md`) | Cualquier cambio providers/pipeline |

## Por tipo de testing/verification

| Verificación | Skill | Cuándo |
|---|---|---|
| Frontend bug en vivo | `chrome-devtools-verify` | Reproducir UI bug, validar SSE/polling |
| Pase a producción | `pase-produccion` | Merge dev→main + monitor Actions |
| Test completo backend | `/test-backend` | Pre-commit |
| Test completo full | `/test-all` | Pre-push o pase prod |
| Git workflow | `git-manager` | Commits, PRs, releases |

## Reglas de selección

1. **Empieza sin agente.** PM solo si trabajo es PM (decisiones, docs, research light).
2. **Architect primero si schema/API nueva.** CONTRACT.md = SSoT antes de builders escriban código en paralelo.
3. **UX antes de FE.** Toda UI nueva pasa por `ux-flow-architect` mínimo. `ux-disruptivo` solo si concepto visual desde cero.
4. **Auditor después de implementación.** Solo si hay riesgo DDD/security/tenant isolation. Skip para refactors triviales.
5. **Skills experto + builder.** Skills módulo-específicos (brand-expert, offer-expert) NO reemplazan builder. Se cargan JUNTOS para que builder tenga contexto.
6. **Paralelo cuando posible.** BE + FE en paralelo si CONTRACT.md ready (regla `parallel-sessions-protocol.md`).
7. **Nunca usar agente para "ver qué hay".** Eso es `Read` o `Explore` directo.
8. **PRs amplios cohesivos** — Opus 4.7[1M] permite scope grande. Sprint sizing 1-3 PRs.

## Protocolo `@pm` comment (OBLIGATORIO)

Cada agente builder/UX/auditor termina su última respuesta con comment HTML específico:

```html
<!-- @pm: [phase] done. Próximo paso: ejecutar prompts/{NN}-{next}-start.md o ejecutar /pm "PR-{n} {phase} done" -->
```

Esto:
1. Indica a Chris siguiente prompt a ejecutar
2. Indica al próximo agente qué prompt usar
3. Permite a `/pm` próxima sesión reconstruir estado leyendo última línea de IMPL-LOG/REVIEW/CONTRACT

Los `prompts/{NN}-*.md` que PM produce ya incluyen esta instrucción explícita al builder al final.

**Sin `@pm` comment al final = handoff broken.**

## Anti-patterns

- ❌ Cargar `nicolify-feature` cuando PR es solo backend (over-orchestration)
- ❌ Saltarse `nicolify-architect` en feature cross-stack (frontend implementa contra contrato vago)
- ❌ Skip `ux-flow-architect` en UI nueva ("yo sé lo que va") — produce drift con design system
- ❌ Cargar 3+ agentes en serie sin razón (perder contexto entre handoffs)
- ❌ `nicolify-feature` (orquestador) Y agentes individuales en mismo PR — escoger uno
- ❌ Agente builder/UX/auditor SIN `<!-- @pm: ... -->` comment al final (handoff broken)
- ❌ Builder modifica `roadmap.md`/`process-learnings.md`/`current-state/{m}.md` directo (eso es PM)

## Anchor

- Antes de declarar agentes en `PR.md` → consultar esta tabla.
- Antes de spawn agente → verificar prompt-pre-coce en `PR-folder/prompts/{NN}-*.md` listo.
- Si caso no encaja → registrar en `process-learnings.md` y proponer extensión.
