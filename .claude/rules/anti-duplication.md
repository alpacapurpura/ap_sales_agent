# Anti-Duplication

**Origen:** PR-1-pi1 2026-05-01. Builder agentic mirror `turn_envelope.py` cross-module → revert + lift shared.

## Regla cardinal

ANTES crear archivo `modules/X/<subsystem>/`: grep cross-codebase. Match → **EXTEND vía herencia DESDE shared**. NUNCA mirror.

## Inventario shared abstractions (SSoT)

Patrón canónico vive en `shared/`. Módulos heredan, NUNCA mirror.

| Pattern | Path canónico shared | Consumers |
|---|---|---|
| Observability turn envelope | `shared/agent_observability/recording/turn_envelope.py::BaseObservabilityContext` | copilot · sales_agent · futuros |
| Callback handler base | `shared/agent_observability/recording/base_callback_handler.py::BaseAgentCallbackHandler` | copilot · sales_agent |
| PII sanitization | `shared/agent_observability/recording/sanitization.py::sanitize_payload` | todos agentes |
| FX resolver factory | `shared/agent_observability/cost/fx_resolver.py::FXResolver.default()` | todos agentes con cost |
| Pricing resolver | `shared/agent_observability/cost/calculator.py` + `pricing_snapshot_repository.py` | todos agentes |
| Trace event repo base | `shared/agent_observability/persistence/base_trace_event_repo.py` | copilot · sales_agent |
| LLM call repo base | `shared/agent_observability/persistence/base_llm_call_repo.py` | copilot · sales_agent |
| Channel format registry | `shared/agent_observability/channels/format_for_channel.py` | sales_agent · copilot |
| Intent detector | `shared/agent_observability/channels/intent_detector.py` | sales_agent · futuros |
| Tenant billing config | `shared/agent_observability/persistence/tenant_billing_config_repository.py` | todos cobran |
| Currency resolver tenant | `shared/agent_observability/cost/_resolve_tenant_currency` | todos agentes |
| Extraction orchestrator | `shared/application/extraction/base_orchestrator.py::BaseExtractionOrchestrator` | brand · offer · buyer_persona · landing |
| Locale VO | `shared/domain/locale.py::TenantLocale` | todos UI/timezone |
| LLM router + providers | `shared/infrastructure/llm/router.py` + `providers/` | todos llaman LLMs |
| Outbox pattern | `shared/domain_events/outbox/` | todos emiten eventos |
| Idempotency | `shared/idempotency/` | todos tasks idempotentes |
| Billing guards | `shared/billing/` (BudgetGuard + RateLimiter) | sales_agent · campaigns · copilot |
| Compliance gates | `shared/compliance/` (ComplianceService) | campaigns · sales_agent |
| Domain events | `shared/events/` | todos cross-module |
| Cross-module ports | `shared/links/ports/` | todos cross-domain |

**Shrink-only:** registro NO duplica per-módulo. Patrón nuevo cross-agent → lift shared primer commit.

## Workflow pre-write

1. **Step 0 GATE** (antes `Write`/`Edit` que crea file):
   ```bash
   find /home/chris/AISALESHT/backend/src -name "Z.py" 2>/dev/null
   grep -rn "class <ClassName>" /home/chris/AISALESHT/backend/src/{shared,modules}/ 2>/dev/null
   ```

2. Match → ESCALATE PM con paths + diff conceptual + recomendación (A extend / B lift / C edge new).
3. NO match + categoría coincide tabla → STOP, lift shared primero.
4. PM commit decisión a CONTRACT/PR.md con paths exactos.

## Anti-patterns prohibidos

- ❌ Mirror `modules/X/observability/recording/turn_envelope.py` cuando copilot existe — lift shared
- ❌ Mirror callback handler — heredar `BaseAgentCallbackHandler`
- ❌ Re-implementar `FXResolver(http_client_factory=...)` N módulos — `FXResolver.default()`
- ❌ Copy-paste `lambda: httpx.Client(timeout=10)` — encapsular classmethod
- ❌ Mirror `_resolve_tenant_currency` — lift shared
- ❌ Mirror PricingResolver setup — extract factory shared
- ❌ Re-implementar PII sanitization local — usar shared `sanitization`
- ❌ Mirror channel format dispatch — usar shared `format_for_channel`

## Enforcement layers

| Layer | Mecanismo | Owner |
|---|---|---|
| 1 PM PR.md | Bloque "Existing systems audit" mandatory grep evidence | `/pm` skill |
| 2 Builder Step 0 | Prompt template Step 0 grep + escalate match | builder agent |
| 3 Auditor Cat 12 | Mirror detection scan archivo nuevo PR vs otros módulos | auditor |
| 4 Architect mandatory | Tocar `shared/` o subsystem cross-module → architect Opus pre builder | `/pm` orchestration |
| 5 Skills | copilot-expert + sales-agent-expert cargan rule frontmatter | skills |

## Penalizaciones

- Builder sin Step 0 grep → REVERT
- Auditor sin Cat 12 → re-audit
- PM skip architect → process-learnings.md case study
