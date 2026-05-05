# Process Learnings (append-only)

> Owner: `/pm`. NUNCA editar entries históricas. Solo append.
> Cada incident / decisión cardinal / surprise / case study agrega entry.

---

## 2026-05-04 — Migración a SDD Level 3 / Spec-Driven Harness

**Contexto:** Estructura `docs/pm-nico/` se quedó corta. 6 PIs activos. Múltiples sesiones Claude. Necesidad de specs ejecutables + evals AI-resistant + resume protocol robusto.

**Decisiones:**
1. Estructura `docs/{product,projects,specs,process}/` paralela a `pm-nico/`. Migración gradual.
2. Story = unidad atómica. 1 archivo YAML. NO capability monolítico.
3. 3 tipos story: ui / agentic / service. Eval policy distinta.
4. Scenarios AI-resistant obligatorios: happy + negative + edge + adversarial.
5. Personas + Rubrics first-class versionados.
6. 9 skills nuevos: /pm rewrite, /po, /ux-ui, /ux-agentico, /architect (+ 3 sub), /dev-team, /auditor.
7. 11 nicolify-* agents renombrados al nuevo paradigma.
8. Tickets agentic = Opus 4.7 obligatorio (qwen ban).
9. Tickets BE/FE no-agentic = qwen-opencode preferido.
10. Self-fix auditor cap 2 iter, después escala.
11. /pm habla solo nuevo. Legacy `pm-nico/` lee on-demand manual.

**Fuentes consultadas:**
- Anthropic effective-harnesses-for-long-running-agents
- Anthropic harness-design-long-running-apps
- Anthropic multi-agent-research-system
- Anthropic managed-agents
- Anthropic AI-resistant-technical-evaluations
- Anthropic demystifying-evals-for-ai-agents
- Vercel "We removed 80% of our agents tools"
- τ-Bench / τ2-Bench (multi-turn evals)
- ejemplo-harness-subagentes (betta-tech)

**Riesgos identificados:**
- Migration parcial: durante 4-6 semanas, /pm habla solo nuevo pero PIs viejos siguen en pm-nico/. Chris debe pedir manual cuando query algo legacy.
- Aprendizaje curva: 9 skills nuevos. Primer story exemplar piloto crítico.
- Cost: multi-agent multiplica tokens (Anthropic 15x). Mitigación: solo orchestrator + sub-architects en Opus, devs en qwen/sonnet cuando posible.

---

## 2026-05-05 — Process improvement R1-R9 + A0 (post PI-12 S1 piloto)

**Contexto:** PI-12 S1 ejecutado pipeline completo `/po → /architect → /dev-team → /auditor` para 2 stories (litellm-canonicalization 11 tickets + eval-runner-foundation 6 tickets). Completó 5/17 tickets aprobados. Análisis post-mortem reveló 13 debilidades (D1-D13) → 11 recomendaciones (R1-R11). Sesión 2026-05-05 implementó R1-R9 + nueva A0 (hardening context-builder).

**Token baseline sesión origen (5 tickets):** ~3.3M tokens · ~$200-400 USD Opus 4.7. Extrapolación full S1: 10-12M tokens.

**Cambios cardinales (15 commits):**

A0 — Hardening context-builder Haiku (BLOCKER pre-R1, agregada por Chris durante session):
- H1-H10 implementadas: WebSearch+WebFetch+Tessl tool access, maxTurns 60→120, auto-keyword inference, cross-reference anti-duplication.md inventory, canonical docs URL fetch (15 frameworks), domain skill SKILL.md preload, validator pass adversarial probe (NEW agent context-validator), 3-state faithfulness flag (clean/partial/blocking), audit log mandatory, free-form pass §14, self-budget snapshot §16
- Sin hardening, context-builder = punto entrada frágil → R1 cementaba fragilidad
- Bug D4 caso: validador hubiera detectado missing test coverage cross-surface

R1 — context-builder Phase 0 en /dev-team + /auditor SKILL.md:
- Orchestrators ahora spawn context-builder Haiku antes builder/auditor
- Builder agents (BE/FE/agentic) consumen CONTEXT-BRIEF.md priority read
- Patched FE agents (builder-frontend + auditor-frontend) que NO referenciaban brief antes — parity catch-up
- Beneficio esperado: -30-40% tokens leídos repetidos

R2 — gate-runner enforcement orchestrator level:
- /dev-team Step 4 obliga gate-output.json existir + any_fail=false (force spawn si missing)
- /auditor Step 2 verifica fresh JSON (vs LATEST_COMMIT_TS) antes spawn sub-auditor
- Sub-auditor BLOCKED si gate-output.json shows fail (ticket vuelve dev-team)
- Beneficio: -10-15% tokens auditor + cero auditor inviste en código que falla gates

R3 — Auditor downstream regression scope (caso D4 CRÍTICO fix):
- Nuevo rule .claude/rules/auditor-downstream-regression.md (tabla SSoT 25 entries surface→downstream tests)
- auditor-{backend,agentic} agents agregan Step downstream_regression_scope MANDATORY post consume_gate_output
- Verdict math: downstream FAIL → overall FAIL Cat 10
- Sin esto repetimos D4 (cost_recorder approved pese a bug callback handlers cross-surface)

R4 — Pre-commit hook (voseo + ruff completo + format):
- scripts/git-hooks/pre-commit canonical SSoT (voseo regex + ruff check --no-cache + ruff format --check)
- .husky/{pre-commit,pre-push} wrappers exec scripts/git-hooks/* (husky 9.x compat)
- BUG PRE-EXISTING DESCUBIERTO + FIXED: pre-push hook DEAD desde install husky (core.hooksPath = .husky bypassea .git/hooks/pre-push) → ci-parity gate prod auto-deploy bypasseado silenciosamente. R4 wrapper resurrects gate.
- Voseo regex completo glosario spanish-text.md, exclude modules/sales_agent/ voice templates, magic comment voseo-allowed honor
- Tests verified: voseo MD blocked, ruff F632 blocked, clean pass

R5 — Schema-mirror exception codify backend-ddd.md:
- builder-backend MAY touch modules/{copilot,sales_agent}/persistence/models/ purely para schema mirror desde shared/ migration
- Cero juicio caso-a-caso auditor (caso PI-12 S1 T-1 ratificado por Chris ahora regla)
- Lista permitido (Mapped[] cols, indexes, FKs hacia shared, DEPRECATED markers) vs no permitido (touch domain/application/api/observability, change runtime, create table solo agentic)

R6 — Decisions injection 04-tickets template:
- Ticket-level field decisions_applicable: [D1, D3, X2] que lista decisions ratificadas upstream
- Builder commit body MUST cite cada D# en sección "Decisions honored"
- Auditor Cat 11 verifica cite — WARN si missing

R7 — T-6b operational gate 5d→1d (Story A pre-clientes):
- Editado 04-tickets.yaml + 03-arch-be.md Story A T-6b
- Sin tráfico productivo no justifica 5d wall-clock; re-escalable post-clientes activos

R8 — Sub-ticket numbering convention strict:
- T-{N}.a / T-{N}.b / T-{N}.c (con punto obligatorio)
- PROHIBIDO T-Na / T-Nb sin punto (origen confusión PI-12 Story A)
- Renumeración prohibida post-architect

R9 — Single git mv commit pre-scope-expansion (pm SKILL):
- Refactors estructurales = 2 commits separados
- Commit 1: git mv puro (zero content diff, git rename detection auto)
- Commit 2: scope expansion
- Cleaner history, bisect-friendly

Investigation phase produjo:
- docs/process/process-improvements-2026-05-05-investigation.md
- 4 áreas estudiadas: #1 metrics observables, #4 skill consolidation, #5 patterns memory, #6 auditor self-improvement
- 9 nuevas recomendaciones priorizadas R12-R20
- Cluster cohesivo PI-13: R12 + R14 + R16 + R18 (~15-25h, $TBD ROI)

**Lecciones aprendidas (cross-cutting):**

1. **"Punto entrada frágil cementa downstream rabbit hole"** — Chris pause R1 para hardening context-builder cuando se dio cuenta validador downstream era único safety. Lección: invest hardening upstream antes integrate downstream. Sin A0, R1 cementaba fragilidad.

2. **"Hooks invisibles bypasseados silenciosamente"** — pre-push DEAD descubierto incidentalmente al testear pre-commit. Lección: cuando merger tooling (husky 9 + .git/hooks legacy), explicit verify cada hook fires. R4 fix wrappers permite ambos paths funcionar.

3. **"Adversarial validator > checklist verifier"** — context-validator agent hace synonym scan + spot-check + blind audit en lugar de "verify each section is filled". Adversarial mode catch lo que builder MISSED, no confirma lo que tiene.

4. **"R3 mecánica > juicio auditor caso-a-caso"** — tabla SSoT `surface → downstream_test_targets` reemplaza decision-making per-PR. Mantenimiento manual cuando agregás surface shared/ cross-consumer pero amortiza muchos audits.

5. **"Decisions honored cite > confiar builder leyó spec"** — R6 forces explicit traceability. Sin cite → WARN. Pequeña fricción por cada commit (1 line) pero garantiza decisión NO ignorada silenciosamente (D10).

**Riesgos restantes:**

- **Métricas baseline missing:** R12 propone capture pero NO implementado. Validar R1-R9 ROI requiere medir antes/después. Próxima sesión: instrumentar antes spawning otra agent.
- **Skill consolidation deferred:** R14 propone audit pero 50+ skills siguen vigentes. Cognitive overhead persiste hasta PI-13.
- **Pattern-memory empty:** R16 skill diseñada pero patterns/ vacío. Sin seed inicial, skill returns nada útil.

**Fuentes consultadas:**

- docs/process/process-improvement-handoff-2026-05-05.md (handoff sesión anterior)
- bug D4 PI-12 S1 T-1 (cost_recorder canonicalization caso origen R3)
- pre-existing bug husky core.hooksPath ci-parity bypass (descubierto R4)

**Commits sesión:**
- 717123e5 feat(context-builder): harden Haiku pre-flight reader (H1-H10) + adversarial validator
- d276dce5 feat(dev-team,auditor): R1 integrate context-builder Phase 0 + FE agents parity
- e62919ac feat(dev-team,auditor): R2 enforce gate-runner usage at orchestrator level
- a12bf22d feat(auditor): R3 downstream regression scope rule + integrate auditor-{be,agentic}
- 19694702 feat(hooks): R4 voseo regex + ruff in pre-commit, fix dead pre-push under husky
- 1414563d docs(rules): R5 codify schema-mirror exception in backend-ddd.md
- ab56966e docs(templates): R6+R8 decisions injection + sub-ticket numbering convention
- 303a40a7 docs(pi-12-T6b): R7 operational gate 5d→1d pre-clientes
- 5808b7f3 docs(pm): R9 git mv aislado convention pre-scope-expansion
- 3d77e81b docs(process): investigation 4 áreas → R12-R20 priorizadas

---

## 2026-05-05 (cont.) — Process closure A2 + B1 + B2 + A1-partial + C1 + A3 piloto

**Contexto:** Sesión cierre R1-R9 + gaps de paridad detectados + primer piloto end-to-end del pipeline mejorado. Ejecutó 6 ítems + final audit con altísima calidad (audit per-ítem, no batch al final). Computer crash mid-pytest pero state recuperado sin pérdida de avance.

**Cambios cardinales (5 commits):**

A2 — Baseline metrics post-hoc transcripts capture:
- `scripts/extract_baseline_metrics_from_transcripts.py` — parsea Claude Code JSONL transcripts (~/.claude/projects/-home-chris-AISALESHT/) extrayendo per-agent run metrics (tokens, cache breakdown, tool counts, duration, LOC delta) tanto main turns como subagent invocations via `toolUseResult.agentType` schema discovery.
- Frozen baseline `docs/process/metrics/baseline-pre-R1-R9.jsonl` (10,750 rows, 3.2MB) cubre 2026-04-29..2026-05-05 — referencia ROI cuando R12 layer 2 aggregation se implemente PI-13.
- Tests: `backend/tests/scripts/test_extract_baseline_metrics.py` 6/6 PASS.
- `.gitignore` excluye futuros `runs.jsonl`/`all-runs.jsonl` rolling captures.

B1 — auditor-frontend Step 4.5 downstream regression (R3 parity):
- Step 4.5 análogo a auditor-agentic insertado entre `consume_gate_output` y `check_warning_baselines`.
- Tabla SSoT `.claude/rules/auditor-downstream-regression.md` extendida con 14 rows FE: lib/api, lib/tokens, lib/format, hooks/, components/shared, components/ui, features/api+types, lib/zod-schemas, arch fitness allowlists, e2e fixtures, playwright config.
- Workflow section incluye plantillas de spawn gate-runner para BE pytest + FE vitest + E2E playwright.
- Verdict math FE: downstream FAIL → overall FAIL Cat 10 / Cat 1.
- Cierra gap commit a12bf22d que parcheó solo BE + agentic.

B2 — Cat decisions_honored cite (R6 parity agentic + frontend):
- `auditor-agentic.md` Cat 15 + `auditor-frontend.md` Cat 14, mismo pattern que `auditor-backend.md` Cat 11.
- Verdict math: cat FAIL → overall FAIL si ticket tiene `decisions_applicable` pero commit body sin "Decisions honored" sección.
- Output format tablas updated.
- Cierra gap commit ab56966e que parcheó solo templates + BE.

A1 partial — R12 layer 1 instrumentation orchestrator:
- `scripts/emit_process_metric.py` — append-only emitter para `docs/process/metrics/runs.jsonl` (gitignored) con orchestrator-level metadata (ticket, phase, verdict, commit_sha, iter, note). Token-level detail viene del extractor post-hoc.
- `/dev-team` SKILL Step 5.5 + `/auditor` SKILL Step 4.5 invocan emit antes handoff.
- Best-effort emission (script missing → warn + continue, never blocks pipeline).
- Tests: `test_emit_process_metric.py` 6/6 PASS.

C1 (R21 nueva) — Pre-commit hook auto-detect tabla SSoT R3 outdated:
- Hook Section 4: nuevo file (status A/R) bajo `backend/src/shared/.+\.py$` MUST aparecer en tabla SSoT auditor-downstream-regression.md OR carry `# downstream-regression-na: <reason>` magic comment primeras 20 líneas.
- Side fix crítico: hook ahora usa `git show :file | ruff stdin` en lugar de leer working tree — verifica STAGED content que es lo que va a commitearse. Pre-existing silent-pass bug arreglado (encontrado durante A2 commit).
- Hook hace `pushd backend` + ruff `--config` implícito para que `--stdin-filename src/...` resuelva chain `__init__.py` correctamente (INP001) y use `pyproject.toml` (line-length=120).
- Tests: `test_pre_commit_hook.py` 10/10 PASS — clean python, voseo block, ruff staged-violation block, format block, R3 SSoT block, NA marker passes, tabla-listed parent dir passes, M not gated, nested tests/ excluded, modules/ not gated.
- Rule update: nueva sección "Pre-commit freshness gate" en SSoT.

A3 piloto — T-1.bis micro-ticket pipeline completo:
- Bug repro confirmed: commits 5856be4d (T-1) introdujeron LiteLLM CustomLogger bridge donde `cost_usd` se obtiene via `pop_cost(litellm_call_id)` (no más `calculate_cost()` runtime). 2 callback-handler tests mock LLMResult sin `litellm_call_id` en response_metadata → cost None → assertions fail.
- **Misdiagnosis original handoff doc:** sugería fallback en `litellm.get_llm_provider()` raise — pero ese path ya tiene try/except + hint fallback. Real bug = test fixture incompleto.
- Pipeline ejecutado con improvements vivos: context-builder Phase 0 → builder-backend (test-only fix) → gate-runner (no escribió JSON, gate-output.json escrito manualmente) → auditor-backend con R3 downstream + R6 decisions cite verification → APPROVED.
- Fix shipped (commit 3cb98fd4): nuevo `prime_cost_bridge(call_id, cost)` helper en `backend/tests/conftest.py` (lifted shared per D-T1bis-3 — pattern usado 2 modules), 2 tests migrados con `litellm_call_id` injection + cost stash.
- Verification: 27/27 ticket-scoped + 200/200 downstream + 823/823 arch fitness PASS.
- Cero production code changes (cost_recorder.py + base_callback_handler.py untouched per A4 binding).

**Lecciones aprendidas (cross-cutting):**

1. **"Audit per-ítem > audit batch al final"** — Chris pidió mid-stream cambiar cadencia a implement → audit → fix → commit → next por ítem. Resultado: cada commit aterrizó verde pre-pre-commit hook (excepto un par de roundtrips ruff que cazó el hook nuevo). Cero tech debt acumulado.

2. **"Pre-commit hook doble lección"** — A2 commit reveló bug pre-existing (hook chequeaba working tree, no staged). Fix fold dentro C1 (mismo surface) — atomic change. Lección: cuando agregas check al hook, audita patrón de check ANTES (si chequea filesystem vs git index, asume comportamiento incorrecto).

3. **"Gate-runner subagent escribió zero JSON 1ra vez"** — primera invocación gate-runner produjo "log huge, let me extract" output sin escribir gate-output.json. Workaround: orchestrator escribió JSON manualmente con resultados de scoped tests. Mejora futura: gate-runner prompt MUST validate JSON written before returning. Reportable como R22.

4. **"Misdiagnosis upstream → builder enroped por handoff"** — original handoff doc asumió bug en `get_llm_provider()` raise. Builder spawned con corrección quirúrgica habría implementado fix incorrecto. Fix: orchestrator (Chris+Claude) reproduce bug PRIMERO, decide diagnóstico real, después spawnea con scope corregido. Aplicado: T-1.bis spec correctamente identifica test-side fix vs code-side.

5. **"Computer crash recovery"** — sesión hard-resumed mid-pipeline. State recovered: git limpio + commits intactos + tests pasaron al re-correr. Lección: commits pequeños + frecuentes + push origen development = zero pérdida wall-clock cuando WSL2 cuelga.

6. **"Pre-commit hook bloqueó voseo en su propio test fixture"** — el test que verifica que el hook bloquea voseo INTRODUJO voseo en su test data. Hook bloqueó. Fix: magic comment `<!-- voseo-allowed -->` en docstring del test file. Self-referential edge case.

**Token consumption esta sesión (subagents):**

| Agent | Tokens | Tools | Duration | Did |
|---|---|---|---|---|
| context-builder (Haiku) | 113,676 | 35 | 151s | 16-section CONTEXT-BRIEF.md T-1.bis |
| builder-backend (Opus) | 128,587 | 46 | 416s | 3 test files migration + helper lifted to conftest + commits + push |
| gate-runner (Haiku) | 55,033 | 25 | 2,022s | parsed full /test-backend log (NO JSON written — manual workaround) |
| auditor-backend (Opus) | 152,791 | 16 | 176s | R3 + R6 audit categories all green → APPROVED |
| **Total subagents A3** | **450,087** | **122** | **2,765s** | T-1.bis pipeline end-to-end |

Plus orchestrator main session ~150k tokens estimated (tracked post-hoc next session).

**Riesgos restantes:**

- **gate-runner reliability:** subagent didn't write gate-output.json reliably first invocation. Spawn pattern needs `must_write_json: true` enforcement. Backlog R22.
- **Pipeline cost sin budget cap:** T-1.bis pipeline = 450k subagent + 150k main = ~600k tokens (~$10-15 USD). Acceptable para pilot, but R11 (token budget cap) sigue diferido a PI-13.
- **R12 layer 2:** baseline-pre-R1-R9.jsonl + emit_process_metric.py runs.jsonl creados pero NO existe aggregation script (PI-13).

**Commits sesión:**
- 07f138f3 feat(process-metrics): A2 baseline capture script + frozen pre-R1-R9 snapshot
- 909721de feat(auditor): B1+B2 R3+R6 parity to FE/agentic auditors
- ece0ce89 feat(process-metrics): A1 partial R12 layer 1 — orchestrator metric emission
- 1a868ac5 feat(hooks): C1 R21 R3 SSoT freshness gate + fix staged-content lint check
- 3cb98fd4 feat(pi-12-T1.bis): test bridge migration for LiteLLM cost
- d1e099ba docs(pi-12-T1.bis): add result + impl-log for test bridge migration

**Fuentes consultadas:**
- `docs/process/process-improvement-handoff-2026-05-05.md` (T-1.bis micro-ticket diagnóstico — tracked misdiagnosis)
- `docs/process/process-improvements-2026-05-05-investigation.md` (R12-R20 backlog — A1 partial implementa R12 layer 1)
- `.claude/agents/context-builder.md` + `context-validator.md` (H1-H10 hardened in prior session — used live in A3)
- LiteLLM `kwargs['response_cost']` bridge architecture (decision T-1 A4 binding)
- Anthropic prompt caching `usage` schema (cache breakdown extraction A2)

---
