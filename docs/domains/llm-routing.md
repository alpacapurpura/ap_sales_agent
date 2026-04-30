# LLM Routing — SSoT (Single Source of Truth)

> **Owner:** PM + nicolify-architect. Origen: PR-3 PI-2 S2 audit failure 2026-04-30 — codebase tenía dos sistemas paralelos (ModelTier copilot vs ModelRole global) + capa duplicada introducida por PR-3.
>
> **Estado actual (2026-04-30):** EN MIGRACIÓN — convergencia ModelTier→ModelRole programada en sprint S3-copilot-llm-stack-convergence. Roadmap final: hybrid 3-capa (env secrets + DB registry + feature flags + LiteLLM Proxy) en S3+S4+S5.

## Regla de oro

**Para seleccionar qué modelo LLM usar en cualquier capa del backend Nicolify, hay UNA sola API:**

```python
from src.core.enums import ModelRole
from src.core.config import settings

model_name = settings.get_model(ModelRole.NANO)
provider = settings.get_provider_for_role(ModelRole.NANO)  # AIProvider enum
```

NO hay otra API. Si encontrás `TIER_METADATA`, `ModelTier`, `COPILOT_TIER_*_PROVIDER`, `model_config.py` o `provider_factory.py` en `modules/copilot/infrastructure/llm/` — **es deuda técnica deprecada en migración**. NO consumir, NO extender, reportar a `/pm`.

## Capa 5 — LiteLLM Proxy motor multi-provider (S3 PR-2 shipped 2026-04-30)

**Docker svc `visionarias_litellm` v1.83.10-stable** expone `LITELLM_BASE_URL=http://visionarias_litellm:4000/v1` (OpenAI-compat). Routing dispatch único via `LiteLLMService` adapter → reemplaza per-provider adapters interno cuando `LITELLM_PROXY_ENABLED=True` (default).

| Aspecto | Detalle |
|---|---|
| Image | `ghcr.io/berriai/litellm-database:v1.83.10-stable` |
| DB | `visionarias_litellm_db` separada (Prisma vs Alembic isolation) |
| Healthcheck | `GET /health/readiness` (Docker `service_healthy` gate) |
| Models declared | 6 (deepseek-v4-flash, deepseek-reasoner, kimi-k2.6, gpt-4o-mini, gpt-4o, text-embedding-3-large) |
| Fallback chains | deepseek-v4-flash → gpt-4o-mini · deepseek-reasoner → gpt-4o · kimi-k2.6 → gpt-4o |
| `drop_params` | True (auto-filter unsupported kwargs per provider) |
| `request_timeout` | 30s |
| `store_model_in_db` | True (forward-compat S4 admin UI hot-swap) |
| `disable_spend_logs` | True (PII guard — Nicolify usa `model_pricing_snapshot` SSoT inmutable) |
| Toggle rollback | `LITELLM_PROXY_ENABLED=False` → fallback per-provider legacy adapters (deprecated, eliminación física S4) |

**Recorder D-7:** `copilot_llm_call.model` strip prefix `<provider>/<model>` → bare model name. Preserve queries Streamlit existentes (`/costo-copilot`, `/marketing-kb`).

**Admin Streamlit:** `/admin/llm-virtual-keys` read-only S3 (lista keys via `/key/info`). CRUD UI completo S4 PR-1.

## Arquitectura — capas

### Capa 1 — Domain (qué necesitás)

**Enum `ModelRole`** en `src/core/enums.py`. Roles semánticos por capacidad:

| Role | Para qué | Tier económico |
|---|---|---|
| `NANO` | Respuestas triviales, classifier, summarizer, acuses | cheapest |
| `FAST` | Chat estándar, edición simple, copy ligero | cheap |
| `REASONING` | Análisis causal, planes paso-a-paso | mid |
| `AGENT` | Multi-step agentic, tool-use, decisión | high |
| `VISION` | Image+text input | mid |
| `EMBEDDING` | Vectores semánticos | dedicated |

**Antipattern**: NO crear nuevos enums (`ModelTier`, `LLMTier`, `CopilotTier`, etc.). Si necesitás granularidad nueva, extendé `ModelRole` con propuesta a `/pm`.

### Capa 2 — Config selection (qué modelo + qué provider para ese role)

**`src/core/config.py::Settings`** lee env vars:

| Env var | Significado | Ejemplo |
|---|---|---|
| `AI_PROVIDER` | Provider global default | `openai` |
| `AI_PROVIDER_<ROLE>` | Override per-role provider | `AI_PROVIDER_REASONING=deepseek` |
| `AI_MODEL_<ROLE>` | Override per-role model name | `AI_MODEL_NANO=gpt-4o-mini` |
| `<PROVIDER>_API_KEY` | Provider API keys | `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, `KIMI_API_KEY` |

**Funciones**:
- `settings.get_model(role: ModelRole) -> str` — modelo activo para role
- `settings.get_provider_for_role(role: ModelRole) -> AIProvider` — provider activo

**Antipattern**: NO hardcodear `model_name` en archivos `.py` (e.g., NO `model_name="gpt-5.4-nano"`). NO crear capa override paralela (`COPILOT_TIER_*` etc.). NO duplicar `Settings.get_*` en submódulos.

### Capa 3 — Provider routing (cómo hablamos con el provider)

**`src/shared/infrastructure/llm/router.py`** + **`src/shared/infrastructure/llm/providers/`**:

| Archivo | Responsabilidad |
|---|---|
| `router.py` | Dispatch por provider — toma `(role, messages)`, resuelve provider via `Settings.get_provider_for_role`, delega al adapter |
| `providers/openai.py` | OpenAI native API (gpt-4o, gpt-5.x) |
| `providers/kimi.py` | Moonshot Kimi (kimi-k2.6, kimi-latest) |
| `providers/_openai_compat.py` | DeepSeek + cualquier provider OpenAI-compatible (base_url override) |

**Para agregar provider nuevo** (ej: Anthropic Claude):
1. Agregar a `AIProvider` enum (`src/core/enums.py`)
2. Crear `src/shared/infrastructure/llm/providers/anthropic.py` siguiendo el shape de `openai.py`
3. Wire en `router.py` switch
4. Agregar env var `ANTHROPIC_API_KEY`
5. Tests provider integration + fallback
6. Documentar acá

**NO** crear adapter en `modules/<x>/infrastructure/llm/` — todos los providers viven en `shared/`.

### Capa 4 — Pricing snapshot (billing histórico)

**Tabla `model_pricing_snapshot`** (`alembic/versions/075_copilot_observability_rebuild.py`). Schema:
- `(provider, model, input_cost_per_token, output_cost_per_token, valid_from, valid_to)`
- Active row = `valid_to IS NULL`
- Closed rows = pricing histórico inmutable (billing audit)

**Cuando agregás modelo nuevo:**
1. Migration alembic con `INSERT ... WHERE NOT EXISTS` (idempotente)
2. Pricing en USD per **token** (no per 1M — convertir: `0.14 / 1_000_000 = 0.000000140000`)
3. NO hardcodear pricing en código Python — tabla DB es SSoT

## Modelos activos hoy (2026-04-30)

> Actualizar este bloque cuando cambien `.env` o se agregue modelo. Refleja `.env` real, no `Settings` defaults de código.

| Role | Provider | Model | Cost in/out per 1M | Notes |
|---|---|---|---|---|
| NANO | openai | gpt-4o-mini | $0.15 / $0.60 | activo prod |
| FAST | openai | gpt-4o-mini | $0.15 / $0.60 | activo prod |
| REASONING | deepseek | deepseek-reasoner | $0.55 / $2.19 | activo prod (chino) |
| AGENT | kimi (moonshot) | kimi-k2.6 | $0.95 / $4.00 | activo prod (chino) |
| VISION | openai | gpt-4o | $2.50 / $10.00 | activo prod |
| EMBEDDING | openai | text-embedding-3-large | $0.13 (in only) | activo prod |

**Recomendados pendientes activar (research 2026-04-30):**
- NANO + FAST → `deepseek-v4-flash` ($0.14 / $0.28) → 4-15x cost reduction. Activar via `AI_MODEL_NANO=deepseek-v4-flash` + `AI_PROVIDER_NANO=deepseek` post eval gate.
- EMBEDDING → `qwen3-embedding-8b` (MTEB ML 70.58 vs current 63) — requiere re-index Qdrant ventana mantenimiento. PI dedicado.

## Cómo cambiar modelo HOY (procedimiento standard)

1. **Eval gate primero** (cuando S5 esté shipped): correr `python -m src.modules.copilot.evals.runner --use=<role> --candidate=<new_model>` → threshold ≥0.95 vs incumbente.
2. **Pricing snapshot**: agregar row a `model_pricing_snapshot` via migration alembic idempotente.
3. **Editar `.env`** prod: `AI_MODEL_<ROLE>=<new_model>` + `AI_PROVIDER_<ROLE>=<provider>`.
4. **Redeploy** (hoy obligatorio — post S4 será hot-swap admin UI sin deploy).
5. **Validar**: query `SELECT DISTINCT model_id FROM copilot_llm_call WHERE created_at > NOW() - INTERVAL '5 minutes'` — confirmar nuevo modelo en uso.
6. **Rollback** si SLO breach: revert env var + redeploy.

## Cómo cambiar modelo POST S4 (estado deseado)

1. **Eval gate**: admin UI Streamlit `/admin/llm-models` botón "Test candidate" → corre eval gate inline.
2. **Promote**: admin UI botón "Promote to active" → UPDATE `llm_role_binding SET is_active=TRUE WHERE role=X AND model=Y`.
3. **Cache invalidation**: pub/sub Redis emite invalidate → backend pods refrescan en <60s.
4. **Validación**: dashboard observability muestra ratio (old_model, new_model) en queries siguientes.
5. **Rollback**: admin UI botón "Rollback" → UPDATE active al binding previo. <30s MTTR.
6. **Per-tenant override**: GrowthBook flag `llm_model_override_<role>` con bucketing por `tenant_id` para A/B + premium tiers.

## Reglas no-negociables (escala 1000+ tenants)

1. **Pricing inmutable**: tabla snapshot append-only, valid_from/valid_to nunca update — billing histórico requiere prueba de qué precio aplicaba en cada request.
2. **Cache obligatorio** en service layer: in-memory TTL 60s + pub/sub invalidation. Sin cache, 1000 tenants × 100 turns/día = 100K queries DB redundantes.
3. **Tenant isolation**: per-tenant override (S4+) NO puede leer modelo de otro tenant. Cada query filter `tenant_id`.
4. **Audit trail**: cada cambio admin UI emite event `llm_config_changed(role, old_model, new_model, admin_user, timestamp)` → tabla `llm_config_audit`.
5. **Best-effort en provider failure**: si provider X cae, fallback chain transparente al consumer (router.py maneja, builder NO).
6. **No reasoning hardcoded en consumers**: NUNCA `if model == "deepseek-v4-flash": ...` en código de aplicación. Provider abstraction debe esconder modelo.
7. **Eval gate antes promote**: NO promote modelo nuevo a activo sin score ≥0.95 vs incumbente en 50+ goldens. Sin eval gate = riesgo regresión silenciosa.

## Anti-patterns documentados (lecciones aprendidas)

| Anti-pattern | Origen | Impacto | Fix |
|---|---|---|---|
| `TIER_METADATA` hardcoded en `copilot/domain/model_tier.py` | Pre-existing legacy | Desincronizado del `.env` real (decía gpt-5.4-nano, .env tenía gpt-4o-mini) | S3 PR-1 — eliminar archivo, migrar consumers a ModelRole |
| `COPILOT_TIER_*_PROVIDER` env override layer (PR-3) | Audit failure 2026-04-30 | Capa duplicada paralelo a `AI_PROVIDER_<ROLE>` que ya existía | S3 PR-1 — eliminar `model_config.py + provider_factory.py + providers/deepseek.py` |
| Hardcodear pricing en código Python | Common pre-2025 | Billing miente cuando provider cambia precio | Tabla `model_pricing_snapshot` única SSoT |
| Crear `LLMProvider` Protocol nuevo en `modules/<x>/domain/ports.py` | Common cuando no se conoce shared/ | Bypass router central, multi-provider quebrado | EXTEND `shared/infrastructure/llm/providers/` |
| `model_name` parameter en services | Common quick-fix | Acopla service al modelo concreto, swap requiere refactor | Service recibe `role: ModelRole`, resuelve via Settings |

## Migration timeline

| Sprint | PRs | Resultado |
|---|---|---|
| S2-copilot-cero-deuda-stack (shipped 2026-04-30) | PR-3 PARTIAL | Infra duplicada introducida — DEUDA |
| S3-copilot-llm-stack-convergence (DONE 2026-04-30) | PR-1 cleanup ModelTier + PR-2 LiteLLM Proxy | ModelRole único SSoT + DeepSeek V4-Flash NANO+FAST + LiteLLM Proxy motor multi-provider live (visionarias_litellm Docker svc) |
| S4-copilot-model-registry-runtime (DONE 2026-04-30) | PR-1 DB registry + admin UI, PR-2 GrowthBook per-tenant scaffold | Hot-swap modelo <60s sin deploy + per-tenant override scaffold + cache 60s + Redis pub/sub invalidation |
| S5-copilot-eval-gate-pre-promote (DONE 2026-04-30) | PR-1 eval gate framework + CI workflow + PR-2 retro | NO promote sin score >= per-role threshold (NANO/FAST/AGENT/EMBEDDING=0.95, REASONING=0.93, VISION=0.90). PI-2 cerrado. |

Post S5 shipped: timeline cambio modelo = `~5 segundos sin deploy + eval gate automatic`. Esto es el norte escalable a 1000+ tenants.

## Referencias

- Research base: `docs/pm-nico/research/2026-04-30-llm-config-storage-best-practices.md`
- Research stack chinos: `docs/pm-nico/research/2026-04-30-llm-landscape-chinese-models.md`
- Sprint S2 retro: `docs/pm-nico/pis/active/PI-2-copilot-improvement/sprints/S2-copilot-cero-deuda-stack/learnings.md`
- LiteLLM Proxy: https://docs.litellm.ai/docs/proxy/quick_start
- GrowthBook AI Configs: https://docs.growthbook.io/app/ai-configs

## Cuándo actualizar este doc

- Modelo activo cambia → tabla "Modelos activos hoy"
- Provider nuevo agregado → sección "Capa 3" + tabla activos
- Anti-pattern detectado → sección "Anti-patterns"
- Sprint LLM-routing shipped → sección "Migration timeline"
- Regla nueva no-negociable → sección "Reglas no-negociables"

NO actualizar para cambios cosméticos. Doc viva.
