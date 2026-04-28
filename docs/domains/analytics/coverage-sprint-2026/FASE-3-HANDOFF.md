# FASE 3 — Handoff Prompt

**Fecha creación:** 2026-04-28
**Cobertura al iniciar Fase 3:** 60.89% (7931 stmts, 3102 missing)
**Commit de entrega Fase 0-2:** `0c6c9b2e`

---

## Prompt para pegar al inicio de la próxima sesión

```
Continuamos el sprint de cobertura analytics de Nicolify.

Contexto: rama `development`, backend Python/FastAPI/pytest. Hay OTRA sesión de Claude Code
activa en esta misma rama — stage commits SOLO por nombre de archivo (nunca `git add .`/`-A`/`-u`).

Lee primero:
- docs/domains/analytics/coverage-sprint-2026/PROGRESS.md — progreso y patrones aprendidos
- backend/src/modules/analytics/infrastructure/etl/period_pipeline.py — archivo objetivo Fase 3a
- backend/src/modules/analytics/application/services/etl_service.py — archivo objetivo Fase 3b
- backend/tests/modules/analytics/test_etl_pipeline.py — referencia de patrón existente

Estado actual:
- 60.89% cobertura analytics (7931 stmts, 3102 missing)
- Fases 0-2 completas: dead code eliminado, factories creadas, 4 repos stage 0%→94%
- Fase 3 objetivo: period_pipeline.py (0%→85%, +55 stmts) + etl_service.py (22%→80%, +175 stmts)

Reglas TDD obligatorio:
1. Escribir tests PRIMERO (RED), luego verificar pasan (GREEN)
2. Ruff lint/format antes de cada commit
3. Arch tests no deben romperse: `cd backend && .venv/bin/pytest tests/architecture/ -x -q`

Empieza por Fase 3a: crear `backend/tests/modules/analytics/test_period_pipeline.py`.
Patrón referencia en `test_etl_pipeline.py:62-120` (_run helper sync→async).
Cubrir: success path, partial sub-extractor failure, ConnectionRevokedException, period overlap detection.

Al terminar Fase 3, actualiza docs/domains/analytics/coverage-sprint-2026/PROGRESS.md
con la nueva cobertura y déjame el prompt de handoff para Fase 4 en un archivo
docs/domains/analytics/coverage-sprint-2026/FASE-4-HANDOFF.md.
```

---

## Contexto técnico para el agente

### Archivos de referencia clave

```
backend/src/modules/analytics/infrastructure/etl/period_pipeline.py     # 65 stmts, 0% cov
backend/src/modules/analytics/application/services/etl_service.py       # ~300 stmts, 22% cov
backend/tests/modules/analytics/test_etl_pipeline.py                    # patrón _run()
backend/tests/modules/analytics/conftest.py                              # fixtures reutilizables
backend/tests/factories/analytics.py                                     # 4 factories
```

### Patrón _run() para tests async ETL

```python
import asyncio
from unittest.mock import AsyncMock, MagicMock

def _run(coro):
    """Ejecuta coroutine en el event loop de test."""
    return asyncio.get_event_loop().run_until_complete(coro)
```

Con `asyncio_mode=auto` en pytest, los tests `async def` no necesitan `_run()`. Pero
`period_pipeline.py` puede tener métodos async que se llaman con `.run_until_complete`
internamente — ver cómo está implementado antes de decidir el patrón.

### Imports necesarios para mocks ETL

```python
from unittest.mock import AsyncMock, MagicMock, patch, call
from uuid import uuid4

from src.modules.analytics.infrastructure.etl.period_pipeline import PeriodPipeline
from src.modules.analytics.infrastructure.providers.base import ConnectionRevokedException
```

### Qué cubrir en period_pipeline.py

1. **Success path**: `extract_period_metrics()` con provider que retorna metrics → repo upsert llamado
2. **Partial failure**: un sub-extractor lanza excepción → extraction_run.sub_extractor_failures poblado, run no aborta
3. **ConnectionRevokedException**: lanzada por provider → propagada correctamente
4. **Period overlap detection**: si ya existe extraction_run para ese período → behavior esperado (skip o overwrite)

### Qué expandir en etl_service.py (22% → 80%)

Los gaps actuales (ver `coverage-term-missing`) incluyen:
- `run_period_extraction()` (lines 381-453)
- Multi-provider loop en `run_sync_all()`
- Shopify line items branch (lines 723-892)
- `_sync_ig_dm()` invocation
- Error paths cuando provider lanza exception

Referencia: `test_etl_pipeline.py` ya tiene algunos tests de `run_sync_all` — **expandir** en ese
archivo, no crear uno nuevo (para mantener fixtures compartidas).

### Cobertura math para Fase 3

- Inicio Fase 3: 4829/7931 cubiertos = 60.89%
- `period_pipeline.py` +55: → 4884/7931 = 61.6%
- `etl_service.py` +175: → 5059/7931 = 63.8%
- Acumulado estimado al cierre Fase 3: ~64%

### Parallel session safety — CRÍTICO

```bash
# Revisar ANTES de commit:
git status --short

# Stage SOLO los archivos de analytics:
git add backend/tests/modules/analytics/test_period_pipeline.py
git add backend/tests/modules/analytics/test_etl_pipeline.py  # si expandido

# NUNCA:
# git add .
# git add -A
# git add -u
```

La otra sesión de Claude Code trabaja en `sales_agent/` y tiene WIP no commiteado.
