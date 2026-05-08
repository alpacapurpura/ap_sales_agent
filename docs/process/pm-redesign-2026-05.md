# PM Redesign 2026-05 — Working Doc

> **Status:** DRAFT — refining iterativamente con Chris.
> **Owner:** `/pm`.
> **Ratifica:** Chris.
> **Origen:** sesión 2026-05-05. Disparado por friction percibido en pipeline `/pm` actual + bloat skills + falta backlog visible + complejidad PI/Sprint para founder solo.
> **Anti-context-rot:** captura decisiones cardinales por punto. Cada punto cerrado se ratifica acá antes de avanzar al siguiente.

---

## Decisiones cardinales (consolidado punto-por-punto)

### Punto 1 — Ready package + autonomous build (CERRADO 2026-05-05)

**7 estados macro vocabulary unificado cross-nivel (idea/epic/story/capability):**

| Estado | Significado | Trigger entry | Owner |
|---|---|---|---|
| `idea` | Spark crudo, no validado | Chris tira | Chris + `/pm` |
| `validated` | Problem worth solving (OST aplicado) | `/pm` confirma | `/pm` + Chris |
| `ready` | Paquete autocontenido completo para autonomous build | `/architect` cierra | `/architect` Sonnet |
| `building` | Autonomous loop opencode + Sonnet iterando | opencode pickup | opencode |
| `done` | Merged a development + scenarios migrados a capability | `/auditor` APPROVED | `/auditor` |
| `parked` | De-prioritized, NO abandonado | manual | Chris |
| `dropped` | Won't do (terminal) | manual | Chris |

**`ready` = paquete autocontenido = 5 archivos:**

```
docs/product/stories/{story-id}/
├── 01-spec.md              # /po-ux fusión: Gherkin + wireframes inline (UI std)
├── 03-arch.md              # /architect: technical design
├── 04-validators.yaml      # ★ CRITICAL ★ tests ejecutables, must_pass:true cada uno
├── 05-guidelines.md        # decisiones técnicas + patterns + anti-patterns concretos
├── 06-tickets.yaml         # T-1, T-2, ... work units atómicos
└── checkpoint.md           # state + phase + next_action vivo
```

**`04-validators.yaml` shape (corazón del autonomous build):**

```yaml
validators:
  - id: <slug>
    type: pytest|playwright|shell
    cmd: "<exact shell command>"
    must_pass: true
    timeout_sec: <n>

scenario_coverage:
  - scenario_id: <gherkin-id from 01-spec>
    validators: [<id>, <id>]

iteration:
  max_iterations: 10
  on_fail: "fix targeted file based on test output, re-run failing validator only"
  on_all_pass: "set state=building→review, append iteration_log"
  on_cap_reached: "set state=building→blocked, escalate to Chris"
```

Sonnet itera contra estos validators sin supervisión humana. Determinista (no LLM judges en happy path).

**`05-guidelines.md` debe tener:**
- Patterns required (concretos: "SQLAlchemy 2.0 select(), no session.query()")
- Patterns forbidden (concretos: "no datetime.utcnow(), usar utc_now()")
- Files in scope (Sonnet only edits estos)
- Files Sonnet NUNCA toca (escala a Chris)
- Reference docs (skill names + rules paths a cargar antes coding)

**3 conversaciones separadas (aprovecha context isolation):**

```
Conv 1 — DISCOVERY + READY  (Chris + /pm + /po-ux + /architect)
  output: ready package complete, state=ready
  
Conv 2 — AUTONOMOUS BUILD   (opencode + Sonnet, sin supervisión humana)
  loop: implement → run validators → fix → repeat hasta GREEN
  output: state=ready→building→review (GREEN) o blocked (cap reached)
  
Conv 3 — REVIEW + MERGE     (/architect-review + /auditor + /pm merge)
  output: state=review→done, scenarios migran a capability, story archived
```

**Skills fusión:**
- `/po-ux` (NUEVO, fusión `/po` + `/ux-ui`) para UI standard (CRUD/list/detail/form/dashboard)
- `/ux-agentico` se mantiene separado (state machine + slot architecture es bestia distinta)
- `/po` standalone se mantiene para service-stories (no UI)

---

### Punto 2 — Backlog + visualizador + folder structure (CERRADO 2026-05-05)

**ROADMAP.md ELIMINADO como archivo separado.** Se vuelve sección de `BACKLOG.md` auto-gen.

Razón: roadmap (Now/Next/Later/Done/Cancelled) es 100% derivable filtrando estados del backlog. Audiencia única (Chris + Claude) — no justifica ceremonia 2 archivos.

`why_now` y `why_next` viven en frontmatter de `outcomes/{id}.md` (es propiedad del outcome, no del roadmap).

**`ideas-pool.yaml` único** (no folder split idea/opportunity).

```yaml
# docs/product/ideas-pool.yaml
ideas:
  - id: <slug>
    one_liner: "1-3 lines"
    state: idea|validated|dropped
    tags: [module:..., effort:S|M|L, value:..., source:...]
    created: <date>
    last_touched: <date>
    promoted_at: <date>          # cuando state=validated
    promoted_to_outcome: <id>    # cuando promoted a epic
    ost:                         # solo cuando state=validated (Torres OST)
      outcome: "..."
      opportunities: [...]
      solutions: [...]
      tests: [...]
```

**Visualizador stack — Mermaid kanban en BACKLOG.md (Phase 1):**
- Generador Python emite `BACKLOG.yaml` (machine) + `BACKLOG.md` con bloques Mermaid (human)
- Renderiza nativo en GitHub web, VSCode preview, Obsidian, Cursor, etc.
- 0 infra, 0 deps nuevas, 0 token cost mantenimiento (solo Python script, viewer es nativo)
- Phase 2 opcional: Eleventy + 2D Story Map HTML solo si Mermaid 1D no alcanza (defer)

**3 layers freshness:**
1. Pre-commit hook (extiende Section 6 R32-pattern): si commit toca sources backlog → regen + auto-stage
2. Stop hook validator: invariants check + auto-regen si stale
3. `/pm` bootstrap: verifica mtime + regen si needed

**`modules/{m}.md` refactorizado, NO eliminado:**

Razón: module tiene metadata único (studio_parent, copilot_operable, agentic_eval_suite_path, status) + narrativa "qué hace POR EL USER" alto-nivel que NO existe en capabilities/.

Sí elimina: campos derivables (capabilities_count, stories_count) y lista capabilities con descripción duplicada (auto-gen al render).

```markdown
---
module: <id>
status: active|maintenance|placeholder
studio_parent: <ui-grouping>
copilot_operable: bool
agentic_eval_suite_path: <path|null>
last_audit: <date>
---

# <module> — Estado funcional

## Qué hace por el user
<narrativa alto-nivel — UNIQUE>

## Capacidades
> Auto-list generated from capabilities/<m>/

(generador inserta lista al render — NO manual)
```

**Folder structure final (CERRADO):**

```
docs/
├── product/                                # SSoT vivo producto
│   ├── INDEX.md                            # entrypoint
│   ├── BACKLOG.yaml                        # 🤖 auto-gen SSoT machine-readable
│   ├── BACKLOG.md                          # 🤖 auto-gen — Roadmap section + Mermaid kanban + Caps snapshot
│   ├── ideas-pool.yaml                     # 📝 manual: ideas + validated (OST inline)
│   ├── outcomes/                           # 📝 1 file per epic — narrativa + story_ids
│   │   └── {outcome-id}.md
│   ├── stories/                            # 📝 1 folder per active story (FLAT)
│   │   └── {story-id}/
│   │       ├── checkpoint.md
│   │       ├── 01-spec.md
│   │       ├── 03-arch.md
│   │       ├── 04-validators.yaml
│   │       ├── 05-guidelines.md
│   │       ├── 06-tickets.yaml
│   │       ├── T-{n}-impl-log.md
│   │       ├── T-{n}-result.md
│   │       ├── T-{n}-review.md
│   │       └── 07-merge.md
│   ├── capabilities/                       # 📝 durable behavior — scenarios embedded post-merge
│   │   └── {module}/
│   │       └── {cap}.yaml
│   └── modules/                            # 📝 1 file per módulo — solo unique parts
│       └── {module}.md
├── archive/                                # 🗄 stories done snapshot inmutable
│   └── {year}/
│       └── stories/
│           └── {story-id}/
├── process/                                # 📋 rules + protocols + learnings
├── domains/                                # 🔧 technical reference (existing)
├── specs/                                  # 📄 templates + personas + rubrics
└── pm-nico/                                # 🗄 legacy (cierran ahí, NO migran)
```

**Profundidad max:**
- Active: 4 niveles (`docs/product/stories/{id}/01-spec.md`)
- Archive: 5 niveles (acceptable)

**Decisiones cardinales estructura:**
- Stories carpeta flat (no agrupada per outcome) — outcome relationship via frontmatter, BACKLOG.yaml deriva grouping
- Tickets archivos flat dentro de story (T-N-*.md) — si llegás >10 tickets, story es demasiado grande, split
- Capabilities sub-folder per módulo (único acceptable, 50+ caps mixed sería caótico)
- Archive con year sub-folder (audit trail histórico)
- Done state stories archivan automático en merge step (active dir queda limpio)

---

### Punto 3 — Matar PI/Sprint, replace con Outcome + flow continuo (CERRADO 2026-05-05)

- ❌ Eliminar PI como container temporal — replace con Outcome semántico
- ❌ Eliminar Sprint como ceremonia — replace con WIP limits structural
- ✅ Outcome (epic) = agrupación semántica de stories por objetivo común
- ✅ Story = work unit + Ticket = sub-unit
- ✅ Stop hook valida WIP caps: `validated ≤ 10`, `ready ≤ 5`, `building ≤ 3`, `review ≤ 2`
- ✅ Outcome cierra event-driven, no time-driven
- ✅ Retro = outcome retro + weekly learnings sweep
- ✅ Slug semántico per outcome (`sales-eval-foundation`, no `PI-N`)
- ✅ PI-12 + legacy cierran paradigma viejo, NO migran
- ✅ Próximo outcome nace paradigma nuevo

---

### Punto 4 — Pipeline 10 estados + agentic eval methodology (CERRADO 2026-05-06)

> **Origen:** sesión 2026-05-06 con Chris. Friction percibido: 7 estados macro mezclaban "raw idea con research" + "spec ratificada" en mismo bucket `validated`. Mezclaban "build en curso" + "build cerrado pre-audit" en mismo bucket `building`. Necesidad: pipeline más granular que distinga claramente fases de discovery (idea/research) vs refinement (decompose+specs+UX) vs architect-package vs build vs review. Adicional: formalizar metodología validable conversacional state-of-art 2026.

#### State machine — 10 estados (REEMPLAZA 7 estados de Punto 1)

```
                                       ┌── parked (manual, opt-out reversible)
                                       │
idea ─→ refining ─→ refined ─→ ready ─→ developing ─→ developed ─→ reviewing ─→ done
  │       │           │         │           │             │            │           │
  └─→ dropped (terminal won't do)                                                   └─→ archive
```

| # | Estado | Disparador entry | Owner | Output canónico | WIP cap |
|---|---|---|---|---|---|
| 1 | `idea` | Chris tira | Chris + `/pm` | ideas-pool entry + (opcional) `00-research.md` | ∞ |
| 2 | `refining` | Chris dice "refinemos {idea}" | `/pm` orquesta + `/po-ux` o `/po` + `/ux-agentico` | `00-story.md` + `01-spec.md` (drafts) + `02-design-*.md` (drafts) + decomposition stories | ≤ 3 |
| 3 | `refined` | Chris ratifica spec + diseño UX/conversacional | `/pm` cierra | mismos archivos pero `ratified_by_chris: true` | ≤ 5 |
| 4 | `ready` | `/architect` orchestrator cierra package | `/architect` (Opus) | `03-arch.md` + `04-validators.yaml` + `05-guidelines.md` + `06-tickets.yaml` | ≤ 5 |
| 5 | `developing` | `/dev-team` picks ticket | opencode/Sonnet (Opus si agentic prod) | `T-N-impl-log.md` + iteration logs | ≤ 3 |
| 6 | `developed` | Todos validators GREEN | `/dev-team` cierra | `T-N-result.md` por ticket | ≤ 10 |
| 7 | `reviewing` | Chris triggers `/auditor` | `/auditor` (Opus + Sonnet split) | `T-N-review.md` + `CHECKPOINTS.md` (C1-C5) | ≤ 2 |
| 8 | `done` | Auditor APPROVED + `/pm` merge | `/pm` | `07-merge.md` + capabilities promoted + archive | rolling 90d |
| 9 | `parked` | Manual Chris | Chris | reason field | ∞ |
| 10 | `dropped` | Manual Chris | Chris | reason field | ∞ (terminal) |

#### Mapeo old (7) → new (10)

| Old state | New state(s) | Razón split |
|---|---|---|
| `idea` | `idea` | sin cambio. Aclara que research opcional vive aquí (`00-research.md`) |
| `validated` | `refining` (en proceso) + `refined` (specs ratificadas, awaiting architect) | separa "Chris ratificando spec activamente" de "spec lista para architect" |
| `ready` | `ready` | sin cambio (architect package autocontenido) |
| `building` | `developing` (build en curso) + `developed` (validators GREEN, awaiting QA) | separa "build activo" de "build cerrado, esperando review" |
| `review` | `reviewing` | rename solo (más natural en español/inglés mixto) |
| `done` | `done` | sin cambio |
| `parked` / `dropped` | `parked` / `dropped` | sin cambio |

**Caps cambian:** sumando 3 estados nuevos, total WIP discovery+refinement+development capabilities sigue limitado pero distribuido más finamente. `idea` sin cap (capturar libre); `refining` ≤ 3 (focus deep work); `refined` ≤ 5 (queue para architects); `ready` ≤ 5 (queue para devs); `developing` ≤ 3 (concurrent builds); `developed` ≤ 10 (queue para auditor — outcome multi-story batched); `reviewing` ≤ 2 (concurrent audits).

#### Gates de transición

| Transition | Gate (qué Chris/sistema verifica) |
|---|---|
| `idea → refining` | Chris explícito ("refinemos {x}"). NO automático. Pueden coexistir 50 ideas sin nunca refinarse |
| `refining → refined` | Chris ratifica: (a) spec scenarios completos (happy/negative/edge/adversarial), (b) UX/diseño conversacional ratificado, (c) decomposition stories si épica |
| `refined → ready` | `/architect` Opus produce paquete autocontenido (4 archivos canónicos: arch + validators + guidelines + tickets) |
| `ready → developing` | `/dev-team` picks. Autonomous build SIN supervisión humana (paquete autocontenido cualquier AI debería poder) |
| `developing → developed` | TODOS validators GREEN. NO escalations open. NO uncommitted WIP |
| `developed → reviewing` | Chris triggers manual (controla cuándo gastar Opus auditor). NO automático |
| `reviewing → done` | Auditor APPROVED + `/pm` aplica merge + capabilities promovidas + docs actualizados |

#### Cost-routing por phase (model split óptimo)

| Phase | Modelo | Razón |
|---|---|---|
| `idea`/`refining` (research, decomposition, decisión coherencia) | **Opus 4.7** | Pensamiento estratégico, alto valor, baja frecuencia |
| `/po-ux` + `/po` + `/ux-agentico` (specs + designs) | **Opus 4.7** | Calidad spec define todo downstream |
| `/architect` orchestrator + sub-architects | **Opus 4.7** | Decisiones arquitectónicas, ROI altísimo |
| `/dev-team` BE/FE no-agentic | **Sonnet/opencode** | Ejecución contra validators, barato |
| `/dev-team` agentic production code (R23 hard rule) | **Opus 4.7** | Calidad agentic = experiencia usuario directa |
| `/auditor` categorías críticas (C1 código + C2 spec + C3 arch) | **Opus 4.7** | Juicio cualitativo |
| `/auditor` tests/lint/format runs | **Sonnet** | Determinístico, barato |
| `gate-runner` ejecutor `make ci-parity` etc. | **Haiku** | Solo ejecuta + parsea JSON |
| `context-builder` lecturas previas | **Haiku** | Solo agrega contexto |

#### Metodología validable conversacional (state-of-art 2026)

> **Trigger:** stories con `category: agentic` o `frontend_conversational`. Bind durante `refining` → formalize durante `ready` (architect produce machinery en `04-validators.yaml`).

**Stack canónico:**

| Capa | Qué | Cuándo aplicarlo |
|---|---|---|
| **Spec-driven development** | Markdown estructurado con scenarios Gherkin AI-resistant + invariantes | `refining` |
| **Personas + golden datasets** | Mix hand-crafted (Chris ratifica) + sampled production traces (anonimizado via `sanitize_payload`) | `refining` |
| **LLM-as-judge rubrics** | Voice fidelity · goal completion · tone · helpfulness · scope | `refining` (selección) → `ready` (binding) |
| **Trajectory evaluators** (`agentevals` LangChain) | Tool call sequence + LangGraph state transitions + subagent isolation | `ready` |
| **Code-based assertions** | Programmatic checks (state DB, cost USD < X, tokens < Y) | `ready` |
| **Multi-turn evals** (LangSmith Threads) | Conversación entera como unidad coherente, no turn-by-turn aislado | `ready` |
| **Pass^k metric** | trials_per_scenario · per_trial_threshold · pass_k_threshold | `refining` (definir umbrales) |
| **Adversarial set** | Prompt injection · out-of-scope · loop bait · PII probes · jailbreak | `refining` |
| **Observability invariants** | `copilot_trace_event` records · cost budget · latency p95 | `ready` |
| **Self-Refine / Reflexion loops** | LLM evaluator feedback iterativo durante build | `developing` |
| **HITL annotation queues** | Sample dudosos → Chris labelea → re-bootstrap rubric | `developed`/`done` |

**Sources:**
- LangSmith Evaluation Framework (`langchain.com/langsmith/evaluation`)
- agentevals — LangGraph trajectory evaluators (`github.com/langchain-ai/agentevals`)
- Insights Agent + Multi-turn Evals (`blog.langchain.com/insights-agent-multiturn-evals-langsmith/`)
- Evaluation and Benchmarking of LLM Agents — Survey (`arxiv.org/html/2507.21504v1`)
- Agentic Workflows 2026 — Vellum (`vellum.ai/blog/agentic-workflows-emerging-architectures-and-design-patterns`)
- State of Agent Engineering — LangChain (`langchain.com/state-of-agent-engineering`)
- Practical Guide for Designing Production-Grade Agentic AI Workflows (`arxiv.org/html/2512.08769v1`)

#### Artefactos por estado (template carpeta canónico)

```
docs/product/stories/{story-id}/
├── checkpoint.md                       # state machine vivo (todo estado)
├── 00-research.md                      # estado=idea (OPCIONAL — research deep, competitive analysis, mockups HTML)
├── 00-story.md                         # estado=refining (brief decomposed)
├── 01-spec.md                          # estado=refining→refined (Gherkin + scenarios + grader refs)
├── 02-design-ui.md                     # estado=refining→refined (si UI std/disruptiva)
├── 02-design-agentic.md                # estado=refining→refined (si conversacional)
├── 03-arch.md                          # estado=refined→ready (sub-arq BE/FE/agentic consolidado)
├── 04-validators.yaml                  # estado=refined→ready (★ tests ejecutables — non_functional/functional/visual/agentic_eval)
├── 05-guidelines.md                    # estado=refined→ready (patterns + skills + rutas)
├── 06-tickets.yaml                     # estado=refined→ready (T-1, T-2, ...)
├── T-{n}-impl-log.md                   # estado=developing
├── T-{n}-result.md                     # estado=developed
├── T-{n}-review.md                     # estado=reviewing
├── CHECKPOINTS.md                      # estado=reviewing (C1-C5 grid)
└── 07-merge.md                         # estado=done (capability promotion record)
```

#### `04-validators.yaml` — categorías extendidas

```yaml
validators:
  # NON-FUNCTIONAL (lint, arch fitness, type-check, format)
  - id: arch-fitness-be
    category: non_functional
    command: "cd backend && .venv/bin/pytest tests/architecture/ -x -q"
    must_pass: true

  - id: lint-ruff
    category: non_functional
    command: "cd backend && .venv/bin/ruff check src/ tests/"
    must_pass: true

  # FUNCTIONAL (Gherkin scenarios — happy/negative/edge/adversarial)
  - id: scenario-happy-path
    category: functional
    command: "cd backend && .venv/bin/pytest tests/modules/X/test_story.py::test_happy -v"
    must_pass: true

  # AGENTIC EVAL (pass^k, rubrics, trajectory, cost/latency budgets)
  - id: agentic-pass-k
    category: agentic_eval
    runner: "python scripts/run_agent_evals.py --story={id} --personas=A,B,C"
    rubrics: [voice-fidelity, goal-completion, tool-call-accuracy]
    pass_k:
      trials: 3
      per_trial_threshold: 0.66
      pass_k_threshold: 0.5
    must_pass: true

  - id: trajectory-tool-sequence
    category: agentic_eval
    runner: "python scripts/run_trajectory_eval.py --expected=docs/specs/trajectories/{story}.yaml"
    must_pass: true

  - id: cost-budget
    category: agentic_eval
    threshold: { cost_usd_max: 0.50, tokens_max: 6000, latency_p95_max: 8.0 }
    must_pass: true

  # VISUAL (responsive + visual fidelity Playwright + screenshots)
  - id: visual-fidelity
    category: visual
    runner: "cd frontend && npx playwright test e2e/visual/{story}.spec.ts"
    capture: screenshots
    must_pass: true

  - id: responsive-coverage
    category: visual
    breakpoints: [mobile, tablet, desktop]
    must_pass: true
```

#### Decisiones cardinales adicionales (ratificadas Chris 2026-05-06)

1. ✅ **10 estados ratificados** (idea/refining/refined/ready/developing/developed/reviewing/done/parked/dropped)
2. ✅ **Legacy exempt cap going forward** — stories pre-paradigma (PI-12 sales-agent-eval) NO violan caps al migrar; cap aplica solo a stories nuevas creadas post 2026-05-06
3. ✅ **`00-research.md` opcional** — encouraged para ideas grandes (>5d trabajo), pequeñas pueden saltar directo a refining
4. ✅ **Validators visual ahora** — agregar `category: visual` desde día 1 a templates; `must_pass: true` cuando spec lo defina (Playwright screenshots baseline opcional iter 1)
5. ✅ **Output `/pm` amigable** — cuando user pide estado backlog, agrupar por 10 estados con emojis + 1 línea resumen por bucket. NO dump técnico crudo

#### Plan de implementación Punto 4 (F1-F7)

| Fase | Scope | Status |
|---|---|---|
| **F1** | Doc canónico (este Punto 4) + CLAUDE.md + AGENTS.md + PM friendly output | 🟡 EN CURSO |
| **F2** | Update skills `/pm` `/po` `/po-ux` `/ux-agentico` `/architect` `/dev-team` `/auditor` con nuevos estados | 🔴 PENDIENTE |
| **F3** | Update `generate_backlog.py` + `pre-commit` Section 7 + tests | 🔴 PENDIENTE |
| **F4** | Crear template `00-research-template.md` + extender `04-validators-template.yaml` con categorías | 🔴 PENDIENTE |
| **F5** | Migración PI-12 (Olas 1-5 — stories sin spec → `refining`) | 🔴 PENDIENTE |
| **F6** | Update Stop hook validator `validate_session_close.py` WIP caps a 10 estados | 🔴 PENDIENTE |
| **F7** | Regen backlog + tests + commit final | 🔴 PENDIENTE |

#### Bitácora Punto 4

- 2026-05-06 — Chris ratifica propuesta 10 estados + metodología agéntica state-of-art + cost-routing per phase + 5 decisiones (legacy exempt + research opcional + validators visual ahora + friendly output `/pm` + F1 first then F2-F7). F1 inicia inmediato.

---

## Wave plan implementación (4 waves)

| Wave | Scope | Status | Risk |
|---|---|---|---|
| 1 | Foundation: folder skeleton + ideas-pool + generate_backlog.py + tests + pre-commit Section 6 | ✅ DONE 2026-05-05 | Bajo |
| 2 | Migration: refactor `modules/{m}.md` (strip duplicate caps info) + migrate `pm-nico` active PIs to `outcomes/` + legacy `stories/{m}/{id}.yaml` to states correctos según artefactos | 🟡 PENDIENTE | Medio (bulk file moves) |
| 3 | Skills update: `/po-ux` fusión, retire deprecated, update CLAUDE.md/AGENTS.md/key skills, consolidación domain experts | 🟡 PENDIENTE | Alto (touches 30+ skills) |
| 4 | Automation extras: Stop hook validator (WIP caps + checkpoint freshness), Story Map 2D HTML opcional Phase 2, validators-first ratification | 🟡 PENDIENTE | Bajo (additive) |

### Wave 1 deliverables (committed)

- `docs/product/outcomes/.gitkeep`
- `docs/product/stories/.gitkeep` (coexists con legacy `stories/{module}/` subdirs)
- `docs/archive/2026/stories/.gitkeep`
- `docs/product/ideas-pool.yaml` (2 ideas migradas: calendario-comercial, metricas-atraccion)
- `docs/product/BACKLOG.yaml` (auto-gen SSoT)
- `docs/product/BACKLOG.md` (auto-gen — Roadmap section + Mermaid kanban + caps snapshot)
- `scripts/generate_backlog.py` (Wave 1 generator, ~340 LOC, lint clean)
- `backend/tests/scripts/test_generate_backlog.py` (21 tests)
- `scripts/git-hooks/pre-commit` Section 6 (R33 — backlog freshness gate, auto-regen + auto-stage)

### Wave 2 plan (próximo)

Spawn agent `general-purpose` con scope:

1. **Refactor modules/{m}.md** — strip campos derivables (`capabilities_count`, `stories_count`), eliminar lista capabilities con descripción duplicada, mantener solo unique parts (frontmatter module-level + narrativa "qué hace POR EL USER" + auto-list comment marker for generator).

2. **Migrate pm-nico/pis/active/PI-{3,4,5,9,10,11}/** — leer cada PI legacy y crear:
   - `docs/product/outcomes/pi-{n}-{slug}.md` con frontmatter (state según artifacts presentes)
   - State assignment heuristic:
     - PI con specs + arch + tickets done = `done`
     - PI con specs + arch pero sin tickets builders = `ready`
     - PI con specs sin arch = `validated`
     - PI con discovery doc only = `validated` (con preparing flag)
   - Mantener PI.md original referenced en frontmatter (audit trail)

3. **Migrate active legacy stories `docs/product/stories/{m}/{id}.yaml`** según state:
   - state=live → migrate scenarios a capability (R32 already keeps them in sync), archive yaml a `docs/archive/2026/stories/legacy-yaml/{id}.yaml`
   - state=ratified → keep en pool stories (transition), state=`validated` (en discovery)
   - state=in-progress → mantener legacy paradigm hasta cierre PI-12

### Wave 3 plan

Spawn agent `general-purpose` con scope skills:
- Crear `/po-ux` fusión (combina /po + /ux-ui para UI std)
- Retire `/ux-ui` (mantain `/ux-disruptivo` + `/ux-agentico` + `/ux-flow-architect` + `/ux-disruptivo`)
- Consolidar 8+ domain expert skills en `/domain-expert <module>` con args
- Update CLAUDE.md / AGENTS.md / `/pm` skill / `/po` / `/architect` / `/dev-team` / `/auditor` para referenciar paradigma nuevo
- Anti-telephone-game rule codificada en agent prompts (subagent return MUST be `<verdict> -> <path>`)

### Wave 4 plan

- `scripts/validate_session_close.py` — Stop hook validator (WIP caps + checkpoint freshness + WIP no commiteado)
- Stop hook integration en `.claude/settings.json`
- Pre-commit hook Section 7 — WIP cap warning (warn, no block)
- Story Map 2D HTML (Eleventy) si Mermaid 1D no alcanza después uso real
- Validators-first ratification: cada nueva story DEBE tener `04-validators.yaml` antes state=ready

---

## Open questions

- ¿Qué hacer con PI-12 en vuelo durante migration? **CERRADO** — cierra paradigma viejo, no migra mid-flight.
- ¿Cuándo retire skill list bloat? **PLAN** — Wave 3.
- ¿Phase 2 visualizador 2D vale la pena? **DEFER** — usar Mermaid 1D, evaluar Phase 2 después uso real.

## Bitácora

- 2026-05-05 — Sesión inicial. Puntos 1, 2, 3 cerrados.
- 2026-05-05 — Wave 1 implementada (folder skeleton + ideas-pool + generate_backlog.py + tests + pre-commit hook Section 6). Lint clean. 21 tests verde.
- 2026-05-06 — **Wave 2 ejecutada** (`docs/pm-nico/` eliminada por completo).
- 2026-05-06 — **Wave 3 ejecutada** (skills + CLAUDE.md + AGENTS.md + rules updated to nuevo paradigma).

### Wave 2 — Resumen ejecución (2026-05-06)

**PIs migrados a outcomes (still-active):** 6
- `pi-3-sales-agent-improvement` → state=validated (discovery placeholder)
- `pi-4-brand-evolutive-maintenance` → state=building (rolling maintenance)
- `pi-5-copilot-multicanal-telegram` → state=building (S1+S2 shipped, S3+ pendientes)
- `pi-9-growth-studio-architecture` → state=validated (discovery, blocked by PI-8)
- `pi-10-growth-studio-ux-homologation` → state=validated (placeholder, blocked by PI-9)
- `pi-11-backend-quality-guardrails` → state=building (PR-1+PR-3+PR-4 shipped, PR-2 partial)

**PIs archivados a `docs/archive/2026/legacy-pis/` (DONE / preserved as audit trail):** 11 total
- PI-1, PI-1.1, PI-2, PI-7, PI-8 (originalmente en `pm-nico/pis/archive/`)
- PI-3, PI-4, PI-5, PI-9, PI-10, PI-11 (originalmente en `pm-nico/pis/active/`, contenido completo preservado además de outcomes/ migration)

**Modules refactorizados:** 16 archivos `docs/product/modules/*.md`
- Stripped: `capabilities_count`, `stories_count`, `legacy_pm_nico` desde frontmatter
- Replaced: sección `## Capacidades actuales` (+ subsecciones `### Cap: ...` arrastradas) → marker `## Capacidades > Auto-list generated...`
- Excepción: `campaigns.md` (sin sección "Capacidades actuales" — formato distinto, dejado intacto)

**Otros artefactos migrados:**
- `pm-nico/current-state/` (16 archivos) → `docs/archive/2026/legacy-pm-nico-current-state/current-state/` (audit trail; contenido vivo está en `docs/product/modules/`)
- `pm-nico/opportunities/` (6 archivos) → `docs/product/opportunities/` (mantener accesibles como SSoT discovery)
- `pm-nico/ideas/live-selling-whatsapp-assistant.md` (research-rich) → entry agregada a `docs/product/ideas-pool.yaml` + archivo original preservado en `docs/archive/2026/legacy-pm-nico-research/ideas/`
- `pm-nico/story-map/backbone.md` → `docs/product/story-map/backbone.md`
- `pm-nico/process/` → `docs/archive/2026/legacy-pm-nico-research/process/` (templates legacy superseded por `docs/specs/templates/`; learnings ya migrados a `docs/process/learnings.md`)
- `pm-nico/research/` (6 docs) → `docs/archive/2026/legacy-pm-nico-research/research/`
- `pm-nico/glossary.md` → `docs/product/glossary.md` (no existía, copia directa)
- `pm-nico/vision-compressed.md` → `docs/product/vision.md` (no existía, copia directa)
- `pm-nico/INDEX.md` + `pm-nico/TEMPLATES/` + `pm-nico/roadmap.md` → archived a `docs/archive/2026/legacy-pm-nico-research/` (superseded por `docs/product/INDEX.md` + `docs/product/BACKLOG.md` auto-gen)

**Code refs actualizados (pm-nico → archive paths):** 9 archivos
- BE arch tests: `test_copilot_anchors.py`, `test_sales_agent_anchors.py`, `test_campaign_state_additive.py`, `test_outbound_orchestrator_non_breaking.py`
- BE source: `modules/copilot/application/orchestrator/invoke_result.py`, `modules/sales_agent/application/orchestrator/outbound_orchestrator.py`
- BE other tests: `tests/quality/golden/test_voice_fidelity_outbound.py`, `tests/integration/test_outbox_cutover_e2e.py`, `tests/modules/sales_agent/application/orchestrator/test_state_additive.py`
- Hook: `scripts/git-hooks/pre-commit` (removed `pm-nico/pis/active/` from BACKLOG_SOURCES regex; updated comment)
- Generator: `scripts/generate_backlog.py` (docstring update; legacy reader returns `[]` defensively when path absent)

**Decisiones / juicio aplicado:**
- PI-4 marcado `building` (rolling track) en vez de `validated` — track sigue activo aunque sin sprint nuevo en vuelo, refleja realidad mejor que `validated`.
- PI-11 marcado `building` (no `done`) porque PR-2 commit `6a352df2` mergeado pero sin RESULT.md formal y S2 no iniciado; closure formal pendiente.
- `pm-nico/current-state/` archivado en vez de eliminado — contenido nominal duplicado por `docs/product/modules/` (Wave 1) pero algunos pm-nico files tienen info marginalmente distinta; archive preserva como audit trail.
- `pm-nico/opportunities/` migrado a `docs/product/opportunities/` (no archived) — son artefactos vivos de discovery, no historia legacy.
- `live-selling-whatsapp-assistant.md` agregada a ideas-pool.yaml con notes section + archivo original preservado en archive (research detail demasiado rico para perder).
- `campaigns.md` dejado sin refactor (no tenía sección "Capacidades actuales"; estructura alternativa "S1 SHIPPED / S2 SHIPPED" con info única no duplicada).

**Conflictos / archivos sobrescritos:** ninguno (no hubo destinos pre-existentes que requirieran archivar a `conflicts/`).

**Verificación post-migración:**
- `docs/pm-nico/` no existe (verificado con `ls docs/pm-nico` → No such file or directory)
- `python3 scripts/generate_backlog.py` regenera limpio; nuevos outcomes visibles en BACKLOG.md
- `python3 scripts/reconcile_capabilities.py --check` PASS
- `pytest tests/scripts/test_generate_backlog.py --no-cov -q` 21/21 PASS
- `pytest` arch tests modificadas (4 archivos) 15/15 PASS
- `ruff check` clean en files touched
- `python3 scripts/generate_backlog.py --check` PASS (sin drift)

### Wave 3 — Resumen ejecución (2026-05-06)

**Skills creados:** 1
- `/po-ux` (NEW fusión `/po` + `/ux-ui`) — para UI standard stories. Produce `01-spec.md` UNIFICADO con Gherkin + wireframes inline + estados visuales + microcopy + Playwright graders en single artifact.

**Skills updated to nuevo paradigma:** 6
- `/pm` — paradigma 7 estados + WIP caps + bootstrap single-read BACKLOG.md + capability promotion R32+R33 + comandos típicos refresh
- `/po` — scope clarificado (service-only + agentic spec; UI std → `/po-ux`); paths actualizados a `docs/product/stories/{id}/`
- `/ux-agentico` — paths actualizados; cross-link a `/po-ux` + decision matrix
- `/architect` — orchestrator produces ready package (03-arch + 04-validators + 05-guidelines + 06-tickets); state transition validated→ready; templates inline
- `/dev-team` — Conv 2 autonomous build mode; iteration loop vs `04-validators.yaml`; cap_reached → blocked + escalate
- `/auditor` — Conv 3 review+merge; CHECKPOINTS.md C1-C5 grid replacing REVIEW-final.md categories; spawns auditor-{be,fe,agentic}

**Skills deprecated (kept con deprecation notice):** 2
- `/ux-ui` → marked DEPRECATED, redirects to `/po-ux` (UI std), `/ux-disruptivo` (novel UI), `/ux-agentico` (agentic flows)
- `/nicolify-feature` → marked DEPRECATED, redirects to 3-conversation flow `/pm + /po-ux + /architect + /dev-team + /auditor`

**Skills NOT consolidated (deferred per task spec):** 8 domain experts
- brand-expert, offer-expert, offer-type-preset-expert, sales-agent-expert, copilot-expert, metrics-expert, manychat-expert, frontend-expert/backend-expert — kept separate. Future work item.

**Anti-telephone-game rule added to:** 11 agent prompts
- `builder-{backend,frontend,agentic}.md` — `done|blocked|failed -> path`
- `auditor-{backend,frontend,agentic}.md` — `done|changes_requested|escalated -> path`
- `architect-orchestrator.md` — `done|blocked|escalated -> path`
- `context-builder.md` — `done|partial|blocking -> path`
- `context-validator.md` — `clean|partial|blocking -> path`
- `gate-runner.md` — `done|ERROR -> path`
- `grep-bot.md` — `found|not_found|RECOMMEND_SONNET_EXPLORE -> short-result`

**Root files updated:** 2
- `CLAUDE.md` — paradigma updated (vocabulary 7 estados + 3 conversaciones + ready package + skills ejes table refresh + resume protocol single-read + conditional rules table refresh + R32/R33 mentions)
- `AGENTS.md` — Skills (load when touching) table refresh; new entries po-ux/po/ux-agentico/architect/dev-team/auditor + R33/R32 hooks

**Rules updated:** 3
- `.claude/rules/pm-nico-ssot.md` — replaced with deprecation stub pointing to `docs/product/BACKLOG.md` + `docs/product/{outcomes,stories,capabilities,modules}` as new SSoT
- `.claude/rules/parallel-safety.md` — M1/M2/M4/M6/M7 + bottom prohibitions list updated to new paradigm vocabulary (story instead of PR, learnings.md instead of process-learnings.md, BACKLOG.md instead of roadmap.md, etc.)
- `.claude/skills/pm/references/pm-nico-ssot.md` — replaced with deprecation stub
- `.claude/skills/pm/references/04-prd-template.md` — pm-nico path replaced with `docs/product/stories/{id}/01-spec.md` reference
- `.claude/skills/pm/references/02-user-story-mapping.md` — pm-nico backbone path → `docs/product/story-map/backbone.md`

**Sub-architects path updates:** 3
- `architect-be/SKILL.md`, `architect-fe/SKILL.md`, `architect-agentic/SKILL.md` — output paths updated `docs/product/stories/{story-id}/03-arch-{be,fe,agentic}.md`

**Other skill path updates:** 3
- `ux-flow-architect/SKILL.md` — PM handoff mode path updated; legacy reference preserved
- `data-storyteller/SKILL.md` — standalone output path updated
- `copilot-expert/SKILL.md` + `sales-agent-expert/SKILL.md` — PR-2 CONTRACT.md ref redirected to `docs/archive/2026/legacy-pis/`

**Agent prompts pm-nico cleanup:** 4
- `architect-orchestrator.md` (4 places), `auditor-backend.md` (1), `auditor-frontend.md` (1) — `pm-nico/current-state` → `capability YAML + modules/{m}.md` (post 2026-05 paradigma)

**Verification results:**
- `python3 scripts/generate_backlog.py --check` PASS
- `python3 scripts/reconcile_capabilities.py --check` PASS
- `pytest tests/scripts/ --no-cov -q` 75/75 PASS
- `pytest tests/architecture/ --no-cov -q --override-ini='addopts='` 827/827 PASS
- Combined: 902/902 PASS
- Active `pm-nico` references in `.claude/`: 0 (only deprecation/migration notes remain — explicit + acceptable)
- Active legacy `PI-N/sprints/SN/stories` references in `.claude/`: 0 (only "Legacy PI-12" disclaimers remain)

**Decisiones / juicio aplicado durante Wave 3:**
- Created `.claude/skills/po-ux/` as new folder (no existing nicolify-feature legacy folder to replace; cleaner delineation)
- Marked `/ux-ui` DEPRECATED instead of deleting — preserved historical content under deprecation notice for safety per task constraints (parallel-safety: never destructive)
- Marked `/nicolify-feature` DEPRECATED for same reason — its monolithic orchestrator pattern incompatible with 3-conversation paradigm
- Sub-architect skills (architect-be/fe/agentic) — light touch path updates only (output paths to new story location); deeper refactor deferred since they're invoked by `/architect` orchestrator which already has new paradigm
- Domain expert consolidation deferred per task spec (low priority, time-bounded)
- Builder/auditor agent files (.claude/agents/*) — added anti-telephone-game return contract HEADER but did NOT deeply restructure category grids/checklists (per task constraints "DO NOT modify deeply — Wave 4 revisits")
- pm-nico cleanup in agent prompts: replaced "pm-nico/current-state" with new "capability YAML + modules/{m}.md" wording inline (rather than removing entirely) — preserves the *intent* (post-merge SSoT update reminder) under new vocabulary
- `architect` skill emits both `03-arch.md` consolidado AND sub-arquitecturas (`03-arch-{be,fe,agentic}.md`) — matched against pm-redesign spec which lists single `03-arch.md` in 5-file ready package; rationale: orchestrator's 03-arch.md is the consolidated entry point, sub-files are persisted detail (avoids losing detail from sub-architects but keeps single canonical entry)

---

### Wave 4 deliverables (2026-05-06)

**R34 Stop hook validator (`scripts/validate_session_close.py`):**
- 4 checks at session close:
  - WIP cap enforcement (BLOCK exit 1) — building≤3, ready≤5, validated≤10, review≤2
  - BACKLOG freshness (WARN exit 2) — generate_backlog --check + reconcile_capabilities --check
  - Uncommitted WIP (WARN) — git status not clean
  - Story checkpoint staleness (WARN) — checkpoint.md > 7d para stories ready/building/review
- 12 unit tests (`backend/tests/scripts/test_validate_session_close.py`)
- Lint clean, format clean

**Stop hook integration en `.claude/settings.json`:**
- Stop hook block invocando validator --quiet (only print on violations)
- 30s timeout

**Story Map 2D HTML (Eleventy) — DEFERRED:**
- Mermaid kanban en BACKLOG.md (Wave 1) suficiente Phase 1
- Phase 2 si uso real demuestra necesidad

**Bitácora Wave 4:**
- 2026-05-06 — Wave 4 implementada. Pipeline completo (Wave 1-4) operativo.

## Estado final pm-redesign 2026-05

| Wave | Status | Commit |
|---|---|---|
| 1 — Foundation | ✅ DONE | 207760c1 |
| 2 — Migration pm-nico/ | ✅ DONE | f23c3403 |
| 3 — Skills + paradigm refresh | ✅ DONE | b3d09e38 |
| 4 — Stop hook + automation | ✅ DONE | 26191622 |
| 5 — Punto 4: 10 estados + agentic eval methodology (F1-F7) | ✅ DONE | F1=38ac9940 · F2=e9034426 · F3+F4=fb65897c · F5={Olas 1-5} · F6=c2d95aae |

Sistema PM Nicolify v4 (post Punto 4) operativo. Resumen Wave 5:
- F1: doc canónico Punto 4 + CLAUDE.md + AGENTS.md + /pm friendly output
- F2: 6 pipeline skills adopt 10-state vocabulary (po, po-ux, ux-agentico, architect, dev-team, auditor)
- F3: generate_backlog.py recognize 10 states + LEGACY_STATE_MAP coercion + tests + pre-commit Section 7 (state enum validator)
- F4: 00-research-template.md + 04-validators-template.yaml (4 categories) + checkpoint-template.md v4
- F5: PI-12 migration (5 olas) — outcome creado + 2 done stories archived + 7 PM_DRAFT stories migradas a state=refining + carcasa legacy eliminada + cleanup refs
- F6: validate_session_close.py adopts 10-state caps + 16/16 tests PASS
- F7: regen + 934/934 tests PASS

Próximo step Chris: `/pm` 10-state pipeline operativo. Para refinar las 7 PI-12 stories pendientes usar `/po` (service-stories) o `/po + /ux-agentico` (agentic-stories) según cada caso.
