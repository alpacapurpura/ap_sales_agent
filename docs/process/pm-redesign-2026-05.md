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
