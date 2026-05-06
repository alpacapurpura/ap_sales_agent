# T-1-review.md — Scaffold dirs eval harness sales_agent (auditor verdict)

---
ticket_id: T-1
story_id: sales-agent-eval-runner-foundation
auditor_run: 1
audited_at: 2026-05-04T23:10:00Z
auditor_model: claude-opus-4-7
verdict: APPROVED
self_fix_applied: false
escalation_reason: null
---

## Resumen 1-frase

T-1 entrega scaffolding puro (4 dirs + 4 `__init__.py` vacíos + `_artifacts/.gitignore` + `goldens/.gitkeep` + README stub Spanish neutro) para que T-2..T-6 implementen el harness `sales_agent` agentic eval. Todo verificado: estructura, gitignore funcional, README con cobertura completa de scope/costo/`--run-evals`/goldens versionados/T-2..T-6 listados, lint clean, pytest collect-only limpio, scope discipline (cero archivos fuera de `backend/tests/agentic_evals/` y `docs/projects/.../sales-agent-eval-runner-foundation/`).

## Acceptance verification (re-corrido por auditor)

| ID | Criterio | Re-verified | Resultado |
|---|---|---|---|
| A1 | 4 dirs existen (runner/fixtures/_artifacts/goldens) | `ls -la` confirma 4 subdirs presentes | ✅ |
| A2 | `_artifacts/*` gitignored | `touch test-ignore.txt && git check-ignore -v` → `_artifacts/.gitignore:1:* test-ignore.txt` | ✅ |
| A3 | README.md y `__init__.py` files existen | `ls` confirma README.md (4778 bytes) + 4× `__init__.py` (0 bytes) + `goldens/.gitkeep` | ✅ |

## Quality gates re-corridos

```
$ cd backend && .venv/bin/ruff check tests/agentic_evals/ --no-cache
All checks passed!

$ cd backend && .venv/bin/ruff format --check tests/agentic_evals/
4 files already formatted

$ cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/ --collect-only -q --override-ini="addopts="
no tests collected in 0.29s   # exit 5, esperado para scaffold (0 tests)

$ git show 9ffae2ce --stat
backend/tests/agentic_evals/__init__.py            |   0
backend/tests/agentic_evals/sales_agent/README.md  | 113 ++++++   (real: 113 líneas, README excede los 95 estimados — más completo, mejor)
backend/tests/agentic_evals/sales_agent/__init__.py
backend/tests/agentic_evals/sales_agent/_artifacts/.gitignore     | 2
backend/tests/agentic_evals/sales_agent/fixtures/__init__.py
backend/tests/agentic_evals/sales_agent/goldens/.gitkeep
backend/tests/agentic_evals/sales_agent/runner/__init__.py
docs/projects/.../04-tickets.yaml                  | 433 +++
docs/projects/.../05-impl/T-1-impl-log.md          | 129 +++
docs/projects/.../05-impl/T-1-result.md            | 146 +++
docs/projects/.../checkpoint.md                    |  42 +-
11 files changed, 851 insertions(+), 14 deletions(-)
```

Nota: NO se corrió `/test-backend` full ni `make ci-parity` — T-1 es scaffolding puro (sin Python operacional). T-2 será el primer ticket que justifique full suite. Auditor ratifica esa decisión del builder.

## 10 checks scored

### Check 1 — Directory structure exact ✅ PASS

Per `03-arch-be.md` § "Estructura de directorio" — todos los 4 subdirs presentes (`runner`, `fixtures`, `_artifacts`, `goldens`), todos los 4 `__init__.py` vacíos creados, `.gitkeep` en `goldens` para tracking, `.gitignore` en `_artifacts`. Estructura match 1:1.

### Check 2 — `_artifacts/.gitignore` contents ✅ PASS

```
$ cat backend/tests/agentic_evals/sales_agent/_artifacts/.gitignore
*
!.gitignore
```

Pattern correcto: `*` ignora todo, `!.gitignore` excluye explicitamente al gitignore mismo (robustez). Verifier dinámico:
```
$ touch _artifacts/test-ignore.txt
$ git check-ignore -v _artifacts/test-ignore.txt
backend/tests/agentic_evals/sales_agent/_artifacts/.gitignore:1:* test-ignore.txt
```
Confirmado: cualquier archivo en `_artifacts/` queda ignorado, `.gitignore` permanece tracked.

Nota menor: ticket YAML deliverable §5 dice contenido `*` (sin negación). Builder eligió `*\n!.gitignore` (más robusto, 2 líneas vs 1). Implementation valid — A2 verifier passes igual y el patrón es estándar en este repo. **No bloqueante.**

### Check 3 — README.md content quality ✅ PASS

113 líneas (builder estimó 95, entregó 113 — más completo). Cubrió todos los puntos requeridos:
- L9-13: harness cubre **únicamente** sales_agent (otros agentes harness hermano).
- L25-30: costo real por smoke ≈ **USD 0.005** (deepseek-v4-flash via LiteLLM).
- L29-30: `pytest --run-evals` flag gatea ejecución; sin flag → `SKIPPED`.
- L57-63: goldens en YAML versionado bajo git (decisión B7).
- L46-50: pre-condiciones tenant Visionarias canonical seed (DB + LiteLLM proxy + `VISIONARIAS_TENANT_ID`).
- L88-95: T-2..T-6 pila pendiente con scope cada uno.
- L17-22: diferencia con `tests/quality/sales_agent_goldens/` (S10 LLM-as-judge weekly stub) explícita — anti-confusión post-merge.
- L98-101: cleanup `_artifacts/` documented.
- L104-113: out-of-scope futuras stories listadas (Pass^k Story 2, budget cap Story 3, voice grader Story 7, etc.).

Spanish neutro: sin voseo. Verificado regex `\b(podés|tenés|sos|querés|hacés|venís|decís|mirá|dejá|poné|usá|hacé|elegí|seleccioná|arrancá|empezá|agregá|configurá|revisá|escribí|guardá|abrí|volvé|cambiá)\b` → 0 matches reales. Match único `reescribe` (línea 4) es 3ª persona singular formal del verbo `reescribir` ("T-6 reescribe este README" = "T-6 will rewrite this README"), NO voseo.

### Check 4 — Lint clean ✅ PASS

```
$ ruff check tests/agentic_evals/  → All checks passed!
$ ruff format --check tests/agentic_evals/  → 4 files already formatted
```

### Check 5 — Pytest collection clean ✅ PASS

```
$ pytest tests/agentic_evals/sales_agent/ --collect-only -q --override-ini="addopts="
no tests collected in 0.29s
```

Exit code 5 = "no tests collected" (esperado para scaffold). Warning único de `src/core/config.py:9` (Pydantic v1 ConfigDict deprecation) es **pre-existente** del codebase, NO introducido por T-1.

### Check 6 — Scope discipline ✅ PASS

`git show 9ffae2ce --stat` confirma exclusivamente:
- 7 archivos NEW en `backend/tests/agentic_evals/` (scaffold)
- 4 archivos en `docs/projects/active/.../sales-agent-eval-runner-foundation/` (04-tickets.yaml, checkpoint.md, 05-impl/T-1-result.md, 05-impl/T-1-impl-log.md)

Cero toques a:
- `backend/src/modules/copilot/` ✅
- `backend/src/modules/sales_agent/` ✅
- `backend/src/shared/` ✅
- Story A files (`docs/projects/active/.../sales-agent-litellm-canonicalization/`) ✅
- Otros módulos `backend/src/modules/*` ✅

### Check 7 — Anti-duplication ✅ PASS

Builder ejecutó Step 0 GATE grep (documentado en `T-1-impl-log.md` § 22:32):
- `find /home/chris/AISALESHT/backend -path '*/agentic_evals*'` → vacío pre-T-1 (greenfield confirmed).
- `tests/quality/sales_agent_goldens/` co-existe pero **distinto propósito** (S10 LLM-as-judge weekly cron, no invoca agente real). README línea 18-22 documenta diferencia explícita.
- Auditor re-verificó: `find tests -type d -name "*eval*"` → solo `agentic_evals/` (NEW) + `tests/quality/deepeval/` (pre-existente, sin colisión semántica).

Sin mirror de pattern shared (zero Python operacional para mirror). Cat 12 anti-duplication clean.

### Check 8 — Story B 04-tickets.yaml T-1 state ✅ PASS

`04-tickets.yaml` línea 19: `state: tests-passing` — refleja realidad (commit local hecho, push diferido por controller).

Transitions log (líneas 109-112) registra:
- `draft @ 2026-05-05T03:40Z by /architect`
- `building @ 2026-05-04T22:30Z by dev-team-opus`
- `tests-passing @ 2026-05-04T22:55Z by dev-team-opus`

Próximo cambio de state → `audit-passed` post este review.

### Check 9 — Spanish neutro check (README.md) ✅ PASS

Ya verificado en Check 3. Regex voseo (incluye `tenés/podés/sos/querés/hacés/sabés/mirá/dejá/poné/usá/hacé/elegí/agregá/configurá/revisá/escribí/guardá/abrí/volvé/cambiá/seleccioná/arrancá/empezá`) → 0 matches reales. README usa neutro (`reescribe` 3ª persona, `popula` 3ª persona, `cubre` 3ª persona, etc.).

### Check 10 — PR-folder hygiene ✅ PASS

| Artefacto | Existe | Lleno (no stub) |
|---|---|---|
| `05-impl/T-1-result.md` | ✅ 158 líneas | ✅ resumen + acceptance + diff + quality gates output literal + skills consultadas + anti-duplication grep + commits + notas auditor + riesgos |
| `05-impl/T-1-impl-log.md` | ✅ 130 líneas | ✅ plan inicial + skills (Step 0 GATE) + bitácora paso-a-paso (22:30→22:54) + decisiones + tests corridos + cross-module reads + commits + estado cierre |
| `checkpoint.md` updated | ✅ `phase: DEV_T1_DONE` | ✅ línea 4 + bitácora 2026-05-04 22:55 (línea 25) + próximo paso "/auditor revisa T-1" |

## Code review categories

### Cat 1 — DDD inside-out ✅ NA
T-1 sin Python operacional. No layers tocados.

### Cat 2 — Tenant isolation ✅ NA
T-1 sin queries.

### Cat 3 — Master data + currency ✅ NA
T-1 sin DTOs/datetimes.

### Cat 4 — Migrations ✅ NA
T-1 sin migration (arch-be § "Migrations" → "None").

### Cat 5 — Spanish neutro UI ✅ PASS
README sin voseo, sin léxico marcado, tildes/¿/¡ correctos donde aplica.

### Cat 6 — PII ✅ NA
T-1 sin response model ni payload sanitizable.

### Cat 7 — Test coverage + quality ✅ NA
T-1 sin tests (scaffold). Suite eval queda fuera de `[tool.coverage.run].source` (decisión architect — coverage 43% gate intacto).

### Cat 8 — Anti-duplication ✅ PASS
Greenfield confirmed (Step 0 GATE grep evidence en impl log + result + commit body). README diferencia explícitamente vs `tests/quality/sales_agent_goldens/` (S10 weekly judge).

### Cat 9 — Code quality ✅ PASS
Naming consistente (`_artifacts` snake_case, `runner/fixtures/goldens` lowercase). Sin `# noqa`. Sin TODO. README estructura clara con headers nivel 2.

### Cat 10 — Architecture fitness ✅ NA
T-1 NO toca `src/`. Arch fitness gates intactos. Allowlists no modificadas.

### Cat 11 — Documentation ✅ PASS
README stub completo + impl log + result.md exhaustivos. Builder anota explícitamente "T-6 reescribe completo" para evitar deuda doc oculta. Commit body conventional con bloques claros (deliverables/quality gates/anti-duplication/skills consultadas).

### Cat 12 — Mirror detection ✅ PASS
Builder declaró Step 0 GATE en impl log + result. Auditor re-verificó: greenfield, README documenta co-existencia con S10 stub. Sin mirror de pattern shared.

### Cat 13 — Default flip side-effect coverage ✅ NA
T-1 no toca `core/config.py` ni feature flags. Builder marcó explícitamente "Step 0.5 GATE: N/A" en impl log línea 36-37.

## Self-fix log

❌ N/A — verdict APPROVED en run 1, sin necesidad de self-fix.

## Findings

Sin findings bloqueantes. Notas menores (no bloqueantes):

- **Note 1 (informativo)**: builder eligió `*\n!.gitignore` para `_artifacts/.gitignore` (vs el `*` literal del ticket YAML deliverable §5). Cambio justificado en impl log línea 64-66 — más robusto, no rompe verifier A2. **Aceptado.**
- **Note 2 (informativo)**: README de 113 líneas vs estimación 95 del result.md. Builder entregó más completo, no menos. **Aceptado.**

## Verdict

**APPROVED** ✅

Razón: los 3 acceptance criteria verificados (A1/A2/A3 PASS), quality gates verdes (ruff check + ruff format + pytest collect-only), code review 13 categorías OK (la mayoría NA por scaffolding-only, las relevantes PASS), Spanish neutro confirmado, scope discipline impecable (cero contaminación cross-story / cross-módulo), anti-duplication greenfield documentado, PR-folder hygiene completa (result + impl-log + checkpoint actualizado).

Iteración 1/2 — no se requiere segunda pasada.

## Output al orchestrator

```
APPROVED -> docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/S1-eval-runner/stories/sales-agent-eval-runner-foundation/06-audit/T-1-review.md
ticket state: audit-passed
ready to launch: T-2 builder Story B
```
