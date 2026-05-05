---
story_id: sales-agent-litellm-canonicalization
surface: BE
sub_architect: /architect (acting as architect-be — service-story sin /ux ni /architect-fe ni /architect-agentic)
arch_version: 1
last_modified: 2026-05-05T03:30Z
links:
  spec: "01-spec.md"
  story_md: "00-story.md"
  story_yaml: "../../../../../../product/stories/sales-agent/sales-agent-litellm-canonicalization.yaml"
  capability_yaml: "../../../../../../product/capabilities/sales-agent/sales-observability-cost-tracking.yaml"
  domain_doc: "../../../../../../domains/llm-routing.md"
  rules:
    - ".claude/rules/backend-ddd.md"
    - ".claude/rules/tenant-isolation.md"
    - ".claude/rules/backend-migrations.md"
    - ".claude/rules/anti-default-flip-audit.md"
    - ".claude/rules/anti-duplication.md"
    - ".claude/rules/architectural-fitness.md"
    - ".claude/rules/tdd-mandatory.md"
    - ".claude/rules/master-data.md"
---

# 03-arch-be — sales-agent-litellm-canonicalization

> Service-story BE-only. NO UI surface, NO LangGraph state-machine surface (sales_agent
> graph se mantiene tal cual; solo cambia el callback observability + provider/cost source).
> Owner builders: `dev-team` Opus 4.7 (todos los tickets). Auditor: `auditor-be`.

## 0. Decisión arquitectónica clave

**Three SSoT collapse:** (1) cost runtime ahora viene de `kwargs["response_cost"]` que LiteLLM
computa nativo en su `CustomLogger` callback — `calculate_cost()` se retira del path runtime
(X2). (2) `provider` ahora se deriva via `litellm.get_llm_provider(model)[1]` — la 4-tupla
canónica de LiteLLM, con la posición 1 = `custom_llm_provider`. (3) Single execution path:
`LiteLLMService` es el único `BaseLLMService` runtime; los 6 adaptadores legacy
(`openai.py`, `deepseek.py`, `kimi.py`, `qwen.py`, `gemini.py`, `_openai_compat.py`) son
borrados, el flag `LITELLM_PROXY_ENABLED` se elimina del `Settings` (no path-toggle, ergo
no flip). `model_pricing_snapshot` queda como audit ledger inmutable, alimentado por
`make sync-pricing` (extiende existing `litellm_sync.py`) — NO consultado en runtime de
turn.

**Tradeoff:** sin `LITELLM_PROXY_ENABLED=False` flag-toggle se pierde el rollback in-flight.
Mitigación: pre-T4 deletion + T7 tests audit garantizan que el path nuevo es correcto en
toda la suite; rollback emergencia = `git revert` del commit (desktop-procedure
explicitada en `docs/domains/llm-routing.md`). Justificación Chris ratificada (X1, A6):
"robustez/escalabilidad > costo hoy". Anti-default-flip-audit aplicado a T5 con extra rigor
(grep + run both flag values + commit body — ver T5 detalle).

**Flag flip semantics — clarificación crítica:** este cleanup NO es un flag flip "False→True";
es un flag deletion "True→removed". Default actual = `True` (post S3 PR-2, ya en prod desde
2026-04-30). El flag se elimina como atributo de `Settings` y todos los call paths se
simplifican a la rama `True` only. Tests que mockean `LITELLM_PROXY_ENABLED=False` deben
borrarse (probaban path muerto). Anti-default-flip-audit 4-step se aplica al **deletion
path** (Step 1: grep tests path viejo `LITELLM_PROXY_ENABLED=False`; Step 2: migrar / borrar
tests; Step 3: run suite con flag = `True` only; Step 4: commit body documenta).

## 1. Existing systems audit (NO NEW LAYER rule)

### Source of evidence
- [x] Self-run greps (Path B fallback — no CONTEXT-BRIEF.md disponible)
- [x] Grep matrix ejecutado pre-architecture

### Audit cross-module ejecutado

```bash
# Sistema 1: callback handler base (T1)
grep -rn "class.*BaseCallbackHandler\|class.*CallbackHandler" backend/src/shared/agent_observability/recording/
# → BaseAgentCallbackHandler (lifted shared S11A) — EXTEND, no mirror

# Sistema 2: pricing sync (T2)
grep -rn "sync_pricing\|litellm_sync" backend/src/shared/ backend/src/modules/
# → backend/src/shared/agent_observability/pricing/litellm_sync.py + workers/pricing_sync_task.py — EXTEND, no NEW

# Sistema 3: pricing snapshot repo (T3)
grep -rn "PricingSnapshotRepository\|model_pricing_snapshot" backend/src/shared/
# → shared/agent_observability/persistence/pricing_snapshot_repository.py — EXTEND, no NEW

# Sistema 4: ARQ scheduler (T2)
grep -rn "sync_litellm_pricing\|cron(" backend/src/workers/settings.py
# → cron 03:00 UTC ya existe — EXTEND el callable

# Sistema 5: tenant model (T6)
grep -rn "openai_api_key\|deepseek_api_key\|kimi_api_key\|dashscope_api_key" backend/src/modules/iam/
# → 5 columnas + domain Tenant Pydantic + repo + factory._extract_tenant_key — EXTEND (deprecate-then-drop)

# Sistema 6: LLM router (T5)
grep -rn "LITELLM_PROXY_ENABLED\|build_provider_service" backend/src/
# → router.py + factory.py + main.py + admin/llm_virtual_keys.py — EXTEND (simplify), no NEW

# Sistema 7: arch fitness (T8)
ls backend/tests/architecture/test_llm_routing_ssot.py
# → existe, KNOWN_LEGACY_LLM_FILES = set() ya. Solo agregar nuevas assertions — EXTEND.
```

### Sistemas existentes encontrados

| Sistema | Path | Enum/Config | Factory/Router | Providers/Adapters | Estado |
|---|---|---|---|---|---|
| Callback handler base | `shared/agent_observability/recording/base_callback_handler.py::BaseAgentCallbackHandler` | — | Template Method | subclases sales+copilot | active, lifted shared S11A |
| Cost calculator | `shared/agent_observability/cost/calculator.py::calculate_cost` | — | función pura | — | active (retain como utility) |
| FX resolver | `shared/agent_observability/cost/fx_resolver.py::FXResolver.default()` | — | factory classmethod | — | active |
| Pricing resolver | `shared/agent_observability/pricing/resolver.py::PricingResolver` | — | resolver runtime | — | active (retain — sigue usándose para `pricing_version_id` denormalisation, no para cost compute) |
| LiteLLM sync | `shared/agent_observability/pricing/litellm_sync.py::sync_pricing` | URL constant | — | — | active, daily ARQ cron 03:00 UTC |
| Pricing sync ARQ task | `shared/agent_observability/workers/pricing_sync_task.py::sync_litellm_pricing` | — | ARQ task | — | active, registrado en `WorkerSettings.functions` + `SchedulerSettings.cron_jobs` |
| LiteLLM service | `shared/infrastructure/llm/providers/litellm.py::LiteLLMService` | — | concrete BaseLLMService | LiteLLM Proxy adapter | active, canonical post-cleanup |
| Multi-role router | `shared/infrastructure/llm/router.py::MultiRoleLLMRouter` | — | facade | dual-path (litellm vs legacy) | T5 simplifica a litellm-only |
| Tenant API key columns | `iam/infrastructure/models/tenant_model.py:33-37` | — | — | — | T6 deprecate→drop (4 cols + 1 retained: gemini_api_key) |
| Arch fitness ratchet | `tests/architecture/test_llm_routing_ssot.py::KNOWN_LEGACY_LLM_FILES` | `set()` | — | — | active, T8 expande assertions |
| Tests con mocks legacy | `tests/shared/infrastructure/llm/test_provider_routing.py`, `test_openai_compat_providers.py`, `test_router_litellm_dispatch.py`, ~17 más | — | — | — | T7 migra → LiteLLMService mock + delete obsoletos |

### Decisión por sistema (EXTEND > REPLACE > NEW priority)

- **Callback handler (T1)**: **EXTEND** — modificar `BaseAgentCallbackHandler._extract_provider_and_model` (drop "/" partition) + agregar nuevo `CostRecorderCustomLogger(litellm.integrations.custom_logger.CustomLogger)` que envuelve el handler para registrar `kwargs["response_cost"]`. Anti-duplication: NO crear mirror per-agent. Ambos sales + copilot consumen la misma extensión via shared.
- **Cost calculator (X2)**: **REPLACE en runtime path** — `_persist_llm_call` deja de llamar `calculate_cost()`; en su lugar consume `kwargs["response_cost"]` desde el `CostRecorderCustomLogger`. `calculate_cost()` se conserva como **utility de reconciliación** (billing disputes, audit recompute) — invocable manual, NO en hot path.
- **LiteLLM sync (T2)**: **EXTEND** — `litellm_sync.py` ya lee upstream JSON. T2 agrega: (a) fuente local `litellm_config.yaml model_list` para validar que cada modelo en uso está reconocido por LiteLLM (`litellm.model_cost` registry); (b) `make sync-pricing` Makefile target que invoca el ARQ task localmente; (c) reconciliation drift detection (warn si upstream model entry diverge de snapshot activo).
- **Pricing snapshot repo (T3)**: **EXTEND** — agregar Alembic migration de repair (no nuevo repo).
- **LLM router (T5)**: **REPLACE simplify** — eliminar branch `if settings.LITELLM_PROXY_ENABLED` + `build_provider_service` + dual-path. Router queda con LiteLLMService singleton únicamente.
- **Tenant API key cols (T6a/T6c)**: **EXTEND deprecate→drop** — Stripe-style expand-contract. T6a: NULL las 4 cols + Pydantic dominio marca deprecated + factory deja de leer. T6b: deploy-and-verify gate. T6c: DROP COLUMN + remove Pydantic fields + remove repo wiring. `gemini_api_key` queda fuera del scope (Q4 ratificada decisión: drop solo las 4 specifically).
- **Arch fitness (T8)**: **EXTEND** — agregar tests `test_no_legacy_adapter_imports` + `test_settings_has_no_litellm_proxy_enabled_attr` + `test_known_legacy_files_set_is_empty` al file existente.
- **Tests audit (T7)**: **REPLACE** ~20 tests que mockean per-provider Services → mockean `LiteLLMService.generate_response` + `litellm.completion`. Borrar tests que probaban path legacy (`test_provider_routing.py` bloque `LegacyDispatch`, `test_openai_compat_providers.py`).

(**NEW solo en T1**: clase nueva `CostRecorderCustomLogger` en `shared/agent_observability/recording/cost_recorder.py` — no existe equivalente. Justificación: LiteLLM `CustomLogger` se registra via `litellm.callbacks = [...]`, conceptualmente distinto del LangChain `BaseCallbackHandler` (este último opera dentro del runtime LangChain via `RunnableConfig.callbacks`). Los dos coexisten — el LangChain handler captura el span semántico (provider/model/tokens del LangChain message), el LiteLLM CustomLogger captura `kwargs["response_cost"]` LiteLLM-native. Ambos persisten al mismo `*_llm_call` row via id de correlación `run_id`. El `BaseAgentCallbackHandler` se modifica para consumir el cost desde un cache thread-safe que el `CostRecorderCustomLogger` populates. Ver § 4 detalle.)

## 2. Critical decisions encoded (per architect prompt § "Critical architectural decisions")

### 2.1 LiteLLM `CustomLogger` callback registration

**Where:** `backend/src/main.py` lifespan (FastAPI startup hook). Registration es proceso-level
(litellm es un módulo singleton); registrar 1 vez at boot evita race conditions worker vs api.
También se registra en `backend/src/workers/settings.py::WorkerSettings.on_startup` (workers
ejecutan extraction orchestrators que invocan LLM via LiteLLM).

```python
# backend/src/main.py — dentro del @app.on_event("startup") existente
import litellm
from src.shared.agent_observability.recording.cost_recorder import CostRecorderCustomLogger

# 1 instancia process-wide. State puro (cache thread-safe by run_id) — sin tenant context.
# El BaseAgentCallbackHandler captura tenant context y luego consulta el cache por run_id.
litellm.callbacks = [CostRecorderCustomLogger()]
```

**Lifecycle:** singleton process-wide. NO per-request, NO per-tenant (tenant context fluye via
`BaseAgentCallbackHandler`, no via litellm). El `CostRecorderCustomLogger` es **stateful with
TTL cache** — persiste `kwargs["response_cost"]` keyed by `litellm_call_id` (LiteLLM lo
genera per request) + `model` + `start_time` por hasta 60s post-completion, después del cual
el LangChain `on_llm_end` ya consumió y purgó la entry. Si nunca se consume → TTL expire +
structlog warn `cost_recorder_orphan_entry`.

**Bridge LangChain→LiteLLM:** ambos callbacks reciben el mismo `litellm_call_id` cuando
LiteLLM responde. El LangChain `BaseAgentCallbackHandler.on_llm_end` ahora:
1. Extrae `litellm_call_id` desde `response.llm_output["litellm_call_id"]` (o equivalente).
2. Consulta `CostRecorderCustomLogger.pop_cost(litellm_call_id)` → retorna `Decimal` o `None`.
3. Si `None` (cache miss / non-LiteLLM call / pre-cleanup compatibility) → `cost_usd=0` +
   structlog warn `cost_recorder.cache_miss` con context. Test scenario.
4. Si `Decimal` → `cost_usd = value` directamente. Snapshot params se denormalizan via
   `PricingResolver` (para `pricing_version_id` + `input_unit_cost_usd` audit fields), pero
   el cálculo total NO se re-ejecuta.

### 2.2 `get_llm_provider(model)` failure mode

**Default:** si `litellm.get_llm_provider(model)` raises `litellm.exceptions.BadRequestError`
(modelo no reconocido), el callback handler:
1. Log structured warning `cost_recorder.unknown_provider` con `model=<value>` + `error_class`.
2. Persiste `provider="unknown"` en `copilot_llm_call` / `sales_agent_llm_call`.
3. Persiste `cost_usd = None` (NULL — distingue de un cost = $0 valid case como turn cancelado).
4. NO bloquea el turn. Best-effort observability.

**Test:** `test_litellm_canonicalization.py::test_unknown_model_records_unknown_provider_and_null_cost`.

**Schema implication:** `copilot_llm_call.cost_usd` ya es `NUMERIC(16,10) NULL` post-Phase-1
observability rebuild. Verify con grep + alembic history. Si NOT NULL → T1 deliverable agrega
migration `ALTER COLUMN cost_usd DROP NOT NULL` idempotente.

### 2.3 `model_pricing_snapshot` schema migration (T3)

**Schema actual (verified via grep + repo class):**

```sql
CREATE TABLE model_pricing_snapshot (
  id UUID PRIMARY KEY,
  provider VARCHAR(64) NOT NULL,        -- ya varchar, acepta "deepseek"/"openai"/"kimi"/etc.
  model VARCHAR(255) NOT NULL,          -- ya varchar, acepta "deepseek/deepseek-v4-flash"
  input_cost_per_token NUMERIC(20,12),
  output_cost_per_token NUMERIC(20,12),
  cache_read_cost_per_token NUMERIC(20,12),
  cache_write_cost_per_token NUMERIC(20,12),
  batch_input_cost_per_token NUMERIC(20,12),
  raw_payload JSONB,
  source VARCHAR(32),
  source_etag VARCHAR(64),
  valid_from TIMESTAMPTZ NOT NULL,
  valid_to TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT uq_provider_model_active UNIQUE (provider, model, valid_to)
);
CREATE INDEX ix_pricing_snapshot_provider_model ON model_pricing_snapshot(provider, model);
```

**A1 (slashed) implication:** `model` column ya acepta `/`. NO se requiere ALTER. El
backfill T3 actualiza filas históricas que tengan `provider='openai' AND model LIKE 'deepseek%' OR 'kimi%' OR 'qwen%'` para:
1. Re-tag `provider` al canonical via `litellm.get_llm_provider(model)[1]`.
2. Update `model` field a forma slashed cuando aplique (e.g. `'deepseek-v4-flash' → 'deepseek/deepseek-v4-flash'`).
3. Transaction atomic con backup table `model_pricing_snapshot_backup_pre_T3` (CTAS).

**Idempotency:** migration usa `IF EXISTS` para backup table create (re-runnable) + `WHERE id IN (...)` para excluir filas ya re-tagged (chequea pattern `provider='openai' AND model LIKE 'deepseek/%'` post-update).

### 2.4 `tenant.{provider}_api_key` removal blast radius (T6a/T6c)

**Callers (verificado via grep):**

```bash
grep -rn "tenant\.\(openai\|deepseek\|kimi\|dashscope\)_api_key" backend/src/
```

→ 5 callers identificados:
1. `iam/infrastructure/models/tenant_model.py:33-37` — column declaration (target T6c).
2. `iam/infrastructure/repositories/tenant_repository.py:45-49,66-70` — read+write Pydantic↔SQLA (target T6a→T6c).
3. `iam/domain/tenant.py:17-21,32-47` — Pydantic model fields (target T6a marca deprecated, T6c remove).
4. `iam/api/settings.py:118` — endpoint serialization (target T6a remove from response_model).
5. `shared/infrastructure/llm/factory.py:67-71` — `_extract_tenant_key` reads (target T6a stub return None, T6c remove method).

**Post-T6a state:** `factory._extract_tenant_key` retorna siempre `None` (master key path only via
LiteLLMService que lee `os.environ/{PROVIDER}_API_KEY` desde `litellm_config.yaml`). Single
caller `factory.get_service_for_tenant` keepea path "no user key but allowed to use platform"
→ retorna router singleton.

**Verify zero non-null in prod (T6a deploy gate):** Streamlit `/admin/tenants` query +
structured log query `SELECT COUNT(*) FROM tenants WHERE openai_api_key IS NOT NULL OR deepseek_api_key IS NOT NULL OR kimi_api_key IS NOT NULL OR dashscope_api_key IS NOT NULL` → expect 0 across 1-sprint window.

### 2.5 ARQ worker integration (T2)

**Existing (read first):** `sync_litellm_pricing` ARQ task ya está registrado en
`WorkerSettings.functions` + `SchedulerSettings.cron_jobs` con `cron(sync_litellm_pricing,
hour=3, minute=0)` (03:00 UTC daily). Queue: ARQ default queue (mismo Redis que el resto de
workers nicolify, `settings.REDIS_URL`).

**T2 modifications:**
1. `litellm_sync.py::sync_pricing` agrega secondary source: parsea `litellm_config.yaml`
   model_list → cross-check que cada `model_name` tiene entrada en `litellm.model_cost`.
   Si falta → structlog warn `pricing_sync.config_yaml_model_unknown_to_litellm` con
   `model=<value>`.
2. Reconciliation drift: post-upsert, compara cada nueva snapshot row vs upstream
   `model_prices_and_context_window.json` original entry → si delta > 0.0001 USD → structlog
   warn `pricing_sync.upstream_drift_detected` con `model`, `field`, `delta`.
3. Makefile target `sync-pricing` invoca el ARQ task localmente (NO via worker queue, sync
   call para CI debug).

### 2.6 `make sync-pricing` Makefile target

```makefile
# Run LiteLLM pricing sync sync (one-shot, NOT via ARQ queue) — for CI debug / manual ops.
# Native-first: no docker exec.
sync-pricing:
	cd backend && .venv/bin/python -c "import asyncio; from src.shared.agent_observability.workers.pricing_sync_task import sync_litellm_pricing; from src.core.database import SessionLocal; result = asyncio.run(sync_litellm_pricing({})); exit(0 if result['ok'] else 1)"
```

**Dependencies:**
- DB available (`DATABASE_URL` env var) — conexión vía `SessionLocal`.
- Internet reachable (httpx GET to `raw.githubusercontent.com`).
- LiteLLM Python pkg installed (`backend/.venv/`).

**Error semantics:**
- exit 0 on success (rows_added/updated returned).
- exit 1 on connection failure / parsing error / SQL exception.
- structlog logs JSON output con `result` dict para capture por CI.

**Trigger primario (A6):** ARQ scheduler 03:00 UTC daily (ya configurado). `make sync-pricing`
es backup CI manual para debug. NO github actions cron — ratificado A6 mantiene security
perimeter dentro Nicolify.

### 2.7 Anti-flip audit checklist (T5) — 5-line OBLIGATORIO

> Per `.claude/rules/anti-default-flip-audit.md` — flag deletion = special case. Default
> actual `True` (post S3 PR-2); deletion path es "True → removed". Tests que mockean
> `LITELLM_PROXY_ENABLED=False` probaban path muerto post-S3 → MUST delete or migrate.

```bash
# Step 1 — grep tests path viejo (LITELLM_PROXY_ENABLED=False MOCKS)
grep -rln "LITELLM_PROXY_ENABLED.*False\|setattr.*LITELLM_PROXY_ENABLED" backend/tests/ 2>/dev/null
# Expected: ~7 files including test_provider_routing.py, test_router_litellm_dispatch.py

# Step 2 — mock migration pattern
# Para cada test detectado:
# - Si test prueba LiteLLM dispatch path (default True path) → DELETE el setattr line
# - Si test prueba legacy adapter path (False path) → DELETE the entire test (legacy gone)
# - NO migrar a "monkeypatch.setattr(..., True)" — innecesario, default ya es True post-removal

# Step 3 — dual-flag test command (verify both old + new behavior pre-removal)
cd backend && .venv/bin/pytest tests/shared/infrastructure/llm/ -x -q --tb=short  # current default True
LITELLM_PROXY_ENABLED=false .venv/bin/pytest tests/shared/infrastructure/llm/ -x -q  # legacy path (last run pre-deletion)

# Step 4 — commit body template
# flag LITELLM_PROXY_ENABLED removed from Settings (was True default, post S3 PR-2)
#
# ## Tests audited
# - 0 tests retained mocking False path (legacy was already dead, removed entirely)
# - N tests migrated: setattr lines removed (default True is the only path)
# - test_provider_routing.py::TestLegacyDispatch class deleted entirely
# - test_router_litellm_dispatch.py simplified to LiteLLM-only assertions
# - test_openai_compat_providers.py deleted (legacy adapters gone)
#
# ## Path old: src/shared/infrastructure/llm/router.py::MultiRoleLLMRouter._resolve branch False
# ## Path new: src/shared/infrastructure/llm/router.py::MultiRoleLLMRouter._resolve LiteLLM-only
# ## Verification:
# - pytest -x -q PASS (1 path only)
# - arch fitness test_no_legacy_adapter_imports PASS

# Step 5 — Update inventory in .claude/rules/anti-default-flip-audit.md
# REMOVE row "LITELLM_PROXY_ENABLED" from the "Inventario flags side-effect" table.
# This is special: the inventory tracks live flags; a removed flag exits the table.
# Add a one-line footnote: "LITELLM_PROXY_ENABLED — removed 2026-05-XX (PI-12 S1 sales-agent-litellm-canonicalization T5). Legacy adapters deleted T4."
```

## 3. Surface diff (BE)

### 3.1 Endpoints nuevos / modificados

**Ninguno.** Service-story = backend internals. NO se modifica API surface (tenant CRUD endpoints en `iam/api/settings.py` se actualizan SOLO para excluir API key fields del response_model — sin cambio de path o status code).

### 3.2 DTOs

**Modified — `iam/api/settings.py::TenantUpdateDTO + TenantResponseDTO` (T6a):**

```python
# backend/src/modules/iam/api/settings.py
class TenantResponseDTO(BaseModel):
    id: UUID
    name: str
    can_use_platform_keys: bool
    # REMOVED post-T6a: openai_api_key, deepseek_api_key, kimi_api_key, dashscope_api_key
    # KEPT: gemini_api_key (out of scope per A4)
    gemini_api_key: str | None = None
    model_config = ConfigDict(from_attributes=True)
```

**New — `shared/agent_observability/recording/cost_recorder.py::CostRecorderCustomLogger` (T1):**

```python
# backend/src/shared/agent_observability/recording/cost_recorder.py — NEW FILE
from decimal import Decimal
from threading import Lock
from time import monotonic
from typing import Any

import litellm
import structlog
from litellm.integrations.custom_logger import CustomLogger

logger = structlog.get_logger()

# TTL cache: litellm_call_id → (cost_usd, expires_at_monotonic)
_CACHE_TTL_S = 60.0
_cache: dict[str, tuple[Decimal | None, float]] = {}
_lock = Lock()


class CostRecorderCustomLogger(CustomLogger):
    """Captures kwargs['response_cost'] from LiteLLM, stashed by litellm_call_id.

    The LangChain BaseAgentCallbackHandler.on_llm_end consumes via pop_cost(call_id).
    Best-effort: any exception in the callback is logged + swallowed (NEVER blocks turn).
    """

    async def async_log_success_event(
        self, kwargs: dict[str, Any], response_obj: Any, start_time: float, end_time: float,
    ) -> None:
        try:
            call_id = self._call_id(kwargs, response_obj)
            cost = kwargs.get("response_cost")
            cost_decimal = Decimal(str(cost)) if cost is not None else None
            self._stash(call_id, cost_decimal)
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning("cost_recorder.async_log_success_failed", error=str(exc))

    def log_success_event(self, kwargs, response_obj, start_time, end_time) -> None:  # noqa: ANN001
        try:
            call_id = self._call_id(kwargs, response_obj)
            cost = kwargs.get("response_cost")
            cost_decimal = Decimal(str(cost)) if cost is not None else None
            self._stash(call_id, cost_decimal)
        except Exception as exc:  # noqa: BLE001
            logger.warning("cost_recorder.log_success_failed", error=str(exc))

    @staticmethod
    def _call_id(kwargs: dict[str, Any], response_obj: Any) -> str:
        # LiteLLM populates litellm_call_id in kwargs OR response_obj.id (provider-specific).
        return (
            kwargs.get("litellm_call_id")
            or getattr(response_obj, "id", None)
            or kwargs.get("model", "unknown") + "_" + str(monotonic())
        )

    @staticmethod
    def _stash(call_id: str, cost: Decimal | None) -> None:
        with _lock:
            _purge_expired()
            _cache[call_id] = (cost, monotonic() + _CACHE_TTL_S)


def pop_cost(call_id: str) -> Decimal | None:
    """Retrieve + delete the cost for a call_id. Returns None on miss."""
    with _lock:
        _purge_expired()
        entry = _cache.pop(call_id, None)
        return entry[0] if entry else None


def _purge_expired() -> None:
    now = monotonic()
    expired = [cid for cid, (_, exp) in _cache.items() if exp < now]
    for cid in expired:
        cost, _ = _cache.pop(cid)
        logger.warning("cost_recorder.orphan_entry_purged", call_id=cid, cost=str(cost))


__all__ = ["CostRecorderCustomLogger", "pop_cost"]
```

### 3.3 Domain entities / VOs

**Modified — `iam/domain/tenant.py` (T6a):**

```python
# backend/src/modules/iam/domain/tenant.py
class Tenant(BaseModel):
    id: UUID
    name: str
    can_use_platform_keys: bool = True
    # T6a — DEPRECATED, schedule for drop in T6c.
    # NULLed by migration; factory no longer reads them. Excluded from response_model.
    openai_api_key: str | None = Field(default=None, deprecated=True, exclude=True)
    deepseek_api_key: str | None = Field(default=None, deprecated=True, exclude=True)
    kimi_api_key: str | None = Field(default=None, deprecated=True, exclude=True)
    dashscope_api_key: str | None = Field(default=None, deprecated=True, exclude=True)
    # KEPT (out of scope per A4 — Q4 ratificada).
    gemini_api_key: str | None = None
    model_config = ConfigDict(from_attributes=True)
```

**Post-T6c (deleted):** los 4 fields deprecated se eliminan. Solo `gemini_api_key` queda.

### 3.4 Migrations (T3 + T6a + T6c)

**T3 — repair `model_pricing_snapshot`:**

```python
# backend/alembic/versions/XXXX_repair_pricing_snapshot_provider_tagging.py
"""repair_pricing_snapshot_provider_tagging

Revision ID: <auto>
Revises: <head>
Create Date: 2026-05-XX
"""
from alembic import op

revision = "<auto>"
down_revision = "<head>"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Backup snapshot (idempotent — drop if exists then recreate).
    op.execute("DROP TABLE IF EXISTS model_pricing_snapshot_backup_pre_t3")
    op.execute(
        "CREATE TABLE model_pricing_snapshot_backup_pre_t3 AS "
        "SELECT * FROM model_pricing_snapshot",
    )
    # 2. Repair historical mis-tagged rows.
    # provider='openai' AND model LIKE non-openai prefix → re-tag.
    op.execute("""
        UPDATE model_pricing_snapshot
        SET provider = 'deepseek',
            model = CASE WHEN model LIKE 'deepseek/%' THEN model
                         ELSE 'deepseek/' || model END
        WHERE provider = 'openai'
          AND (model LIKE 'deepseek%' OR model LIKE '%deepseek%')
    """)
    op.execute("""
        UPDATE model_pricing_snapshot
        SET provider = 'kimi',
            model = CASE WHEN model LIKE 'kimi/%' THEN model
                         WHEN model LIKE 'moonshot/%' THEN model
                         ELSE 'kimi/' || model END
        WHERE provider = 'openai'
          AND (model LIKE 'kimi%' OR model LIKE 'moonshot%')
    """)
    op.execute("""
        UPDATE model_pricing_snapshot
        SET provider = 'dashscope',
            model = CASE WHEN model LIKE 'dashscope/%' THEN model
                         WHEN model LIKE 'qwen/%' THEN model
                         ELSE 'qwen/' || model END
        WHERE provider = 'openai'
          AND (model LIKE 'qwen%' OR model LIKE 'dashscope%')
    """)


def downgrade() -> None:
    # Restore from backup (idempotent — only if backup exists).
    op.execute("""
        DELETE FROM model_pricing_snapshot
        WHERE id IN (SELECT id FROM model_pricing_snapshot_backup_pre_t3)
    """)
    op.execute("""
        INSERT INTO model_pricing_snapshot
        SELECT * FROM model_pricing_snapshot_backup_pre_t3
    """)
```

**T6a — deprecation NULL:**

```python
# backend/alembic/versions/XXXX_deprecate_tenant_provider_api_keys.py
"""deprecate_tenant_provider_api_keys (NULL all 4 cols, code stops reading)

Revision ID: <auto>
"""
from alembic import op


def upgrade() -> None:
    op.execute("""
        UPDATE tenants
        SET openai_api_key = NULL,
            deepseek_api_key = NULL,
            kimi_api_key = NULL,
            dashscope_api_key = NULL
        WHERE openai_api_key IS NOT NULL
           OR deepseek_api_key IS NOT NULL
           OR kimi_api_key IS NOT NULL
           OR dashscope_api_key IS NOT NULL
    """)


def downgrade() -> None:
    # Cannot restore data — keys were ephemeral. No-op.
    pass
```

**T6c — drop columns:**

```python
# backend/alembic/versions/XXXX_drop_tenant_provider_api_keys.py
"""drop_tenant_provider_api_keys (post 1-sprint zero-read verification)

Revision ID: <auto>
"""
from alembic import op


def upgrade() -> None:
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS openai_api_key")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS deepseek_api_key")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS kimi_api_key")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS dashscope_api_key")


def downgrade() -> None:
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS openai_api_key VARCHAR")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS deepseek_api_key VARCHAR")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS kimi_api_key VARCHAR")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS dashscope_api_key VARCHAR")
```

> **Verificación idempotencia:** correr cada migration 2x sin error.
> `docker exec visionarias_brain_dev alembic upgrade head && alembic upgrade head` para T3.
> Para T6a: re-run no-op (rows ya NULL). Para T6c: `IF EXISTS` makes 2nd run no-op.

### 3.5 Servicios + Repos

**No new services.** Modificaciones puntuales en componentes existentes:

| Componente | Path | Cambio |
|---|---|---|
| `BaseAgentCallbackHandler._extract_provider_and_model` | `shared/agent_observability/recording/base_callback_handler.py` | T1: drop "/" partition (model field stored slashed per A1). Provider derived via new helper `_canonical_provider(model)` que llama `litellm.get_llm_provider(model)[1]` con fallback `"unknown"`. |
| `BaseAgentCallbackHandler._persist_llm_call` | idem | T1: consume `pop_cost(litellm_call_id)` desde `cost_recorder` en lugar de `calculate_cost()`. Si miss → `cost_usd = None` + structlog warn. |
| `MultiRoleLLMRouter._resolve` | `shared/infrastructure/llm/router.py` | T5: drop branch `if settings.LITELLM_PROXY_ENABLED`, drop `_legacy_providers` dict, drop `build_provider_service` import. Solo path LiteLLMService singleton. |
| `MultiRoleLLMRouter.reset_cache` | idem | T5: drop (no más `_legacy_providers`). |
| `build_provider_service` | idem | T5: DELETE entire function (orphaned post-router simplify). |
| `LLMFactory._extract_tenant_key` | `shared/infrastructure/llm/factory.py` | T6a: stub return `None` (master-key path only). T6c: DELETE method + caller `get_service_for_tenant` simplified. |
| `TenantRepository.create / update` | `iam/infrastructure/repositories/tenant_repository.py` | T6a: stop assigning to deprecated cols. T6c: drop the lines entirely. |
| `sync_pricing` | `shared/agent_observability/pricing/litellm_sync.py` | T2: agrega cross-check `litellm_config.yaml model_list` vs `litellm.model_cost`. Agrega upstream drift detection. |

### 3.6 Eventos emitidos / consumidos

- **Emite:** `pricing_alias_resolved` (capability sales-observability-cost-tracking) **se conserva** post-T1. Verify que el callback handler sigue emitiéndolo cuando el provider es resuelto canonical.
- **Consume:** ninguno (callback es trigger LiteLLM, no consumer de domain events).

### 3.7 Tests requeridos (TDD RED-first per ticket — ver §4 detalle)

**New file:** `backend/tests/shared/agent_observability/cost/test_litellm_canonicalization.py`

- `test_canonical_provider_and_cost_from_kwargs` (Scenario 1)
- `test_runtime_cost_independent_of_snapshot_during_sync` (Scenario 3)
- `test_all_recorded_calls_pass_through_litellm` (Scenario 4)
- `test_unknown_model_records_unknown_provider_and_null_cost` (failure mode 2.2)
- `test_cost_recorder_orphan_entry_warning` (TTL purge)
- `test_callback_p95_under_50ms` (NFR latency, pytest-benchmark)

**Extended:** `backend/tests/architecture/test_llm_routing_ssot.py`

- `test_no_legacy_adapter_imports` (Scenario 2)
- `test_known_legacy_files_set_is_empty` (Scenario 2)
- `test_settings_has_no_litellm_proxy_enabled_attr` (Scenario 4)

**Tests audit (T7) — migration / deletion:**

- DELETE `backend/tests/shared/infrastructure/llm/test_openai_compat_providers.py` entirely.
- DELETE `backend/tests/shared/infrastructure/llm/test_provider_routing.py::TestLegacyDispatch` class.
- SIMPLIFY `backend/tests/shared/infrastructure/llm/test_router_litellm_dispatch.py` (LiteLLM-only assertions; drop False-path test).
- MIGRATE ~17 other test files mocking `OpenAIService.generate_response` / `KimiService.generate_response` / etc. → `LiteLLMService.generate_response` mock.

Coverage minimum: 43% del backend (no debe bajar). Module-specific coverage `shared/agent_observability/`: target ≥ pre-cleanup baseline + 5pp (NEW cost_recorder.py + extended tests).

## 4. Ticket-by-ticket detail (alineado con 04-tickets.yaml)

### T1 — Cost recorder canonicalization

**Touches:** 3 files modify + 1 NEW.

```
M  backend/src/shared/agent_observability/recording/base_callback_handler.py
N  backend/src/shared/agent_observability/recording/cost_recorder.py        ← NEW
M  backend/src/shared/agent_observability/cost/calculator.py                ← retain, add docstring "reconciliation utility only" + remove from runtime path
M  backend/src/main.py                                                       ← register litellm.callbacks at startup
M  backend/src/workers/settings.py                                           ← register litellm.callbacks at WorkerSettings.on_startup
```

**Acceptance criteria (4 testable):**

- A1: `test_canonical_provider_and_cost_from_kwargs` — turn LiteLLM con DeepSeek → row `provider='deepseek'` + `cost_usd > 0`. (Scenario 1.)
- A2: `test_unknown_model_records_unknown_provider_and_null_cost` — modelo unknown → `provider='unknown'`, `cost_usd IS NULL`. (Failure mode 2.2.)
- A3: `test_callback_p95_under_50ms` — pytest-benchmark p95 callback `on_llm_end` < 50ms cuando hay cache hit + cache miss path.
- A4: `calculate_cost()` NO se invoca desde `BaseAgentCallbackHandler._persist_llm_call` post-T1 (verify via mock `unittest.mock.patch('...calculate_cost')` count == 0).

**Estimated hours:** 5h (clase nueva + cache thread-safe + tests + integration con LangChain handler).

### T2 — `make sync-pricing` extends litellm_sync.py

**Touches:**

```
M  backend/src/shared/agent_observability/pricing/litellm_sync.py            ← agrega config yaml cross-check + drift detection
M  backend/src/shared/agent_observability/workers/pricing_sync_task.py       ← propaga result fields
M  Makefile                                                                   ← agrega target sync-pricing (native call, not docker exec)
M  backend/src/workers/settings.py                                           ← cron ya existe; verify
```

**Acceptance criteria:**

- A1: `make sync-pricing` exit 0 en happy path con upserts logged.
- A2: `make sync-pricing` exit 1 cuando upstream URL unreachable (httpx ConnectError).
- A3: cuando `litellm_config.yaml` lista model NO en `litellm.model_cost` → structlog warn `pricing_sync.config_yaml_model_unknown_to_litellm`.
- A4: cuando snapshot row diverge de upstream JSON entry → structlog warn `pricing_sync.upstream_drift_detected` con delta.

**Estimated hours:** 4h.

### T3 — Alembic migration repair pricing snapshot

**Touches:**

```
N  backend/alembic/versions/XXXX_repair_pricing_snapshot_provider_tagging.py  ← NEW migration
```

**Acceptance criteria:**

- A1: migration aplica idempotente (correr 2x sin error: `alembic upgrade head && alembic upgrade head`).
- A2: post-upgrade, query `SELECT COUNT(*) FROM model_pricing_snapshot WHERE provider='openai' AND (model LIKE 'deepseek%' OR model LIKE 'kimi%' OR model LIKE 'qwen%' OR model LIKE 'moonshot%')` returns 0.
- A3: backup table `model_pricing_snapshot_backup_pre_t3` existe + row count = pre-migration row count.
- A4: downgrade restaura backup (test in migration_test DB).

**Estimated hours:** 3h.

### T4 — DELETE legacy adapters

**Touches:**

```
D  backend/src/shared/infrastructure/llm/providers/openai.py
D  backend/src/shared/infrastructure/llm/providers/deepseek.py
D  backend/src/shared/infrastructure/llm/providers/kimi.py
D  backend/src/shared/infrastructure/llm/providers/qwen.py
D  backend/src/shared/infrastructure/llm/providers/gemini.py            ← MANDATORY pre-delete audit (A3)
D  backend/src/shared/infrastructure/llm/providers/_openai_compat.py
?  backend/src/shared/infrastructure/llm/providers/_chat_model_resolver.py    ← audit usage; delete if orphaned
?  backend/src/shared/infrastructure/llm/providers/_response_validation.py    ← audit usage; delete if orphaned
?  backend/src/shared/infrastructure/llm/providers/_kwargs.py                 ← audit; LiteLLMService may still consume
```

**MANDATORY pre-delete `gemini.py` audit checklist (A3 ratificada — BLOQUEANTE):**

Architect-level audit. Si CUALQUIERA falla → ESCALATE Chris BLOCK T4.

- [ ] **Function calling:** `gemini.py` registers `tools=[]` con shape Gemini-specific (`tool_config.function_calling_config.mode`). Verify LiteLLM proxy maneja via `extra_body={"tool_config": ...}` — test 1 contract scenario en `tests/shared/infrastructure/llm/test_litellm_gemini_function_call.py` que envía un function call vía LiteLLM y verifica response shape Gemini.
- [ ] **Safety settings:** `gemini.py` envía `safety_settings=[{HARM_CATEGORY_X: BLOCK_NONE}, ...]`. Verify LiteLLM proxy pasa via `extra_body={"safety_settings": [...]}`.
- [ ] **System instruction:** Gemini usa `system_instruction` field (no `system` role). Verify LiteLLM convierte automáticamente desde OpenAI-format messages cuando model = `gemini/*`.
- [ ] **Generation config:** `temperature`, `top_p`, `top_k`, `max_output_tokens`. Verify LiteLLM tiene mapping (drop_params=True debería filtrar unsupported).
- [ ] **Vision multipart:** si gemini.py soporta image inputs → verify LiteLLM Gemini Vision compatible (multipart format `image_url` → conversion).
- [ ] **Streaming:** Gemini stream chunks tienen shape distinto vs OpenAI delta. Verify LiteLLM normaliza.

Si CUALQUIER kwarg/quirk irreplicable detectado → architect ESCALATE Chris ANTES delete. Chris decide: defer T4 gemini.py specifically + mantener adapter o drop unsupported feature.

**Acceptance criteria T4:**

- A1: 6 archivos eliminados (verify via `git status` + `find ... -name openai.py`).
- A2: post-deletion, `pytest backend/ -x -q` PASS (T7 already migrated tests).
- A3: arch fitness `test_no_legacy_adapter_imports` PASS (T8 already added).
- A4: gemini audit checklist 6/6 ✓ documented in commit body.

**Dependencies:** T7 PRECEDE T4 (tests must be migrated/deleted before code deletion).

**Estimated hours:** 4h (+ 3h gemini audit = 7h total).

### T5 — Kill flag LITELLM_PROXY_ENABLED

**Touches:**

```
M  backend/src/core/config.py                                ← drop field LITELLM_PROXY_ENABLED
M  backend/src/shared/infrastructure/llm/router.py           ← simplify (drop dual-path)
M  backend/src/shared/infrastructure/llm/factory.py          ← drop build_provider_service references
M  backend/src/main.py                                       ← drop conditional warning at startup
M  backend/src/admin/modules/llm_virtual_keys.py             ← drop fallback message
M  .claude/rules/anti-default-flip-audit.md                  ← remove flag from inventory + footnote
```

**Acceptance criteria:**

- A1: `Settings` class no tiene attr `LITELLM_PROXY_ENABLED` (verify via `getattr(settings, 'LITELLM_PROXY_ENABLED', SENTINEL) == SENTINEL` test).
- A2: anti-flip-audit 4-step COMPLETE en commit body (Step 1-5 documented).
- A3: pytest -x -q PASS sin tests mockeando `LITELLM_PROXY_ENABLED`.
- A4: arch fitness `test_settings_has_no_litellm_proxy_enabled_attr` PASS.

**Dependencies:** T7 PRECEDE T5 (test_provider_routing.py::TestLegacyDispatch deleted FIRST).

**Estimated hours:** 4h.

### T6a — Migration deprecation tenant API keys (Phase 1 expand-contract)

**Touches:**

```
N  backend/alembic/versions/XXXX_deprecate_tenant_provider_api_keys.py     ← NEW migration NULL cols
M  backend/src/modules/iam/domain/tenant.py                                 ← Pydantic Field(deprecated=True, exclude=True)
M  backend/src/modules/iam/api/settings.py                                  ← drop fields from response_model
M  backend/src/shared/infrastructure/llm/factory.py                         ← _extract_tenant_key returns None always
M  backend/src/modules/iam/infrastructure/repositories/tenant_repository.py ← stop assigning deprecated cols on create/update
```

**Acceptance criteria:**

- A1: post-migration, `SELECT COUNT(*) FROM tenants WHERE openai_api_key IS NOT NULL OR deepseek_api_key IS NOT NULL OR kimi_api_key IS NOT NULL OR dashscope_api_key IS NOT NULL` = 0.
- A2: factory `_extract_tenant_key` returns `None` for the 4 deprecated providers.
- A3: TenantResponseDTO no incluye 4 deprecated fields (verify via Pydantic schema dump).
- A4: gemini_api_key UNCHANGED (still in domain + repo + DTO + column).

**Dependencies:** T5 PRECEDE T6a (anti-flip-audit pattern same template).

**Estimated hours:** 3h.

### T6b — DEPLOY-AND-VERIFY 1-day zero-read window (operational gate, pre-clientes)

**NOT a code ticket.** Operational pause documented as architectural gate.

**Gate criteria (must pass before T6c starts):**

- T6a code merged + deployed to prod.
- **Min 1 working day elapsed** (was 5d — R7 process-improvement 2026-05-05; pre-clientes activos no justifica 5d wall-clock; re-escalable a 5d post-go-live cuando hay tráfico real).
- Streamlit `/admin/tenants` query confirms 0 non-NULL across all 4 deprecated columns over the 1-day verification window.
- Structured log query confirms 0 reads from factory `_extract_tenant_key` for the 4 deprecated providers (Datadog / structlog aggregation).
- Smoke test prod: tenant create/update flow PASS sin referenciar las 4 cols.

**Owner:** PM (`/pm` skill — operational gate). T6c blocked until PM ratifies T6b PASS.

**Estimated hours:** 0 (waiting period). Pre-clientes: 1 working day. Post-clientes: re-escalable a 1-sprint = 5 working days.

### T6c — Migration DROP COLUMN

**Touches:**

```
N  backend/alembic/versions/XXXX_drop_tenant_provider_api_keys.py          ← NEW DROP COLUMN migration
M  backend/src/modules/iam/infrastructure/models/tenant_model.py            ← remove 4 Column declarations
M  backend/src/modules/iam/domain/tenant.py                                 ← remove 4 deprecated fields
M  backend/src/modules/iam/infrastructure/repositories/tenant_repository.py ← remove all references to 4 cols
M  backend/src/shared/infrastructure/llm/factory.py                         ← remove _extract_tenant_key entirely + simplify get_service_for_tenant
```

**Acceptance criteria:**

- A1: migration applies idempotent (DROP COLUMN IF EXISTS).
- A2: post-deploy, `\d tenants` no muestra las 4 cols.
- A3: `factory.py::LLMFactory._extract_tenant_key` no existe.
- A4: backend tests + arch fitness PASS.

**Dependencies:** T6b PASS (operational gate).

**Estimated hours:** 2h.

### T7 — Tests audit (~20 files)

**Touches (audit scope):**

```
D  backend/tests/shared/infrastructure/llm/test_openai_compat_providers.py            ← DELETE entire file
D  backend/tests/shared/infrastructure/llm/test_provider_routing.py::TestLegacyDispatch ← DELETE class
M  backend/tests/shared/infrastructure/llm/test_router_litellm_dispatch.py             ← simplify LiteLLM-only
M  backend/tests/shared/infrastructure/llm/test_chat_model_resolver.py                  ← audit, may delete if helpers gone
M  backend/tests/shared/infrastructure/llm/test_kwargs_normalization.py                 ← keep (LiteLLM still uses _kwargs.py)
M  backend/tests/modules/copilot/test_deep_agent_factory_wire.py                        ← migrate mock
M  backend/tests/modules/sales_agent/test_specialist_provider_routing.py                ← migrate mock
M  ~17 other test files mocking OpenAIService/KimiService/DeepSeekService/QwenService/GeminiService
```

**Migration pattern:**

```python
# OLD (per-provider mock):
@patch("src.shared.infrastructure.llm.providers.openai.OpenAIService.generate_response")
def test_x(mock_gen):
    mock_gen.return_value = "..."
    ...

# NEW (LiteLLMService mock + litellm.completion):
@patch("src.shared.infrastructure.llm.providers.litellm.LiteLLMService.generate_response")
def test_x(mock_gen):
    mock_gen.return_value = "..."
    ...
# OR for cost recorder tests, also mock litellm.completion to inject kwargs["response_cost"].
```

**Acceptance criteria:**

- A1: 0 test files importan from `src.shared.infrastructure.llm.providers.{openai,deepseek,kimi,qwen,gemini,_openai_compat}` (post-T7 grep returns empty).
- A2: pytest backend/ -x -q PASS pre-T4.
- A3: coverage backend ≥43% (pre-cleanup baseline maintained).
- A4: anti-flip-audit Step 4 commit body lists tests deleted vs migrated.

**Dependencies:** T1 PRECEDE T7 (cost_recorder.py needs to exist for migrated mocks to reference).

**Estimated hours:** 6h (~20 files, varying complexity).

### T8 — Arch fitness

**Touches:**

```
M  backend/tests/architecture/test_llm_routing_ssot.py
```

**New tests:**

```python
def test_no_legacy_adapter_imports() -> None:
    """Forbidden: import of any of the 6 deleted adapters."""
    forbidden = [
        "src.shared.infrastructure.llm.providers.openai",
        "src.shared.infrastructure.llm.providers.deepseek",
        "src.shared.infrastructure.llm.providers.kimi",
        "src.shared.infrastructure.llm.providers.qwen",
        "src.shared.infrastructure.llm.providers.gemini",
        "src.shared.infrastructure.llm.providers._openai_compat",
    ]
    pattern = re.compile(rf"\bfrom\s+({'|'.join(re.escape(p) for p in forbidden)})\s+import")
    violations = _scan_for_pattern(pattern, REPO_ROOT / "src")
    test_violations = _scan_for_pattern(pattern, REPO_ROOT / "tests")
    all_violations = violations + test_violations
    assert not all_violations, (
        "Forbidden import detected. Canonical path is LiteLLMService via litellm.completion.\n"
        "Violations:\n  - " + "\n  - ".join(all_violations)
    )


def test_known_legacy_files_set_is_empty() -> None:
    """KNOWN_LEGACY_LLM_FILES must remain empty post-cleanup."""
    assert KNOWN_LEGACY_LLM_FILES == set(), (
        "Allowlist must shrink only — adding new entries requires architect approval."
    )


def test_settings_has_no_litellm_proxy_enabled_attr() -> None:
    """LITELLM_PROXY_ENABLED removed from Settings class — adversarial scenario 4."""
    from src.core.config import settings
    SENTINEL = object()
    assert getattr(settings, "LITELLM_PROXY_ENABLED", SENTINEL) is SENTINEL
```

**Acceptance criteria:**

- A1: 3 new tests PASS post-cleanup.
- A2: tests FAIL when introducing legacy import (verify via temp file + revert).

**Dependencies:** T4 + T5 (assertions need post-deletion state).

**Estimated hours:** 2h.

### T9 — Documentation

**Touches:**

```
M  docs/domains/llm-routing.md                                              ← kill rollback section + legacy refs
M  docs/domains/tech_module_shared.md                                        ← purge LITELLM_PROXY_ENABLED refs
M  backend/src/modules/sales_agent/domain/model_tier.py:30                   ← drop docstring KimiService/OpenAIService refs
M  backend/src/modules/sales_agent/application/agents/sales/nodes.py:192     ← drop docstring KimiService/OpenAIService refs
```

**Acceptance criteria:**

- A1: `docs/domains/llm-routing.md` no menciona `LITELLM_PROXY_ENABLED` ni rollback.
- A2: docstrings legacy provider refs removed (grep `KimiService\|DeepSeekService\|OpenAIService\|QwenService\|GeminiService` en docstrings retorna 0).
- A3: New section "LiteLLM CustomLogger pattern" en `docs/domains/llm-routing.md` documenta el cost_recorder + cache pattern.

**Dependencies:** T8 (code is truth — docs reflect post-cleanup state).

**Estimated hours:** 2h.

## 5. Cross-cutting concerns

- **Tenant isolation:** todo write a `*_llm_call` + `*_trace_event` carries `tenant_id` desde `BaseObservabilityContext` upstream. Cost recorder cache **NO** carries tenant context (process-wide). Tenant scoping happens en `BaseAgentCallbackHandler._persist_llm_call_row` que tiene `self.tenant_id` set at construct time. Verify post-T1: existing tenant isolation tests pass (no regression).
- **Idempotency:** `(tenant_id, turn_id, llm_call_seq)` UNIQUE en `*_llm_call` ya existe pre-cleanup. NO change.
- **PII:** `sanitize_payload` pipeline preservado en `_persist_trace_event_row`. Cost recorder payload = solo `kwargs["response_cost"]` Decimal — no PII (verify in Pydantic schema review).
- **Currency:** `cost_usd` Decimal (no float). FX rate denormalised desde `FXResolver.default()` (unchanged). Tenant currency conversion mantenida.
- **Master data UTC:** `started_at` UTC TZ-aware (unchanged). `valid_from`/`valid_to` en `model_pricing_snapshot` UTC (unchanged).
- **Spanish neutro N/A:** sin UI surface. Logs en inglés (structlog convention).
- **Native-first dev:** todos los tests + lint + migration tests en native WSL (`backend/.venv/bin/{ruff,pytest,alembic}`). NUNCA `docker exec ruff`. Migration verify usa `docker exec visionarias_brain_dev alembic upgrade head` (correct — migrations ejecutan dentro container que tiene DB conn).

## 6. Risks + mitigations

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Cache miss bridge LangChain↔LiteLLM (`pop_cost` returns None) → cost_usd=NULL | high | Test `test_cost_recorder_cache_hit_under_real_litellm_call` verifies bridge end-to-end con mocked `litellm.completion` que injects `kwargs["response_cost"]`. Si miss > 1% en prod 24h post-deploy → revisit `_call_id` extraction |
| Gemini quirks irreplicable via LiteLLM → silent failure tenant Gemini-bound | high | T4 sub-task pre-delete audit checklist (A3 ratificada — BLOCK if any quirk falla) |
| T3 migration locks `model_pricing_snapshot` durante backup CTAS — workers cron 03:00 podría timeout | medium | Run T3 migration at low-traffic window (manually scheduled by Chris) + pre-mig pause ARQ scheduler (`docker compose stop visionarias_arq`) |
| T6a deploy + T6c gap > 1 sprint induce code rot (Pydantic deprecated fields visible to devs) | low | T6b operational gate ratificada → 5 working days, no infinite drift |
| Anti-flip audit Step 5 (update inventory) skipped → future flag flipper repeats failure | medium | T5 commit body REQUIRES "## Tests audited" + "## Inventory updated" sections. Auditor Cat 14 enforce. |
| Tests migrated en T7 mock LiteLLMService incorrectly (mocking method that doesn't exist) → false pass | medium | T7 deliverable explicit: "verify mock target method exists in LiteLLMService class" — `getattr(LiteLLMService, '<method>') is not None` pre-mock setup |

## 7. Architectural fitness gates impact

Tests que MUST stay green post-cleanup:

```
backend/tests/architecture/test_llm_routing_ssot.py
backend/tests/architecture/test_extraction_orchestrator_inheritance.py
backend/tests/architecture/test_no_cross_module_imports.py (DDD boundary)
backend/tests/architecture/test_response_model_required.py (PII allowlist)
backend/tests/architecture/test_no_hard_deletes.py
backend/tests/architecture/test_sqla_2_0_only.py
```

T8 expande `test_llm_routing_ssot.py` con 3 nuevos tests. Allowlists shrink only (`KNOWN_LEGACY_LLM_FILES = set()` ya). NO new arch fitness tests required outside T8.

## 8. pm-nico/current-state updates required (post-merge)

- `docs/product/modules/sales-agent.md` § "LLM routing" — actualizar con LiteLLM-only + remove rollback timeline.
- `docs/product/capabilities/sales-agent/sales-observability-cost-tracking.yaml` — actualizar `gaps` (remove "Cost tracking accuracy degraded"), añadir story_id history.
- `docs/domains/llm-routing.md` — sección "Capa 5 — LiteLLM Proxy" reescrita como SSoT único.

PM ratifica updates en 07-merge.md.

## 9. Tests audit (default flip — N/A flag-deletion)

> Aplica `.claude/rules/anti-default-flip-audit.md` al T5 con special case "deletion not flip".
> Inventory update: REMOVE row `LITELLM_PROXY_ENABLED` post-merge + footnote "removed PI-12 S1 sales-agent-litellm-canonicalization T5".

| Field | Value |
|---|---|
| Flag | `LITELLM_PROXY_ENABLED` |
| Old default | `True` (post S3 PR-2 default 2026-04-30) |
| New default | **REMOVED** (no longer attribute of `Settings`) |
| Side-effect path old | `MultiRoleLLMRouter._resolve` branch False → `build_provider_service(provider)` → per-provider Service |
| Side-effect path new | `MultiRoleLLMRouter._resolve` LiteLLMService singleton (single path) |
| Tests mockean path viejo | `test_provider_routing.py::TestLegacyDispatch` (3 tests) + `test_router_litellm_dispatch.py::test_resolve_returns_legacy_provider_when_disabled` (1 test) + arch fitness `test_router_dispatches_via_litellm_only` references in docstring |
| Migration strategy per test | DELETE `TestLegacyDispatch` class + DELETE legacy-path test in `test_router_litellm_dispatch.py` (legacy is gone, test useless). NO migrate. |
| Run with both flag values | NO necesario (flag deletado, single path). Solo run `pytest -x -q` PASS post-T7 + T5. |
| Commit body docs | "## Tests audited\n- N tests deleted (legacy path gone)\n- 0 tests migrated\n## Path old: ...\n## Path new: ...\n## Inventory updated: removed row from anti-default-flip-audit.md" |
| Arch fitness coverage | T8 adds `test_settings_has_no_litellm_proxy_enabled_attr` |

## 10. Decisiones registradas (architect)

- **2026-05-05** — `CostRecorderCustomLogger` is a NEW class (cross-cutting LiteLLM-CustomLogger surface, not a mirror). Justification: LiteLLM proxy `CustomLogger` is conceptually distinct from LangChain `BaseCallbackHandler` — both coexist, bridged by `litellm_call_id` + thread-safe TTL cache. Anti-duplication rule honored: this is a NEW abstraction at a NEW surface (LiteLLM), not a duplicate of an existing one.
- **2026-05-05** — Cost cache TTL = 60s. Trade-off: longer TTL = more orphan retention if LangChain handler never consumes; shorter = risk of cache miss for slow async chains. 60s covers p99 typical LLM call latency (~30s) + 2x margin.
- **2026-05-05** — `pop_cost` returns Decimal | None — None signals miss → caller persists `cost_usd = NULL` (NOT 0). Distinguishes "we don't know" from "valid 0 cost".
- **2026-05-05** — Tier pricing >200k tokens (S12 Kimi K2.6): post-T1, LiteLLM `kwargs["response_cost"]` ALREADY incorporates tier split natively. NO need for `calculate_cost()` reproducción in runtime path. `calculate_cost()` retained as reconciliation utility.
- **2026-05-05** — `gemini_api_key` column UNCHANGED (out of scope per A4 + Q4). T6 specifically targets the 4 cols that map to providers being deleted. Gemini adapter is being deleted in T4 but the column is retained for now (Chris may decide future PR).
- **2026-05-05** — T6b operational gate = 5 working days OR Chris ratification, whichever earlier (architect recommends shorter post-Sprint-end if zero-read evidence is clean within 2-3 days).

## 11. Próximo paso

`done -> 03-arch-be.md`. Architect orchestrator integra con 04-tickets.yaml (siguiente artifact). Phase advanced PO_RATIFIED → ARCHITECT_COMPLETE.
