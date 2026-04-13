# Wave 4: Lint Audit-Ready — Plan de ejecucion completo

> **Prompt para nueva conversacion:**
> "Ejecuta Wave 4 del lint audit-ready. Plan: `docs/superpowers/plans/2026-04-13-lint-wave4-audit-ready.md`"

## Estado actual (post Wave 3)

- **31 categorias** en `select`
- **17 reglas** en `ignore` global (15 permanentes + 2 format conflicts)
- **0 violaciones** en `ruff check`
- **2264 tests** pasando, 0 skip real
- **ruff format** clean en 1003 archivos
- **mccabe max-complexity:** 20 (0 violaciones)

## Objetivo Wave 4

Llevar el proyecto a un nivel que pase una **auditoria de calidad de codigo por expertos**.
Eso significa:
1. Activar TODAS las categorias de ruff que apliquen al stack
2. Documentar y justificar cada regla ignorada permanentemente
3. Reducir el mccabe threshold a 15 (industria standard: 10)
4. Eliminar toda deuda que sea mecanicamente fixeable

---

## Fase 0: Zero-effort wins (activar reglas con 0 violaciones)

Agregar a `select` sin ningun cambio en codigo:

```toml
"YTT",   # flake8-2020: sys.version checks
"ASYNC", # flake8-async: async patterns
"FA",    # flake8-future-annotations
"ICN",   # flake8-import-conventions
"Q",     # flake8-quotes
"SLOT",  # flake8-slots
"TID",   # flake8-tidy-imports
"INT",   # flake8-gettext
"T10",   # flake8-debugger
"EXE",   # flake8-executable
```

**Accion:** Agregar al select, correr `ruff check`, verificar 0 violaciones, commit.

---

## Fase 1: Quick fixes (7-50 violaciones, esfuerzo bajo)

### 1a. DTZ005 — `datetime.now()` sin timezone (7 violaciones)

Actualmente en `ignore` global. Solo 7 instancias restantes.

```bash
ruff check src/ --select DTZ005 --no-cache
```

Fix: Reemplazar `datetime.now()` con `datetime.now(UTC)` o `utc_now()` de `shared/domain/datetime_utils.py`.
Despues de fixear: **remover DTZ005 del ignore global**.

### 1b. RUF013 — Implicit Optional (45 violaciones)

Actualmente en `ignore` global. Fix mecanico con unsafe-fix.

```bash
ruff check src/ --select RUF013 --no-cache --statistics
# Fix: ruff check src/ --select RUF013 --fix --unsafe-fixes
```

Fix: `str | None = None` es lo que queda. Overlap con UP045 (ya enforced).
Verificar que no rompe nada, despues: **remover RUF013 del ignore global**.

### 1c. NPY — NumPy deprecated (3 violaciones)

```bash
ruff check src/ --select NPY --no-cache
```

Fix: Migrar `np.random.seed()` a `np.random.default_rng()` o similar.
**Agregar NPY a `select`.**

### 1d. PYI — Stub files (2 violaciones)

```bash
ruff check src/ --select PYI --no-cache
```

Fix: 1 auto-fixable, 1 manual. Trivial.
**Agregar PYI a `select`.**

### 1e. PTH — Pathlib migration (50 violaciones)

```bash
ruff check src/ --select PTH --no-cache --statistics
```

Fix: `os.path.join()` -> `Path()`, `os.path.exists()` -> `Path.exists()`, etc.
**Agregar PTH a `select`.**

### 1f. TD + FIX — TODO format (20 + 11 = 31 violaciones)

```bash
ruff check src/ --select TD,FIX --no-cache --statistics
```

Fix: Agregar links a issues, o convertir TODOs a items en `docs/mejoras-proceso/to-do.md`.
**Agregar TD,FIX a `select`.**

---

## Fase 2: Medium effort — reglas de alta calidad

### 2a. FAST — FastAPI Annotated migration (787 violaciones)

La regla mas importante para un proyecto FastAPI moderno.

```bash
ruff check src/ --select FAST --no-cache --statistics
# 756 FAST002 (Depends → Annotated[T, Depends()])
#  31 FAST001 (no-response-model — ya enforced por arch tests)
```

**Estrategia:** Agentes paralelos por modulo:
1. `analytics/` (~150 endpoints)
2. `connections/` (~80 endpoints)
3. `sales_agent/` (~60 endpoints)
4. `brand/` + `offer/` (~100 endpoints)
5. `iam/` + `crm/` + `copilot/` + `landing/` + `scheduling/` + `advertising/` (~200 endpoints)

Cada agente:
```bash
ruff check src/modules/{module}/ --select FAST --fix --unsafe-fixes
# Luego verificar manualmente que la typing funciona
pytest tests/modules/{module}/ -x -q
```

**FAST001** (31 violaciones): Estos son endpoints sin `response_model`. Algunos ya tienen arch fitness tests que lo detectan (allowlist). Consolidar la allowlist con las violaciones de FAST001 para tener un solo tracking.

**Agregar FAST a `select`.** FAST001 puede ir al per-file-ignores de archivos especificos o al allowlist del arch test.

### 2b. BLE — Blind except (264 violaciones)

```bash
ruff check src/ --select BLE --no-cache --statistics
# BLE001: blind except (bare `except:` or `except Exception:`)
```

**Alta prioridad para auditoria.** Cada `except Exception` debe especificar la excepcion esperada.

**Estrategia:** Agentes por modulo. Para cada `except Exception as e`:
1. Identificar que excepciones puede lanzar el bloque try
2. Reemplazar con excepciones especificas
3. Si es genuinamente "catch-all" (ej: top-level en un worker), agregar `# noqa: BLE001` con comentario

**Agregar BLE a `select`.** Meta: <30 noqa.

### 2c. G — Logging format (103 violaciones)

```bash
ruff check src/ --select G --no-cache --statistics
# G004: f-string in logging call (94)
# G201: logging .exception with exc_info (9)
```

Fix:
- `logger.info(f"message {var}")` -> `logger.info("message %s", var)` o `logger.info("message", var=var)` (structlog)
- `logger.error(..., exc_info=True)` -> `logger.exception(...)`

**Nota:** El proyecto usa `structlog` que acepta kwargs: `logger.info("msg", key=value)`. NO usar `%s` formatting con structlog — usar kwargs.

**Agregar G a `select`.**

### 2d. TRY — Exception patterns (276 violaciones)

```bash
ruff check src/ --select TRY --no-cache --statistics
# TRY003: long message in raise (169 — unsafe-fixable)
# TRY301: raise in try (24)
# TRY400: logging.error in except with exc_info (22)
# TRY002: raise vanilla Exception (30)
# etc.
```

**Estrategia:**
- TRY003 (169): `raise ValueError("long message")` -> usar variables para mensajes, o crear custom exceptions
- TRY002 (30): Crear excepciones especificas en `domain/` de cada modulo
- TRY301 (24): Restructurar para evitar raise dentro de try
- TRY400 (22): `logger.error(exc_info=True)` -> `logger.exception()`

**Agregar TRY a `select`.** TRY003 puede tener allowlist temporal.

### 2e. E501 — Line length (856 violaciones)

```bash
ruff check src/ --select E501 --no-cache --statistics
```

**El mas tedioso.** Muchas son strings largos, URLs, imports.

**Estrategia:**
1. `ruff check --fix` arregla ~200 automaticamente (line breaks en imports, etc.)
2. El resto son strings largos, asserts, URLs — evaluar caso a caso
3. Considerar subir `line-length` a 120 (muy comun en proyectos FastAPI) en vez de los 88 default

**Agregar E501 a `select` (o subir line-length a 120 y agregar).**

---

## Fase 3: Massive — sprints dedicados

### 3a. ANN — Type annotations (4,862 violaciones)

```bash
ruff check src/ --select ANN --no-cache --statistics
# ANN001: missing function arg type (2,150)
# ANN002: missing *args type (85)
# ANN003: missing **kwargs type (78)
# ANN201: missing return type (public) (1,738)
# ANN202: missing return type (private) (811)
```

**Estrategia de audit:**
1. Activar ANN con allowlist por modulo (ratchet pattern como arch tests)
2. Nuevos archivos DEBEN tener type annotations
3. Sprint de anotacion por modulo (estimado: 2-3 dias por modulo con agentes)
4. Considerar `mypy --strict` como objetivo final

### 3b. D — Docstrings (4,579 violaciones)

```bash
ruff check src/ --select D --no-cache --statistics
# D100: missing module docstring (168)
# D101: missing class docstring (116)
# D102: missing method docstring (1,098)
# D103: missing function docstring (1,122)
# D104: missing __init__.py docstring (178)
# D200-D415: format issues (rest)
```

**Estrategia de audit:**
1. Configurar `[tool.ruff.lint.pydocstyle]` con convention = "google"
2. Fase A: D100+D104 (module/init docstrings) — rapido
3. Fase B: D101 (class docstrings) — medium
4. Fase C: D102+D103 (method/function) — massive, agentes por modulo
5. Fase D: Format rules — auto-fixable mayormente

### 3c. SLF — Private member access (263 violaciones)

```bash
ruff check src/ --select SLF --no-cache --statistics
# SLF001: private member access (263)
```

Muchas son accesos internos validos (ej: `self._repo._session`). Evaluar modulo por modulo.
Considerar mover a permanent ignore si >80% son internos.

---

## Fase 4: Hardening — mccabe y per-file-ignores

### 4a. Reducir mccabe max-complexity

| Target | Funciones que fallan | Esfuerzo |
|--------|---------------------|----------|
| 20 (actual) | 0 | DONE |
| 15 | 3 (commercial_calendar, home_dashboard, email_dashboard_service) | Bajo |
| 12 | ~10 | Medium |
| 10 (industria) | ~26 | Alto — objetivo largo plazo |

**Accion Wave 4:** Bajar a 15. Fixear las 3 funciones, commit.
**Accion futura:** Bajar a 12, luego 10 en sprints posteriores.

### 4b. Limpiar per-file-ignores debt

Los per-file-ignores mas relevantes para auditoria:

| Scope | Rule | Count | Accion |
|-------|------|-------|--------|
| `src/admin/**` | PLR0911/0912/0915 | 21 | Mantener — Streamlit pages, no DDD |
| `src/scripts/**` | PLR0912/0915 | 1 | Mantener — scripts one-shot |
| `tests/**` | S101 | 4,353 | **Correcto** — assert en tests es standard |
| `tests/**` | PLR2004 | 793 | Mantener — magic values en assertions |
| `tests/**` | ARG | 290 | Mantener — fixtures |
| `tests/**` | N806 | 80 | Mantener — `MockClient = MagicMock()` |
| `tests/**` | DTZ011 | 20 | **Podria fixear** — `date.today()` en tests |
| `tests/**` | PLR0912 | 1 | Mantener — test helper |

**Accion:** Solo DTZ011 en tests podria limpiarse (20 fixes). El resto es correcto.

---

## Inventario de ignore global — Justificacion para auditores

```toml
# === JUSTIFICADOS — false positives para FastAPI/DDD/Spanish stack ===
"B008"     # Depends()/Header()/Query() en defaults — patron standard FastAPI. 652 usos.
"PLC0415"  # Imports condicionales — evitan circular imports en DDD modular. 383 usos.
"PLR2004"  # Valores magicos en comparaciones — demasiado ruidoso, bajo valor. 194 usos en src/.
"PLR0913"  # Muchos args en funciones — constructores DDD y endpoints FastAPI. 145 usos.
"ARG001"   # Arg no usado en funciones — dependencias FastAPI, contratos de interfaz. 45 usos.
"ARG002"   # Arg no usado en metodos — implementaciones de interfaz. 80 usos.
"RUF001"   # Unicode ambiguo — texto en espanol en prompts es intencional. 37 usos.
"RUF012"   # ClassVar mutable — Pydantic maneja esto correctamente. 44 usos.
"RET504"   # Variable innecesaria antes de return — preferencia de legibilidad. 21 usos.
"UP017"    # datetime.UTC alias — proyecto prefiere timezone.utc explicito. 22 usos en src/.
"PT028"    # pytest fixture default — false positive en endpoints FastAPI test_*. 22 usos.

# === FORMAT CONFLICTS — ruff format los maneja ===
"ISC001"   # Implicit string concat — conflicto con ruff format
"COM812"   # Trailing comma — conflicto con ruff format

# === GRADUABLES — podrian removerse con esfuerzo ===
"DTZ005"   # datetime.now() sin tz — solo 7 instancias restantes. FACIL.
"FBT001"   # Bool positional arg — 61 usos. MEDIUM. Migrar a keyword-only.
"FBT002"   # Bool default value — 33 usos. MEDIUM. Igual que FBT001.
```

---

## Orden de ejecucion recomendado

| Paso | Fase | Reglas | Violaciones | Esfuerzo | Commit |
|------|------|--------|-------------|----------|--------|
| 1 | 0 | 10 zero-effort rules | 0 | 5 min | Si |
| 2 | 1a | DTZ005 un-ignore | 7 | 15 min | Si |
| 3 | 1b | RUF013 un-ignore | 45 | 30 min | Si |
| 4 | 1c-1f | NPY, PYI, PTH, TD, FIX | ~86 | 2h | Si |
| 5 | 4a | mccabe 20→15 | 3 | 30 min | Si |
| 6 | 2c | G (logging) | 103 | 2h | Si |
| 7 | 2d | TRY (exceptions) | 276 | 4h | Si |
| 8 | 2b | BLE (blind except) | 264 | 4h | Si |
| 9 | 2a | FAST (Annotated) | 787 | 8h | Si, por modulo |
| 10 | 2e | E501 (line length) | 856 | 6h | Si |
| 11 | 3a | ANN (type annotations) | 4,862 | Sprint | Parcial |
| 12 | 3b | D (docstrings) | 4,579 | Sprint | Parcial |

**Pasos 1-5:** Una sesion (~3h). Resultado: 37 categorias activas, mccabe 15.
**Pasos 6-10:** 2-3 sesiones (~24h). Resultado: 42+ categorias, ~0 violaciones.
**Pasos 11-12:** Sprints dedicados. Resultado: full audit-ready.

---

## Metricas objetivo para pasar auditoria

| Metrica | Actual | Wave 4 target | Industry standard |
|---------|--------|---------------|-------------------|
| Ruff categories active | 31 | 42+ | All applicable |
| Ruff violations | 0 | 0 | 0 |
| mccabe max-complexity | 20 | 15 → 12 | 10 |
| Type annotation coverage | ~30% | 50%+ | 90%+ |
| Docstring coverage | ~20% | 40%+ | 80%+ |
| Test coverage | untested | 70%+ | 80%+ |
| Per-file-ignores | 12 entries | 8 entries | <5 |
| Global ignores | 17 rules | 14 rules | <10 |

---

## Notas para el ejecutor

1. **Siempre verificar** despues de cada cambio: `ruff check + ruff format --check + pytest`
2. **Nunca agregar `# noqa`** sin justificacion en el commit message
3. **El ratchet pattern** funciona: un allowlist que solo encoge, nunca crece
4. **FBT001/FBT002** son los mas debatibles — si el auditor no los exige, mantener en ignore
5. **SLF001** es el menos valioso — muchos accesos internos son validos en DDD
6. **E501** es el mas tedioso — considerar subir line-length a 120 como alternativa practica
7. **ANN y D** son los mas grandes — no intentar en una sesion, planificar como proyecto
