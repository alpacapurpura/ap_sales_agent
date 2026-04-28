# Fase 4 — Stage Services + Metrics Service

## Estado al iniciar

- **Cobertura analytics:** 64% (7931 stmts, 2870 missing)
- **Target final:** 85% (≥6771 stmts cubiertos)
- **Commit de partida:** `4972afcd`
- **Rama:** `development`

## Contexto de Fase 3 (patrones aprendidos)

Ver `PROGRESS.md` sección "Fase 3 — completada" para:
- `provider_name()` es sync → usar `MagicMock(return_value=...)` no `AsyncMock`
- Lazy imports dentro de métodos: parchear en módulo fuente
- `_stage_transform_upsert_aggregate` testeable directo (sync)
- `run_sync_all` → parchear `_run_provider_isolated` directamente en `svc`

## Archivos target Fase 4

| Archivo | Stmts | Cov actual | Target | Gain est. |
|---------|-------|------------|--------|-----------|
| `stage_services/adoption_stage.py` | 72 | 19% | 80% | +44 |
| `stage_services/capture_stage.py` | 149 | 17% | 75% | +86 |
| `stage_services/evangelization_stage.py` | 43 | 28% | 80% | +22 |
| `stage_services/expansion_stage.py` | 84 | 18% | 75% | +48 |
| `stage_services/nurture_stage.py` | 107 | 25% | 75% | +54 |
| `stage_services/opportunity_stage.py` | 95 | 24% | 75% | +48 |
| `stage_services/sales_stage.py` | 168 | 13% | 70% | +96 |
| `stage_services/summary_stage.py` | 105 | 17% | 70% | +56 |
| `stage_services/timeseries_stage.py` | 87 | 20% | 75% | +52 |
| `ig_dm_sync_service.py` | 112 | 18% | 70% | +58 |
| `metrics_service.py` | 216 | 13% | 50% | +80 |

**Total estimado Fase 4:** +644 stmts cubiertos → ~72% acumulado

## Archivos test existentes

```
backend/tests/modules/analytics/
  test_attraction_stage.py      # ya existe — 78% cov (referencia de patrón)
  conftest.py                   # fixtures: mock_db_session, mock_cache, mock_credentials
  test_etl_service.py           # etl_service tests — NO modificar para stage services
  test_period_pipeline.py       # nuevo en Fase 3
```

## Patrón de referencia: attraction_stage

```python
# test_attraction_stage.py patrón
def _make_stage(session_kwargs=None):
    from src.modules.analytics.application.services.stage_services.attraction_stage import (
        AttractionStageService,
    )
    session = MagicMock()
    session.execute.return_value.all.return_value = []
    session.execute.return_value.scalar.return_value = 0
    # MagicMock necesario — repos usan PostgreSQL-specific SQL (jsonb, func.extract)
    svc = AttractionStageService(db=session, cache=AsyncMock())
    return svc, session
```

Todos los stage services usan `Session` sync + SQL PostgreSQL-specific → **MagicMock obligatorio**, no SQLite.

## Patrón stage service: get_metrics()

```python
async def test_get_metrics_returns_dto(self):
    svc, session = _make_stage()
    session.execute.return_value.all.return_value = []  # sin datos = vacío
    session.execute.return_value.scalar.return_value = 0
    session.execute.return_value.first.return_value = (0, 0, 0, 0, None)

    from datetime import date
    result = _run(svc.get_metrics(TENANT_ID, date(2026, 3, 1), date(2026, 3, 31)))

    assert result is not None  # DTO retornado aunque vacío
```

## Patrón summary_stage / timeseries_stage

Estos leen de `cache` primero (cache-first pattern):

```python
async def test_get_summary_cache_miss(self):
    svc, session = _make_stage()
    # cache miss → llama repos
    svc.cache.get.return_value = None
    session.execute.return_value.all.return_value = []
    
    result = _run(svc.get_summary(TENANT_ID))
    assert result is not None
```

## Patrón ig_dm_sync_service

```python
from unittest.mock import AsyncMock, MagicMock, patch

def _make_sync_svc():
    from src.modules.analytics.application.services.ig_dm_sync_service import (
        InstagramDMSyncService,
    )
    mock_db = MagicMock()
    mock_conn_port = AsyncMock()
    return InstagramDMSyncService(mock_db, connection_port=mock_conn_port), mock_db, mock_conn_port

# Test: no Meta connection → returns None
async def test_sync_returns_none_when_no_meta_credentials():
    svc, _, port = _make_sync_svc()
    port.get_credentials.side_effect = Exception("No connection")
    result = _run(svc.sync(TENANT_ID))
    assert result is None
```

## Patrón metrics_service (legacy 3 entrypoints)

Solo testear: `get_bowtie_summary`, `get_marketing_sankey_metrics`, `get_stage_timeseries`.
NO testear métodos marcados deprecated o sin uso activo.

```python
def _make_metrics_svc():
    from src.modules.analytics.application.services.metrics_service import MetricsService
    mock_db = MagicMock()
    mock_db.execute.return_value.all.return_value = []
    mock_db.execute.return_value.scalar.return_value = 0
    mock_db.execute.return_value.first.return_value = None
    svc = MetricsService(db=mock_db, cache=AsyncMock())
    return svc, mock_db
```

## Estrategia Fase 4

### Paso 4a — stage services individuales (en paralelo posible)

Crear un archivo por stage service o agrupar los menores (evangelization + expansion):

```
tests/modules/analytics/test_adoption_stage.py
tests/modules/analytics/test_capture_stage.py
tests/modules/analytics/test_nurture_stage.py
tests/modules/analytics/test_opportunity_stage.py
tests/modules/analytics/test_sales_stage.py
tests/modules/analytics/test_summary_stage.py
tests/modules/analytics/test_timeseries_stage.py
tests/modules/analytics/test_evangelization_expansion_stage.py
```

Cada archivo cubre: get_metrics() happy path, cache-miss path, empty data path, error path.

### Paso 4b — ig_dm_sync_service

```
tests/modules/analytics/test_ig_dm_sync_service.py
```

Cubre: `sync()` sin conexión Meta, `sync()` con credentials OK, error en API.

### Paso 4c — metrics_service (3 entrypoints)

Expandir existente o crear `tests/modules/analytics/test_metrics_service.py`.

## Reglas paralelo (CRÍTICO)

Otro Claude Code activo en `sales_agent/`. Stage commits SOLO por nombre:
```bash
git add tests/modules/analytics/test_NUEVO.py
# NUNCA: git add . / -A / -u
```

## Math cobertura Fase 4

- Inicio: 64% (5061/7931 cubiertos)
- Target: 85% (6771/7931)
- Necesario: +1710 stmts
- Fase 4 aporta: ~644 stmts → 71% acumulado
- Fases 5-6 necesitan: ~1066 stmts más

## Comandos útiles

```bash
# Coverage analytics completo
cd backend && .venv/bin/pytest tests/modules/analytics/ \
  --cov=src/modules/analytics --cov-report=term-missing -q 2>&1 | tail -30

# Run tests nuevos
cd backend && .venv/bin/pytest tests/modules/analytics/test_NUEVO.py -v

# Lint antes commit
cd backend && .venv/bin/ruff check tests/modules/analytics/ --no-cache
cd backend && .venv/bin/ruff format --check tests/modules/analytics/

# Arch tests (no romper)
cd backend && .venv/bin/pytest tests/architecture/ -x -q
```
