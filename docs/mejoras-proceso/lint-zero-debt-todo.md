# Lint Zero-Debt — To-Do para Wave 4+

> Estado al 2026-04-13 después de Wave 3.
> Waves 1-3 completas: 29 reglas enforced, ~660 fixes, 0 violaciones en `ruff check`.

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

### Wave 3 (2026-04-13) — 5 reglas, ~97 fixes (49 files)
| Regla | Violaciones | Fix | Status |
|-------|-------------|-----|--------|
| N801 (class name) | 5 | TestStep*_ → TestStep* (CapWords) | ENFORCED |
| N802 (function name) | 4 | OPENAI_MODEL→openai_model, DATABASE_URL→database_url | ENFORCED |
| PLR0911 (return stmts) | 11 | Dispatch dicts, extract helpers (19→5 in _validate_section) | ENFORCED |
| PLR0912 (branches) | 37 | Dispatch dicts, guard clauses, extract helpers | ENFORCED |
| PLR0915 (statements) | 37 | Extract private methods (236→<50 in chat.py orchestrator) | ENFORCED |

Scripts (`src/scripts/`) and test helpers exempted via per-file-ignores.
PT028 already in permanent ignore since Wave 2.

### Wave 3b (2026-04-13) — 2 reglas, ~2,578 fixes (527 files)
| Regla | Violaciones | Fix | Status |
|-------|-------------|-----|--------|
| COM812 (trailing commas) | 2,349 | `ruff --fix`, luego movido a permanent ignore (conflicto con ruff format) | ENFORCED via format |
| INP001 (missing __init__.py) | 236 | 66 __init__.py creados (src/tests/ exempted) | ENFORCED |

**Total Wave 1+2+3:** 31 reglas enforced + INP, ~3,240 fixes, **0 violations remaining in `ruff check`**

## Wave 4: Audit-Ready — Plan detallado

> Plan completo: `docs/superpowers/plans/2026-04-13-lint-wave4-audit-ready.md`
>
> Prompt: "Ejecuta Wave 4 del lint audit-ready. Plan: `docs/superpowers/plans/2026-04-13-lint-wave4-audit-ready.md`"

### Resumen por fase

| Fase | Reglas | Violaciones | Esfuerzo |
|------|--------|-------------|----------|
| 0: Zero-effort | 10 categorias con 0 violaciones | 0 | 5 min |
| 1: Quick fixes | DTZ005, RUF013, NPY, PYI, PTH, TD, FIX | ~138 | 3h |
| 2: Medium | FAST, BLE, G, TRY, E501 | ~2,286 | 24h (3-4 sesiones) |
| 3: Massive | ANN, D | ~9,441 | Sprints dedicados |
| 4: Hardening | mccabe 15, cleanup per-file-ignores | ~26 | 2h |

### Global ignore audit (17 reglas)
- **13 permanentes:** B008, PLC0415, PLR2004, PLR0913, ARG001, ARG002, RUF001, RUF012, RET504, UP017, PT028, ISC001, COM812
- **2 format conflicts:** ISC001, COM812
- **3 graduables:** DTZ005 (7), FBT001 (61), FBT002 (33)

### Objetivo audit-ready
- 42+ categorias activas (actual: 31+INP)
- mccabe max-complexity: 15 (actual: 20)
- 0 violaciones globales
- <14 reglas en ignore global (todas justificadas)
- Type coverage: 50%+ (actual: ~30%)
- Docstring coverage: 40%+ (actual: ~20%)
