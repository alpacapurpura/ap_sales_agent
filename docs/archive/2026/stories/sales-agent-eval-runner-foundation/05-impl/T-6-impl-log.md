# T-6 — Makefile target eval-smoke + README operability docs — Implementation log

<!-- voseo-allowed: documentation log mentions voseo glosario verbatim for technical reference (R25 escape per .claude/rules/spanish-text.md) -->

**Builder:** claude-opus-4-7 (1M ctx, agentic story mandate)
**Phase:** builder
**Surface:** agentic (docs only — no production code touched, no test files written)
**Started:** 2026-05-05 (Wave 6 spawn, post T-5 audit-passed `d5b7886a`+`e1b67e74`)
**Commit:** `01c078e4` (pushed to `origin/development` 2026-05-05, fast-forward `e1b67e74..01c078e4`)
**State on completion:** `tests-passing` (orchestrator → gate-runner → auditor-agentic for independent verdict)

---

## R24 brief acceptance gate

T-6 is pure docs. Per controller note: "no fresh CONTEXT-BRIEF — T-6 is pure
docs work, ticket spec sufficient". Builder ratifies: read directly from
`04-tickets.yaml § T-6` (lines 394-444) which carries the full deliverable
spec, acceptance verifiers, and quality gates. No brief drift risk for
docs-only ticket.

---

## Skills consulted

| Skill | Why invoked | Decision captured |
|---|---|---|
| **copilot-expert** (skill-format inline) | Loaded by orchestrator (agentic story owner). | §0 anti-duplication cardinal: T-6 introduces ZERO new abstractions. The README documents existing fixtures (T-2), runner (T-3+T-4+T-5), and YAML schema (T-5). The Makefile target wraps existing pytest invocation — no logic, no new layer. NUNCA mirror callback / cost / pricing patterns — N/A here (no code). |
| **sales-agent-expert** (skill-format inline) | Loaded by orchestrator (sales_agent surface). | §3 protected surfaces NOT touched. README references `BufferService`, `OutputManager.process_response`, compiler v2, and `sales_agent_llm_call` table only as documentation pointers — no edits to those surfaces. Voice tenant respect honored: README Spanish neutro LATAM (no voseo) since it's user-facing OPS doc, not agent output (which respects tenant voice per spanish-text.md exception). Cost budget section cites Kimi K2.6 tier pricing >200k threshold (S12 cementado) faithfully. |
| **tessl__langgraph** | NOT applicable — no graph/state/edge code touched. | — |
| **tessl__graceful-degradation** | NOT applicable — no external calls touched. | — |
| **tessl__pytest-api-testing** | NOT applicable — no pytest test files written. | — |
| **tessl__fastapi** | NOT applicable — no FastAPI routes touched. | — |

Step 0.5 default-flip detection: **N/A** — T-6 does NOT touch
`backend/src/core/config.py` defaults nor any feature flag side-effect path.

---

## Step 0 GATE — pre-implementation greps (anti-duplication audit)

```bash
# 1. Verify no existing backend/Makefile (we create it new).
$ find /home/chris/AISALESHT/backend -maxdepth 2 -name "Makefile" 2>/dev/null
→ 0 matches (clean — backend/Makefile is new, root Makefile remains intact)

# 2. Verify no existing eval-smoke target anywhere (root Makefile already
#    surveyed before edits — confirmed no eval-smoke / PROJECT_ROOT mention).
$ grep -n "eval-smoke" /home/chris/AISALESHT/Makefile 2>/dev/null
→ 0 matches

# 3. Verify --run-evals flag is registered upstream (T-2 plumbing).
$ grep -rln "addoption.*run-evals" /home/chris/AISALESHT/backend/
→ backend/tests/agentic_evals/conftest.py (T-2 canonical registration)
```

**Verdict:** anti-duplication §0 satisfied. T-6 introduces:
- 1 new file: `backend/Makefile` (8 lines functional + comments)
- 1 file rewrite: `backend/tests/agentic_evals/sales_agent/README.md`
  (extends T-1 stub from 113 to 318 lines per ticket § deliverable 2)

Zero overlap with existing infrastructure. No NEW-LAYER created (Makefile
target wraps existing pytest invocation; README purely consumes existing
fixtures+runner+YAML+observability surfaces).

---

## Cross-module systems audit (NO-NEW-LAYER per architect rule)

| Surface T-6 touches | Existing system >= 80% overlap? | Recommendation | Evidence |
|---|---|---|---|
| `backend/Makefile` (new) | NO — root Makefile is convenience wrapper for Docker+cross-stack; backend/Makefile for BE-pure ops is justified pattern | NEW (justified) | Root Makefile mixes Docker/cross-stack/E2E concerns. Adding `eval-smoke` directly to root would dilute its purpose. backend/Makefile is BE-only convenience namespace per native-first AGENTS.md |
| `README.md` rewrite | EXTENDS T-1 stub | EXTEND (per parallel-safety M8) | T-1 left stub explicitly noting "T-6 reescribe este README". Forward extension, not destroy/replace |

---

## Decision: backend/Makefile vs root Makefile (architect spec interpretation)

The 04-tickets.yaml T-6 has a structural ambiguity that needed resolution:

- **Deliverable 1 text:** "Agregar target eval-smoke al `backend/Makefile`"
- **A1 verifier:** `cd backend && make -n eval-smoke 2>&1 | grep -q 'pytest.*--run-evals'`

A1 verifier requires `cd backend && make -n eval-smoke` to succeed. Since
`make` invocation post `cd backend` looks for `backend/Makefile` (NOT root
`Makefile`), the verifier ITSELF presumes `backend/Makefile` exists.

Resolution: **create `backend/Makefile`** (new) with the eval-smoke target.
Honors both the deliverable text + A1 verifier exactly. Root Makefile
remains unmodified (its `pytest:` and `arch-test:` patterns at lines
121-138 stay as the cross-stack SSoT for general BE testing).

Trade-off acknowledged: two Makefiles in the repo could drift over time.
Mitigated by: (a) backend/Makefile header explicitly documents convivencia
with root Makefile; (b) backend/Makefile scope is BE-pure ops only (no
Docker, no cross-stack); (c) `eval-smoke` is the single target this PR
adds. Future BE-pure targets (S2 budget cap, Story 8 CI cron variants)
can land in backend/Makefile naturally without overloading root.

---

## Bitácora paso-a-paso

### 03:50 — Setup + lectura de inputs

- Read `04-tickets.yaml § T-6` (lines 394-444): deliverables 1+2, A1/A2/A3 verifiers, quality gates.
- Read existing `backend/tests/agentic_evals/sales_agent/README.md` (113-line T-1 stub).
- Read root `/home/chris/AISALESHT/Makefile` (273 lines — convenience targets for Docker+cross-stack+E2E+ETL).
- Read `goldens/visionarias-smoke-golden.yaml` to extract real schema field names + decision bindings (B2/B4/B5/B6/B7) accurately.
- Read `runner/regenerate_golden.py:15-50` to document CLI usage (`--dry-run` flag).
- Read existing fixtures via `grep` of `fixtures/__init__.py` to enumerate the 4 canonical names.
- Read `T-5-impl-log.md:24-35` to understand prior skill consultation pattern + IMPL-LOG format.

### 03:54 — Step 0 GATE skills + anti-duplication grep

- `find /home/chris/AISALESHT/backend -maxdepth 2 -name "Makefile"` → 0 matches (clean).
- `grep "eval-smoke\|PROJECT_ROOT\|tests/agentic_evals" /home/chris/AISALESHT/Makefile` → 0 matches.
- `grep -rln "addoption.*run-evals" /home/chris/AISALESHT/backend/` → confirmed T-2 registers flag at `backend/tests/agentic_evals/conftest.py`.
- Greenfield confirmed for backend/Makefile.

### 03:55 — Git status check (parallel-safety)

```
M docs/product/capabilities/brand/brand-credentials.yaml         # PM session (M8 ajeno)
M docs/product/capabilities/connections/...                      # PM session (M8 ajeno)
M docs/product/capabilities/sales-agent/...                      # PM session (M8 ajeno)
M docs/projects/active/PI-12.../CONTEXT-BRIEF.md                 # context-builder (M8 ajeno)
M docs/projects/active/PI-12.../gate-output.json                 # gate-runner (M8 ajeno)
?? docs/projects/active/PI-12.../06-audit/T-5-review.md          # auditor (M8 ajeno)
?? backend/tests/scripts/test_reconcile_capabilities.py          # PM session (M8 ajeno)
?? scripts/reconcile_capabilities.py                             # PM session (M8 ajeno)
?? docs/product/roadmap.md                                       # PM session (M8 ajeno)
```

All WIP belongs to other concurrent sessions (PM `/pm` + auditor + context-builder + gate-runner). Per parallel-safety M8: I touch ZERO of these. My PR scope is exclusively `backend/Makefile` (NEW) + `backend/tests/agentic_evals/sales_agent/README.md` (REWRITE) + `docs/projects/active/PI-12.../05-impl/T-6-impl-log.md` (NEW).

### 03:58 — Create `backend/Makefile`

Wrote 31-line Makefile with:
- `.PHONY: eval-smoke` declaration
- Header comment documenting origin (PI-12 S1 T-6 2026-05-05) + convivencia with root Makefile
- `eval-smoke` target body: `cd $(CURDIR) && .venv/bin/pytest tests/agentic_evals/sales_agent/test_eval_runner_smoke.py -v --run-evals`
- Block comment documenting pre-conditions (env var, seed, LiteLLM proxy, brain UP) + cost expectation (~$0.005/run, alert >$0.05/run)

`$(CURDIR)` resolves to `/home/chris/AISALESHT/backend` when invoked as `cd backend && make eval-smoke` — matches A1 verifier semantics exactly.

### 04:00 — A1 verifier

```bash
$ cd backend && make -n eval-smoke 2>&1
cd /home/chris/AISALESHT/backend && .venv/bin/pytest tests/agentic_evals/sales_agent/test_eval_runner_smoke.py -v --run-evals

$ cd backend && make -n eval-smoke 2>&1 | grep -q 'pytest.*--run-evals' && echo "A1 PASS"
A1 PASS
```

**A1 verifier: PASS.**

### 04:02 — Rewrite README.md

Drafted Spanish neutro LATAM rewrite covering all 8 mandatory sections per
ticket deliverable 2. First pass written without diacritics for speed; A2
verifier (which expects `Qué es`, `Cómo correr`, `Cómo agregar` with
accents) failed on first run.

Iterative tilde correction across the body (per spanish-text.md R1 — tildes
mandatory on user-facing strings):

- Section headers: `Que → Qué`, `Como → Cómo` (sections 1, 2, 3 + subsection "Que esperar → Qué esperar" + "Verificacion → Verificación").
- Body content: `documentacion → documentación`, `arquitectonico → arquitectónico`, `modulo → módulo`, `multiples → múltiples`, `unicamente → únicamente`, `tendrian → tendrían`, `seccion → sección`, `si → sí`, `razon → razón`, `pre-condicion → pre-condición`, `Verificacion → Verificación`, `distincion → distinción`, `senales → señales`, `regresion → regresión`, `explicito → explícito`, `Ubicacion → Ubicación`, `Descripcion → Descripción`, `unico → único`, `Version → Versión`, `catalogos → catálogos`, `Proposito → Propósito`, `deterministico → determinístico`, `propositos → propósitos`, `eliminara → eliminará`, `esta → está`, `metricas → métricas`, `interpolacion → interpolación`, `automatico → automático`, `accion → acción`, `canonicas → canónicas`, `via → vía`, `invocacion → invocación`, `colisionar → colisionar` (already correct), `evalua → evalúa`, `mide → mide` (already correct, but Que mide → Qué mide), `genericas → genéricas`, `tipicas → típicas`, `subira → subirá`, `actuan → actúan`, `implementacion → implementación`, `produccion → producción`, `empezo → empezó`, `subio → subió`, `vacio → vacío`, `union → unión`, `ahi → ahí`, `sesion → sesión`.

After tilde sweep, voseo regex check:

```bash
$ grep -nE '\b(vos|sos|tenés|querés|podés|sabés|hacés|venís|decís|mirá|dejá|...)\b' README.md
→ 0 matches (clean per pre-commit hook regex)
```

### 04:18 — Acceptance verifiers final run

```bash
=== A1 verifier ===
$ cd backend && make -n eval-smoke 2>&1 | grep -q 'pytest.*--run-evals'
A1 PASS

=== A2 verifier ===
$ for s in 'Qué es' 'Cómo correr' 'Cómo agregar' 'Fixtures' 'Diferencia' 'Cleanup' 'Cost budget' 'Future story'; do
    grep -q "$s" backend/tests/agentic_evals/sales_agent/README.md || exit 1
  done
A2 PASS (8/8 sections present)

=== A3 verifier ===
$ ! grep -E '\b(podés|tenés|sos|querés|hacés|configurá|seleccioná)\b' README.md
A3 PASS (no voseo)

=== Voseo full glosario (pre-commit hook regex) ===
$ ! grep -nE '<full glosario>' README.md
Voseo CLEAN
```

### 04:20 — Quality gates

```bash
$ cd backend && .venv/bin/ruff check tests/agentic_evals/ --no-cache
All checks passed!

$ cd backend && .venv/bin/ruff format --check tests/agentic_evals/
17 files already formatted

$ cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/test_eval_runner_fixtures.py -v
39 passed, 4 skipped, 1 warning in 11.81s

$ cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/ --collect-only -q
47 tests collected in 0.30s
```

All quality gates green. No regression introduced (T-6 is docs+Makefile,
no Python touched — but verified collection still works as sanity check).

---

## Files changed (PR scope)

| File | Status | LOC |
|---|---|---|
| `backend/Makefile` | NEW | 31 lines (8 functional + comments) |
| `backend/tests/agentic_evals/sales_agent/README.md` | REWRITE | 318 lines (was 113-line T-1 stub) |
| `docs/projects/active/PI-12-.../05-impl/T-6-impl-log.md` | NEW | this file |

Total: 2 production-relevant files + 1 impl log.

---

## Acceptance verifiers — Final verdict

| Verifier | Command | Result |
|---|---|---|
| **A1** | `cd backend && make -n eval-smoke 2>&1 \| grep -q 'pytest.*--run-evals'` | **PASS** |
| **A2** | for-loop checks 8 section headers in README.md | **PASS** (8/8) |
| **A3** | `! grep -E '\b(podés\|tenés\|sos\|querés\|hacés\|configurá\|seleccioná)\b' README.md` | **PASS** |

Quality gates:
- `/test-backend pass (no impact)` — meta-tests still 39 passed, 4 skipped (no regression).
- Spanish neutro check — full glosario voseo regex CLEAN.
- `make eval-smoke documentation accurate` — README documents exact command + pre-conditions + expected output, matches Makefile target body verbatim.

---

## R30 footer compliance

This builder phase output is **`tests-passing`** state only. Audit verdict
is independent — orchestrator spawns gate-runner → auditor-agentic for
the verdict. Builder MUST NOT claim `audit-passed` / `verdict PASS` /
`APPROVED` in the final reply (R30 enforcement 2026-05-05).

---

## Pending (orchestrator next steps)

1. Builder commits + pushes (this session).
2. Orchestrator spawns `gate-runner` Haiku for `/test-backend` 13 gates.
3. If gates green → orchestrator spawns `auditor-agentic` Opus for independent verdict.
4. If APPROVED → ticket transitions to `audit-passed`. Wave 8 REVIEW-final unblocks.
5. If CHANGES_REQUESTED → builder iterates within scope. Max 3 iter then escalate `/pm`.
