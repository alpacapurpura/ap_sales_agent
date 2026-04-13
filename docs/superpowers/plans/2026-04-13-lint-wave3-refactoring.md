# Wave 3: Lint Zero-Debt — Refactoring de funciones complejas

> **Prompt para nueva conversacion:**
> "Ejecuta Wave 3 del lint zero-debt. Plan: `docs/superpowers/plans/2026-04-13-lint-wave3-refactoring.md`"

## Estado actual

- **24 reglas enforced** en Waves 1-2 (~560 fixes)
- **5 reglas quedan** en `pyproject.toml` ignore (progressive adoption)
- Lint pasa: `All checks passed!`
- Tests pasan: `2264 passed, 3 skipped`
- Branch: `development` (limpio)

## Reglas pendientes

| Regla | Violaciones | Funciones unicas | Descripcion |
|-------|-------------|-------------------|-------------|
| PLR0912 | 39 | 39 | Too many branches (>12) |
| PLR0915 | 37 | 37 | Too many statements (>50) |
| PLR0911 | 11 | 11 | Too many return statements (>6) |
| N801 | 5 | 5 | Class name should use CapWords |
| N802 | 4 | 4 | Function name should be lowercase |

**Muchas funciones tienen overlap PLR0912+PLR0915** (28 funciones). Total funciones unicas: ~57.

## Parte 1: N801 + N802 (trivial, 9 fixes)

### N801 — 5 clases en `src/tests/test_telegram_flow.py`

```
TestStep1_IdentityResolution → TestStep1IdentityResolution
TestStep2_CustomerProfileCreation → TestStep2CustomerProfileCreation
TestStep3_LeadCreation → TestStep3LeadCreation
TestStep4_AuditLogging → TestStep4AuditLogging
TestStep5_FullFlowIntegration → TestStep5FullFlowIntegration
```

Fix: Quitar los underscores de los nombres de clase. Buscar `TestStep*_` y renombrar.

### N802 — 4 funciones en `src/core/config.py`

```
OPENAI_MODEL (line 72) → openai_model
OPENAI_FAST_MODEL (line 76) → openai_fast_model
OPENAI_EMBEDDING_MODEL (line 80) → openai_embedding_model
DATABASE_URL (line 157) → database_url
```

Fix: Son `@property` o `@computed_field` en la clase Settings. Renombrar a lowercase + buscar TODOS los usages en el codebase (`settings.OPENAI_MODEL`, etc.) y actualizarlos.

**Accion:** Fix directo, commit, remover de ignore.

## Parte 2: PLR0911 (11 funciones, returns excesivos)

| Archivo | Linea | Returns | Funcion |
|---------|-------|---------|---------|
| `advertising/.../health_check_service.py` | 375 | 9 | ? |
| `advertising/domain/enums.py` | 85 | 8 | ? |
| `analytics/domain/metric_resolver.py` | 324 | 7 | ? |
| `connections/api/channel_info.py` | 84 | 7 | ? |
| `connections/api/marketing_webhooks.py` | 42 | 10 | ? |
| `connections/api/marketing_webhooks.py` | 83 | 8 | ? |
| `copilot/api/nudge.py` | 38 | 7 | ? |
| `copilot/.../procedures/base.py` | 62 | 7 | ? |
| `copilot/.../tools/brand_tools.py` | 54 | 8 | ? |
| `copilot/.../tools/module_tools.py` | 148 | 13 | ? |
| `offer/.../offer_completion_service.py` | 148 | 19 | ? |

Fix patterns:
- Dispatch dicts en vez de if/elif chains
- Early returns consolidados
- Extraer subfunciones por caso

**Accion:** Leer cada funcion, aplicar refactor apropiado, tests despues de cada archivo.

## Parte 3: PLR0912 + PLR0915 (la mas grande, ~57 funciones)

### Concentracion por modulo

| Modulo | Funciones | Prioridad |
|--------|-----------|-----------|
| analytics/ | 23 | ALTA (la mas afectada) |
| connections/ | 5 | MEDIA |
| copilot/ | 5 | MEDIA |
| sales_agent/ | 6 | MEDIA |
| brand/ | 3 | MEDIA |
| shared/ | 2 | BAJA |
| offer/ | 1 | BAJA |
| iam/ | 1 | BAJA |
| crm/ | 1 | BAJA |
| admin/ | — | YA IGNORADO en per-file-ignores |
| scripts/ | 1 | BAJA |

### Top 10 funciones mas complejas (priorizar estas)

| Archivo | Linea | Stmts | Branches | Funcion |
|---------|-------|-------|----------|---------|
| `sales_agent/.../orchestrator/chat.py` | 255 | **236** | **58** | ? |
| `analytics/.../stage_services/sales_stage.py` | 55 | **129** | 26 | ? |
| `brand/.../extraction_orchestrator.py` | 559 | **105** | 36 | ? |
| `analytics/.../metrics_service.py` | 167 | **100** | 21 | ? |
| `analytics/.../stage_services/summary_stage.py` | 45 | **99** | 21 | ? |
| `analytics/.../stage_services/capture_stage.py` | 107 | **95** | 18 | ? |
| `analytics/.../etl_service.py` | 602 | **84** | 17 | ? |
| `sales_agent/workers/follow_up_engine.py` | 29 | **81** | 18 | ? |
| `connections/.../channels/meta.py` | 177 | **80** | 27 | ? |
| `brand/.../extraction_orchestrator.py` | 132 | **76** | 16 | ? |

### Archivos que son SOLO PLR0915 (statements, no branches)

Estos son mas faciles — la funcion es larga pero no tiene logica compleja:

```
analytics/.../stage_services/adoption_stage.py:39 (51 stmts)
analytics/.../stage_services/expansion_stage.py:40 (66 stmts)
analytics/.../etl_service.py:429 (56 stmts)
analytics/infrastructure/etl/pipeline.py:78 (62 stmts)
analytics/workers/tasks.py:495 (58 stmts)
connections/api/meta.py:252 (52 stmts)
sales_agent/.../monitoring/tracing.py:19 (69 stmts)
sales_agent/.../monitoring/tracing.py:26 (67 stmts)
scripts/migrate_local_to_r2.py:37 (53 stmts)
```

### Archivos que son SOLO PLR0912 (branches, no statements)

```
analytics/.../aggregations.py:28 (14 branches)
analytics/.../shopify_provider.py:413 (13 branches)
copilot/api/nudge.py:72 (14 branches)
copilot/.../knowledge_ingestion.py:62 (17 branches)
copilot/.../tools/brand_tools.py:54 (15 branches)
copilot/.../tools/module_tools.py:148 (15 branches)
copilot/.../tools/offer_tools.py:98 (13 branches)
crm/.../lead_metrics_repository.py:121 (18 branches)
offer/api/product_mappings.py:97 (13 branches)
```

### Estrategia de refactoring

**Para PLR0915 (statements):**
- Extraer bloques logicos a subfunciones privadas (`_compute_X`, `_build_Y`)
- Cada subfuncion: 1 responsabilidad, <30 statements

**Para PLR0912 (branches):**
- Dispatch dicts en vez de if/elif
- Early returns para reducir nesting
- Guard clauses al inicio
- Extraer validacion a funciones separadas

**Para funciones con ambos:**
- Combinar ambas estrategias
- Empezar por extraer subfunciones (reduce statements Y branches)

## Limites del ruff

| Config | Valor actual | Threshold |
|--------|-------------|-----------|
| `max-complexity` (C901) | 20 | PLR0912 threshold = 12 |
| PLR0912 threshold | 12 (default) | — |
| PLR0915 threshold | 50 (default) | — |
| PLR0911 threshold | 6 (default) | — |

Considerar subir temporalmente los thresholds si el refactoring de algunas funciones es demasiado riesgoso (ej: `sales_agent/orchestrator/chat.py:255` con 236 statements).

## Workflow por funcion

1. Leer la funcion completa
2. Identificar bloques extraibles
3. Escribir test si no existe (TDD: verificar que el comportamiento actual esta cubierto)
4. Extraer subfunciones
5. Verificar: `ruff check <file> --select PLR0912,PLR0915,PLR0911 --no-cache`
6. Correr tests del modulo: `pytest tests/modules/<module>/ -x -q`
7. Siguiente funcion

## Orden de ejecucion recomendado

1. **N801 + N802** (9 fixes triviales) → commit
2. **PLR0911** (11 funciones con returns excesivos) → commit
3. **PLR0912/PLR0915 solo-branch o solo-statement** (~18 funciones mas faciles) → commit por modulo
4. **PLR0912+PLR0915 overlap** (28 funciones con ambos) → commit por modulo
5. Remover reglas del ignore → commit final
6. Full test suite: `ruff check + pytest + ruff format`

## Per-file-ignores existentes (no tocar)

```toml
"src/admin/**/*.py" = ["PLR0911", "PLR0912", "PLR0915"]  # Streamlit pages
```

Esto excluye Streamlit admin pages del refactoring (correcto).

## Notas

- **NO tocar la logica de negocio** — solo reestructurar (extract method, early return, dispatch dict)
- **Sales agent orchestrator** (236 stmts, 58 branches) es la mas riesgosa — considerar hacer esa al final o pedir feedback antes
- Los stage services de analytics tienen un patron repetitivo — el refactoring de uno sirve de template para los demas
- `src/scripts/migrate_local_to_r2.py` es un script one-shot, evaluar si vale la pena refactorizar o mover a permanent ignore
