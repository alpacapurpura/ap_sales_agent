# Analytics Coverage Sprint 2026 — Progress Tracker

**Target:** 85% (≥6771/7931 stmts covered)
**Baseline:** 59.7% (7966 stmts pre-Fase 0)
**Last measured:** 60.89% (7931 stmts, 3102 missing) — post Fase 0-2

---

## Phase Status

| Fase | Descripción | Estado | Cobertura al cerrar |
|------|-------------|--------|---------------------|
| 0 | Dead code + tests triviales | ✅ DONE | 61% |
| 1 | Foundation (conftest, factories) | ✅ DONE | 61% (habilitador) |
| 2 | Stage repositories 0% → 94% | ✅ DONE | 60.89% (3102 missing) |
| 3 | ETL pipelines críticos | ⏳ PENDING | — |
| 4 | Stage services cache-miss paths | ⏳ PENDING | — |
| 5 | Servicios secundarios | ⏳ PENDING | — |
| 6 | API HTTP-level | ⏳ PENDING | — |

---

## Commits relevantes

| Hash | Contenido |
|------|-----------|
| `0c6c9b2e` | Fases 0-2: dead code delete + repos stage 0%→94% |

---

## Lo que se hizo en Fases 0-2

### Fase 0 — Dead code eliminado
- `backend/src/modules/analytics/infrastructure/engines/rfm.py` — eliminado (21 stmts, 0 call-sites)
- `backend/src/modules/analytics/infrastructure/engines/scoring.py` — eliminado (14 stmts, 0 call-sites)
- `backend/src/modules/analytics/infrastructure/engines/__init__.py` — eliminado
- Net effect: –35 denominador (7966→7931 stmts)

### Fase 0 — Tests triviales creados
- `backend/tests/modules/analytics/test_campaign_entities.py` — 6 StrEnums, 14 tests
- `backend/tests/modules/analytics/test_journey_event.py` — JourneyEvent Pydantic, 7 tests

### Fase 1 — Foundation
- `backend/tests/factories/analytics.py` — 4 factories: `OfficialMetricFactory`, `ExtractionRunFactory`, `PeriodMetricFactory`, `MetricAggregationFactory`
- `backend/tests/modules/analytics/conftest.py` — agregado `seed_official_metrics()` helper

### Fase 2 — Stage repositories 0% → cubiertos
- `test_opportunity_repository.py` — `OpportunityMetricsRepository` (52 stmts → 94%)
- `test_expansion_repository.py` — `ExpansionMetricsRepository` (40 stmts → 100%)
- `test_adoption_repository.py` — `AdoptionMetricsRepository` (33 stmts → 100%)
- `test_evangelization_repository.py` — `EvangelizationRepository` (88 stmts → 94%)

---

## Patrones aprendidos

### MagicMock session pattern (repos con PostgreSQL-specific SQL)
```python
def _make_repo():
    session = MagicMock()
    session.execute.return_value.scalar.return_value = 0
    session.execute.return_value.all.return_value = []
    session.execute.return_value.first.return_value = (0, 0, 0, 0, None)
    return Repo(session), session
```
**Por qué**: repos con `jsonb_extract_path_text`, `func.extract("epoch")`, etc. no corren en SQLite.
**Regla**: usar 5-tupla en `first()` cuando el método accede índices 0-4 en distintos ramas.

### Multiple sequential execute() calls
```python
# Dos queries con valores distintos:
session.execute.return_value.scalar.side_effect = [val1, val2]
session.execute.return_value.all.side_effect = [list1, list2]
```

### Async methods con session sync interna
- `get_evangelization_data()` es `async def` pero usa `self.db.execute()` (sync).
- Funciona con `asyncio_mode=auto` — el coroutine corre, las llamadas sync dentro completan normal.
- Tests: `async def test_*(self)` sin `@pytest.mark.asyncio` necesario.

### 5-tuple pitfall
- `_compute_k_factor` accede `result[0]` y `result[1]` del `first()`
- `_get_nps_summary` accede `result[0]` hasta `result[4]`
- Si se comparte el mock de `first()`, usar la tupla más larga: `(0, 0, 0, 0, None)`

### Parallel session safety
- Otro Claude Code trabaja en `sales_agent/` en la misma rama `development`
- Siempre `git add path/to/file` por nombre explícito
- NUNCA `git add .` / `-A` / `-u`
- Revisar `git status` antes de commit — ignorar archivos ajenos

### Variable no usada en test (RUF059)
```python
# MAL:
repo, session = _make_repo()  # session no se usa → RUF059 error

# BIEN:
repo, _session = _make_repo()  # underscore prefix = intencional
```

---

## Próximo paso: Fase 3 — ETL pipelines críticos

### Archivos target
| Archivo | Stmts | Cov actual | Target | Gain est. |
|---------|-------|------------|--------|-----------|
| `period_pipeline.py` | 65 | 0% | 85% | +55 |
| `etl_service.py` | ~300 | 22% | 80% | +175 |

### Estrategia Fase 3
Ver `FASE-3-HANDOFF.md` para el prompt completo.

Patrón recomendado para `period_pipeline.py`:
- `_run(coro)` helper para sync→async (ver `test_etl_pipeline.py:62-120` como referencia)
- `MagicMock` providers/repos/cache
- Cubrir: success, partial failure sub-extractor, `ConnectionRevokedException`, period overlap

Patrón para `etl_service.py`:
- Expandir los tests existentes en `test_etl_pipeline.py`
- Agregar branches: `run_period_extraction`, `_sync_ig_dm`, Shopify line items, error paths

---

## Decisiones de arquitectura de tests

1. **NO aiosqlite**: Evitar dependencia nueva. Usar `db` sync + `AsyncSession` adapter delgado por test.
2. **MagicMock para repos stage**: Todos los 4 repos stage usan PostgreSQL-specific SQL → mock obligatorio.
3. **SQLite real para repos con SQLA puro**: `official_metrics_repository.py`, `period_metrics_repository.py`, etc. usan SQLA estándar → pueden usar `db` fixture de `tests/conftest.py`.
4. **AsyncClient para Fase 6**: `app.dependency_overrides` para `get_current_user` + `get_tenant_id` — montar sub-app solo con analytics router si tests lentos (>200ms).
5. **metrics_service.py legacy**: Testear solo 3 entrypoints activos: `get_bowtie_summary`, `get_marketing_sankey_metrics`, `get_stage_timeseries`. No testear el resto.

---

## Comandos útiles

```bash
# Coverage analytics solo
cd backend && .venv/bin/pytest tests/modules/analytics/ \
  --cov=src/modules/analytics --cov-report=term-missing -q 2>&1 | tail -30

# Run tests de un archivo nuevo
cd backend && .venv/bin/pytest tests/modules/analytics/test_NUEVO.py -v

# Lint rápido antes commit
cd backend && .venv/bin/ruff check tests/modules/analytics/ --no-cache
cd backend && .venv/bin/ruff format --check tests/modules/analytics/

# Arch tests (no romper)
cd backend && .venv/bin/pytest tests/architecture/ -x -q

# Gate final (≥85% analytics)
cd backend && .venv/bin/pytest tests/modules/analytics/ \
  --cov=src/modules/analytics --cov-report=term -q | grep "TOTAL\|passed\|failed"
```
