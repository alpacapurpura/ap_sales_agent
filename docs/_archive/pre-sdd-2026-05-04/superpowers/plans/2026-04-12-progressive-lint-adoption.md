# Progressive Lint Adoption — Execution Plan

> **Objetivo:** Eliminar TODAS las reglas del `ignore` en pyproject.toml y activar las reglas faltantes.
> **Estrategia:** Por regla, de más fácil a más difícil. Commit + remove from ignore después de cada regla.

## Wave 1: Auto-fix (ruff --fix)

| # | Regla | Count | Fix | Riesgo |
|---|-------|-------|-----|--------|
| 1a | SIM105 | 14 | `ruff --fix` | Bajo |
| 1b | B904 | 114 | `ruff --fix --unsafe-fixes` | Bajo (agrega `from e`) |
| 1c | PERF401 | 34 | `ruff --fix --unsafe-fixes` | Medio (revisar comprehensions) |

**Workflow:** fix → run tests → remove from ignore → commit.

## Wave 2: Mecánico (agentes paralelos)

| # | Regla | Count | Fix pattern |
|---|-------|-------|-------------|
| 2a | EM101 | 69 | `raise ValueError("msg")` → `msg = "msg"; raise ValueError(msg)` |
| 2b | EM102 | 47 | Same but f-strings |
| 2c | T201 | 69 | `print(...)` → `logger.info/debug(...)` |
| 2d | ERA001 | 42 | Delete commented-out code |

## Wave 3: Medio (agentes con contexto)

| # | Regla | Count | Fix pattern |
|---|-------|-------|-------------|
| 3a | UP042 | 78 | `class X(str, Enum)` → `class X(StrEnum)` + imports |
| 3b | DTZ011 | 46 | `date.today()` → timezone-aware equivalent |
| 3c | DTZ007 | 2 | `strptime()` + tz |
| 3d | N806 | 90 | Rename uppercase vars in functions to lowercase |
| 3e | N801/N802/N811/N814/N818 | 31 | Naming fixes (case by case) |

## Wave 4: Difícil (refactor)

| # | Regla | Count | Fix pattern |
|---|-------|-------|-------------|
| 4a | PLR0912 | 41 | Extract branches to methods/early returns |
| 4b | PLR0915 | 37 | Split long functions |

## Wave 5: Nivel 3 — Reglas no activadas

| # | Regla | Count | Strategy |
|---|-------|-------|----------|
| 5a | COM812 | 2366 | `ruff --fix` (auto) |
| 5b | INP001 | 236 | Create __init__.py files |
| 5c | FAST | 785 | Migrate to Annotated pattern |
| 5d | TRY | 380 | Exception patterns |
| 5e | E501 | 865 | Break long lines |
| 5f | ANN | 4698 | Add type annotations |
| 5g | D | 4526 | Add docstrings |

## After each rule

1. Run `ruff check src/ tests/ --select RULE --no-cache` → 0 errors
2. Run `ruff check src/ tests/ --no-cache` → All checks passed
3. Run `pytest -x -q --tb=short` → all pass
4. Remove rule from `ignore` list (or add to `select`) in pyproject.toml
5. Commit: `refactor: enforce RULE — <description>`
