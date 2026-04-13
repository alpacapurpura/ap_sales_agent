# Lint Zero-Debt — To-Do para Wave 3+

> Estado al 2026-04-13 después de Wave 2.
> Ejecutar en nueva conversación: "Continúa con Wave 3 del plan de lint zero-debt en `docs/mejoras-proceso/lint-zero-debt-todo.md`"

## Resumen de lo completado

### Wave 1 (2026-04-12) — 7 reglas, ~389 fixes
| Regla | Violaciones | Status |
|-------|-------------|--------|
| B904 (raise without from) | 114 | ENFORCED |
| SIM105 (contextlib.suppress) | 14 | ENFORCED |
| EM101 (string in exception) | 69 | ENFORCED |
| EM102 (f-string in exception) | 47 | ENFORCED |
| ERA001 (commented-out code) | 42 | ENFORCED |
| PERF401 (loop → comprehension) | 34 | ENFORCED |
| T201 (print → structlog) | 69 | ENFORCED |

### Wave 2a — Quick Wins (2026-04-13) — 12 reglas, ~30 fixes
| Regla | Fix | Status |
|-------|-----|--------|
| DTZ003 (utcnow) | 0 violations (already clean) | ENFORCED |
| DTZ006 (fromtimestamp) | 0 violations | ENFORCED |
| DTZ007 (strptime tz) | 2 → `.replace(tzinfo=UTC)` in GA4 | ENFORCED |
| PERF203 (try in loop) | 0 violations | ENFORCED |
| N818 (exception naming) | ConnectionRevokedException→Error, TokenRefreshFailed→Error | ENFORCED |
| N811 (const import) | UUID alias removed | ENFORCED |
| N814 (camelCase import) | test conftest aliases cleaned | ENFORCED |
| N815 (mixedCase var) | who_is_NOT_for → snake_case + alias | ENFORCED |
| RUF002 (ambiguous unicode) | × → x in docstrings | ENFORCED |
| PLW0603 (global) | → functools.lru_cache | ENFORCED |
| PLW2901 (loop var) | renamed in Shopify/Offer repos | ENFORCED |
| PLC0206 (dict items) | → .items() in GA4 | ENFORCED |

### Wave 2b — StrEnum (2026-04-13) — 1 regla, 78 fixes
| Regla | Fix | Status |
|-------|-----|--------|
| UP042 (StrEnum) | `ruff --fix --unsafe-fixes` across 19 files | ENFORCED |

### Wave 2c — Medium (2026-04-13) — 4 reglas, ~65 fixes
| Regla | Fix | Status |
|-------|-----|--------|
| FBT003 (bool positional) | Form(False)→Form(default=False) | ENFORCED |
| N806 (uppercase vars) | Renamed 12 local UPPER_CASE vars (tests exempted) | ENFORCED |
| A002 (builtin shadowing) | type→type_, id→id_, range→range_ + Query(alias=...) | ENFORCED |
| DTZ011 (date.today) | Added utc_today() helper, replaced 26 usages (tests exempted) | ENFORCED |

**Total Wave 1+2:** 24 reglas enforced, ~560 fixes

## Wave 3: Reglas pendientes en `ignore` (~124 violaciones en src/)

### Refactoring complejo (requieren diseño caso a caso)
- [ ] **PLR0912** (40) — Too many branches (>20). Extraer subfunciones, early returns
- [ ] **PLR0915** (38) — Too many statements. Dividir funciones grandes
- [ ] **PLR0911** (12) — Too many return statements. Simplificar lógica

### Naming (evaluar caso a caso)
- [ ] **N801** (6) — Invalid class name
- [ ] **N802** (5) — Invalid function name (test_ endpoints en FastAPI)

### False positive (mantener en ignore permanente)
- [ ] **PT028** (22) — pytest fixture default → 100% false positives (FastAPI `test_connection` endpoints con `Depends()`)

## Wave 4: Reglas NO activadas (~13,712 violaciones)

### Auto-fix posible
- [ ] **COM812** (2,338) — Trailing commas. `ruff --fix --select COM812`
- [ ] **INP001** (236) — Missing `__init__.py`. Crear archivos vacíos

### Migración masiva (agentes por módulo)
- [ ] **FAST** (785) — FastAPI endpoints sin `Annotated`. Migrar `Depends(x)` → `Annotated[T, Depends(x)]`
- [ ] **E501** (857) — Lines >88 chars. Mix de auto-fix y manual
- [ ] **TRY** (272) — Exception patterns (TRY003, etc.)

### Massive (miles, requieren estrategia)
- [ ] **ANN** (4,698) — Type annotations en todo el codebase
- [ ] **D** (4,526) — Docstrings en todo el codebase

## Estrategia recomendada para Wave 3

1. **PT028 → Mover a permanent ignores** — son 100% false positives (FastAPI endpoints con `test_` prefix)
2. **N801 + N802 (11)** — evaluar caso a caso, probablemente movibles a permanent ignore
3. **PLR0912 + PLR0915 + PLR0911 (~90)** — refactoring real. Priorizar por módulo:
   - analytics/ (mayor concentración)
   - connections/ (varios providers)
   - admin/ (Streamlit pages — ya ignorados en per-file-ignores)
