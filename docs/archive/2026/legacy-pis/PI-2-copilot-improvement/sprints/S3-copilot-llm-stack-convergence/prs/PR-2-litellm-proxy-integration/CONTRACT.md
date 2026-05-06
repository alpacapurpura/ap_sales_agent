# CONTRACT — PR-2-litellm-proxy-integration

> Owner: `nicolify-architect`. SSoT pre-implementación. Backend builders + auditor consumen.
> **Versión**: 2026-04-30 (architect Opus 1M).
> **Skills consultados**: `copilot-expert` (verificar invariantes orquestador + observability), `sales-agent-expert` (§3 protected surfaces NO se tocan), `backend-expert` (DDD + arch fitness gates).

---

## 0. Context Summary

| Campo | Valor |
|---|---|
| PR | PR-2-litellm-proxy-integration |
| Sprint | S3-copilot-llm-stack-convergence |
| PI | PI-2-copilot-improvement |
| Modules tocados | `src/shared/infrastructure/llm/` (REFACTOR), `src/core/config.py` (EXTEND), `src/shared/agent_observability/pricing/` (EXTEND), `src/admin/` (NEW page), Docker (NEW svc) |
| Type | Infra + Refactor cero-deuda |
| pm-nico/current-state files afectados (post-merge) | `current-state/copilot.md` (cap "LiteLLM Proxy motor multi-provider activo"), `current-state/sales_agent.md` (sin cambios funcionales — verify no regression) |
| Arch fitness gates a satisfacer | `tests/architecture/test_llm_routing_ssot.py` (4 tests + allowlist=0), `test_no_new_copilot_module_imports.py` (ratchet 22 frozen), `test_no_response_model_drift.py` |

**Goal**: introducir LiteLLM Proxy (BerriAI) como motor multi-provider centralizado. EXTEND `shared/infrastructure/llm/router.py` + `providers/_chat_model_resolver.py` para que TODA dispatch pase por endpoint OpenAI-compatible LiteLLM. Cero breaking change consumers (`Settings.get_model` + `LLMFactory.get_service` siguen idéntico). Habilita S4 PR-1 (DB registry + admin UI hot-swap) y S4 PR-2 (GrowthBook per-tenant) con virtual keys per-tenant prep.

---

## 1. Existing systems audit (NO NEW LAYER rule — architect-mandatory)

### Audit cross-module ejecutado (2026-04-30)

```bash
# 1. Direct LLM client instantiation cross-codebase
grep -rn "AsyncOpenAI\|ChatOpenAI\|OpenAI(" src/

# 2. Shared LLM infra layout
ls src/shared/infrastructure/llm/                    # base.py factory.py router.py providers/
ls src/shared/infrastructure/llm/providers/          # openai|kimi|deepseek|qwen|gemini|_openai_compat|_chat_model_resolver|_kwargs|_response_validation

# 3. Pricing snapshot consumers (already exists)
grep -rn "model_pricing_snapshot" src/               # 9 hits — table + repos + LiteLLM JSON sync

# 4. SSoT API consumers (Settings.get_model / get_provider_for_role)
grep -rn "settings\.get_model\|settings\.get_provider_for_role" src/
# → 13 hits across providers/openai.py, _openai_compat.py, kimi.py, router.py, deepseek.py

# 5. LLMFactory consumers (downstream wire points)
grep -rn "from src.shared.infrastructure.llm.factory import LLMFactory" src/
# → 17 hits: copilot/{deep_agent,judge,memory,classifiers,tools/*}, sales_agent/{nodes,follow_up,quality,prompts}, brand/{voice_fidelity,personality,style_analyzer}, shared/{ai_action_service,brand_summary_regen,files/image_analysis}

# 6. Existing LiteLLM artifact (CRITICAL — already there)
grep -rn "litellm" src/
# → src/shared/agent_observability/pricing/litellm_sync.py (daily JSON sync from BerriAI repo)
# → src/shared/agent_observability/workers/pricing_sync_task.py (ARQ cron 03:00 UTC)
# → src/workers/settings.py:53 sync_litellm_pricing en cron jobs

# 7. ARQ scheduler patterns existentes (worker pricing sync)
grep -n "cron_jobs\|cron(" src/workers/settings.py  # → SchedulerSettings.cron_jobs ya tiene sync_litellm_pricing 03:00 UTC

# 8. Container check
docker ps | grep -i litellm                         # → 0 results — no svc currently running

# 9. Tenant API key columns (for virtual keys decision)
grep -n "api_key" src/modules/iam/infrastructure/models/tenant_model.py
# → openai_api_key, gemini_api_key, deepseek_api_key, kimi_api_key, dashscope_api_key (per-tenant overrides)
```

### Sistemas existentes encontrados

| Sistema | Path | Enum/Config | Factory/Router | Providers/Adapters | Estado |
|---|---|---|---|---|---|
| **A. SSoT Settings API** | `src/core/config.py:Settings` | `AIProvider`, `ModelRole` (`src/core/enums.py`) | `get_model(role)`, `get_provider_for_role(role)` | n/a | **active SSoT — KEEP UNTOUCHED public surface** |
| **B. LLM Factory + Router** | `src/shared/infrastructure/llm/{factory.py, router.py, base.py}` | n/a | `LLMFactory.get_service()` → `MultiRoleLLMRouter`; `build_provider_service(provider)` | n/a | **active — EXTEND (replace internal dispatch, keep public API)** |
| **C. Provider adapters (5)** | `src/shared/infrastructure/llm/providers/{openai, _openai_compat, deepseek, kimi, qwen, gemini}.py` + helpers `_chat_model_resolver`, `_kwargs`, `_response_validation` | `CHAT_MODEL_SPEC` registry per provider | n/a | LangChain `ChatOpenAI` + native partner classes | **active — REPLACE most with single LiteLLM-routed adapter; KEEP `gemini.py` (non-OpenAI protocol) until LiteLLM Proxy verified for Gemini** |
| **D. Pricing snapshot (table + repo + LiteLLM JSON sync)** | `src/shared/agent_observability/{persistence/{models/pricing_snapshot_model.py, pricing_snapshot_repository.py}, pricing/litellm_sync.py, workers/pricing_sync_task.py}` | `model_pricing_snapshot` table | `PricingSnapshotRepository`, `sync_pricing()` ARQ daily 03:00 UTC | n/a | **active SSoT inmutable — KEEP UNTOUCHED. LiteLLM Proxy NO writes here.** |
| **E. ARQ scheduler** | `src/workers/settings.py:SchedulerSettings.cron_jobs` | n/a | `cron(sync_litellm_pricing, hour=3, minute=0)` | n/a | **active — EXTEND (no nuevo scheduler standalone)** |
| **F. Tenant API key per-provider columns** | `src/modules/iam/infrastructure/models/tenant_model.py` (`openai_api_key`, `deepseek_api_key`, `kimi_api_key`, `gemini_api_key`, `dashscope_api_key`) | n/a | `LLMFactory.get_service_for_tenant()` | n/a | **active — KEEP. PR-2 NO toca virtual keys per-tenant CRUD (defer S4).** |
| **G. Streamlit admin** | `src/admin/{app.py, pages/, modules/}` registry-based | `PageSpec` registry | `st.navigation` | n/a | **active — EXTEND (1 nueva page `llm_virtual_keys.py` read-only S3, CRUD UI completo S4)** |
| **H. Arch fitness LLM SSoT** | `tests/architecture/test_llm_routing_ssot.py` | `KNOWN_LEGACY_LLM_FILES` allowlist=0 | n/a | n/a | **active gate — must stay verde, allowlist shrinks only** |

### Decisión por sistema

- **Sistema A (`core/config.py:Settings`)**: KEEP — public API `get_model` + `get_provider_for_role` permanecen idénticas. Cero breaking change. Solo se agrega 1 field nuevo `LITELLM_BASE_URL`.
- **Sistema B (`shared/infrastructure/llm/router.py + factory.py`)**: EXTEND — `MultiRoleLLMRouter._resolve(role)` sigue retornando `BaseLLMService`. Cambia internamente: en lugar de instanciar `OpenAIService`/`KimiService`/`DeepSeekService`/`QwenService` separados, retorna **un único `LiteLLMService`** que apunta a `LITELLM_BASE_URL` con OpenAI-format API. `gemini.py` queda como excepción legacy (Gemini en LiteLLM funciona, pero validación pre-cutover en sprint siguiente). `LLMFactory.get_service_for_tenant()` no se modifica en S3 (per-tenant keys defer S4).
- **Sistema C (provider adapters)**: REPLACE (mayoría) — `openai.py`, `_openai_compat.py`, `deepseek.py`, `kimi.py`, `qwen.py` reemplazados por **un único `litellm.py` adapter**. `gemini.py` se mantiene legacy hasta sprint siguiente (verificación nativa en LiteLLM). Helpers `_chat_model_resolver.py`, `_kwargs.py`, `_response_validation.py` permanecen (LangChain `ChatOpenAI` sigue siendo el cliente, solo apuntando a `LITELLM_BASE_URL`).
- **Sistema D (pricing snapshot)**: KEEP UNTOUCHED — `model_pricing_snapshot` es SSoT inmutable de billing. LiteLLM Proxy emite cost tracking interno (tablas `LiteLLM_SpendLogs`), pero **Nicolify NUNCA usa esos costos para billing**. `sync_litellm_pricing` ARQ task sigue siendo el único path de update (JSON oficial BerriAI → tabla Nicolify). LiteLLM Proxy mismo lee la JSON BerriAI internamente para `completion_cost()`; no hay sync bidireccional.
- **Sistema E (ARQ scheduler)**: EXTEND — `sync_litellm_pricing` sigue corriendo 03:00 UTC. Sin nuevos cron jobs en S3 (admin sync UI defer S4).
- **Sistema F (tenant API keys)**: KEEP — `tenant.openai_api_key` etc. siguen en uso para `get_service_for_tenant`. En S4 PR-1 estas se migrarán a virtual keys LiteLLM. S3 NO toca.
- **Sistema G (Streamlit admin)**: EXTEND — 1 nueva page `pages/llm-virtual-keys.py` + module `modules/llm_virtual_keys.py` con vista **read-only** del LiteLLM Proxy `/key/info` endpoint (master key). Sin CRUD (S4).
- **Sistema H (arch fitness)**: KEEP — extender `test_llm_routing_ssot.py` con guard adicional: `test_no_direct_provider_dispatch_in_router` que verifica que `router.py` NO importa `OpenAIService`/`KimiService`/etc directamente — solo `LiteLLMService`. `KNOWN_LEGACY_LLM_FILES` se expande temporalmente con `gemini.py` (deprecation S4).

### Por qué NEW svc Docker `visionarias_litellm` se justifica

LiteLLM Proxy es **una capa OSS estándar industria** (40% adopción tier-1 LLMOps 2026 — research base). Cubre 80% del problema gratis: 100+ providers OpenAI-compatible nativamente, fallback chain transparente, retry semantics, cost tracking interno, virtual keys per-tenant, hot-swap admin UI sin restart, overhead documentado <11μs (Bifrost benchmark).

**Construir esto manual reinventando = 6+ semanas dev + maintenance eternal + NIH syndrome.** La capa NEW NO es duplicada de nada: el codebase actual hace dispatch a través de adapters custom (`OpenAIService`, `KimiService`, `DeepSeekService`, `QwenService`) que son thin wrappers sobre `langchain_openai.ChatOpenAI` con `base_url` swap. **LiteLLM Proxy reemplaza el `base_url` swap + provider routing logic con una sola URL** (`http://visionarias_litellm:4000/v1`) y delega la elección de provider al config YAML del proxy.

Criterio escala 1000+ tenants:
- Agregar provider nuevo = 3 líneas YAML, 0 código Python, 0 deploy backend.
- Fallback chain (DeepSeek down → OpenAI gpt-4o-mini transparent retry) = config YAML.
- Per-tenant virtual keys con budget cap = 1 row en LiteLLM DB tabla `LiteLLM_VerificationToken` via API call admin.

Cero deuda: la public API `Settings.get_model(role)` + `LLMFactory.get_service()` no se altera. Consumers (17 hits `LLMFactory.get_service`) NO requieren cambio.

---

## 2. Domain entities (nuevas o modificadas)

**Cero nuevas entidades en S3.** No se crean modelos SQLAlchemy nuevos en Nicolify (LiteLLM Proxy maneja sus tablas vía Prisma en su propio schema `LiteLLM_*`). Solo extension de Pydantic Settings:

```python
# src/core/config.py — EXTEND class Settings
class Settings(BaseSettings):
    # ... existing fields ...

    # ── LiteLLM Proxy (PI-2 S3 PR-2) ────────────────────────────────────
    # Endpoint del proxy. En dev/prod compose: http://visionarias_litellm:4000/v1
    # Local dev sin compose: override a http://localhost:4000/v1
    LITELLM_BASE_URL: str = "http://visionarias_litellm:4000/v1"
    # Master key del proxy. En dev: sk-litellm-master-dev (warning si default).
    # En prod: rotation policy per-environment via secrets manager (Q4 — open).
    LITELLM_MASTER_KEY: str = "sk-litellm-master-dev"
    # Salt key (LiteLLM encrypts stored credentials con este key — cannot
    # change post-deployment without re-keying).
    LITELLM_SALT_KEY: str = "sk-litellm-salt-dev"
    # Toggle global. False = bypass LiteLLM, fallback al router legacy
    # (SOLO para emergency rollback. Default ON post-merge).
    LITELLM_PROXY_ENABLED: bool = True
```

D-decision (ver §10 D-3): rotation policy de keys = **defer S4** (admin UI virtual keys CRUD).

---

## 3. SQLAlchemy 2.0 Models

**Cero models nuevos en Nicolify.** LiteLLM Proxy crea sus tablas vía Prisma migration startup en su Postgres connection. Tablas creadas (no editar manualmente, no Alembic):

| Tabla LiteLLM | Propósito | ¿Nicolify lee? |
|---|---|---|
| `LiteLLM_VerificationToken` | Virtual keys (per-tenant cuando se wirea S4) | NO en S3 |
| `LiteLLM_UserTable` | User-level spend tracking | NO en S3 |
| `LiteLLM_TeamTable` | Team-level spend tracking | NO en S3 |
| `LiteLLM_SpendLogs` | Cost ledger interno | **NO** — Nicolify usa `model_pricing_snapshot` SSoT inmutable |
| `LiteLLM_BudgetTable` | Budget caps per key | NO en S3 |
| `LiteLLM_ModelTable` | Models registered hot-swap (cuando `STORE_MODEL_IN_DB=true`) | NO en S3 (defer S4 admin UI) |

D-decision (ver §10 D-1): **`visionarias_postgres` shared con DB separada `visionarias_litellm_db`**, NO el mismo `visionarias_logs` schema. Justificación: aislamiento Prisma migrations vs Alembic Nicolify. Sin esto, Prisma intentaría aplicar al schema general y Alembic perdería ownership de su schema. Mismo Postgres instance → 0 nuevos containers, 1 nueva DB declarada en `init.sql` o vía Alembic `CREATE DATABASE IF NOT EXISTS`.

---

## 4. Pydantic v2 DTOs

**Cero DTOs públicos nuevos en API Nicolify.** PR-2 es infra. Los únicos DTOs son internos a la admin Streamlit page (read-only S3):

```python
# src/admin/modules/llm_virtual_keys.py — internal DTOs (Pydantic v2)
class VirtualKeyView(BaseModel):
    """Read-only view del LiteLLM /key/info endpoint."""
    model_config = ConfigDict(from_attributes=True)

    key_alias: str | None
    user_id: str | None
    team_id: str | None
    models: list[str]
    max_budget: float | None
    spend: float
    rpm_limit: int | None
    tpm_limit: int | None
    expires: datetime | None
    metadata: dict[str, str]


class VirtualKeysList(BaseModel):
    """Aggregate response para tabla admin."""
    model_config = ConfigDict(from_attributes=True)

    keys: list[VirtualKeyView]
    total_count: int
```

**FastAPI NO expone endpoints en `/api/v1/`** para PR-2. La admin Streamlit page hace HTTP directo a `LITELLM_BASE_URL/key/info` con master key (server-side, no exposed al cliente). Esto evita superficie pública de PR-2.

---

## 5. API Routes

**CERO nuevas rutas en `src/main.py`.** PR-2 NO agrega endpoints públicos.

LiteLLM Proxy expone su propio API en `LITELLM_BASE_URL`:
- `POST /v1/chat/completions` (OpenAI-compatible — único consumer = backend Nicolify)
- `POST /key/generate`, `GET /key/info`, `POST /key/block` (admin endpoints — solo Streamlit con master key)
- `GET /health/readiness`, `GET /health/liveness` (Docker healthcheck)

Acceso desde fuera del Docker network = **prohibido**: el svc `visionarias_litellm` NO publica puerto al host (`expose: ["4000"]`, NO `ports:`). Solo accesible vía Docker internal network desde `api_dev`, `worker`, `admin_dashboard_dev`.

---

## 6. TypeScript Types (Frontend)

**CERO cambios FE.** PR-2 es 100% backend infra. `current-state/copilot.md` documenta capacidad post-merge pero la UX usuario-facing del copilot no cambia (sigue chat conversacional + cards SSE).

---

## 7. Repository Interfaces

**CERO repos nuevos.** El `PricingSnapshotRepository` existente (Sistema D) sigue siendo SSoT pricing. LiteLLM Proxy interno es opaco — no abrimos repos contra sus tablas.

---

## 8. Application Services

### 8.1 — `LiteLLMService` (NEW provider adapter)

Reemplaza `OpenAIService` + `OpenAICompatibleService` + `DeepSeekService` + `KimiService` + `QwenService` (5 adapters → 1 adapter único).

```python
# src/shared/infrastructure/llm/providers/litellm.py — NEW
"""LiteLLM Proxy provider adapter.

Single adapter that talks to ALL providers via the LiteLLM Proxy
OpenAI-compatible endpoint. Replaces per-provider adapters that
each duplicated ChatOpenAI(base_url=...) plumbing.

Flow:
  consumer
    ↓ LLMFactory.get_service().get_client(role)
  MultiRoleLLMRouter._resolve(role) → LiteLLMService
    ↓ resolves model = settings.get_model(role)
    ↓ resolves provider = settings.get_provider_for_role(role)
    ↓ LiteLLM model_name = f"{provider}/{model}"
       (e.g. "deepseek/deepseek-v4-flash", "openai/gpt-4o-mini")
  ChatOpenAI(api_key=LITELLM_MASTER_KEY,
             base_url=LITELLM_BASE_URL,
             model=litellm_model_name)
    ↓ POST /v1/chat/completions
  LiteLLM Proxy (Docker svc visionarias_litellm:4000)
    ↓ routes to provider per litellm_config.yaml
  OpenAI / DeepSeek / Kimi / Qwen / Gemini / future Anthropic etc.
"""

from typing import Any

import structlog
from langchain_core.language_models import BaseChatModel

from src.core.config import settings
from src.core.enums import ModelRole
from src.shared.infrastructure.llm.base import BaseLLMService
from src.shared.infrastructure.llm.providers._chat_model_resolver import (
    DEFAULT_OPENAI_SPEC,
    ChatBuildContext,
    ChatModelSpec,
    _build_chat_from_spec,
)
from src.shared.infrastructure.llm.providers._response_validation import (
    detect_reasoning_budget_exhaustion,
)

logger = structlog.get_logger()

_LEGACY_MODEL_TYPE_MAP: dict[str, ModelRole] = {
    "smart": ModelRole.REASONING,
    "fast": ModelRole.FAST,
    "nano": ModelRole.NANO,
    "vision": ModelRole.VISION,
    "agent": ModelRole.AGENT,
}


class LiteLLMService(BaseLLMService):
    """Single LangChain client targeting LiteLLM Proxy OpenAI-compat endpoint."""

    _DEFAULT_TEMPERATURE = 0.7
    CHAT_MODEL_SPEC: ChatModelSpec = DEFAULT_OPENAI_SPEC

    def __init__(self) -> None:
        self.api_key = settings.LITELLM_MASTER_KEY
        self.base_url = settings.LITELLM_BASE_URL
        # Cache key: ``(litellm_model_name, temperature)``.
        self._models: dict[tuple[str, float], BaseChatModel] = {}

    @staticmethod
    def _litellm_model_name(role: ModelRole) -> str:
        """Build LiteLLM model alias = '<provider>/<model>'."""
        provider = settings.get_provider_for_role(role).value  # AIProvider str
        model = settings.get_model(role)
        # LiteLLM convention: deepseek/deepseek-v4-flash, openai/gpt-4o-mini, kimi/kimi-k2.6
        return f"{provider}/{model}"

    def _get_chat_model(
        self,
        role: ModelRole,
        temperature: float | None = None,
    ) -> BaseChatModel:
        spec = self.CHAT_MODEL_SPEC
        litellm_model = self._litellm_model_name(role)
        effective_temp = self._DEFAULT_TEMPERATURE if temperature is None else temperature
        cache_key = (litellm_model, effective_temp)
        if cache_key not in self._models:
            ctx = ChatBuildContext(
                api_key=self.api_key,
                base_url=self.base_url,
                model=litellm_model,
                temperature=effective_temp,
            )
            self._models[cache_key] = _build_chat_from_spec(spec, ctx)
        return self._models[cache_key]

    @staticmethod
    def _resolve_role(model_type: str | ModelRole) -> ModelRole:
        if isinstance(model_type, ModelRole):
            return model_type
        return _LEGACY_MODEL_TYPE_MAP.get(model_type, ModelRole.REASONING)

    def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        model_type: str | ModelRole = "smart",
        **kwargs: Any,
    ) -> str:
        # … convert messages, normalize kwargs, invoke, detect reasoning exhaustion …
        # (idéntico shape a OpenAICompatibleService.generate_response actual)
        ...

    def get_embedding_model(self) -> Any:
        # LiteLLM Proxy soporta /v1/embeddings → routea a OpenAI / Qwen / etc.
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            model=settings.get_model(ModelRole.EMBEDDING),
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def get_client(
        self,
        role: ModelRole = ModelRole.REASONING,
        *,
        temperature: float | None = None,
    ) -> BaseChatModel:
        return self._get_chat_model(role, temperature=temperature)
```

### 8.2 — `MultiRoleLLMRouter` refactor

```python
# src/shared/infrastructure/llm/router.py — REFACTOR
class MultiRoleLLMRouter(BaseLLMService):
    """Routes ``BaseLLMService`` calls to LiteLLM (single adapter post-S3)."""

    def __init__(self) -> None:
        # S3 PR-2: dispatch via single LiteLLMService.
        # Legacy per-provider services kept BEHIND `LITELLM_PROXY_ENABLED=False`
        # toggle for emergency rollback ONLY. Default path = LiteLLM.
        self._litellm: BaseLLMService | None = None
        self._legacy_providers: dict[AIProvider, BaseLLMService] = {}

    def _resolve(self, role: ModelRole) -> BaseLLMService:
        if settings.LITELLM_PROXY_ENABLED:
            if self._litellm is None:
                from src.shared.infrastructure.llm.providers.litellm import LiteLLMService
                self._litellm = LiteLLMService()
            return self._litellm
        # Emergency rollback path — same dispatch as pre-S3.
        provider = settings.get_provider_for_role(role)
        if provider not in self._legacy_providers:
            self._legacy_providers[provider] = build_provider_service(provider)
        return self._legacy_providers[provider]
```

D-decision (ver §10 D-6): **legacy adapters quedan deprecated en S3, eliminación física en S4**. Razones: (1) emergency rollback toggle `LITELLM_PROXY_ENABLED=False` debe funcionar sin recompile durante la primera semana post-merge. (2) `gemini.py` mantenido legacy hasta verificar Gemini en LiteLLM Proxy (research no confirmó full reasoning support nativa).

### 8.3 — Boot-time healthcheck (`api_dev` startup)

```python
# src/main.py — EXTEND startup event
@app.on_event("startup")
async def _verify_litellm_proxy_reachable() -> None:
    """Best-effort check: log warning if LiteLLM unreachable.

    NOT bloqueante — sistema arranca aunque proxy esté down (lazy init en
    primera invocación retornaría error tendría a consumer). Esto solo
    da visibilidad temprana en logs.
    """
    if not settings.LITELLM_PROXY_ENABLED:
        logger.warning("litellm_proxy_disabled_via_toggle")
        return
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{settings.LITELLM_BASE_URL.rstrip('/v1')}/health/readiness")
            resp.raise_for_status()
        logger.info("litellm_proxy_ready", url=settings.LITELLM_BASE_URL)
    except Exception as e:
        logger.warning("litellm_proxy_unreachable_at_boot", error=str(e), url=settings.LITELLM_BASE_URL)
```

---

## 9. Agentic Surfaces (copilot + sales_agent compliance verification)

### 9.1 — Copilot (`copilot-expert` skill consultation)

**Decisión (`copilot-expert` SSoT):** PR-2 NO toca topología copilot inmutable. NO modifica:
- LangGraph state shape
- Node responsibilities (orchestrator, deep_agent harness, ask_tenant_data pipeline)
- `[COPILOT-*]` anchors (cap 36/36)
- System prompt order (slots 1-11 cementados F0-F11)
- SSE v2 protocol (canonical events)
- Trace event names (`copilot_trace_event` + `copilot_llm_call` + `copilot_routing_log`)

**Lo único que cambia para copilot:** el cliente LangChain devuelto por `LLMFactory.get_service().get_client(role)` ahora apunta a `LITELLM_BASE_URL` con `model=f"{provider}/{model}"`. `BaseChatModel.invoke()` semantics permanecen idénticas.

**Observability invariants (best-effort):** `copilot_llm_call` recorder sigue capturando `(provider, model, tokens_in, tokens_out, cost_usd, duration_ms)`. El `model` capturado ahora es `"deepseek/deepseek-v4-flash"` (LiteLLM alias) en lugar de `"deepseek-v4-flash"`. Esto requiere:

D-decision (ver §10 D-7): **`copilot_llm_call` columna `model` mantiene compat — recorder strip el prefix `provider/`** (e.g. `deepseek/deepseek-v4-flash` → `deepseek-v4-flash`) para preserve queries existentes (Streamlit `/costo-copilot` filtra by `model='deepseek-v4-flash'`). Provider se almacena separado en `provider` column ya existente.

### 9.2 — Sales Agent (`sales-agent-expert` skill consultation)

**Decisión (`sales-agent-expert` §3 PROTECTED):** PR-2 NO toca:
- `closer_studio.py` API + WS
- `BufferService.smart_debounce`
- `OutputManager.process_response` chunking
- `enrollment_*` end-to-end
- `agent_state_checkpoint` schema
- Webhook adapters (Telegram/WhatsApp/IG)
- `follow_up_engine` cadence math
- `PromptVersionModel`
- `model_pricing_snapshot` schema (extend solo via raw_payload, no en S3)
- `tool_call_dedup.py`

**Sales agent consumers de `LLMFactory.get_service()`** (8 hits): `nodes.py`, `follow_up_engine`, `appointment_reminder_engine`, `quality/judge`, `prompts/semantic`, `infrastructure/{memory/vector_store, external/safety_service}`, `application/orchestrator/conversation_pipeline`. Todos siguen recibiendo `BaseChatModel` LangChain client — semantics idénticas. PersonalityProfile compiler, brand_voice slots, channel registry, eval goldens — TODOS no afectados.

**Tier pricing >200k tokens (S12 Kimi K2.6):** PR-2 mantiene compat. `LLMFactory.get_service().generate_response()` sigue ruteando vía `OpenAICompatibleService.generate_response()` → `selected_model.invoke()`. La tier pricing math ocurre en el calculator de billing (`shared/agent_observability/cost/`), NO en el provider adapter. PR-2 no altera esto.

### 9.3 — Prompt cache (Anthropic-style + DeepSeek auto-cache)

D-decision (ver §10 D-8): LiteLLM Proxy soporta Anthropic prompt cache + OpenAI prompt cache + DeepSeek auto-cache **sin código adicional** — pasa `cache_control` markers transparente. Slot architecture (5 prefix slots cross-tenant + per-tenant + volatile per-turn) — copilot-expert mandate `compose_system_prompt` order — preservada exacta. Cache hit rate target ≥60% post-deploy = mismo objetivo F8 cementado.

### 9.4 — Trace events emitidos (S3 PR-2)

| Event | Cuándo | Capa |
|---|---|---|
| `litellm_proxy_ready` (info) | startup api_dev cuando proxy responde 200 OK | structlog |
| `litellm_proxy_unreachable_at_boot` (warning) | startup cuando proxy no responde 2s | structlog |
| `litellm_proxy_disabled_via_toggle` (warning) | cuando `LITELLM_PROXY_ENABLED=False` (rollback) | structlog |
| `litellm_dispatch_failed` (warning) | cuando `LiteLLMService.generate_response` recibe error 5xx del proxy | structlog (existente patrón `openai_compat_generate_response_failed`) |

NO se agregan nuevos `copilot_trace_event` types — el trace recorder existente captura todo.

---

## 10. D-numbered decisions (≥10 mandatory)

| # | Decisión | Rationale | Impact |
|---|---|---|---|
| **D-1** | **LiteLLM Postgres = mismo `visionarias_postgres` instance, DB separada `visionarias_litellm_db`** | Aislamiento Prisma migrations vs Alembic. Sin DB separada, Prisma intentaría aplicar al schema general → conflict con Alembic ownership. Mismo Postgres instance evita nuevo container = 0 overhead infra. | Alembic 116 migration crea `CREATE DATABASE IF NOT EXISTS visionarias_litellm_db` + grant permissions al usuario `postgres`. LiteLLM Proxy `DATABASE_URL` apunta a ese DB. |
| **D-2** | **`LITELLM_MASTER_KEY` + `LITELLM_SALT_KEY` en `.env` solo. Default dev = `sk-litellm-master-dev` con startup warning si default detected.** | LiteLLM docs: salt key NO se puede cambiar post-deploy sin re-keying credenciales. Master key rotation = manual proceso ops S3 (CRUD admin = S4). | Settings field con default, log warning at startup si `== "sk-litellm-master-dev"` y `ENVIRONMENT != "dev"`. NO hardcoded en código, NO commiteado al repo. |
| **D-3** | **Virtual keys per-tenant CRUD = read-only S3 (Streamlit page lista keys via `/key/info`). CRUD UI completo = S4 PR-1.** | S3 enfoca convergencia + LiteLLM intro mínimo viable. Virtual keys CRUD requiere tenant isolation policy + budget caps decision producto + audit trail Nicolify schema (defer). | S3: 1 admin page read-only. S4: CRUD page + tabla custom Nicolify `tenant_litellm_key_binding` (mapea `tenant_id` ↔ LiteLLM `key_alias`) — defer. |
| **D-4** | **Worker pricing sync 5min → reuse existing ARQ cron `sync_litellm_pricing` 03:00 UTC daily.** Sin nuevo scheduler 5min en S3. | Existing JSON sync de BerriAI repo es **diario** (BerriAI commitea pricing updates ~weekly cadence). 5min granularity over-engineered. La spec PR.md original mencionaba "5min sync" — **ajuste a daily existing ya cubre el use case**. | Cero cambio scheduler. `pricing_sync_task.py` sigue idéntico. Si en S4 admin UI requiere sync más frecuente → bump a hourly. |
| **D-5** | **Fallback chain config YAML: `deepseek-v4-flash → openai/gpt-4o-mini` (NANO+FAST), `deepseek-reasoner → openai/gpt-4o` (REASONING), `kimi-k2.6 → openai/gpt-4o` (AGENT).** | Cost reduction default + retry transparente cuando proveedor chino tiene outage (DeepSeek SLA conservador). OpenAI fallback siempre disponible (provider más estable). | `litellm_config.yaml` declara cada role con su `fallbacks: [...]` list. Test integration con mock 503 deepseek → expect dispatch retorna gpt-4o-mini response. |
| **D-6** | **Refactor strategy: wrap completo via LiteLLM. Legacy adapters (`openai.py`, `_openai_compat.py`, `deepseek.py`, `kimi.py`, `qwen.py`) quedan deprecated en S3 (allowlisted en arch test) — eliminación física = S4 PR-1 post-verificación 1 sprint en prod.** Excepción: `gemini.py` mantenido legacy por razones de research (Gemini en LiteLLM no validado para reasoning). | Cero deuda ≠ delete-all-now. El toggle `LITELLM_PROXY_ENABLED=False` debe funcionar la primera semana post-merge para rollback emergency. Si verificación end-to-end pasa 1 sprint → S4 PR-1 elimina adapters físicamente. | Allowlist `KNOWN_LEGACY_LLM_FILES` agrega los 5 adapters + helpers. Allowlist shrinks en S4 a 0. |
| **D-7** | **`copilot_llm_call.model` column strip prefix `provider/`** — recorder almacena `"deepseek-v4-flash"` no `"deepseek/deepseek-v4-flash"`. | Preserve queries Streamlit existentes (`/costo-copilot`, `/marketing-kb`) que filtran by model name sin prefix. Provider ya está en `provider` column separada. | Recorder regex split `litellm_model.partition("/")` → `(provider, _, model)`. `LiteLLMService` expone `_litellm_model_name(role)` para invocation, pero el callback handler captura el `model` post-split. |
| **D-8** | **Prompt cache (Anthropic + OpenAI + DeepSeek auto) preservado transparente.** PR-2 NO altera `compose_system_prompt(fragments)` ni los slot 1-11 cementados copilot F0-F11. | LiteLLM Proxy passes `cache_control` markers + `extra_body` kwargs al provider underlying. Cache hit rate target ≥60% post-deploy mantenido. | Test asserts: prompt construction code path en `copilot/orchestrator` no se modifica. Cache hit rate query post-deploy `SELECT AVG(cache_hit_rate) FROM copilot_llm_call WHERE created_at > NOW() - INTERVAL '24h'` ≥0.5. |
| **D-9** | **Cost tracking dual-source: `model_pricing_snapshot` Nicolify SSoT inmutable (billing). LiteLLM `LiteLLM_SpendLogs` = info auxiliar opcional, NUNCA path billing.** | `model_pricing_snapshot` ya tiene 4 sem de production data. Migrar SSoT mid-flight = riesgo billing histórico. LiteLLM cost = sanity check contra Nicolify, no replacement. | `copilot/observability/recording/callback_handler.py` sigue computando cost via `PricingSnapshotRepository.find_active(provider, model)` exactamente como pre-S3. Cero cambio billing path. |
| **D-10** | **Latency overhead p99 < 50ms enforce via integration test inline pre-merge.** | Spec PR.md acceptance criteria. Research base estima ~11μs proxy overhead (Bifrost benchmark) — 50ms cap deja headroom 4500x para cold-start + Docker network. | `tests/integration/test_litellm_proxy_overhead.py` mide N=100 invocations vs direct provider call (mock OpenAI), assert `p99(litellm_route - direct_route) < 50ms`. Falla → bloquea merge. |
| **D-11** | **Healthcheck endpoint = `GET /health/readiness`** (LiteLLM expone esto nativo). Docker `healthcheck:` sección con 30s interval, 10s timeout, 3 retries, 60s start_period. | Readiness chequea DB connection + provider keys cargadas. Liveness no documentado oficialmente — readiness es el canonical gate. | docker-compose.yml usa `curl -f http://localhost:4000/health/readiness`. Si falla → svc no entra al `depends_on healthy` de `api_dev`/`worker`. |
| **D-12** | **`store_model_in_db: True` activado en config YAML** (admin UI hot-swap S4 lo requiere). PERO PR-2 NO usa la admin UI todavía — los modelos están declarados en YAML. Cuando un model existe en YAML *y* en DB, **DB wins** post-S4. | Forward-compat S4 sin breaking change S3. `litellm_config.yaml` declarado en repo + checked-in = SSoT versioned hasta S4 admin UI. | YAML model_list incluye los 6 modelos activos hoy (DeepSeek V4-Flash, DeepSeek-Reasoner, Kimi K2.6, GPT-4o-mini, GPT-4o, text-embedding-3-large). |
| **D-13** | **`drop_params: True` en LiteLLM settings** = auto-filter unsupported kwargs por provider. | DeepSeek no soporta `temperature` en algunos contextos; OpenAI ignora `top_p` cuando `temperature` set. LangChain `ChatOpenAI` envía kwargs uniformemente — LiteLLM resuelve. | Reduce errores 400 silenciosos provider-specific. Existing `_kwargs.py` normalizer también activo (defense-in-depth). |
| **D-14** | **`num_workers = nproc` en LiteLLM Proxy command. Connection pool = 10 per worker.** | LiteLLM docs prod best practices. En dev compose: `--num_workers 2` (CPU minimal), pool 10. En prod compose: `--num_workers 4` (uvicorn-style), pool 10. | Total connections Postgres = 4 workers × 10 = 40 connections. `visionarias_postgres` tiene capacity 100 default. Sin issue. |
| **D-15** | **`request_timeout: 30s` en litellm_settings.** | Match Nicolify general LLM timeout. DeepSeek-Reasoner puede tardar ~20s en queries complejas — 30s deja margin sin breach. | Documentado en CONTRACT, no hardcoded por consumer. Bigger if user complaint surface. |
| **D-16** | **Admin Streamlit page `pages/llm-virtual-keys.py` = read-only S3, scope = listar virtual keys + spend per key. CRUD = S4.** | Sigue rule `admin-panel.md`: 1 PageSpec + 1 wrapper + 1 module logic. Smoke test obligatorio. | Wrapper `pages/llm-virtual-keys.py` thin (`from src.admin.modules.llm_virtual_keys import render_keys; render_keys()`). Module hace HTTP GET a `LITELLM_BASE_URL/key/info` con master key. |
| **D-17** | **Migration `116_litellm_db_marker.py` solo crea DB separada `visionarias_litellm_db`.** NO crea tablas LiteLLM (Prisma lo hace). | Idempotente raw SQL `CREATE DATABASE IF NOT EXISTS`. Prod-clone test antes deploy obligatorio. | Migration test command: ver §11. |
| **D-18** | **Arch fitness `test_llm_routing_ssot.py` extend con guard `test_router_dispatches_via_litellm_only`** que verifica `MultiRoleLLMRouter._resolve` retorna `LiteLLMService` cuando `LITELLM_PROXY_ENABLED=True`. | Ratchet defense post-S3: previene regression silent a per-provider dispatch. | `KNOWN_LEGACY_LLM_FILES` allowlist crece temporalmente con 5 adapters + helpers (D-6 timeline) — shrinks en S4. |

---

## 11. Migration Notes

### Alembic 116 — `116_litellm_db_marker.py` (idempotente raw SQL)

```python
"""LiteLLM Proxy: separate Postgres database creation marker.

S3 PR-2 PI-2. Crea DB `visionarias_litellm_db` separada del schema
Nicolify (`visionarias_logs`). LiteLLM Proxy ejecuta sus propias Prisma
migrations en startup contra esta DB. Nicolify Alembic NO ownership de
tablas `LiteLLM_*`.

Idempotente: `CREATE DATABASE IF NOT EXISTS` + GRANT.

Revision ID: 116_litellm_db_marker
Revises: 115_routing_log_tier_to_role
Create Date: 2026-04-30
"""

from __future__ import annotations

from alembic import op

revision: str = "116_litellm_db_marker"
down_revision: str | None = "115_routing_log_tier_to_role"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create separate database for LiteLLM Proxy."""
    # NOTE: CREATE DATABASE no puede ejecutarse dentro de transaction.
    # Alembic auto-wraps en transaction → must commit + use isolation level.
    # Workaround: use psycopg2 raw connection with autocommit.
    #
    # Idempotente: catch DuplicateDatabaseError.
    op.execute("COMMIT")  # release alembic transaction
    try:
        op.execute("CREATE DATABASE visionarias_litellm_db")
    except Exception as e:
        # Already exists OR user lacks privilege — log + continue.
        # Production: privilege should be granted via init.sql.
        if "already exists" not in str(e).lower():
            raise


def downgrade() -> None:
    """No-op. Dropping LiteLLM DB destroys virtual keys + spend logs."""
    # Explicit no-op por safety. Si requerido manual:
    # docker exec visionarias_postgres psql -U postgres -c "DROP DATABASE visionarias_litellm_db"
    pass
```

### Prod-clone test command (mandatory)

```bash
# Crear DB clon, aplicar migration, verify, cleanup
docker exec -t visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test;"
docker exec visionarias_postgres bash -c 'pg_dump -U postgres -s visionarias_logs | psql -U postgres -d migration_test'
docker exec -t visionarias_brain_dev bash -c 'cd /app && POSTGRES_DB=migration_test alembic stamp 115_routing_log_tier_to_role && POSTGRES_DB=migration_test alembic upgrade head'
# Verify visionarias_litellm_db creada
docker exec -t visionarias_postgres psql -U postgres -c "\l" | grep visionarias_litellm_db
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test;"
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE visionarias_litellm_db;"
```

### LiteLLM Prisma migrations (auto-aplicadas startup)

LiteLLM Proxy con `DATABASE_URL` set ejecuta `prisma migrate deploy` automático al arrancar. Tablas creadas:
`LiteLLM_VerificationToken`, `LiteLLM_UserTable`, `LiteLLM_TeamTable`, `LiteLLM_SpendLogs`, `LiteLLM_BudgetTable`, `LiteLLM_ModelTable`, `LiteLLM_OrganizationTable`, `LiteLLM_ProxyModelTable`. **Nicolify NO toca estas.**

---

## 12. File Structure (file-by-file plan, paths absolutos)

| Path | Tipo | Descripción |
|---|---|---|
| `/home/chris/AISALESHT/docker-compose.yml` | EDIT | Agregar svc `visionarias_litellm` + svc adicional `visionarias_litellm_postgres_init` (one-shot) o init.sql volume mount |
| `/home/chris/AISALESHT/docker-compose.prod.yml` | EDIT | Mismo patrón producción (image pinned, healthcheck, restart policy) |
| `/home/chris/AISALESHT/litellm_config.yaml` | NEW | Model list + fallbacks + general_settings (master_key+salt_key+store_model_in_db) + litellm_settings (drop_params, request_timeout) + router_settings (least-busy strategy) |
| `/home/chris/AISALESHT/.env.example` | EDIT | `LITELLM_BASE_URL`, `LITELLM_MASTER_KEY`, `LITELLM_SALT_KEY`, `LITELLM_PROXY_ENABLED=true` |
| `/home/chris/AISALESHT/backend/src/core/config.py` | EDIT | `Settings` agregar 4 fields (D-2 + D-12) |
| `/home/chris/AISALESHT/backend/src/shared/infrastructure/llm/providers/litellm.py` | NEW | `LiteLLMService` adapter (§8.1) |
| `/home/chris/AISALESHT/backend/src/shared/infrastructure/llm/providers/__init__.py` | EDIT | Export `LiteLLMService` |
| `/home/chris/AISALESHT/backend/src/shared/infrastructure/llm/router.py` | EDIT | `MultiRoleLLMRouter._resolve` toggle-based (§8.2) |
| `/home/chris/AISALESHT/backend/src/shared/agent_observability/recording/callback_handler.py` | EDIT (cuidadoso) | Strip provider prefix del `model` capturado (§D-7). Preserve schema `copilot_llm_call`. |
| `/home/chris/AISALESHT/backend/src/main.py` | EDIT | Startup event healthcheck best-effort (§8.3) |
| `/home/chris/AISALESHT/backend/alembic/versions/116_litellm_db_marker.py` | NEW | Idempotent raw SQL `CREATE DATABASE IF NOT EXISTS visionarias_litellm_db` |
| `/home/chris/AISALESHT/backend/src/admin/modules/llm_virtual_keys.py` | NEW | Read-only Streamlit module — list virtual keys via `LITELLM_BASE_URL/key/info` |
| `/home/chris/AISALESHT/backend/src/admin/pages/llm-virtual-keys.py` | NEW | Wrapper thin (PageSpec contract) |
| `/home/chris/AISALESHT/backend/src/admin/registry.py` | EDIT | Register PageSpec `llm-virtual-keys` |
| `/home/chris/AISALESHT/backend/tests/shared/infrastructure/llm/test_litellm_service.py` | NEW | Unit tests `LiteLLMService` adapter (mock proxy) |
| `/home/chris/AISALESHT/backend/tests/shared/infrastructure/llm/test_router_litellm_dispatch.py` | NEW | Unit test `MultiRoleLLMRouter._resolve` retorna `LiteLLMService` cuando enabled |
| `/home/chris/AISALESHT/backend/tests/integration/test_litellm_proxy_overhead.py` | NEW | Integration test latency p99 < 50ms vs direct (D-10) |
| `/home/chris/AISALESHT/backend/tests/integration/test_litellm_fallback_chain.py` | NEW | Integration test mock 503 deepseek → fallback openai gpt-4o-mini (D-5) |
| `/home/chris/AISALESHT/backend/tests/architecture/test_llm_routing_ssot.py` | EDIT | Agregar `test_router_dispatches_via_litellm_only` (§D-18) + extend `KNOWN_LEGACY_LLM_FILES` allowlist temporalmente |
| `/home/chris/AISALESHT/backend/tests/admin/test_llm_virtual_keys_smoke.py` | NEW | Smoke test admin page render + LiteLLM HTTP mock |
| `/home/chris/AISALESHT/backend/tests/migrations/test_116_litellm_db_marker.py` | NEW | Migration idempotency test |
| `/home/chris/AISALESHT/docs/domains/llm-routing.md` | EDIT (post-merge) | Cap "Capa 5 — LiteLLM Proxy motor multi-provider" + actualizar "Migration timeline" |
| `/home/chris/AISALESHT/docs/pm-nico/current-state/copilot.md` | EDIT (post-merge) | Cap "LiteLLM Proxy motor multi-provider activo" |

**NO TOCAR (cross-checked con `copilot-expert` + `sales-agent-expert`):**
- `src/modules/copilot/**` (excepto recorder D-7)
- `src/modules/sales_agent/**` (§3 protected)
- `src/shared/agent_observability/persistence/**` (pricing snapshot SSoT)
- `src/shared/agent_observability/cost/**` (billing path)
- `src/modules/copilot/evals/**` (S2 PR-3 shipped)
- `src/modules/copilot/domain/model_tier.py` (eliminado S3 PR-1)

---

## 13. Cross-Cutting Concerns

| Concern | Strategy |
|---|---|
| **Tenant isolation** | LiteLLM Proxy en S3 = global key (master). Per-tenant virtual keys = S4 PR-1. La master key NUNCA se expone al frontend ni a tenant data. Backend Python único consumer. |
| **Currency** | N/A — PR-2 no toca DTOs monetarios. `model_pricing_snapshot` SSoT preservado. |
| **Master data** | N/A — UTC store/display preservado. |
| **Spanish neutro LatAm** | Streamlit admin page strings en Spanish neutro (D-16). LLM output prompts no afectados (sales-agent voice respeta voseo tenant — sin cambio). |
| **PII** | LiteLLM `LiteLLM_SpendLogs` puede contener prompt content. Toggle `general_settings.disable_spend_logs: false` (default false = enabled). Decisión: `disable_spend_logs: True` activado en config YAML — Nicolify usa `model_pricing_snapshot` + `copilot_llm_call` SSoT, NO LiteLLM logs. Esto previene PII leak inadvertido en LiteLLM DB. |
| **Native-first dev** | Tests corren native: `cd backend && .venv/bin/pytest tests/shared/infrastructure/llm/ tests/integration/test_litellm_*.py tests/admin/test_llm_virtual_keys_smoke.py -v`. Proxy svc levantado vía `docker compose up litellm`. |
| **Observability best-effort** | Startup healthcheck warning-only (§8.3). `LiteLLMService.generate_response` warning + raise (idéntico patrón pre-S3). Recorder `copilot_llm_call` writes try/except + structlog warning + rollback (existing F0+ guarantee). |
| **Architectural fitness** | `test_llm_routing_ssot.py` extend (§D-18). Allowlist crece 5 entries (D-6 timeline) — documented commit msg. |
| **Idempotency on writes** | Migration 116 idempotent (`CREATE DATABASE IF NOT EXISTS`). LiteLLM `/key/generate` idempotente via `key_alias` natural key. |
| **Graceful degradation** | (`tessl/graceful-degradation` skill) Toggle `LITELLM_PROXY_ENABLED=False` = circuit breaker manual emergency. Timeout 30s configured (D-15). Fallback chain YAML (D-5) = retry transparent. Boot warning unreachable (§8.3) NO bloquea startup. |

---

## 14. Architecture Fitness Impact

| Test | Impact | Allowlist behavior |
|---|---|---|
| `tests/architecture/test_llm_routing_ssot.py::test_no_new_modeltier_imports` | Sin cambio (post S3 PR-1 todos consumers en ModelRole) | empty stays empty |
| `tests/architecture/test_llm_routing_ssot.py::test_no_copilot_tier_env_vars` | Sin cambio | empty stays empty |
| `tests/architecture/test_llm_routing_ssot.py::test_no_new_llm_factory_layers` | Sin cambio (LiteLLMService vive en `shared/`, no en `modules/<x>/`) | empty stays empty |
| `tests/architecture/test_llm_routing_ssot.py::test_router_dispatches_via_litellm_only` (NEW) | Verifica `MultiRoleLLMRouter._resolve` retorna `LiteLLMService` con toggle ON. Allowlist `KNOWN_LEGACY_LLM_FILES` extends temporalmente con `openai.py, _openai_compat.py, deepseek.py, kimi.py, qwen.py` (5 files). Shrinks a 0 en S4 PR-1. | crece +5 (justified, documented in commit msg) |
| `tests/architecture/test_no_new_copilot_module_imports.py` | Ratchet 22 frozen — sin cambio | empty |
| `tests/architecture/test_copilot_anchors.py` | Cap 36/36 — sin cambio | n/a |
| `tests/architecture/test_extraction_contract.py` | N/A — analytics no afectado | n/a |
| `tests/architecture/test_no_response_model_drift.py` | Verify admin Streamlit module no expone HTTP endpoints | n/a |

**Justification commit msg para allowlist crecer:**
> Allowlist extends temporalmente con 5 legacy adapters durante D-6 timeline (deprecated S3, eliminación S4 PR-1 post-verification 1 sprint en prod). Shrink a 0 obligatorio S4. Sin esto, toggle `LITELLM_PROXY_ENABLED=False` rollback emergency rompe.

---

## 15. pm-nico/current-state Updates Required

| File | Sección | Update post-merge |
|---|---|---|
| `docs/pm-nico/current-state/copilot.md` | **Capacidades runtime** | Append cap: "LiteLLM Proxy motor multi-provider activo (Docker svc `visionarias_litellm`). Dispatch único via OpenAI-compat endpoint. Fallback chain transparente: deepseek-v4-flash→gpt-4o-mini, deepseek-reasoner→gpt-4o, kimi-k2.6→gpt-4o. Hot-swap modelo + per-tenant virtual keys = S4." |
| `docs/pm-nico/current-state/copilot.md` | **Observability** | Append nota: "`copilot_llm_call.model` strip prefix `provider/` (recorder normalize). Pricing SSoT inmutable `model_pricing_snapshot`. LiteLLM `LiteLLM_SpendLogs` disabled (PII guard)." |
| `docs/pm-nico/current-state/sales_agent.md` | **No changes** (§3 protected) | Verify smoke: post-deploy 1 turn end-to-end (qualifier→product_expert→closer) sin regression. |
| `docs/domains/llm-routing.md` | **Capa 5 (NEW)** | "Capa 5 — LiteLLM Proxy (S3 PR-2)" con architecture diagram updated, fallback chain table, healthcheck endpoint. |
| `docs/domains/llm-routing.md` | **Migration timeline** | Mark S3 shipped post-merge. |

---

## 16. Test Surfaces (TDD-mandatory, RED first)

### Domain layer
- N/A (no domain entities new)

### Infrastructure layer
**RED-first tests:**

```python
# tests/shared/infrastructure/llm/test_litellm_service.py
def test_litellm_service_builds_model_alias_provider_slash_model():
    """LiteLLMService._litellm_model_name(NANO) returns 'deepseek/deepseek-v4-flash'."""
    # Arrange: settings with NANO=deepseek/deepseek-v4-flash
    # Act: service._litellm_model_name(ModelRole.NANO)
    # Assert: == "deepseek/deepseek-v4-flash"

def test_litellm_service_get_client_targets_litellm_base_url():
    """get_client returns ChatOpenAI with base_url=LITELLM_BASE_URL."""

def test_litellm_service_caches_per_model_temperature():
    """get_client(NANO, temperature=0.5) cached separately from temperature=0.7."""

def test_litellm_service_get_embedding_model_targets_litellm():
    """get_embedding_model returns OpenAIEmbeddings with base_url=LITELLM_BASE_URL."""

# tests/shared/infrastructure/llm/test_router_litellm_dispatch.py
def test_router_resolve_returns_litellm_when_toggle_on():
    """LITELLM_PROXY_ENABLED=True → _resolve(role) returns LiteLLMService."""

def test_router_resolve_returns_legacy_when_toggle_off():
    """LITELLM_PROXY_ENABLED=False → _resolve(role) returns per-provider service."""

def test_router_litellm_singleton_across_roles():
    """Same LiteLLMService instance for NANO + REASONING + AGENT."""
```

### Application layer
**RED-first:**

```python
# tests/integration/test_litellm_proxy_overhead.py  (D-10)
@pytest.mark.integration
async def test_litellm_overhead_p99_under_50ms():
    """N=100 invocations: LiteLLM-routed p99 - direct-mock p99 < 50ms."""
    # Setup: mock OpenAI direct, mock LiteLLM Proxy (httpx mock)
    # Run: 100 calls each path
    # Assert: numpy.percentile(deltas, 99) < 0.050

# tests/integration/test_litellm_fallback_chain.py  (D-5)
@pytest.mark.integration
async def test_fallback_deepseek_to_openai_on_503():
    """Mock LiteLLM proxy: deepseek 503 → openai gpt-4o-mini response."""
```

### API layer
**RED-first:**

```python
# tests/admin/test_llm_virtual_keys_smoke.py
def test_llm_virtual_keys_page_renders_read_only():
    """Streamlit page renders + HTTP mock /key/info returns dummy keys."""
```

### Architecture layer
**RED-first:**

```python
# tests/architecture/test_llm_routing_ssot.py (EDIT — append)
def test_router_dispatches_via_litellm_only():
    """MultiRoleLLMRouter._resolve must NOT import per-provider Services
    when LITELLM_PROXY_ENABLED=True (default)."""
    # AST scan router.py: forbidden imports = {OpenAIService, KimiService,
    # DeepSeekService, QwenService} unless guarded by LITELLM_PROXY_ENABLED check.
```

### Migration layer
**RED-first:**

```python
# tests/migrations/test_116_litellm_db_marker.py
def test_migration_116_idempotent():
    """Running upgrade twice does not raise."""

def test_migration_116_creates_litellm_db():
    """Post-upgrade: \\l shows visionarias_litellm_db."""
```

### Eval/agentic layer
- **Copilot evals (`copilot-expert`):** smoke run conversación 1 turn post-deploy. NO se agregan eval goldens nuevos (PR-2 infra, no semantic).
- **Sales agent evals (`sales-agent-expert`):** weekly cron `weekly_sales_agent_quality_eval` corre lunes 07:00 UTC — primera corrida post-merge debe mantener score ≥ baseline (no regression).

---

## 17. Docker compose svc spec + healthcheck

```yaml
# docker-compose.yml — APPEND services section
  litellm:
    image: ghcr.io/berriai/litellm-database:v1.83.10-stable
    container_name: visionarias_litellm
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_started
    environment:
      DATABASE_URL: "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/visionarias_litellm_db"
      LITELLM_MASTER_KEY: "${LITELLM_MASTER_KEY}"
      LITELLM_SALT_KEY: "${LITELLM_SALT_KEY}"
      OPENAI_API_KEY: "${OPENAI_API_KEY}"
      DEEPSEEK_API_KEY: "${DEEPSEEK_API_KEY}"
      KIMI_API_KEY: "${KIMI_API_KEY}"
      DASHSCOPE_API_KEY: "${DASHSCOPE_API_KEY}"
      GEMINI_API_KEY: "${GEMINI_API_KEY}"
      DISABLE_SPEND_LOGS: "true"  # PII guard (§13)
    volumes:
      - ./litellm_config.yaml:/app/config.yaml:ro
    command:
      - "--config"
      - "/app/config.yaml"
      - "--port"
      - "4000"
      - "--num_workers"
      - "2"
    expose:
      - "4000"
    networks:
      - internal_net
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:4000/health/readiness"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          cpus: '1.00'
          memory: 768M
        reservations:
          memory: 256M
```

**`api_dev` + `worker` `depends_on` extend:**
```yaml
  api_dev:
    depends_on:
      redis:
        condition: service_healthy
      qdrant:
        condition: service_started
      postgres:
        condition: service_started
      litellm:
        condition: service_healthy   # NEW
```

---

## 18. `litellm_config.yaml` initial spec

```yaml
# /home/chris/AISALESHT/litellm_config.yaml
# SSoT model routing config. Versioned in git hasta S4 admin UI hot-swap.
# 2026-04-30 — S3 PR-2 PI-2.

model_list:
  # NANO + FAST — DeepSeek V4-Flash (cost reduction 4-15x)
  - model_name: deepseek/deepseek-v4-flash
    litellm_params:
      model: deepseek/deepseek-v4-flash
      api_key: "os.environ/DEEPSEEK_API_KEY"
    model_info:
      supported_environments: ["dev", "staging", "production"]

  # REASONING — DeepSeek-Reasoner
  - model_name: deepseek/deepseek-reasoner
    litellm_params:
      model: deepseek/deepseek-reasoner
      api_key: "os.environ/DEEPSEEK_API_KEY"

  # AGENT — Kimi K2.6
  - model_name: kimi/kimi-k2.6
    litellm_params:
      model: moonshot/kimi-k2.6
      api_key: "os.environ/KIMI_API_KEY"

  # FALLBACK + VISION + EMBEDDING — OpenAI
  - model_name: openai/gpt-4o-mini
    litellm_params:
      model: openai/gpt-4o-mini
      api_key: "os.environ/OPENAI_API_KEY"

  - model_name: openai/gpt-4o
    litellm_params:
      model: openai/gpt-4o
      api_key: "os.environ/OPENAI_API_KEY"

  - model_name: openai/text-embedding-3-large
    litellm_params:
      model: openai/text-embedding-3-large
      api_key: "os.environ/OPENAI_API_KEY"

router_settings:
  routing_strategy: "least-busy"
  num_retries: 2
  timeout: 30
  fallbacks:
    - "deepseek/deepseek-v4-flash": ["openai/gpt-4o-mini"]
    - "deepseek/deepseek-reasoner": ["openai/gpt-4o"]
    - "kimi/kimi-k2.6": ["openai/gpt-4o"]
  allowed_fails: 3
  cooldown_time: 30  # seconds before retry-after-fail

litellm_settings:
  drop_params: True            # D-13 — auto-filter unsupported kwargs
  set_verbose: False
  request_timeout: 30          # D-15
  cache: false                 # NICETOhave S4

general_settings:
  master_key: "os.environ/LITELLM_MASTER_KEY"   # D-2
  salt_key: "os.environ/LITELLM_SALT_KEY"        # D-2
  database_url: "os.environ/DATABASE_URL"
  database_connection_pool_limit: 10              # D-14
  database_connection_timeout: 60
  store_model_in_db: True                         # D-12 (forward-compat S4)
  disable_spend_logs: True                        # PII guard §13
```

---

## 19. Research Notes

| Source | Date accessed | Version | Key takeaway | Why over alternatives |
|---|---|---|---|---|
| https://github.com/BerriAI/litellm/releases | 2026-04-30 | v1.83.10-stable | Pin `v1.83.10-stable` (Q2 2026 latest stable). Min Python 3.10 required. | Avoid `main-stable` floating tag (reproducibility) + avoid pre-1.83 pre-Python 3.10 break. |
| https://docs.litellm.ai/docs/proxy/deploy | 2026-04-30 | current | `litellm-database` image required for DB features. Master key starts `sk-`. Salt key encrypts credentials, NO post-deploy change. Prisma migrations auto-startup. | Standard prod recipe. |
| https://docs.litellm.ai/docs/proxy/db_info | 2026-04-30 | current | Tables prefixed `LiteLLM_*` (Prisma-managed). Separate database recommended for isolation from app Alembic. | D-1 decision separate DB justified. |
| https://docs.litellm.ai/docs/proxy/virtual_keys | 2026-04-30 | current | `/key/generate`, `/key/info`, `/key/block` endpoints. Per-key budgets, model allowlist, rpm/tpm limits, metadata. | D-3 read-only S3 → CRUD S4 path verified. |
| https://docs.litellm.ai/docs/proxy/prod | 2026-04-30 | current | `--num_workers $(nproc)`, pool 10/worker, `request_timeout: 30s`. `DISABLE_SCHEMA_UPDATE=true` for Helm pre-sync (NOT needed compose). `LITELLM_SALT_KEY` encrypts stored credentials. | D-14 + D-15 calibrated. |
| https://docs.litellm.ai/docs/proxy/configs | 2026-04-30 | current | `model_list` + `litellm_params.model: <provider>/<id>` format. `os.environ/<VAR>` references. `drop_params: True` defense. `fallbacks: [{model_name: [fallback_list]}]`. `least-busy` strategy. | D-5 + D-13 + §18 YAML calibrated. |
| `docs/pm-nico/research/2026-04-30-llm-config-storage-best-practices.md` (internal) | 2026-04-30 | n/a | Hybrid 3-capa winning pattern (~60% adoption). LiteLLM resuelve 80%. <11μs overhead Bifrost benchmark. | Architecture validation D-10 50ms cap conservador (4500x headroom). |

---

## 20. Open Questions for PM

1. **Q1 — `LITELLM_MASTER_KEY` rotation policy production:** No es bloqueante para S3 PR-2 (admin UI completo S4 lo formaliza). Decisión PM: ¿manual ops process documentado en `docs/ops/` antes de deploy prod, o esperar S4? **Recomendación architect**: documentar manual process pre-prod-deploy.

2. **Q2 — Spending logs PII vs cost reconciliation:** D-9 + §13 settean `disable_spend_logs: True` (Nicolify usa SSoT inmutable `model_pricing_snapshot`). Si producto quiere spending dashboards LiteLLM-native (mejor UI default), trade-off es PII en LiteLLM DB. **Recomendación architect**: keep disabled S3, revisitar producto S4 si admin UI hot-swap requiere spending real-time view.

3. **Q3 — `gemini.py` legacy adapter destino:** D-6 lo mantiene legacy. Research no validó Gemini en LiteLLM Proxy para reasoning. ¿PM aprueba spike S4 para verificar Gemini en LiteLLM, o eliminar Gemini support por completo (tenant data show 0% Gemini usage current)? **Recomendación architect**: spike S4 (1 día) — Gemini OSS adopting bajando, pero brand cross-vendor preserve.

4. **Q4 — `current-state/copilot.md` cap update timing:** post-merge inmediato o post-1-sprint-verification? **Recomendación architect**: post-merge inmediato (cap "activo" — refleja reality runtime).

5. **Q5 — LiteLLM `model_name` aliases internals vs Nicolify-friendly aliases:** YAML usa `deepseek/deepseek-v4-flash` (LiteLLM convention). `LiteLLMService._litellm_model_name(role)` construye exactamente esto. ¿PM quiere Nicolify-friendly alias layer (`nano-default` → `deepseek/deepseek-v4-flash`) ahora o defer S4? **Recomendación architect**: defer S4 (admin UI lo justifica). S3 mantiene transparente provider/model.

---

## 21. Acceptance criteria (cross-checked PR.md §Aceptación)

- [ ] Tests verde: `cd backend && .venv/bin/pytest tests/shared/infrastructure/llm/ tests/integration/test_litellm_*.py tests/admin/test_llm_virtual_keys_smoke.py tests/migrations/test_116_*.py tests/architecture/test_llm_routing_ssot.py -v`
- [ ] Lint verde: `cd backend && .venv/bin/ruff check src/ && .venv/bin/ruff format --check src/`
- [ ] Arch fitness verde: `cd backend && .venv/bin/pytest tests/architecture/ -x -q`
- [ ] `docker compose ps` shows `visionarias_litellm` healthy post `docker compose up -d litellm`
- [ ] Manual dispatch test: `curl -X POST http://localhost:4000/v1/chat/completions -H "Authorization: Bearer ${LITELLM_MASTER_KEY}" -d '{"model":"deepseek/deepseek-v4-flash","messages":[{"role":"user","content":"ping"}]}'` returns 200 OK
- [ ] Latency overhead p99 < 50ms (D-10 integration test)
- [ ] `litellm_config.yaml` versioned in repo
- [ ] IMPL-LOG.md completo
- [ ] REVIEW.md PASS
- [ ] RESULT.md
- [ ] `current-state/copilot.md` updated cap "LiteLLM Proxy"
- [ ] `docs/domains/llm-routing.md` updated cap 5 + migration timeline
- [ ] Decisiones D-1..D-18 registradas
- [ ] Sales agent quality eval weekly post-merge: score ≥ baseline (no regression)
- [ ] Copilot conversation manual smoke 1 turn end-to-end OK

---

<!-- @pm: CONTRACT.md ready (architect-empowered). -->
