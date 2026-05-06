---
story_id: sales-agent-litellm-canonicalization
type: service-story
module: sales_agent
capability: sales-observability-cost-tracking
po_version: 2
last_modified: 2026-05-05T03:01:12Z
ratified_by_chris: true
links:
  story_yaml: "../../../../../../product/stories/sales-agent/sales-agent-litellm-canonicalization.yaml"
  story_md: "00-story.md"
---

## Resumen ejecutivo

Canonicalización completa de la ejecución LLM en Nicolify: LiteLLM pasa a ser el **único** camino runtime, los 6 adaptadores legacy (`openai.py`, `deepseek.py`, `kimi.py`, `qwen.py`, `gemini.py`, `_openai_compat.py`) se eliminan, el flag `LITELLM_PROXY_ENABLED` se borra del code, las 4 columnas `tenant.{openai,deepseek,kimi,dashscope}_api_key` se dropean (Nicolify cobra suscripción + paga LLM con master key, tenants no traen keys), y `model_pricing_snapshot` queda como **ledger inmutable de auditoría** — el costo runtime viene de `kwargs["response_cost"]` que LiteLLM computa nativo en su `CustomLogger` callback. Outcome consumer-observable: `copilot_llm_call.provider` siempre canónico, `cost_usd > 0` para todo turn LLM, agregar un modelo nuevo cuesta 1 entrada YAML. Refactor zero-tech-debt orquestado en 9 sub-tickets que `/architect` materializa en `04-tickets.yaml`.

## Acceptance Criteria (Gherkin AI-resistant)

> 4 scenarios obligatorios: 1 happy + 1 negative + 1 edge + 1 adversarial. Cada uno testeable + grader explícito.

### Scenario 1 — `cost-tracking-canonical-litellm-flow` (`type: happy`)

**Given:**
- Tenant `T1` activo con feature flag legacy `LITELLM_PROXY_ENABLED` ya eliminado del codebase (post-T5).
- `litellm_config.yaml` `model_list` contiene la entrada `model_name: deepseek/deepseek-v4-flash` con `api_key: os.environ/DEEPSEEK_API_KEY`.
- `model_pricing_snapshot` recién sincronizado por `make sync-pricing` (T2): contiene una row activa con `provider="deepseek"`, `model="deepseek/deepseek-v4-flash"`, `valid_to IS NULL`.
- `BaseAgentCallbackHandler` (shared) registra `litellm.callbacks = [CostRecorderCustomLogger()]` en su inicialización (post-T1).

**When:**
- El sales_agent ejecuta 1 turn que invoca el `LiteLLMService` con `model="deepseek/deepseek-v4-flash"` (mocked en test: `litellm.completion` retorna response con `kwargs["response_cost"] = 0.000123`).

**Then:**
- Se inserta exactamente 1 row en `copilot_llm_call` con:
  - `provider = "deepseek"` (derivado por `litellm.get_llm_provider("deepseek/deepseek-v4-flash")[1]`, NUNCA `"openai"`).
  - `model = "deepseek/deepseek-v4-flash"` (formato canonical LiteLLM completo, NO stripped — ver Q1 abierta).
  - `cost_usd = Decimal("0.000123")` (consumido directo de `kwargs["response_cost"]`, NO recomputado).
  - `tenant_id = T1` (tenant isolation).
  - `turn_id` + `llm_call_seq` poblados (idempotency natural-key).
- Se inserta 1 trace event en `copilot_trace_event` con `event_type="llm_call_completed"`, `payload.provider="deepseek"`, `payload.cost_usd=0.000123`.
- structlog emite log `cost_recorder.canonical_provider_resolved` con `provider="deepseek"`, `model="deepseek/deepseek-v4-flash"`, `source="kwargs.response_cost"`.
- NO se hace ninguna query adicional a `model_pricing_snapshot` durante el turn (snapshot es ledger, no runtime).
- p95 latency del callback `on_llm_end` < 50ms (medido vía `pytest-benchmark` o instrumentación structlog `duration_ms`).

**Graders:**
- `contract_test` — path `backend/tests/shared/agent_observability/cost/test_litellm_canonicalization.py::test_canonical_provider_and_cost_from_kwargs`
- `state_check` — target db, query `SELECT provider, model, cost_usd FROM copilot_llm_call WHERE tenant_id = :t1 AND turn_id = :turn ORDER BY llm_call_seq DESC LIMIT 1`, expect `provider='deepseek' AND cost_usd > 0`
- `state_check` — target db, query `SELECT event_type, payload->>'provider' AS p FROM copilot_trace_event WHERE tenant_id = :t1 AND turn_id = :turn AND event_type = 'llm_call_completed'`, expect `p='deepseek'`

---

### Scenario 2 — `legacy-adapter-import-arch-fitness-fails` (`type: negative`)

**Given:**
- Codebase post-cleanup (post-T4): los archivos `backend/src/shared/infrastructure/llm/providers/{openai,deepseek,kimi,qwen,gemini,_openai_compat}.py` NO existen.
- Arch fitness test `backend/tests/architecture/test_llm_routing_ssot.py` con `KNOWN_LEGACY_LLM_FILES = set()` y assertions explícitas (post-T8).

**When:**
- Un developer (o agent) intenta agregar a cualquier archivo del codebase: `from src.shared.infrastructure.llm.providers.deepseek import DeepSeekService` (o cualquier import equivalente de los 6 adaptadores eliminados).

**Then:**
- En tiempo de runtime: `ModuleNotFoundError: No module named 'src.shared.infrastructure.llm.providers.deepseek'`.
- En tiempo de CI: `pytest backend/tests/architecture/test_llm_routing_ssot.py` FALLA con mensaje explícito `"Forbidden import detected: <file>:<line> imports legacy LLM adapter '<adapter_name>'. Canonical path is LiteLLMService via litellm.completion."` que nombra el archivo violador y el adaptador prohibido.
- El build NO pasa el quality gate `make ci-parity`.
- NO se hace merge a `development` (pre-commit hook + CI workflow E2E gate).

**Graders:**
- `contract_test` — path `backend/tests/architecture/test_llm_routing_ssot.py::test_no_legacy_adapter_imports`
- `contract_test` — path `backend/tests/architecture/test_llm_routing_ssot.py::test_known_legacy_files_set_is_empty`

---

### Scenario 3 — `pricing-snapshot-stale-during-sync` (`type: edge`)

**Given:**
- Job `make sync-pricing` (T2 extension de `litellm_sync.py`) está corriendo: ha leído `litellm_config.yaml` model_list + `litellm.model_cost` registry, está en medio de upserts a `model_pricing_snapshot` (transaction abierta, commit pendiente).
- Tenant `T2` envía un mensaje al sales_agent durante esa ventana → triggerea 1 LLM call vía LiteLLM.
- Race condition: el callback `on_llm_end` del `BaseAgentCallbackHandler` se dispara ANTES de que el sync job commitee.

**When:**
- LiteLLM responde con `kwargs["response_cost"] = 0.000456` calculado a partir de `litellm.model_cost` in-memory registry.
- El callback consume `kwargs["response_cost"]` y persiste a `copilot_llm_call`.
- Reconciliation worker (post-sync) compara `copilot_llm_call.cost_usd` vs `model_pricing_snapshot` recalculation y encuentra mismatch (snapshot stale).

**Then:**
- `copilot_llm_call.cost_usd = Decimal("0.000456")` (correcto, viene de LiteLLM-native — NO depende de snapshot).
- NO hay error ni excepción durante el turn (el cost recorder no consulta snapshot en runtime).
- structlog emite warning `pricing_snapshot_stale_during_sync` con campos `tenant_id`, `model`, `runtime_cost_usd`, `snapshot_cost_usd_after_commit`, `delta_usd`. NO eleva `ERROR` (es esperado durante sync).
- El reconciliation reading post-commit registra el delta como `audit_anomaly_type="snapshot_stale_during_sync"` (informational, no bloquea billing).
- `model_pricing_snapshot` post-commit refleja el state correcto (eventual consistency, tolerada).
- p95 latency del callback NO degrada (sigue < 50ms — el job sync corre en proceso separado, lock-free para reads).

**Graders:**
- `contract_test` — path `backend/tests/shared/agent_observability/cost/test_litellm_canonicalization.py::test_runtime_cost_independent_of_snapshot_during_sync`
- `state_check` — target db, query `SELECT cost_usd FROM copilot_llm_call WHERE tenant_id = :t2 AND turn_id = :turn`, expect `cost_usd = 0.000456`
- `state_check` — target logs (structlog capture fixture), expect 1 warning `pricing_snapshot_stale_during_sync` con `delta_usd` field presente

---

### Scenario 4 — `deleted-flag-rollback-attempt` (`type: adversarial`)

> AI-resistant: hostil intentando reactivar path legacy ya borrado, sea por revert mal aplicado, env var manual, o test rogue.

**Given:**
- Cleanup completo merged a `main` (post-T1..T9). `LITELLM_PROXY_ENABLED` eliminado de `core/config.py` (no es atributo de `Settings`). Los 6 adaptadores legacy no existen como módulos.
- CI gate activo: `pytest backend/tests/architecture/test_llm_routing_ssot.py` corre en cada PR.

**When:**
- Actor hostil (o test rogue, o agent confundido) ejecuta en runtime / CI / local:
  - `os.environ["LITELLM_PROXY_ENABLED"] = "false"` antes del startup, +
  - `from src.shared.infrastructure.llm.providers.deepseek import DeepSeekService` en cualquier archivo nuevo, +
  - intenta `settings.LITELLM_PROXY_ENABLED` en un service.

**Then:**
- El import del adapter raises `ModuleNotFoundError` inmediatamente — la app falla al import-time, NO arranca con path legacy resucitado.
- El acceso `settings.LITELLM_PROXY_ENABLED` raises `AttributeError: 'Settings' object has no attribute 'LITELLM_PROXY_ENABLED'`. Pydantic-settings NO lee la env var hostil porque el field no existe en el `Settings` class.
- El env var `LITELLM_PROXY_ENABLED=false` queda como ruido sin efecto (no hay consumer en code).
- `pytest backend/tests/architecture/test_llm_routing_ssot.py::test_no_legacy_adapter_imports` cachea el import violador y FALLA antes del deploy.
- structlog emite log `boot.legacy_llm_path_attempt_blocked` con `attempted_import=<path>`, `blocked_by="ModuleNotFoundError"` si por alguna razón el AttributeError es swallowed por código resiliente (defense-in-depth).
- NO existe code path en producción que sirva una request bypass-eando LiteLLM.
- `copilot_trace_event` nunca registra una llamada que NO pasó por `LiteLLMService`.

**Graders:**
- `contract_test` — path `backend/tests/architecture/test_llm_routing_ssot.py::test_settings_has_no_litellm_proxy_enabled_attr`
- `contract_test` — path `backend/tests/architecture/test_llm_routing_ssot.py::test_no_legacy_adapter_imports`
- `contract_test` — path `backend/tests/shared/agent_observability/cost/test_litellm_canonicalization.py::test_all_recorded_calls_pass_through_litellm`

---

## Service contract (consolidado, aplica a los 4 scenarios)

| Field | Valor |
|---|---|
| type | `event_handler` (cost recorder es callback `on_llm_end` ejecutado in-process por LiteLLM via `litellm.callbacks = [CustomLogger()]`) |
| auth | `internal` (callback se ejecuta dentro del agent runtime, no expuesto a red) |
| trigger | `litellm.completion` retorno → `CustomLogger.log_success_event(kwargs, response_obj, start_time, end_time)` |
| idempotency | `natural-key` — `(tenant_id, turn_id, llm_call_seq)` UNIQUE en `copilot_llm_call` |
| rate_limit_per_tenant | N/A (gobernado por `BudgetGuard` upstream, fuera de scope) |
| request_schema | LiteLLM kwargs dict — fields canónicos: `model: str`, `messages: list[dict]`, `response_cost: float\|None`, `usage: dict`, `custom_llm_provider: str` |
| response_schema | Inserción a `copilot_llm_call` (Pydantic DTO `LLMCallRecord` en `shared/agent_observability/persistence/`) |

## Non-functional requirements

| Categoría | Requisito | Verificador |
|---|---|---|
| Latencia | p95 callback `on_llm_end` < 50ms (NO debe agregar DB round-trip a snapshot) | `pytest-benchmark` en `test_litellm_canonicalization.py` + structlog `duration_ms` field instrumentado |
| Cost | `cost_usd > 0` para 100% de turns que pasan por LiteLLM con un modelo en `model_cost` registry | `state_check` SQL `WHERE cost_usd = 0` count 0 post-deploy 24h |
| Failure rate | 0 incremento post-cleanup vs pre-cleanup (baseline measured pre-merge) | Smoke test prod 24h post-deploy + Datadog/structlog error rate metric |
| Tech debt | 0 archivos legacy importables. 0 flags side-effect dead. 0 tests con mocks per-provider stale. | Arch fitness `test_llm_routing_ssot.py::KNOWN_LEGACY_LLM_FILES == set()` + `test_known_legacy_files_set_is_empty` |
| Mobile | N/A (service-story, sin UI) | — |
| Accesibilidad | N/A (service-story, sin UI) | — |
| i18n | structlog log fields en inglés, mensajes user-facing N/A (no hay UI) | code review |
| PII | NO loggear `messages` content en log entries del recorder. `sanitize_payload` shared aplicado en `BaseAgentCallbackHandler.on_llm_end` (ya existe pre-cleanup, mantener invariante). | `tessl pii-sanitisation` rule + code review |
| Tenant isolation | `copilot_llm_call.tenant_id` + `copilot_trace_event.tenant_id` poblados desde `BaseObservabilityContext` upstream. NO query cross-tenant. | adversarial scenario 4 + arch fitness test_tenant_filter_required |
| Migration safety | T3 + T6 idempotentes (`IF EXISTS` / `IF NOT EXISTS`) + backup table snapshot pre-execution | `.claude/rules/backend-migrations.md` + dry-run en migration_test DB |
| Anti-default-flip-audit | T5 (eliminar flag) cumple 4-step: grep tests path viejo → migrate mocks → run both flag values pre-deletion → document commit body. | `.claude/rules/anti-default-flip-audit.md` + auditor Cat 14 |
| Anti-duplication | T1 extiende `BaseAgentCallbackHandler` shared, NO crea mirror per-módulo. | `.claude/rules/anti-duplication.md` + auditor Cat 12 |
| Arch fitness ratchet | T8: `KNOWN_LEGACY_LLM_FILES` shrinks a `set()`. Si futuro intenta engordar la lista, falla CI. | `tests/architecture/test_llm_routing_ssot.py` |

## Constraints técnicos heredados

- `.claude/rules/backend-ddd.md` — Inside-Out DDD: T6 modifica `iam` (domain → infrastructure → repository → API thin).
- `.claude/rules/tenant-isolation.md` — Toda query a `copilot_llm_call` filtra por `tenant_id`. Verify post-cleanup.
- `.claude/rules/backend-migrations.md` — T3 + T6 SQL crudo `IF EXISTS` + backup table.
- `.claude/rules/anti-default-flip-audit.md` — T5 obligatorio 4-step + commit body section "Tests audited".
- `.claude/rules/anti-duplication.md` — T1 extiende `BaseAgentCallbackHandler`, anti-pattern `mirror callback handler`.
- `.claude/rules/tdd-mandatory.md` — § "Default flag flips" aplica a T5: tests RED migración → run ambos valores → GREEN flip → document commit.
- `.claude/rules/architectural-fitness.md` — T8 ratchet shrink-only.
- `.claude/rules/master-data.md` — `cost_usd Decimal` (NO float), `tenant_id` siempre.
- Tessl tiles relevantes: `tessl__fastapi` (DTO patterns), `tessl__pytest-api-testing` (fixtures + mocks), `pii-sanitisation` (recording log fields).

## Cross-module impact

- **Lee de:**
  - `iam` — `tenant_id` (header `X-Tenant-ID`), tenant model post-T6 (sin API key columns).
  - `core` — `Settings` (post-T5, sin `LITELLM_PROXY_ENABLED`).
- **Es leído por:**
  - `copilot` — el mismo `BaseAgentCallbackHandler` shared se usa cuando copilot ejecuta LLM. T1 cambio cross-agent.
  - `sales_agent` — agent runtime usa `BaseAgentCallbackHandler` extendido.
  - `admin/modules/llm_virtual_keys.py` + `admin/modules/copilot_routing.py` — T5 ajusta UI strings.
  - Billing future readers (`mv_sales_agent_cost_daily` via `sales-cost-tracking-cycle-billing.yaml`) — `copilot_llm_call.provider` correcto desbloquea aggregation accuracy.
  - Todas extraction orchestrators que invocan LLM (brand, offer, buyer_persona, landing) — heredan `BaseAgentCallbackHandler` cost recording.
- **Eventos emitidos:** ninguno nuevo (cost tracking es write-to-table, no domain event en sí). Existe `pricing_alias_resolved` (capability `sales-observability-cost-tracking`) que sigue emitiéndose desde el callback handler — verify post-T1.
- **Eventos consumidos:** ninguno (callback es trigger LiteLLM, no event consumer).

## Decisiones ratificadas (/po 2026-05-04)

> Chris delegó las 13 open questions al /po con criterio "robustez/escalabilidad > costo hoy". Las decisiones quedaron lockeadas. Cualquier challenge técnico durante /architect debe escalarse explícitamente — los defaults aquí son binding.

| # | Decisión | Razón |
|---|---|---|
| A1 | `model` field stored SLASHED (`"deepseek/deepseek-v4-flash"`) + `provider` column derived via `litellm.get_llm_provider(model)[1]`. Migration backfills historical stripped rows. | LiteLLM canonical. Future-proof for `bedrock/anthropic.claude-v3` etc. |
| A2 | Expand-contract 3-step migration for tenant API key cols: (1) deprecation migration NULLs cols + code stops reading them (master key only); (2) deploy + verify 1 sprint zero reads; (3) DROP COLUMN migration. NO monolithic migration. | Stripe-style. Rollback safe. |
| A3 | MANDATORY audit pre-delete `gemini.py` by architect-be: every kwarg/quirk verified replicable via LiteLLM (`extra_body`, `safety_settings`, `system_instruction`, function calling shape). If ANY irreplicable → ESCALATE + BLOCK T6. | Gemini-specific quirks; silent failure worse than not migrating. |
| A4 | Drop all 4 columns in T6 phase 2 WITHOUT rename: `openai_api_key`, `deepseek_api_key`, `kimi_api_key`, `dashscope_api_key`. | All 4 die together; rename+drop in same migration = visual debt. |
| A5 | T2 EXTENDS existing `backend/src/shared/agent_observability/pricing/litellm_sync.py` + adds reconciliation drift detection vs upstream `model_prices_and_context_window.json`. NO new file. | anti-duplication.md compliance. |
| A6 | `make sync-pricing` triggered by ARQ worker nightly cron (primary, same security perimeter) + GHA manual trigger backup for debug only. | DB creds stay inside Nicolify perimeter. Existing observability catches failures. |
| X1 | KEEP LiteLLM proxy mode (`visionarias_litellm:4000`). NO migration to SDK mode. | Operational visibility (spend dashboards, virtual keys future, rate limits central). +20-50ms hop tolerable for LATAM IG DM context. |
| X2 | `calculate_cost()` REMOVED from cost recording path post-T1; retained only as reconciliation utility for billing disputes. | LiteLLM `kwargs["response_cost"]` is the cost SSoT. No double computation. Tier pricing S12 already handled natively by LiteLLM. |

## Próximo paso

Spec ratificada. Hand off `/architect` (skip /ux porque service-story).
/architect lee 01-spec.md + 00-story.md → spawnea /architect-be (+ /architect-agentic si Story B harness toca sales_agent state) → produce 03-arch-be.md + 04-tickets.yaml con sub-tickets ordenados (T1..T9 para Story A; harness scaffolding para Story B).

## Changelog

- v1 2026-05-04 — `/po` draft inicial post-reframe Chris (scope expansión deepseek-fix → litellm-canonicalization). Incluye los 4 scenarios obligatorios, 6 open questions para Chris, service_contract type `event_handler`.
- v2 2026-05-04 — Chris delegó decisiones; /po lockeó las 13+2 decisions, ratificó.
