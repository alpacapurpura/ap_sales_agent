# LLM Routing — SSoT (Single Source of Truth)

> **Owner:** PM + nicolify-architect. Origen: PR-3 PI-2 S2 audit failure 2026-04-30 — codebase tenía dos sistemas paralelos (ModelTier copilot vs ModelRole global) + capa duplicada introducida por PR-3.
>
> **Estado actual (2026-05-06):** **CANONICALIZADO**. LiteLLM Proxy es el camino único de dispatch LLM en runtime (PI-12 S1 sales-agent-litellm-canonicalization, T-4/T-5 merged). Per-provider adapters legacy (`openai.py`, `kimi.py`, `deepseek.py`, `qwen.py`, `gemini.py`, `_openai_compat.py`) eliminados físicamente. El feature flag que históricamente toggleaba proxy vs adapters fue eliminado de `Settings` (no existe fallback ni toggle). Cost runtime se captura vía `CustomLogger` pattern (ver sección dedicada abajo).

## Regla de oro

**Para seleccionar qué modelo LLM usar en cualquier capa del backend Nicolify, hay UNA sola API:**

```python
from src.core.enums import ModelRole
from src.core.config import settings

model_name = settings.get_model(ModelRole.NANO)
provider = settings.get_provider_for_role(ModelRole.NANO)  # AIProvider enum
```

NO hay otra API. Si encontrás `TIER_METADATA`, `ModelTier`, `COPILOT_TIER_*_PROVIDER`, `model_config.py` o `provider_factory.py` en `modules/copilot/infrastructure/llm/` — **es deuda técnica deprecada en migración**. NO consumir, NO extender, reportar a `/pm`.

## Capa 5 — LiteLLM Proxy = canonical único (PI-12 S1 shipped 2026-05-06)

**Docker svc `visionarias_litellm` v1.83.10-stable** expone `LITELLM_BASE_URL=http://visionarias_litellm:4000/v1` (OpenAI-compat). Es el único motor de dispatch LLM en runtime. `LiteLLMService` (`backend/src/shared/infrastructure/llm/providers/litellm.py`) es el único adapter — no hay fallback, no hay toggle, no hay reversión.

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
| `disable_spend_logs` | True (PII guard — Nicolify usa `model_pricing_snapshot` SSoT inmutable como audit ledger histórico) |

**Helpers retenidos** (consumidos por `LiteLLMService`, NO son adapters paralelos):

- `providers/_kwargs.py` — normalización de kwargs común a todos los providers
- `providers/_chat_model_resolver.py` — selección del wrapper `ChatModel` LangChain compatible
- `providers/_response_validation.py` — validación de payload de respuesta multi-provider

**Recorder:** `copilot_llm_call.model` y `sales_agent_llm_call.model` preservan el formato slashed `<provider>/<model>` (Decision A1 BINDING T-1). Esto permite reconciliación posterior contra `model_pricing_snapshot` y el registry de LiteLLM.

**Admin Streamlit:** `/admin/llm-virtual-keys` lista keys vía `/key/info` (read-only). CRUD UI shipped S4 PR-1.

**Tenant API keys deprecadas** (PI-12 S1 T-6a, commit `f6e7ad0a`): las columnas `tenants.{openai,deepseek,kimi,dashscope}_api_key` quedaron deprecadas y nullificadas. Las API keys de provider viven en `litellm_config.yaml` (env vars del proxy). DROP COLUMN final ocurre en T-6c post operational gate T-6b. `tenants.gemini_api_key` se preserva (uso paralelo en Vertex AI workflows fuera del proxy LLM-text).

## CustomLogger pattern (cost recorder)

LiteLLM calcula nativamente el costo USD de cada completion y lo expone en `kwargs["response_cost"]` durante sus callbacks. Nicolify **no** vuelve a calcular el costo en runtime — lo captura mediante un `CustomLogger` proceso-wide y lo persiste vía el callback handler de LangChain. Este patrón puente fue introducido en PI-12 S1 T-1 (commit `5856be4d`).

### Componentes

| Componente | Path | Rol |
|---|---|---|
| `CostRecorderCustomLogger` | `backend/src/shared/agent_observability/recording/cost_recorder.py` | Hook de LiteLLM. En cada `log_success_event` extrae `kwargs["response_cost"]` y lo guarda en cache TTL keyed by `litellm_call_id` |
| `BaseAgentCallbackHandler.on_llm_end` | `backend/src/shared/agent_observability/recording/base_callback_handler.py` | Hook de LangChain. Lee `litellm_call_id` desde `response.response_metadata`, llama `pop_cost(call_id)` y persiste en `copilot_llm_call.cost_usd` o `sales_agent_llm_call.cost_usd` |
| Bootstrap | `main.py` (FastAPI) + `workers/settings.py` (ARQ) | Registra `litellm.callbacks = [CostRecorderCustomLogger()]` una vez al arranque del proceso |

### Por qué es una clase NUEVA (no mirror)

Per anti-duplication §0 evaluado en T-1 + ratificado por architect 03-arch-be.md §10:

- LiteLLM `CustomLogger` y LangChain `BaseCallbackHandler` viven en superficies conceptualmente distintas (proxy-side vs runtime-side) y se invocan en lifecycle points diferentes.
- Coexisten por diseño: el handler LangChain captura el span LangChain (provider/model/tokens), el `CustomLogger` captura `kwargs["response_cost"]`. Se enlazan vía `litellm_call_id`.
- No es duplicación de `BaseAgentCallbackHandler` — es una abstracción nueva en una frontera nueva.

### TTL cache 60s + best-effort

```text
litellm_call_id  →  (cost_usd: Decimal | None, expires_at_monotonic)
```

Invariantes:

- **Single-use**: `pop_cost(call_id)` drena la entrada. Llamadas repetidas devuelven `None`.
- **TTL purge**: entradas con TTL excedido (60s default) se eliminan lazy en cada operación de cache. Cada purge emite `structlog.warning("cost_recorder.orphan_entry_purged", call_id=..., cost_usd=...)` para observabilidad — orphan típicamente indica consumer LangChain lento o callback LiteLLM disparado sin hook LangChain emparejado.
- **Best-effort**: cada mutación va dentro de `try/except` con `structlog.warning`. El callback nunca bloquea ni rompe el turn.
- **Tenant-agnostic**: la cache es módulo-global (process-wide). El tenant context vive en `BaseAgentCallbackHandler` — el `CustomLogger` se registra una vez al boot sin setup per-request.
- **NFR p95 < 50ms**: micro-benchmark en `backend/tests/shared/agent_observability/cost/test_litellm_canonicalization.py::test_p95_under_50ms` lo verifica.

### Modelo de costo runtime vs reconciliación

| Fuente | Uso | Tabla |
|---|---|---|
| `kwargs["response_cost"]` (LiteLLM-native) | Runtime — único origen del valor en `cost_usd` | `copilot_llm_call`, `sales_agent_llm_call` |
| `model_pricing_snapshot` | Reconciliación / billing audit ledger / análisis histórico | `model_pricing_snapshot` (append-only) |

`shared/agent_observability/cost/calculator.py` quedó como utility de reconciliación post-hoc — **ya no se invoca en runtime path** (Decision X2 BINDING T-1). `make sync-pricing` (`backend/src/shared/agent_observability/cost/litellm_sync.py`, T-2 commit `8b6d798f`) sincroniza `model_pricing_snapshot` desde `litellm_config.yaml` + `litellm.model_cost` cada noche (ARQ cron 03:00 UTC) y emite drift warnings si el upstream diverge >0.0001 USD/token.

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
| `<PROVIDER>_API_KEY` | Provider API keys (consumidas por LiteLLM proxy vía `litellm_config.yaml` env-var refs) | `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, `KIMI_API_KEY` |

**Funciones**:
- `settings.get_model(role: ModelRole) -> str` — modelo activo para role
- `settings.get_provider_for_role(role: ModelRole) -> AIProvider` — provider activo

**Antipattern**: NO hardcodear `model_name` en archivos `.py` (e.g., NO `model_name="gpt-5.4-nano"`). NO crear capa override paralela (`COPILOT_TIER_*` etc.). NO duplicar `Settings.get_*` en submódulos.

### Capa 3 — Provider routing (cómo hablamos con el provider)

**`src/shared/infrastructure/llm/router.py`** + **`src/shared/infrastructure/llm/providers/litellm.py`** + **`litellm_config.yaml`**:

| Archivo | Responsabilidad |
|---|---|
| `router.py` | Dispatch único — toma `(role, messages)`, resuelve provider+model via `Settings.get_provider_for_role` + `Settings.get_model`, delega a `LiteLLMService` |
| `providers/litellm.py` | `LiteLLMService` — único adapter runtime. Llama al proxy LiteLLM vía interfaz OpenAI-compat |
| `providers/_kwargs.py` | Normaliza kwargs (temperature/max_tokens/extra_body) cross-provider |
| `providers/_chat_model_resolver.py` | Selecciona el wrapper `ChatModel` LangChain compatible para el spec activo |
| `providers/_response_validation.py` | Valida shape de la respuesta del proxy multi-provider |
| `litellm_config.yaml` | Registry declarativo de modelos + fallback chains + env-var refs para API keys |

**Para agregar provider nuevo** (ej: Anthropic Claude):
1. Agregar entrada `model_list` en `litellm_config.yaml` con `litellm_params.model: anthropic/claude-X` + `api_key: os.environ/ANTHROPIC_API_KEY`
2. Si el provider expone tier nuevo, agregar `AIProvider` enum value (`src/core/enums.py`) + sumar a `Settings.get_provider_for_role`
3. Tests integration en `backend/tests/shared/infrastructure/llm/`
4. `make sync-pricing` regenera `model_pricing_snapshot` a partir del yaml + `litellm.model_cost`
5. Documentar acá

**NO** crear adapter `providers/anthropic.py` ni `modules/<x>/infrastructure/llm/` — el dispatch corre 100% por LiteLLM proxy. Adapter nuevo per-provider = anti-pattern (ver "Anti-patterns documentados").

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
6. **Reversión** si SLO breach: revertir env var + redeploy.

## Cómo cambiar modelo POST S4 (estado deseado)

1. **Eval gate**: admin UI Streamlit `/admin/llm-models` botón "Test candidate" → corre eval gate inline.
2. **Promote**: admin UI botón "Promote to active" → UPDATE `llm_role_binding SET is_active=TRUE WHERE role=X AND model=Y`.
3. **Cache invalidation**: pub/sub Redis emite invalidate → backend pods refrescan en <60s.
4. **Validación**: dashboard observability muestra ratio (old_model, new_model) en queries siguientes.
5. **Reversión**: admin UI botón "Revertir" → UPDATE active al binding previo. <30s MTTR.
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
