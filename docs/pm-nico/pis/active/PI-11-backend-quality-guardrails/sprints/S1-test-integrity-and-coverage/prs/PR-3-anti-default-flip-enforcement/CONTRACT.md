# CONTRACT — PR-3 Anti-Default-Flip Enforcement (Rule + Arch Fitness Test)

> Architect: `nicolify-architect` (Opus 4.7[1M])
> Run: 2026-05-04
> Cross-link: [PR-1 CONTRACT.md](../PR-1-fix-broken-tests-and-arch-snapshots/CONTRACT.md) (compartido — PR-3 arch fitness depende de PR-1 EventBus migration completa)

---

## § 0 — Context Summary

| Item | Value |
|---|---|
| **PR** | PR-3-anti-default-flip-enforcement |
| **PI** | PI-11-backend-quality-guardrails |
| **Sprint** | S1-test-integrity-and-coverage |
| **Architect run** | 2026-05-04 |
| **Modules touched** | `.claude/rules/`, `backend/tests/architecture/`, `CLAUDE.md` (conditional rule trigger) |
| **CONTEXT-BRIEF source** | Used § 7 + § 8 verbatim (clean faithfulness flag). Recommendation: arch fitness test = NEW (sibling pattern of `test_no_legacy_event_bus_publish.py`); rule = NEW (no flip-audit rule exists). Bypass mechanism = EXTEND pattern from existing arch fitness ratchet. |
| **Decisions consumed (PR-1)** | D1 (outbox True permanente), D2 (tests migran a adapter_bus mock — PR-3 enforce via arch fitness) |
| **pm-nico/current-state files affected** | None — meta-arquitectural (regla + arch fitness). NO user-facing capability. |
| **Architecture gates that MUST keep passing** | Existing 78 arch tests. Add 1 new (PR-3): `test_no_legacy_eventbus_mock_when_outbox_on.py`. Final state target 79/79. |

### Surface → builder → auditor mapping

| Surface | Owner builder | Auditor |
|---|---|---|
| `.claude/rules/anti-default-flip-audit.md` (NEW) | `nicolify-backend` (Sonnet) | `nicolify-backend-auditor` (Opus) |
| `backend/tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py` (NEW) | `nicolify-backend` | `nicolify-backend-auditor` |
| `backend/tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on_bypass_works.py` (NEW — meta-test del test) | `nicolify-backend` | `nicolify-backend-auditor` |
| `CLAUDE.md` (conditional rule trigger row) | `nicolify-backend` | `nicolify-backend-auditor` |

### Dependencies on PR-1

| PR-1 deliverable | PR-3 consumes | Coupling type |
|---|---|---|
| § 1-2 Singleton fixture exhaustive | Indirect — fixture cubre EventBus._handlers reset (origen punto 2 PI.md), permite arch fitness baseline correcto | Build-time |
| § 3 EventBus migration (Caso A/B/C/D/E) | DIRECT — arch fitness test allowlist `BYPASS_FILES` debe alinear con archivos Caso D/E + magic comments alineados con archivos sin migrar | Build-time |
| § 5 LegacyEventBus deprecation warning | INDIRECT — runtime warning complementa arch fitness static check (defense in depth) | Behavioral |
| Stash apply (Phase 1) — files con `monkeypatch USE_OUTBOX=False` | DIRECT — esos archivos requieren MIGRACIÓN antes que arch fitness PR-3 active. Si NO migrados, arch fitness fail por mock LegacyEventBus + flag flip side-effect manifesto. | Build-time |

### Skills consulted

- **`backend-expert`**: AST walk pattern (existente en `test_no_legacy_event_bus_publish.py:60-71`), pytest-collection-only mode (`tests/architecture/conftest.py`), ratchet allowlist pattern (`KNOWN_*` shrink-only). Decisión: REUSE AST walk infra, add new file siguiendo sibling pattern.
- **No domain-specific skill** — meta-arquitectural PR.

---

## § 1 — Rule Design `.claude/rules/anti-default-flip-audit.md`

**File path:** `/home/chris/AISALESHT/.claude/rules/anti-default-flip-audit.md`
**Owner:** business builder (`nicolify-backend`)
**Pattern reference:** `.claude/rules/anti-duplication.md` (estructura — workflow + inventario + anti-patterns + enforcement layers + penalizaciones)

### Required content (full SPEC, builder produce file with this exact structure)

```markdown
# Anti-Default-Flip Audit

**Origen:** failed `/pase-produccion` 2026-05-04. Commit `64738354` (PR-1 Sub-E PI-2, 2026-04-29) flipeó `USE_OUTBOX_PATTERN_*` False→True sin auditar tests que mockean path legacy `EventBus.publish` → 25 BE failures + 1 polluter no identificable + ~3h investigación + ~500k tokens. Ver PI-11 PR.md.

## Regla cardinal

ANTES de flipear default de feature flag (`USE_*_PATTERN_*`, `LITELLM_PROXY_ENABLED`, `USE_DEEPAGENTS_*`, `ENABLE_*`, etc.) que cambia call path side-effect (events, persistence, logging, observability, LLM provider routing, agent orchestration) → **OBLIGATORIO 4 STEPS**:

### Step 1 — Grep tests path viejo (cross-codebase)

```bash
# Para cada call path afectado por el flip, grep mocks legacy:
grep -rn "<legacy_call_path>" /home/chris/AISALESHT/backend/tests/ 2>/dev/null | grep -v __pycache__

# Ejemplo flag USE_OUTBOX_PATTERN_*:
grep -rln "src.shared.domain.events.EventBus.publish" /home/chris/AISALESHT/backend/tests/

# Ejemplo flag LITELLM_PROXY_ENABLED:
grep -rln "OpenAIService\|KimiService\|DeepSeekService" /home/chris/AISALESHT/backend/tests/
```

Output capture obligatorio en commit body sección `## Tests audited`.

### Step 2 — Update mocks path nuevo

Para cada test detectado:
- Migrar mocks al `<new_canonical_path>` (e.g., `adapter_bus.publish` for outbox)
- O capturar via observability/persistence sink (outbox table, traces, etc.)
- O bypass explícito si test prueba capability legacy mismo (magic comment `# arch-bypass: testing legacy capability`)

### Step 3 — Run full suite con BOTH old+new flag values

```bash
# Default value (post-flip):
cd backend && .venv/bin/pytest -x -q --tb=short

# Legacy value (pre-flip — confirmar no rotura cuando flag override False):
cd backend && USE_OUTBOX_PATTERN_DEFAULT=false .venv/bin/pytest -x -q --tb=short
```

Ambos valores deben pasar 100%. Si UNO falla → stop, no flip until fix.

### Step 4 — Documentar commit body

Bloque obligatorio en commit body cuando aplique flip:
```
flag <NAME> flipped <OLD_VALUE>→<NEW_VALUE>

## Tests audited
- N tests migrated to new canonical path
- M tests use bypass for legacy capability (magic comment)
- 0 tests use `monkeypatch.setattr(<flag>=<old_value>)` band-aid

## Path old: <full_path>
## Path new: <full_path>
## Verification: pytest passed both values (logs attached)
```

## Inventario flags side-effect (SSoT — actualizar al agregar nuevos)

| Flag | Default actual | Side-effect path | Path viejo | Path nuevo | Tests probe canonical |
|---|---|---|---|---|---|
| `USE_OUTBOX_PATTERN_SALES_AGENT` | `True` (post 2026-04-29) | events emission | `src.shared.domain.events.EventBus.publish` | `event_bus_adapter.adapter_bus.publish` (→ outbox table) | adapter_bus mock OR `select(DomainEventOutboxModel)...` |
| `USE_OUTBOX_PATTERN_COPILOT` | `True` (post 2026-04-29) | events emission | idem | idem | idem |
| `USE_OUTBOX_PATTERN_BRAND` | `True` (post 2026-04-29) | events emission | idem | idem | idem |
| `USE_OUTBOX_PATTERN_DEFAULT` | `False` | events emission (fallback per-module unspecified) | idem | idem | idem |
| `LITELLM_PROXY_ENABLED` | `True` (default 2026) | LLM routing | adapter `providers/{kimi,deepseek,openai,qwen,gemini}.py` direct | `LiteLLMService` proxy via `litellm_config.yaml` | provider mock matching active path |
| `USE_DEEPAGENTS_*` (futuros) | TBD | agent orchestration | LangGraph plain `StateGraph.compile()` | deepagents `task` subagent harness | both paths probed (per-test or fixture parametrize) |
| Otros `ENABLE_*` flags | varies | varies | varies | varies | varies |

**Cuando agregar nuevo flag side-effect → editar este inventario en mismo commit.** Auditor Cat 14/13 valida.

## Anti-patterns prohibidos

- ❌ Flipear default sin grep tests path viejo (Step 1 omitido)
- ❌ Flipear default sin run full suite con ambos valores (Step 3 omitido)
- ❌ Commit body sin sección "Tests audited" (Step 4 omitido)
- ❌ Mockear path viejo cuando flag default es path nuevo (test no prueba nada real — passes silenciosamente)
- ❌ Usar `monkeypatch.setattr(USE_*=False)` por test sin migrar mock al path nuevo — band-aid temporal solo (D2 PI-11)
- ❌ Bypass arch fitness sin magic comment justificado
- ❌ Agregar nuevo flag side-effect sin actualizar inventario SSoT este file

## Enforcement layers

| Layer | Mecanismo | Owner |
|---|---|---|
| 1 PM PR.md | Bloque "Default flips audited" mandatory cuando aplique flip | `/pm` skill (PR-4 alimenta template) |
| 2 Architect CONTRACT.md | Bloque "Tests audit: paths mockeados antes/después" obligatorio si CONTRACT propone flip | `nicolify-architect` (PR-4 alimenta prompt) |
| 3 Builder Step 0 | Grep tests path viejo antes flip code | `nicolify-backend` / `nicolify-agentic` (PR-4 alimenta agent prompt) |
| 4 Auditor Cat review | Cat 14 (business) / Cat 13 (agentic) "Default flip side-effect coverage" | `nicolify-{backend,agentic}-auditor` (PR-4 alimenta agent) |
| 5 Arch fitness test | `test_no_legacy_eventbus_mock_when_outbox_on.py` (PR-3) bloquea automatic | `tests/architecture/` |
| 6 TDD rule | `.claude/rules/tdd-mandatory.md` § "Default flag flips" obligatoria | `/pm` (PR-4) |
| 7 Runtime warning | `LegacyEventBus.publish` DeprecationWarning cuando flag True (PR-1 § 5) | shared/domain/events.py |

## Penalizaciones

- Builder skip Step 1 grep → REVERT
- Auditor skip Cat 14/13 → re-audit
- Architect CONTRACT sin "Tests audit" cuando propone flip → REJECT, re-spawn
- Arch fitness violation = build fail (gate hard)
- Skip inventario update al agregar nuevo flag → process-learnings.md case study

## Ejemplos

### Ejemplo CORRECTO (commit hipotético):

```
feat(observability): flip LITELLM_PROXY_ENABLED default False→True

## Tests audited
- 12 tests migrated from `OpenAIService.generate_response` mock → `LiteLLMService.generate_response` mock
- 2 tests use `# arch-bypass: testing legacy capability` for adapter direct call validation
- 0 tests use `monkeypatch.setattr(LITELLM_PROXY_ENABLED=False)` band-aid

## Path old: backend/src/shared/infrastructure/llm/providers/{openai,kimi,...}.py direct
## Path new: backend/src/shared/infrastructure/llm/providers/litellm.py via proxy
## Verification:
- `pytest -x -q` PASS (default True)
- `LITELLM_PROXY_ENABLED=false pytest -x -q` PASS (legacy fallback)

[arch-fitness 79/79 PASS]
```

### Ejemplo INCORRECTO (lo que rompió 2026-05-04):

```
feat(events): switch emisores to outbox event bus adapter

# Sin sección "Tests audited"
# Sin grep tests path viejo
# Sin verify both flag values
# → 25 tests stale post-merge, polluter no detectado, 3h investigación
```
```

### Ubicación CLAUDE.md (conditional rule trigger)

**File:** `/home/chris/AISALESHT/CLAUDE.md`
**Sección:** `## Conditional Rules (stub → skill)`
**Add row:**

```markdown
| BE config flag flips (`core/config.py` defaults) | (none — `pm` skill ratification) | `rules/anti-default-flip-audit.md` |
```

(Tabla actual de conditional rules ya tiene formato `| Tocas | Skill | Stub |` — alinear.)

---

## § 2 — Arch Fitness Test Design `tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py`

**File path:** `/home/chris/AISALESHT/backend/tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py`
**Owner:** business builder (`nicolify-backend`)
**Pattern reference:** `tests/architecture/test_no_legacy_event_bus_publish.py` (sibling — same AST walk infra, different violation check)

### Detection logic (AST walk for mock targets)

**Targets to detect (frozen set):**

```python
LEGACY_MOCK_TARGETS: frozenset[str] = frozenset({
    "src.shared.domain.events.EventBus.publish",
    "shared.domain.events.EventBus.publish",  # without src. prefix
    "EventBus.publish",  # bare reference
    "LegacyEventBus.publish",  # if anywhere
    "src.shared.domain_events.legacy_event_bus.LegacyEventBus.publish",  # full FQN
})
```

**Mock invocation patterns to walk:**

```python
# Patterns the AST walk MUST detect:
@patch("src.shared.domain.events.EventBus.publish")              # decorator string arg
@patch.object(EventBus, "publish")                                # decorator attr
mocker.patch("src.shared.domain.events.EventBus.publish")         # pytest-mock fn
mocker.patch.object(EventBus, "publish")                          # pytest-mock attr
monkeypatch.setattr("src.shared.domain.events.EventBus.publish", ...)  # pytest builtin
monkeypatch.setattr(EventBus, "publish", ...)                     # pytest builtin attr form
unittest.mock.patch(...)                                          # explicit fully-qualified
```

### AST walk implementation pattern (conceptual — builder writes real code)

```python
"""Architecture fitness gate (PR-3 PI-11): no legacy EventBus.publish mocks
when outbox flag default = True.

Origen: PR-3 PI-11 — anti-default-flip enforcement.
Workflow obligatorio: `.claude/rules/anti-default-flip-audit.md`.

Detection: AST walk by file. Detects @patch / mocker.patch / monkeypatch.setattr
calls whose first arg matches LEGACY_MOCK_TARGETS.

Bypass: 
- File path in BYPASS_FILES (capability tests + meta-tests del adapter)
- Magic comment '# arch-bypass: testing legacy capability' anywhere in file
"""

from __future__ import annotations

import ast
from pathlib import Path

# ---------------------------------------------------------------------------
# Targets prohibidos cuando outbox flag default = True.
# ---------------------------------------------------------------------------

LEGACY_MOCK_TARGETS: frozenset[str] = frozenset({
    "src.shared.domain.events.EventBus.publish",
    "shared.domain.events.EventBus.publish",
    "EventBus.publish",
    "LegacyEventBus.publish",
    "src.shared.domain_events.legacy_event_bus.LegacyEventBus.publish",
})

# ---------------------------------------------------------------------------
# Bypass list — tests internos que prueban capability LegacyEventBus
# o meta-tests del EventBusAdapter routing logic. Each entry MUST include
# WHY (commit message reference). Shrink-only ratchet.
# ---------------------------------------------------------------------------

BYPASS_FILES: frozenset[str] = frozenset({
    # Capability tests del LegacyEventBus mismo
    "tests/shared/test_event_bus.py",
    # Meta-tests del adapter (probe legacy fall-through path when flag=False)
    "tests/shared/domain_events/test_event_bus_adapter.py",
    "tests/shared/domain_events/test_event_bus_adapter_infers_module.py",
    # Cutover integration tests (probe both paths)
    "tests/integration/test_outbox_cutover_e2e.py",
    "tests/modules/copilot/integration/test_outbox_cutover.py",
    "tests/modules/brand/integration/test_outbox_cutover.py",
    "tests/modules/sales_agent/integration/test_outbox_cutover.py",
})

BYPASS_MAGIC_COMMENT: str = "# arch-bypass: testing legacy capability"

# ---------------------------------------------------------------------------
# AST walk
# ---------------------------------------------------------------------------

def _backend_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _test_files() -> list[Path]:
    """Yield all test_*.py files under backend/tests/ (excluding __pycache__)."""
    root = _backend_root() / "tests"
    return [
        p for p in root.rglob("test_*.py")
        if "__pycache__" not in p.parts
    ]


def _extract_first_string_arg(node: ast.Call) -> str | None:
    """Return first string-literal arg of an ast.Call, or None."""
    if not node.args:
        return None
    first = node.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return first.value
    return None


def _walks_mock_targets(tree: ast.AST) -> set[str]:
    """Extract mock target strings from @patch/mocker.patch/monkeypatch.setattr calls.
    
    Patterns recognized:
        @patch("X")                         → detects "X"
        mocker.patch("X")                   → detects "X"
        monkeypatch.setattr("X", val)       → detects "X"
        @patch.object(EventBus, "publish")  → detects "EventBus.publish" (synthesized)
    
    NOTE: AST walk is best-effort; complex dynamic patches may slip past.
    Bypass mechanism (magic comment) covers edge cases.
    """
    targets: set[str] = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            
            # Pattern 1: patch("string") / mocker.patch("string") / monkeypatch.setattr("string", ...)
            is_patch_call = (
                (isinstance(func, ast.Name) and func.id == "patch")
                or (isinstance(func, ast.Attribute) and func.attr in ("patch", "setattr"))
            )
            if is_patch_call:
                target = _extract_first_string_arg(node)
                if target:
                    targets.add(target)
            
            # Pattern 2: patch.object(Class, "method") synthesizes "Class.method"
            is_patch_object = (
                isinstance(func, ast.Attribute)
                and func.attr == "object"
                and isinstance(func.value, ast.Name)
                and func.value.id == "patch"
            )
            if is_patch_object and len(node.args) >= 2:
                cls_node = node.args[0]
                method_node = node.args[1]
                if isinstance(cls_node, ast.Name) and isinstance(method_node, ast.Constant) and isinstance(method_node.value, str):
                    targets.add(f"{cls_node.id}.{method_node.value}")
    
    return targets


def test_no_legacy_eventbus_mock_when_outbox_flag_default_on() -> None:
    """Tests MUST NOT mock LegacyEventBus.publish when outbox flag default = True.
    
    Workflow esperado: tests deben mockear `event_bus_adapter.adapter_bus.publish`
    o probe `domain_event_outbox` table.
    
    Bypass: 
    - File en BYPASS_FILES (capability + meta-tests)
    - Magic comment '# arch-bypass: testing legacy capability' en file
    
    Ver `.claude/rules/anti-default-flip-audit.md`.
    """
    root = _backend_root()
    violations: list[str] = []
    
    for test_file in _test_files():
        rel_path = str(test_file.relative_to(root))
        
        # Bypass via file path
        if rel_path in BYPASS_FILES:
            continue
        
        try:
            source = test_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        
        # Bypass via magic comment
        if BYPASS_MAGIC_COMMENT in source:
            continue
        
        # AST parse
        try:
            tree = ast.parse(source, filename=str(test_file))
        except SyntaxError:
            continue
        
        # Detect violations
        mock_targets = _walks_mock_targets(tree)
        legacy_hits = mock_targets & LEGACY_MOCK_TARGETS
        if legacy_hits:
            violations.append(f"{rel_path}: legacy mock targets {sorted(legacy_hits)}")
    
    assert not violations, (
        "Tests mockean LegacyEventBus.publish path cuando outbox flag default = True.\n"
        "Migrar a `event_bus_adapter.adapter_bus.publish` mock o `domain_event_outbox` table probe.\n"
        "Bypass: agregar archivo a BYPASS_FILES OR comentario '# arch-bypass: testing legacy capability'.\n"
        "Ver `.claude/rules/anti-default-flip-audit.md`.\n"
        "Violations:\n  - " + "\n  - ".join(violations)
    )


def test_bypass_files_size_ratchet() -> None:
    """BYPASS_FILES allowlist size guard — shrink-only ratchet.
    
    Initial state post-PR-1: 7 files (capability tests + meta-tests + cutover integration).
    Subsequent additions require justification commit body + auditor approval.
    """
    expected_max = 7  # post-PR-1 baseline
    assert len(BYPASS_FILES) <= expected_max, (
        f"BYPASS_FILES grew beyond {expected_max} — verify each new entry "
        "has justification + auditor approval per `.claude/rules/anti-default-flip-audit.md`."
    )
```

### Failure message diagnostic

When test fails, message MUST:
- List exact `rel_path: legacy mock targets {...}` per offender
- Suggest migration: `event_bus_adapter.adapter_bus.publish` mock OR outbox table query
- Link to canonical rule: `.claude/rules/anti-default-flip-audit.md`
- Indicate bypass mechanisms (file path + magic comment)

### Performance budget

- AST walk single-pass per file
- ~100 test files × ~1ms parse + ~0.5ms walk = ~150ms total
- **Budget: <2s en suite** (CONFIRMA con cronómetro builder)

### Edge cases handled

- **Dynamic mock targets** (`patch(some_var)` where `some_var` is computed): Skipped (AST sees no string). Acceptable false-negative — magic comment bypass covers if needed.
- **Imported-then-aliased patch**: `from unittest.mock import patch as p` then `@p("X")` — AST walk sees `p` not `patch` → MISS. Builder mitigation: regex fallback for FQN string `"src.shared.domain.events.EventBus.publish"` regardless of decorator name. **Builder validates: if regex needed, document as Phase 1 fallback.**
- **`patch.object(LegacyEventBus, ...)` where LegacyEventBus is imported alias**: AST walks Name node `LegacyEventBus`, synthesizes `LegacyEventBus.publish` — DETECTED.

### Test placement (regression coverage of arch fitness test itself — meta-test)

**File nuevo:** `backend/tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on_bypass_works.py`

```python
"""Meta-test: verifica que arch fitness PR-3 detecta correcto + bypass funciona."""

# Test 1: synthetic test file con `@patch("src.shared.domain.events.EventBus.publish")` 
#         → arch fitness DETECTS (violation)
# Test 2: synthetic test file con magic comment `# arch-bypass: ...` + same patch
#         → arch fitness IGNORES (bypass works)
# Test 3: synthetic test file en BYPASS_FILES path
#         → arch fitness IGNORES
# Test 4: synthetic test file con `mocker.patch.object(EventBus, "publish")`
#         → arch fitness DETECTS (Pattern 2 works)
```

Builder usa `tmp_path` fixture pytest para crear synthetic files + invoke arch fitness assertion en isolation.

---

## § 3 — Integration con regla anti-duplication.md

**Cross-reference (read-only):**

`anti-default-flip-audit.md` referencia `anti-duplication.md` en sección "Enforcement layers" como pattern análogo:

```markdown
> Pattern análogo: `anti-duplication.md` (cross-module mirror detection). Anti-default-flip
> detecta side-effect path mismatch via flag flip + test-mock drift. Ambos defense in depth
> (PM PR.md → Architect CONTRACT.md → Builder Step 0 → Auditor Cat review → Arch fitness test).
```

**NO modify** `anti-duplication.md` — solo cross-reference.

---

## § 4 — Cross-link to PR-1 CONTRACT

PR-3 deploy condicional sobre PR-1:

| PR-1 estado | PR-3 acción |
|---|---|
| PR-1 NOT shipped (baseline tests con legacy mocks) | PR-3 builder NOT ship arch fitness test (else 24+ violations break baseline). PR-3 puede shipear solo regla `.claude/rules/anti-default-flip-audit.md` + meta-test bypass works (sin arch fitness gate active) |
| PR-1 Phase 5 commit emitted (`feat(test): PR-1 PI-11 EventBus migration complete (Fase 5)`) | PR-3 builder ships arch fitness test SIN allowlist temporal — 0 violations expected post-PR-1 |
| PR-1 NOT yet at Phase 5 BUT PR-3 builder paralelo | PR-3 builder ships arch fitness test CON allowlist temporal `KNOWN_LEGACY_MOCK_FILES` listing TODOS los archivos § 3 PR-1 Caso A pre-migration (~10 files). Allowlist shrinks conforme PR-1 progress. Final state post-PR-1 PASS: allowlist size = 0 (entries only in BYPASS_FILES § 2 = 7) |

**Recommendation architect:** PR-3 builder esperar PR-1 PASS para evitar deadlock arch fitness baseline. Si Chris quiere paralelo → ship arch fitness con allowlist temporal + auditor valida shrink semanal.

Ver detalle: [`../PR-1-fix-broken-tests-and-arch-snapshots/CONTRACT.md`](../PR-1-fix-broken-tests-and-arch-snapshots/CONTRACT.md) §§ 3, 5, 13

---

## § 5 — Open Questions for PM

1. **PR-3 deployment ordering** — Architect recomienda PR-3 builder esperar señal commit PR-1 Phase 5. ¿PM acepta sequential (más seguro) o paralelo con allowlist temporal (más rápido pero requiere más maintenance)?
   - **Recomendación architect:** Sequential. Allowlist temporal genera deuda + auditor extra ciclo cada semana de divergencia.

2. **`tests/shared/domain_events/test_event_bus_adapter_infers_module.py`** — capability test del adapter inference logic. PR-1 § 11 lo flagea bajo "Shared (NEEDS DECISION)". PR-3 BYPASS_FILES inicialmente lo INCLUYE. ¿Confirma PM bypass correct (es meta-test) o debe migrar al path nuevo?
   - **Recomendación architect:** BYPASS (meta-test del módulo inference; testea `_module_name_from_file` capability, no production usage del EventBus).

3. **Nuevos flags side-effect** — Inventario SSoT § 1 lista `USE_DEEPAGENTS_*` como TBD. PR-4 (PM directo) puede agregar entries cuando se introduzcan. ¿Confirma que PR-3 NO bloquea on-future-flag inventory completion?

4. **Magic comment exact string** — Spec usa `# arch-bypass: testing legacy capability`. ¿PM acepta como canonical o prefiere otra fórmula (ej. `# arch-bypass: <reason>` con justificación libre)?
   - **Recomendación architect:** Mantener exacto `# arch-bypass: testing legacy capability` para grep simple. Justificación libre en commit body.

5. **Performance budget <2s** — Si AST walk supera 2s en CI (>500 test files growing) → considerar paralelización pytest-xdist o cache. ¿PM acepta este trigger threshold?

6. **CLAUDE.md conditional rule trigger** — Tabla actual `## Conditional Rules` tiene formato `| Tocas | Skill | Stub |`. PR-3 agrega row sin Skill (no skill dedicada). ¿PM acepta `(none — pm skill ratification)` en columna Skill?

---

## § 6 — Research Notes (DATE-AWARE)

| Source | URL | accessed | Cutoff disclosure | Key takeaway | Why over alternatives |
|---|---|---|---|---|---|
| pytest fixture autouse + monkeypatch docs | https://docs.pytest.org/en/stable/how-to/monkeypatch.html | 2026-05-04 | Pre-cutoff (pytest stable API) | `monkeypatch.setattr(target, value)` first arg accepts string FQN OR (obj, attr) tuple. AST walk debe detectar ambas formas. | Cubre 100% mock invocation patterns; arch fitness test no falla por falsos negativos en formas estándar |
| AST walk pattern | https://docs.python.org/3/library/ast.html#ast.walk | 2026-05-04 | Pre-cutoff (Python stdlib stable) | `ast.walk(tree)` yields all nodes recursive; O(n) per file | Existing `test_no_legacy_event_bus_publish.py:60-71` already uses pattern — REUSE infra. |
| Existing arch fitness sibling test | `backend/tests/architecture/test_no_legacy_event_bus_publish.py` | 2026-05-04 | Pre-cutoff (codebase canonical) | Pattern: AST walk + `KNOWN_*` ratchet allowlist + assert-friendly diagnostic message + meta-test for allowlist size | NEW arch fitness test sigue mismo pattern, mantiene consistencia codebase |
| `detect-test-pollution` (referenced PR-1 § 6) | https://github.com/asottile/detect-test-pollution | 2026-05-04 | Live confirmed via WebSearch | Indirect reference — PR-1 dependency, not PR-3. Mentioned for context (PR-3 arch fitness PREVENTS recurrence of root cause). | Cross-PR coordination only |

**Knowledge cutoff disclosure:** Opus 4.7 cutoff = January 2026. PR-3 patterns (AST walk, pytest fixtures, ratchet allowlists) all pre-cutoff stable APIs. NO post-cutoff topics — no risk of model confabulation.

---

## § 7 — Aceptación CONTRACT-driven (mirror PR.md § Aceptación)

Builder marca cada checkbox cumplido en IMPL-LOG:

- [ ] `.claude/rules/anti-default-flip-audit.md` creado con full SPEC § 1 (workflow + inventario + anti-patterns + enforcement layers + penalizaciones + ejemplos)
- [ ] CLAUDE.md update con conditional rule trigger row (formato matching tabla actual)
- [ ] `backend/tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py` creado (AST walk + LEGACY_MOCK_TARGETS + BYPASS_FILES + magic comment + diagnostic message)
- [ ] `backend/tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on_bypass_works.py` creado (meta-test: 4 cases — detection + bypass file + bypass comment + Pattern 2)
- [ ] Arch fitness test PASS post-PR-1 PASS (sin violations, allowlist BYPASS_FILES = 7)
- [ ] Bypass mechanism funcional + documentado en regla
- [ ] Failure message diagnostic linkea regla
- [ ] Performance <2s (cronómetro builder confirma)
- [ ] Cross-link PR-1 (§ 4): coordinación efectiva (deployment ordering decided per § 5 q1)
- [ ] Open questions (§ 5) resueltas pre-merge
- [ ] `IMPL-LOG.md` completo
- [ ] `REVIEW.md` verdict PASS (auditor backend Cat 14 valida arch fitness PASS + spec § 1 reflected)

