# Agent Routing Matrix

> PM usa esta tabla para decidir qué agente/skill cargar por PR. Default: ningún agente; PM hace solo. **Auditor lo auto-spawnea el builder (regla auto-loop 2026-04-29)** — Chris/PM solo invoca columna Implementation; el builder dispara su auditor al terminar y entra fix-loop max 3 iter hasta verdict PASS o escalate PM.

> Última actualización: 2026-04-30 — división negocio vs agentic + 4 agents nuevos (3 Haiku + 1 agentic-auditor Opus). Total 9 agents.

## Modelos por agente (cost / quality split)

| Agente | Modelo obligatorio | Razón |
|---|---|---|
| `nicolify-architect` | **Opus 4.7[1M]** (`model: "opus"`) | CONTRACT = SSoT downstream; errores de schema cascadean |
| `nicolify-backend` | **Sonnet 4.6** (`model: "sonnet"`) | TDD mecánico desde CONTRACT en módulos negocio |
| `nicolify-frontend` | **Sonnet 4.6** (`model: "sonnet"`) | Componentes desde UI-SPEC |
| `nicolify-agentic` | **Opus 4.7[1M]** (`model: "opus"`) | EXCEPCIÓN a regla Sonnet-builder. Razonamiento sobre cache slots, supervisor topology, eval goldens, deepagents isolation = caro si falla. Owner exclusivo copilot/sales_agent |
| `nicolify-backend-auditor` | **Opus 4.7[1M]** (`model: "opus"`) | False negative DDD/tenant/arch fitness = bug prod |
| `nicolify-frontend-auditor` | **Opus 4.7[1M]** (`model: "opus"`) | Idem + 20 arch fitness FE + warning baselines shrink-only |
| `nicolify-agentic-auditor` | **Opus 4.7[1M]** (`model: "opus"`) | Especializado copilot/sales_agent — LangGraph state, prompt cache slot integrity, observability, eval goldens. Auditor sin esta especialización = false-negative caro |
| `nicolify-context-builder` | **Haiku 4.5** (`model: "haiku"`) | Pre-flight reader mecánico. Produce CONTEXT-BRIEF.md que ahorra 30-50k input al Opus caller |
| `nicolify-gate-runner` | **Haiku 4.5** (`model: "haiku"`) | Runner determinístico de quality gates. Produce gate-output.json estructurado. Auditor consume JSON en vez de parsear 50k de stdout |
| `nicolify-grep-bot` | **Haiku 4.5** (`model: "haiku"`) | Lookups one-shot (count, exists, list). Auto-escalate a Sonnet Explore si query requiere reasoning |

**Override Sonnet → Opus** (excepción documentar IMPL-LOG):
- Builder hits 3-iter loop sin PASS
- Drift CONTRACT vs código
- PR explora paradigma nuevo (sales_agent voice nuevo, copilot orchestration novel)

## División por dominio (negocio vs agentic vs frontend)

| Surface | Owner builder | Owner auditor | Skills experto |
|---|---|---|---|
| `modules/copilot/` (graphs, tools, deepagents, prompt cache, observability, channel format, mutation journal) | **`nicolify-agentic`** | **`nicolify-agentic-auditor`** | `copilot-expert` + `tessl__langgraph` |
| `modules/sales_agent/` (specialists, voice, scheduler/payment tools, semantic router, follow-up, eval, closer studio) | **`nicolify-agentic`** | **`nicolify-agentic-auditor`** | `sales-agent-expert` + `tessl__langgraph` |
| `modules/brand/` | `nicolify-backend` | `nicolify-backend-auditor` | `brand-expert` |
| `modules/offer/` | `nicolify-backend` | `nicolify-backend-auditor` | `offer-expert` / `offer-type-preset-expert` |
| `modules/analytics/` (ETL, channels, stages) | `nicolify-backend` | `nicolify-backend-auditor` | `metrics-expert` |
| `modules/{landing,assets,advertising,social_media,scheduling,connections,iam,crm,core,shared}/` | `nicolify-backend` | `nicolify-backend-auditor` | (per-module skill si aplica) |
| `frontend/src/**` | `nicolify-frontend` | `nicolify-frontend-auditor` | `frontend-expert` + brand/offer-expert si surface |

**Regla cardinal:** un PR puede combinar múltiples owners (ej. cross-stack BE+FE+agentic). Cada surface se trata como sub-PR — builder propio, auditor propio, REVIEW propio (`REVIEW.md`, `REVIEW-frontend.md`, `REVIEW-agentic.md`).

## Pre-flight optimization (ahorro tokens 55-65%)

Antes de architect/builder/auditor (Opus), invocar **`nicolify-context-builder`** Haiku para producir `CONTEXT-BRIEF.md` en el PR-folder. Downstream agent lee ese brief en vez de re-cargar 30-50k de docs.

```
Agent({
  description: "Pre-flight context PR-{n}",
  subagent_type: "nicolify-context-builder",
  model: "haiku",
  prompt: "<pr_folder>: {abs path}; <modules>: {list}; <phase>: {architect|builder|auditor}"
})
```

Después: architect/builder/auditor leen `CONTEXT-BRIEF.md` (3-5k) primero. Solo re-leen raw paths si la sección "Faithfulness gaps" del brief flag algo.

## Gate execution via gate-runner (no más raw stdout parsing)

Auditores **NO corren `/test-backend` directamente**. Spawnean `nicolify-gate-runner`:

```
Agent({
  description: "Run /test-backend gates",
  subagent_type: "nicolify-gate-runner",
  model: "haiku",
  prompt: "<pr_folder>: {abs path}; <command>: test-backend; <iter>: {N}"
})
```

Output: `<pr_folder>/gate-output.json` con schema estable v1.0. Auditor consume el JSON. Raw log preservado en `<pr_folder>/gate-logs/iter-{N}-*.log` por si Opus necesita re-leer (raro, sólo cuando verdict ≠ PASS).

## Por tipo de trabajo

| Trabajo | Pre-flight (Haiku) | Pre-design (Opus) | Implementation (auto-spawnea auditor) | UX | Notas |
|---|---|---|---|---|---|
| Backend negocio puro (brand/offer/analytics/scheduling/connections/etc.) | `nicolify-context-builder` | `nicolify-architect` | `nicolify-backend` (Sonnet) → auto `nicolify-backend-auditor` (Opus) | — | Architect produce CONTRACT.md; backend implementa; backend-auditor scoree 11 categorías (sin agentic hygiene) |
| Backend + DB schema | `nicolify-context-builder` | `nicolify-architect` | `nicolify-backend` → auto `nicolify-backend-auditor` | — | Migration idempotente obligatoria. Schema-clone re-upgrade no-op |
| **Agentic — copilot / sales_agent** | `nicolify-context-builder` | `nicolify-architect` | **`nicolify-agentic`** (Opus) → auto **`nicolify-agentic-auditor`** (Opus) | — | LangGraph 2.0 + deepagents + prompt cache slots. Skills mandatorios: copilot-expert / sales-agent-expert + tessl__langgraph |
| Frontend con UI nueva | `nicolify-context-builder` | — | `nicolify-frontend` (Sonnet) → auto `nicolify-frontend-auditor` (Opus) | `ux-flow-architect` (Sonnet) skill | UX **antes** implementación. UI-SPEC.md → frontend |
| Frontend con UX exploratorio | `nicolify-context-builder` | — | `nicolify-frontend` → auto `nicolify-frontend-auditor` | `ux-disruptivo` (Opus) → `ux-flow-architect` (Sonnet) | Disruptivo genera concepto, flow-architect aterriza spec |
| Cross-stack (BE negocio + FE) | `nicolify-context-builder` | `nicolify-architect` | `nicolify-backend` + `nicolify-frontend` (paralelo) → auto BE-auditor + FE-auditor | `ux-flow-architect` skill | CONTRACT único compartido. REVIEW-backend.md + REVIEW-frontend.md separados. Ambos PASS antes cerrar |
| **Cross-stack agentic + FE** (chat UI nuevo, copilot widget, sales_agent settings) | `nicolify-context-builder` | `nicolify-architect` | `nicolify-agentic` + `nicolify-frontend` (paralelo) → auto agentic-auditor + FE-auditor | `ux-flow-architect` | CONTRACT único. Streaming surface (SSE/WebSocket) coordinado entre builders |
| **Cross-scope total (BE negocio + agentic + FE)** | `nicolify-context-builder` | `nicolify-architect` | `nicolify-backend` + `nicolify-agentic` + `nicolify-frontend` (3 paralelos) → 3 auditores | `ux-flow-architect` | Raro pero existe. Coordinación via filesystem (CONTRACT.md + IMPL-LOG.md por surface). 3 REVIEWs separados |
| Investigación cross-codebase (light) | — | — | `nicolify-grep-bot` (Haiku) | — | One-shot lookup. Si requiere reasoning → escalate Sonnet Explore |
| Investigación cross-codebase (deep) | — | `Explore` (Sonnet) o `general-purpose` | — | — | Read-only. PM transcribe brief a `research/{date}-{slug}.md` |
| Migración research/docs | — | — | — | — | PM solo |
| Bug fix backend negocio | — | — | `nicolify-backend` → auto `nicolify-backend-auditor` | — | TDD: regression test ANTES fix. Para bug pequeño: skip context-builder |
| Bug fix agentic (copilot loop infinito, sales_agent voz drift) | `nicolify-context-builder` (recomendado) | — | `nicolify-agentic` → auto `nicolify-agentic-auditor` | — | TDD: golden regression. Skill obligatorio copilot-expert / sales-agent-expert |
| Bug fix frontend | — | — | `nicolify-frontend` → auto `nicolify-frontend-auditor` | — | E2E si aplica |
| Documentación / current-state update | — | — | — | — | PM solo |

## Auto-audit loop fail-safe

- Builder fix solo: typos, tests faltantes, hardcoded values, refactor menor, gates nuevos del PR.
- Builder escala PM (NO fix solo): drift CONTRACT vs código, cambio arquitectónico, findings cross-PR (regla M7), allowlist arch-fitness shrink negociable, baselines pre-existentes.
- Max 3 iter — si verdict ≠ PASS al iter 3 → escalate PM con findings pendientes.
- Cada iter: builder corre quality gates locales → spawn `nicolify-gate-runner` → spawn auditor → fix scope → commit + push → re-run.
- Detalle: `prompts/02-builder-start.md` template + SKILL `pm` "Auto-orchestration build → audit → fix loop".

## Por tipo de módulo Nicolify (skills domain-specific)

Skills específicos por dominio (cargar JUNTO al builder genérico):

| Módulo | Skill experto | Builder owner | Cuándo cargar |
|---|---|---|---|
| Brand Studio | `brand-expert` | `nicolify-backend` | Modificar fields/schemas/buyer personas/voice tone (data layer) |
| Offer Studio | `offer-expert` | `nicolify-backend` | Fields/secciones/expertise/presets/relaciones |
| Offer Type Presets | `offer-type-preset-expert` | `nicolify-backend` | Agregar preset, conditional questions |
| **Sales Agent** | `sales-agent-expert` | **`nicolify-agentic`** | Voz marca, tools scheduler/payment, observabilidad, callback, eval goldens |
| **Copilot** | `copilot-expert` | **`nicolify-agentic`** | Bugs, loops, cards, extracción, tools, costs, providers, deepagents subagents |
| Growth Studio metrics | `metrics-expert` | `nicolify-backend` | Channels, metrics, stages, groups |
| ManyChat | `manychat-expert` | `nicolify-backend` | Flows, subscribers, webhooks, tags |
| Auditoría brand+offer | `brand-offer-auditor` | (PM directly) | Frameworks marketing coverage |
| ETL/analytics | (ver regla `etl-extraction-contract.md`) | `nicolify-backend` | Cualquier cambio providers/pipeline |

## Por tipo de testing/verification

| Verificación | Skill / Agent | Cuándo |
|---|---|---|
| Frontend bug en vivo | `chrome-devtools-verify` | Reproducir UI bug, validar SSE/polling |
| Pase a producción | `pase-produccion` | Merge dev→main + monitor Actions |
| Quality gates backend | `nicolify-gate-runner` (auto-spawn por auditor) | Phase 2 audit, después de cada fix-loop iter |
| Quality gates frontend | `nicolify-gate-runner` con `<command>: test-frontend` | Idem FE |
| Test completo full local | `/test-all` | Pre-push o pase prod |
| Git workflow | `git-manager` skill | Commits, PRs, releases |

## Reglas de selección

1. **Empieza sin agente.** PM solo si trabajo es PM (decisiones, docs, research light).
2. **Architect primero si schema/API nueva.** CONTRACT.md = SSoT antes de builders escriban código en paralelo. SIEMPRE precedido por `nicolify-context-builder` Haiku.
3. **Routing negocio vs agentic.** Si el PR toca `modules/copilot/` o `modules/sales_agent/` → `nicolify-agentic` (Opus). Otros módulos backend → `nicolify-backend` (Sonnet). PR cross-scope → ambos en paralelo (regla M1).
4. **UX antes de FE.** Toda UI nueva pasa por `ux-flow-architect` skill mínimo. `ux-disruptivo` skill solo si concepto visual desde cero.
5. **Auditor siempre que el builder corrió.** Builder lo auto-spawnea (no es decisión del PM). Backend-auditor para módulos negocio, agentic-auditor para copilot/sales_agent, FE-auditor para frontend.
6. **Skills experto + builder.** Skills módulo-específicos (brand-expert, offer-expert, copilot-expert, sales-agent-expert) NO reemplazan builder. Se cargan JUNTOS para que builder tenga contexto.
7. **Paralelo cuando posible.** BE + FE + agentic en paralelo si CONTRACT.md ready (regla `parallel-sessions-protocol.md`).
8. **Pre-flight Haiku para PRs M+.** Para PR S (small) skip `nicolify-context-builder` — overhead spawn > ahorro. Para M+ siempre invocar primero.
9. **Gate runner Haiku obligatorio.** Auditor consume `gate-output.json`, no parsea stdout. Si JSON ausente → spawn gate-runner antes de scoring.
10. **Grep-bot Haiku para queries triviales.** Reemplaza Explore Sonnet para count/exists/list. Si la query incluye "missing", "should", "violates" → escalate Explore Sonnet.
11. **Nunca usar agente para "ver qué hay".** Eso es `Read` o `Explore` directo (o `nicolify-grep-bot` para queries muy puntuales).
12. **PRs amplios cohesivos** — Opus 4.7[1M] permite scope grande. Sprint sizing 1-3 PRs.

## Spawn pattern (Agent tool — model param obligatorio)

```
Agent({
  description: "<3-5 word>",
  subagent_type: "nicolify-{architect|backend|frontend|agentic|*-auditor|context-builder|gate-runner|grep-bot}",
  model: "opus" | "sonnet" | "haiku",   ← según tabla "Modelos por agente", NO opcional
  prompt: "<contenido>"
})
```

**Anti-pattern crítico:** omitir `model` param. Hereda del parent — impredecible. SIEMPRE explicit.

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
- ❌ Skip `ux-flow-architect` skill en UI nueva ("yo sé lo que va") — produce drift con design system
- ❌ Cargar 3+ agentes en serie sin razón (perder contexto entre handoffs)
- ❌ `nicolify-feature` (orquestador) Y agentes individuales en mismo PR — escoger uno
- ❌ Agente builder/UX/auditor SIN `<!-- @pm: ... -->` comment al final (handoff broken)
- ❌ Builder modifica `roadmap.md`/`process-learnings.md`/`current-state/{m}.md` directo (eso es PM)
- ❌ **Usar `nicolify-backend` para tocar `modules/copilot/` o `modules/sales_agent/`** (router incorrecto — agentic builder es el dueño)
- ❌ **Usar `nicolify-backend-auditor` para auditar copilot/sales_agent** (cat 11 agentic hygiene movido a `nicolify-agentic-auditor`)
- ❌ Usar agentic builder para módulos negocio (sobre-coste, Sonnet basta)
- ❌ Spawn agent sin `model` param explícito (impredecible)
- ❌ Auditor parsea raw `/test-backend` stdout (debe consumir `gate-output.json` del runner)
- ❌ Skip `nicolify-context-builder` Haiku en PR M+ (desperdicia 30-50k input al Opus)
- ❌ Spawn `nicolify-context-builder` para PR S (overhead > ahorro — read directo basta)

## Anchor

- Antes de declarar agentes en `PR.md` → consultar esta tabla.
- Antes de spawn agente → verificar `prompt-pre-coce` en `PR-folder/prompts/{NN}-*.md` listo.
- Si caso no encaja → registrar en `process-learnings.md` y proponer extensión.
- Si PR cross-scope (negocio + agentic + FE) → cada surface = sub-PR con su builder + auditor + REVIEW. Coordinar via filesystem.
