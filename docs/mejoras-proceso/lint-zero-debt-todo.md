# Lint Zero-Debt — To-Do para Wave 2+

> Estado al 2026-04-12 después de Wave 1.
> Ejecutar en nueva conversación: "Continúa con Wave 2 del plan de lint zero-debt en `docs/superpowers/plans/2026-04-12-progressive-lint-adoption.md`"

## Resumen de lo completado (Wave 1)

| Regla | Violaciones | Status |
|-------|-------------|--------|
| B904 (raise without from) | 114 | ENFORCED |
| SIM105 (contextlib.suppress) | 14 | ENFORCED |
| EM101 (string in exception) | 69 | ENFORCED |
| EM102 (f-string in exception) | 47 | ENFORCED |
| ERA001 (commented-out code) | 42 | ENFORCED |
| PERF401 (loop → comprehension) | 34 | ENFORCED |
| T201 (print → structlog) | 69 | ENFORCED |
| **Total Wave 1** | **389** | **7 reglas enforced** |

## Wave 2: Reglas pendientes en `ignore` (~392 violaciones)

### Mecánicas (agentes paralelos)
- [ ] **UP042** (78) — `class X(str, Enum)` → `class X(StrEnum)`. Coordinar imports + tests
- [ ] **DTZ011** (46) — `date.today()` → timezone-aware. Usar `utc_now().date()`
- [ ] **DTZ007** (2) — `strptime()` sin tz
- [ ] **A002** (21) — Shadowing builtins (`type`, `id`). Renombrar parámetros
- [ ] **PT028** (22) — pytest fixture con default value
- [ ] **N814** (18) — camelCase imported as CONSTANT
- [ ] **FBT003** (6) — Boolean positional value in call
- [ ] **N818** (2) — Exception naming
- [ ] **N811** (2) — constant imported as non-constant
- [ ] **N815** (1) — mixed case variable
- [ ] **RUF002** (2) — ambiguous unicode in docstring
- [ ] **PLW0603** (1) — global statement
- [ ] **PLW2901** (2) — redefined loop var
- [ ] **PLC0206** (1) — dict index

### Refactoring (funciones complejas, requieren diseño)
- [ ] **N806** (91) — UPPER_CASE vars in functions → lower_case. Evaluar caso a caso
- [ ] **N801** (5) + **N802** (4) — Naming conventions
- [ ] **PLR0912** (40) — Too many branches (>20). Extraer a subfunciones
- [ ] **PLR0915** (37) — Too many statements. Dividir funciones
- [ ] **PLR0911** (11) — Too many return statements

## Wave 3: Reglas NO activadas (~13,712 violaciones)

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

## Stash pendiente

- `stash@{0}`: WIP channel dashboard service (6 archivos: channel_dashboard_service, metrics repos, docker-compose, frontend meta-ads tabs). Tiene conflictos con los lint fixes de Wave 1. Resolver manualmente con contexto del cambio original.

## Estrategia recomendada

1. **Wave 2 mecánicas** (~200 violaciones): UP042, DTZ*, A002, PT028, N814, FBT003 + menores — agentes paralelos
2. **Wave 2 refactoring** (~183): N806, PLR0912/0915/0911, N801/N802 — requieren diseño caso a caso
3. **Wave 3 auto-fix** (~2,574): COM812, INP001 — instantáneo
4. **Wave 3 migración** (~1,914): FAST, E501, TRY — agentes por módulo
5. **Wave 3 massive** (~9,224): ANN, D — por módulo, varias sesiones
