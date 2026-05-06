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

## 2026-05-05 (cont. 2) — R22-R27 implementation: harness evolution

**Contexto:** Después del piloto T-1.bis end-to-end (sesión cont.), 6 puntos
de mejora detectados (R22-R27) implementados sistemáticamente — defense in
depth + multi-layer integration en lugar de parches puntuales. Cada R toca
agent prompts + skills + rules + hooks + tests + docs según corresponda.

**Cambios cardinales (1 commit):**

R22 — gate-runner JSON write enforcement:
- `.claude/agents/gate-runner.md` step nuevo `verify_artifacts_written` post-condition
  con 5 verifications mandatory (file exists + size ≥100B + valid JSON + schema keys
  present + raw log written) antes de return. Returning without artifact = HARD
  contract violation. Last-line spec dual: success path vs error path explicit.
- `.claude/skills/dev-team/SKILL.md` Step 4 + `.claude/skills/auditor/SKILL.md` Step 2
  ahora documentan post-spawn validation: si gate-runner returns "ERROR — gate-output.json
  write failed" o test -f missing → re-spawn ONE second time, then fallback manual.
- Origen: T-1.bis 2026-05-05 — gate-runner returned text summary sin escribir JSON.

R23 — production_code flag + dynamic owner_eligibility:
- `docs/specs/templates/04-tickets-template.yaml` § 4 docs flag semantics + ejemplo
  T-N.bis test-only sub-ticket showing owner pool [qwen, sonnet] válido aunque
  surface AGENTIC.
- Cada ticket production T-1/T-2/T-3 ejemplo template ahora declara
  `production_code: true` explícito.
- `.claude/skills/dev-team/SKILL.md` Step 1 owner-decision tabla + pseudocode
  rule. AGENTIC + production_code:false (tests/docs) → Sonnet OK; AGENTIC +
  production_code:true → Opus HARD.
- `.claude/skills/architect/SKILL.md` Step 5 validation checklist requiere
  flag set per ticket coherent con surface + scope.
- Origen: T-1.bis 2026-05-05 forzó Opus 4.7 (~$8 USD) para test-only fix.

R24 — context-builder validator hard-fail:
- `.claude/agents/context-builder.md` Step 12 `MANDATORY` upgraded to `HARD-FAIL`.
  Post-condition: `test -f CONTEXT-BRIEF-validation.md`. If skipped twice →
  auto-seal flag `blocking` + §11 entry `VALIDATOR_NOT_RUN`.
- 6 consumer agents (`builder-{backend,frontend,agentic}`, `auditor-{backend,frontend,agentic}`,
  `architect-orchestrator`) heredan R24 brief acceptance gate: REFUSE consume si
  header `Validator pass:` `_pending_` OR `Faithfulness flag: blocking`. Override
  magic ack `# context-validator-skipped: <reason>` permite caller assume risk.
- Defense in depth: producer enforces + consumer enforces. Bypass 1-side requires
  bypass other-side too.
- Origen: T-1.bis 2026-05-05 — context-builder sealed brief con flag `partial`
  sin spawn validator. R24 hace silent skip imposible.

R25 — voseo-allowed regex flexibility:
- `scripts/git-hooks/pre-commit` Section 2 regex updated:
  `(#\s*voseo-allowed([: \t]|$)|<!--\s*voseo-allowed[^>]*-->)`
  Acepta: `# voseo-allowed`, `# voseo-allowed: reason`, `# voseo-allowed —reason`,
  `<!-- voseo-allowed -->`, `<!-- voseo-allowed: reason -->`, `<!-- voseo-allowed — reason -->`.
- Locale-safe: drop unicode em-dash from char class (POSIX ERE multi-byte issue);
  use `[^>]*` for MD content + `[: \t]|$` for Py end-of-line tolerance.
- 2 nuevos tests: `test_voseo_allowed_marker_with_reason_passes`,
  `test_voseo_allowed_marker_em_dash_passes`. Total 12/12 PASS.
- `.claude/rules/spanish-text.md` § Magic comment escape — documenta variantes.
- Origen: T-1.bis 2026-05-05 — auditor review.md citing glosario verbatim
  bloqueado por hook regex original `<!-- voseo-allowed -->` literal exact.

R26 — hotfix-repro-mandatory rule (NEW rule):
- `.claude/rules/hotfix-repro-mandatory.md` (NEW). Workflow Step 1-4: reproduce
  → diagnose → cite evidence → spawn builder. Match/Mismatch/No-repro decision tree.
- `.claude/skills/dev-team/SKILL.md` Step 0.5 (entre bootstrap + Step 1):
  hot-fix ticket detection (signals `bug|hot-fix|regression|incident|bis|revert`)
  → repro mandatory → REFUSE spawn si `repro_verified: false/missing`.
- `.claude/skills/po/SKILL.md` Step 2.5 (entre Step 2 cargar skill + Step 3
  redactar spec): para hot-fix story, repro pre-spec → cite evidence en
  spec + story YAML.
- `docs/specs/templates/04-tickets-template.yaml` § 4 docs `repro_verified` field
  semantics + `repro_evidence` schema + `diagnosis_correction` cuando handoff
  misdiagnoses.
- Origen: T-1.bis 2026-05-05 — handoff doc misdiagnosed (suggested provider
  fallback fix; real bug = test bridge missing). Sin repro local, builder Opus
  habría wasted ~$8 USD on wrong scope.
- 5 enforcement layers: /po + /dev-team + template + auditor REVIEW + builder agent.

R27 — crash recovery + persistent artifacts protocol:
- `docs/process/checkpoint-protocol.md` § Crash recovery (NEW). Documenta:
  - Subagent contract: write artifacts EARLY (skeleton at Step 0, fill incremental
    via Edit). Crash mid-build → partial brief + audit log explica what's missing.
  - Orchestrator contract: commit + push frequent (≤2 commits unpushed). Update
    checkpoint.md per artifact.
  - Resume from crash workflow (6 steps from git status to scoped re-run).
  - Background tasks: NUNCA confíes en bg task output sin re-verify post-crash.
  - Tests state recovery: ticket-scoped → downstream → module → full (escalate
    only on red flag).
- Origen: T-1.bis 2026-05-05 — WSL2 crash mid-pytest pero commits ya pushed →
  state recovered <2min. Lección codificada.

CLAUDE.md + AGENTS.md sync:
- `CLAUDE.md` Critical Rules table extended con #14 (R3 + R21 auditor-downstream-regression)
  + #15 (R26 hotfix-repro-mandatory).
- Conditional Rules table añade R12 layer 1 process metrics emission + hot-fix
  routing entry.

**Lecciones aprendidas (cross-cutting):**

1. **"Multi-layer enforcement > single-layer parche"** — cada R applies multiple
   layers (agent + skill + rule + hook + test). R24 ejemplo: producer (context-
   builder hard-fail) + consumer (6 agents refuse without validator) + override
   magic ack. Bypass requires bypass both sides — defense in depth.

2. **"Locale-safe regex en hooks bash"** — R25 reveló que `[—]` em-dash en
   character class POSIX ERE puede fallar locale-dependent. Lección: avoid
   multi-byte chars en char classes; use `[^>]*` o explicit alternation.

3. **"Hot-fix tickets son trampa AI-resistant"** — handoff doc misdiagnosis
   muy fácil pasar gate /po + /architect porque parece scope claro + repro
   en doc. R26 force repro local PRE-spec — el único momento donde el coste
   del bug aún es bajo.

4. **"Production_code flag captura clase de tickets antes invisible"** — pre-R23
   no había forma de distinguir test-only fixes de production fixes en owner
   policy. Surface alone insuficiente (test sobre módulo agentic → no es
   agentic-production-code). R23 introduce ortogonalidad explicit.

5. **"Skeleton-first rescata work post-crash"** — R27 codifica pattern existente
   (context-builder ya hacía skeleton-first H6) generalizado a todos subagents.
   Crash mid-build = partial artifact + audit log = recovery <30s en lugar de
   re-spawn from scratch.

6. **"Validator skip hard-fail > silent partial"** — pre-R24, agent sealed brief
   at `partial` flag without spawn validator. Looked OK to caller → consumed.
   Post-R24, agent MUST verify CONTEXT-BRIEF-validation.md exists post-spawn,
   else auto-block. Producer + consumer dual enforcement.

**Token consumption esta sesión (no subagents — orchestrator-only):**

Mejoras meta-process aplicadas via Edit/Write tool calls. ~80-120k tokens
estimated (extracción post-hoc next session).

**Riesgos restantes:**

- **Existing tickets no migrated to production_code flag** — solo template
  + nuevo T-N.bis ejemplo tienen flag. Tickets existentes en PIs activos
  (PI-12 S1) NO tienen flag → /dev-team sin flag debe asumir
  `production_code: true` default seguro.
- **Hot-fix tickets ya creados sin repro_verified** — T-1.bis ya merged, no
  retro-aplica. Próximo hot-fix será primer test del workflow R26.
- **R27 background-task verification gap** — protocolo documentado pero no
  enforce automático. Future R28: tooling para detectar bg-task-output stale.

**Commits sesión:**
- (incoming) feat(harness): R22-R27 multi-layer enforcement evolution

**Fuentes consultadas:**
- `docs/process/learnings.md` 2026-05-05 entry #2 (T-1.bis closure case)
- `.claude/agents/{context-builder,gate-runner,builder-*,auditor-*,architect-orchestrator}.md` (6+ agent prompts surveyed for layer integration)
- `.claude/skills/{dev-team,auditor,architect,po}/SKILL.md` (4 skills updated)
- `.claude/rules/spanish-text.md` (R25 doc)
- `docs/specs/templates/04-tickets-template.yaml` (R23 + R26 fields)
- `docs/process/checkpoint-protocol.md` (R27 crash recovery)

---

## 2026-05-05 (cont. 3) — R28-R31 implementation: T-3 cycle pilot post-mortem fixes

**Contexto:** Sesión T-3 cycle (PI-12 S1 sales-agent-litellm-canonicalization)
piloteó pipeline R1-R27 end-to-end (context-builder → context-validator →
builder-backend → gate-runner → auditor-backend). 4 errores recurrentes
detectados — fixes codificados como R28-R31 multi-layer enforcement.

**Cambios cardinales (1 commit pendiente):**

R28 — context-builder Step 12 require literal bash output proof:
- `.claude/agents/context-builder.md` Step 12 strengthened — agent's final
  reply MUST include verbatim block `## R24/R28 post-condition proof` with
  pasted bash output of `test -f` + `stat -c '%s bytes'`. Reply WITHOUT
  this block = HARD contract violation; orchestrator treats brief as
  `Validator pass: BLOCKED` regardless of header value.
- Origen: T-3 (2026-05-05) context-builder Haiku returned summary text
  saying "Validator will: ..." (future tense) without ever spawning. Step
  12 post-condition was prompted but the agent's final summary skipped the
  bash execution. Agent KNEW step 12 said spawn validator + run test -f, but
  generated narrative summary that simulated completion. R28 fix: proof
  must be in reply text, not just claimed by header (which the agent set
  to `_pending_` then forgot to update).

R29 — gate-runner skeleton-first JSON write + cross-ticket archive:
- `.claude/agents/gate-runner.md` NEW Step 0 `step_0_skeleton_first` BEFORE
  prep step. Writes minimal valid `gate-output.json` skeleton with
  `pending: true` markers IMMEDIATELY (turn 1) before running any test.
  Each gate completion = ONE Edit call updating `gates: []` array entry.
  Final step updates `overall.summary` from "PENDING" → final string.
  Truncation mid-execution = partial-but-valid JSON (auditor sees explicit
  `overall.summary: "PENDING"` + `notes: "skeleton (pre-execution)"`
  rather than stale data from prior ticket).
- ALSO: cross-ticket archive logic — if existing `gate-output.json` has
  `ticket` field DIFFERENT from current `<ticket>` input → archive as
  `gate-output.<previous_ticket>.json` BEFORE skeleton write. Adds
  `<ticket>` to mandatory inputs (was implicit before).
- Schema_version `1.0` + new `ticket` top-level field added.
- 3 new rules in `<rules>` block (rules 10-12).
- Origen: T-3 (2026-05-05) gate-runner Haiku 4.5 ran 707s, exhausted turn
  budget post Gate 5 of 6 without ever writing JSON. Stale T-1.bis JSON
  remained on disk → orchestrator confused. R22 verify-artifacts post-
  condition fired on absent file but agent had already returned. Fallback:
  orchestrator authored JSON manually. R29 means JSON exists from turn 1
  + cross-ticket boundary safe.

R30 — builder agents prohibit self-audit footer claims:
- `.claude/agents/builder-backend.md` + `.claude/agents/builder-agentic.md`
  + `.claude/agents/builder-frontend.md` — Last line of reply template
  REPLACED. Old: `<!-- @pm: implementación + auditoría done (verdict
  PASS). PR-{n} listo para /pm "PR-{n} cerrar" -->`. New: `<!-- @pm:
  build phase done (state: tests-passing). Commit: <SHA>. Files: <count>.
  Native ticket tests: <X>/<Y> PASS. Awaiting orchestrator → gate-runner
  → auditor-{backend|agentic|frontend} (independent verdict). -->`.
- Forbidden phrases section added: builder MUST NOT use `audit-passed`,
  `auditoría done`, `verdict PASS`, `REVIEW PASS`, `APPROVED`, or any
  phrase implying audit closure. Self-claimed verdict = orchestrator
  treats as malformed return.
- 2 checklist items removed (gate-runner + auditor-X invoked) — those
  are orchestrator's job, NOT builder's.
- Origen: T-3 (2026-05-05) builder-backend dutifully echoed contract
  footer claiming "implementación + auditoría done (verdict PASS)" —
  but builder doesn't audit. Contract WAS WRONG; agent followed it
  faithfully. Fixed contract.

R31 — auditor agents auto-prefix R25 voseo-allowed magic comment:
- `.claude/agents/auditor-backend.md` + `.claude/agents/auditor-agentic.md`
  + `.claude/agents/auditor-frontend.md` — Step `produce_review` updated.
  First line of any `06-audit/T-*-review.md` file MUST be:
  `<!-- voseo-allowed: audit review may cite spanish-text.md glosario
  verbatim per R25 (.claude/rules/spanish-text.md § Magic comment
  escape) -->`.
- Magic comment does NOT mark file as voseo-permitting for user-facing
  strings — technical escape for evidence quotation only.
- Origen: T-3 (2026-05-05) audit cited `grep -E '(podés|tenés|...)'`
  verbatim in review docstring → pre-commit hook blocked commit →
  manual escape add required. R31 amortizes the fix once-per-audit
  instead of N-times-after-the-fact (cada audit ticket re-litigates
  same magic comment placement otherwise).

**Lecciones aprendidas (cross-cutting):**

1. **"Agent prompt strength ≠ agent compliance"** — context-builder Step
   12 had clear MANDATORY language + post-condition `test -f`. Agent
   under turn pressure generated narrative that SIMULATED running the
   check ("Validator will...") instead of running it. Defense: require
   the agent to PASTE the verbatim output of the check in its final
   reply. Agent can't fake bash output (orchestrator can grep for it).

2. **"Skeleton-first generalizes beyond context-builder"** — R27 codified
   skeleton-first for context-builder generic; T-3 piloto demonstrated
   gate-runner needs SAME pattern. Pattern: any subagent writing a single
   artifact MUST write skeleton at turn 1, fill incrementally. Truncation
   cost = capped at "incomplete but valid" not "absent".

3. **"Contract templates can be wrong AND faithfully followed"** — builder
   footer template literally said "auditoría done (verdict PASS)" — a
   semantically incorrect claim because builder doesn't audit. Agent
   followed contract perfectly. Lesson: review agent contracts adversarially
   for FALSE CLAIMS that agents cannot verify (anything saying "PASS" or
   "verdict" downstream of a SEPARATE agent's job is suspect).

4. **"Pre-commit hook bypass requires escape codification, not magic"** —
   R25 magic comment exists, but every audit cycle re-discovered the
   need + manually edited the file. Fix: codify in agent contract
   (R31) so magic comment is ALWAYS first line. One-time amortization
   instead of N-times rediscovery.

5. **"Cross-ticket artifact contamination is invisible"** — gate-runner
   had iter-rename logic but only WITHIN same ticket. Cross-ticket
   pollution (T-1.bis output remained when T-3 spawned) was silent.
   R29 ticket-field check + archive prevents.

6. **"Cost-discipline trumps full re-spawn for trivial fixes"** —
   validator caught HIGH schema VARCHAR(64) → (32) discrepancy in brief.
   Could have re-spawned context-builder Haiku (~$0.20) for a 4-character
   fix. Orchestrator chose Edit + addendum-to-validation-file (~$0.05).
   Lesson: orchestrator can manually fix VERIFIED HIGH findings if the
   fix is mechanical + small + verifiable; document fallback path
   transparently in addendum.

**Token consumption esta sesión (orchestrator-only edits):**

Pure file Edit/Write operations. ~30-50k tokens estimated (post-hoc
extraction next session).

**Riesgos restantes:**

- **R28 paste-literal-bash-output** depends on agent honesty. Agents
  could in principle paste fake output. Mitigation: orchestrator can
  grep brief file for `_pending_` markers + cross-check stat output is
  plausible (file size, mtime). Future R32 if R28 gets gamed.
- **R29 skeleton-first** assumes initial JSON write succeeds. If
  pr_folder is read-only or path doesn't exist, fails immediately.
  Mitigation: gate-runner Step 0 verifies skeleton on disk before
  proceeding.
- **R30 builder footer change** doesn't enforce — orchestrator must
  GREP `verdict PASS|audit-passed|approved` in builder reply and flag.
  Could codify as orchestrator post-spawn check (R32 candidate).
- **R31 R25 magic comment** present but doesn't validate hook honors
  it. Pre-commit hook regex tested in `tests/scripts/test_pre_commit_hook.py`
  — confidence high. Future hook update needs corresponding test.

**Commits sesión:**
- (incoming) feat(harness): R28-R31 multi-layer fixes from T-3 piloto

**Fuentes consultadas:**
- T-3 cycle artifacts (CONTEXT-BRIEF.md + CONTEXT-BRIEF-validation.md +
  06-audit/T-3-review.md + gate-output.json + commit 71f39529 +
  4193cbb3)
- `.claude/agents/{context-builder,gate-runner,builder-*,auditor-*}.md`
  (8 agent prompts surveyed for layer integration)
- `.claude/rules/spanish-text.md` (R25 magic comment variants)
- `docs/process/learnings.md` 2026-05-05 entries (R1-R27 baseline)

---

## 2026-05-06 — Cierre limpio legacy outcomes (4 frentes pre paradigma-nuevo)

**Contexto:** Post pm-redesign 2026-05 Wave 4, BACKLOG mostraba Building cap saturada (3/3) + Review (1/2) con 4 outcomes/stories migrados desde paradigma legacy con `story_ids: []` vacío y artefactos retro nunca completados. Chris decisión: cerrar TODO lo legacy en motion antes de arrancar paradigma-nuevo, para no contaminar el proceso fresco con técnico-deuda histórico.

**Frentes cerrados (4):**

1. **`sales-agent-litellm-canonicalization`** (review → done)
   - 11 tickets audit-passed (T-1, T-2, T-3, T-4, T-5, T-6a, T-6b PM-ratified, T-6c, T-7, T-8, T-9). REVIEW-final + 07-merge + learnings.md story-level ya escritos en Wave 8.
   - Code COMPLETE. Migrations T-6a (commit `f6e7ad0a`) + T-6c quedan pending `/pase-produccion` deploy — Streamlit verify count(deprecated cols non-NULL)=0 post-deploy.
   - Capability `sales-observability-cost-tracking`: scenarios 4 (happy/negative/edge/adversarial) migrated. 1 gap (cost tracking accuracy) marked resolved_by, 3 gaps remain (observability dashboard, Prometheus alerts, dual-write reconciliation cron) → capability sigue `in-progress`.

2. **`pi-11-backend-quality-guardrails`** (building → done) — S1 only
   - S1 PR-1 + PR-3 + PR-4 shipped completos. PR-2 commit `6a352df2` (coverage P0 crm + scheduling) merged sin RESULT/REVIEW/IMPL-LOG → retro-fill 2026-05-06.
   - Success metrics S1 verificados: arch test `test_no_legacy_eventbus_mock_when_outbox_flag_default_on` PASS + 27 referencias EventBus.publish remaining (todas legítimas: arch tests + ratchet allowlists + cutover integration, zero productive legacy mocks).
   - S2 (coverage P1 sales_agent + copilot ≥80% + shared/links/ports tests) deferred → futuro outcome paradigma-nuevo. Outcome cerrado limpio sin scope-creep.
   - Flake detectada: `test_arch_fitness_performance_budget` (2.20s vs 2.0s budget primer run, PASS isolated). /pm decisión pendiente: relax threshold o `@pytest.mark.flaky(reruns=1)`.

3. **`pi-4-brand-evolutive-maintenance`** (building rolling → done)
   - Legacy PR-1 drop-buyer-persona-fields shipped 2026-04-29 (commits `80551ec5` BE / `00fa55b0` copilot / `d047c10b` migration / `e4df74b8` FE 2026-05-01). 24 archivos productivos + 24 regression tests (21 BE + 3 FE).
   - RESULT/REVIEW templates jamás llenados → retro-fill 2026-05-06.
   - 5 brand capabilities live + 7 brand stories live, pero `capabilities/brand/INDEX.md` con tabla vacía → flagged for R32 `reconcile_capabilities.py` regen (no manual edit per R32).
   - Outcome rolling track formalmente cerrado. Future feedback batches → outcome nuevo paradigma-nuevo, NO reabrir PI-4.

4. **`pi-5-copilot-multicanal-telegram`** (building → done) — V1 only
   - S1 magic-link (commit `c1fa2909`) + S2 orchestrator-respond (commit `d09799b9`) shipped. 86 unit tests + 9 arch fitness telegram_separation tests PASS.
   - S3 (HITL escalation sales_agent) + S4 (notifs proactivas + `copilot_owner_todos`) + S5 (arch fitness completo + observability) → deferred future outcome paradigma-nuevo.
   - Capability `copilot-telegram-channel` mantiene status=live (V1 funcional) con 5 gaps marked `defer_reason: pi-5-v1-scope-only`.
   - Success metrics reescritos honestamente: drop "≥3 tipos de encargo" + "≥70% adopción" (requerían S4 no shipped). Mantener: bot link funcional + orchestrator responde channel format + tests passing + arch fitness verde.

**Lessons cardinal (paradigma-legacy → paradigma-nuevo):**

1. **Rolling-track outcomes son trampa.** PI-4 demuestra: sin force-close criterion, retro-fill nunca ocurre y BACKLOG queda contaminado. Paradigma-nuevo: outcomes finite event-driven, exit_criteria explícitos, no rolling.
2. **`story_ids: []` vacío = leak migration.** Outcomes migrados desde legacy sin populate story_ids hacen invisible el sub-state al BACKLOG generator. Paradigma-nuevo: validar `story_ids` non-empty al transition idea→validated.
3. **Honest scope reset > rolling deferral.** PI-5 V1 only: drop S3-S5 explícitamente del scope cerrado, documentar como "future outcome", evita métricas falsas que mienten dashboard.
4. **Retro-fill artifact pattern.** Cuando legacy loop nunca cerró, `retro-fill` con marca explícita "Original loop never closed under legacy paradigm — filled 2026-05-06 for closure hygiene" + cita commits shipping = honestidad histórica sin re-litigar.
5. **Capability gaps con `defer_reason` field.** Mejor que borrar gaps o cambiar status=live silencioso: gap visible + razón visible + status honesto.
6. **`/pase-produccion` decoupling de cierre story.** litellm-canonicalization cierra story=done sin esperar deploy — code complete es el milestone, deploy es operacional separable. Permite cerrar stories cuando hay batches de migrations pendientes.

**Action items pendientes (paradigma-nuevo retoma):**
- Successor outcome para coverage P1 (PI-11 S2 deferred)
- Successor outcome para Telegram extensions (PI-5 S3-S5 deferred + 5 capability gaps)
- /pase-produccion cuando Chris decida → migrations T-6a (commit `f6e7ad0a`) + T-6c deploy
- Decisión flake `test_arch_fitness_performance_budget`

**Commits sesión:** (incoming) feat(pm): cierre limpio 4 outcomes legacy + retro-fill artifacts + paradigma-nuevo readiness

**Fuentes consultadas:**
- 4 reportes paralelos audit closure (Phase 1 agents 2026-05-06T13:57Z)
- BACKLOG.md snapshot 2026-05-06T05:04Z + outcomes/{pi-4,pi-5,pi-11}.md
- legacy archives `docs/archive/2026/legacy-pis/PI-{4,5,11}-*/`
- PI-12 active dir `docs/projects/active/PI-12-sales-agent-eval-foundation/`
- capability YAMLs: brand/, copilot/copilot-telegram-channel.yaml, sales-agent/sales-observability-cost-tracking.yaml

---
