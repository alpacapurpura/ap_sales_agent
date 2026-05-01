# Anti-Duplication

**Origen rule:** PR-1-pi1-bugs-hotfix 2026-05-01. Builder agentic creó `modules/sales_agent/observability/recording/turn_envelope.py` mirror de `modules/copilot/observability/recording/turn_envelope.py` existente. Chris flagged "no duplicar codigo" → revert + abrir PR-2 shared abstraction.

## Regla cardinal

ANTES de crear cualquier archivo nuevo en `modules/X/<subsystem>/`, ejecutar grep cross-codebase para verificar si patrón equivalente existe en otro módulo o en `shared/`. Si existe → **EXTEND vía herencia/composición DESDE shared**. NUNCA mirror.

## Inventario canónico shared abstractions (SSoT)

Estas abstracciones viven en `shared/` y son el ÚNICO lugar donde cada patrón se define. Módulos los heredan o consumen, NUNCA mirror.

| Pattern | Path canónico shared | Consumers (módulos que heredan) |
|---|---|---|
| **Observability turn envelope** | `shared/agent_observability/recording/turn_envelope.py::BaseObservabilityContext` (PR-2 pendiente) | `copilot/observability/recording/context.py` · `sales_agent/observability/recording/context.py` · futuros agentes |
| **Callback handler base** | `shared/agent_observability/recording/base_callback_handler.py::BaseAgentCallbackHandler` | `copilot/observability/recording/callback_handler.py` · `sales_agent/observability/recording/callback_handler.py` |
| **PII sanitization** | `shared/agent_observability/recording/sanitization.py::sanitize_payload` | todos agentes |
| **FX resolver factory** | `shared/agent_observability/cost/fx_resolver.py::FXResolver.default()` (PR-2 pendiente — actual requiere `http_client_factory` arg) | todos agentes que registran cost |
| **Pricing resolver** | `shared/agent_observability/cost/calculator.py` + `pricing_snapshot_repository.py` | todos agentes |
| **Trace event repo base** | `shared/agent_observability/persistence/base_trace_event_repo.py::BaseTraceEventRepoProtocol` | copilot · sales_agent |
| **LLM call repo base** | `shared/agent_observability/persistence/base_llm_call_repo.py` | copilot · sales_agent |
| **Channel format registry** | `shared/agent_observability/channels/format_for_channel.py` + `channels/format.py` | sales_agent (canónica) · copilot (consume) |
| **Intent detector** | `shared/agent_observability/channels/intent_detector.py` | sales_agent · futuros |
| **Tenant billing config repo** | `shared/agent_observability/persistence/tenant_billing_config_repository.py` | todos agentes que cobran |
| **Currency resolver tenant** | `shared/agent_observability/cost/_resolve_tenant_currency` (TBD shared post PR-2) | todos agentes |
| **Extraction orchestrator base** | `shared/application/extraction/base_orchestrator.py::BaseExtractionOrchestrator` | brand · offer · buyer_persona · landing |
| **Locale VO** | `shared/domain/locale.py::TenantLocale` | todos módulos UI/timezone |
| **LLM router + providers** | `shared/infrastructure/llm/router.py` + `providers/` | todos módulos que llaman LLMs |
| **Outbox pattern** | `shared/domain_events/outbox/` | todos módulos que emiten eventos |
| **Idempotency** | `shared/idempotency/` | todos módulos con tasks idempotentes |
| **Billing guards** | `shared/billing/` (BudgetGuard + RateLimiter) | sales_agent · campaigns · copilot |
| **Compliance gates** | `shared/compliance/` (ComplianceService) | campaigns · sales_agent |
| **Domain events** | `shared/events/` | todos cross-module via event bus |
| **Cross-module ports** | `shared/links/ports/` | todos módulos para integraciones cross-domain |

**Regla shrink-only:** este registro NO se duplica per-módulo. Si un patrón nuevo emerge cross-agent (ej: agente N+1) y dos módulos lo necesitan → primer commit lo sube a shared, NUNCA primero in-module.

## Workflow obligatorio antes crear archivo nuevo

1. **Step 0 GATE pre-write builder** (debe ejecutarse ANTES de cualquier `Write` o `Edit` que crea file):
   ```bash
   # Si vas a crear modules/X/Y/Z.py:
   find /home/chris/AISALESHT/backend/src -name "Z.py" 2>/dev/null
   grep -rn "class <ClassName>" /home/chris/AISALESHT/backend/src/shared/ /home/chris/AISALESHT/backend/src/modules/ 2>/dev/null
   ```

2. **Si match → ESCALATE PM** con findings:
   - Path existing
   - Diff conceptual entre lo que querés crear vs existing
   - Recomendación: A) extend existing, B) lift to shared, C) caso edge real new

3. **Si NO match** y categoría coincide con tabla shared abstractions arriba → STOP, lift a shared primero.

4. **PM commit a CONTRACT/PR.md** la decisión EXTEND vs LIFT vs NEW con paths exactos.

## Anti-patterns prohibidos

- ❌ `modules/X/observability/recording/turn_envelope.py` cuando `modules/copilot/observability/recording/turn_envelope.py` existe — debe ir a `shared/agent_observability/recording/turn_envelope.py` y ambos heredar
- ❌ Mirror callback handler con mismo trace fields/structure — heredar `BaseAgentCallbackHandler`
- ❌ Reimplementar `FXResolver(http_client_factory=...)` en N módulos — usar `FXResolver.default()` factory en shared
- ❌ Copy-paste lambda `lambda: httpx.Client(timeout=10)` en N call sites — encapsular en classmethod
- ❌ Mirror `_resolve_tenant_currency` helper — lift a shared
- ❌ Mirror PricingResolver setup — extract a shared factory
- ❌ Re-implementar PII sanitization local — siempre usar `shared/agent_observability/recording/sanitization`
- ❌ Mirror channel format dispatch — siempre usar `shared/agent_observability/channels/format_for_channel`

## Enforcement layers

| Layer | Mecanismo | Owner |
|---|---|---|
| 1 — PM PR.md template | Bloque "Existing systems audit" mandatory con grep evidence (paths + line numbers) | `/pm` skill |
| 2 — Builder Step 0 GATE | Prompt template `02-builder-*.md` Step 0 ejecuta grep + escalate si match | builder agent |
| 3 — Auditor Cat 12 | Mirror detection scan: para cada archivo nuevo en MR, buscar similar name+structure en otros módulos. FAIL si encontrado | auditor agent |
| 4 — Architect mandatory | Cuando PR toca `shared/` o crea archivo en `modules/X/<subsystem>/` cuyo subsystem existe en otro módulo → architect Opus mandatory antes builder | `/pm` orchestration |
| 5 — Skills (copilot-expert + sales-agent-expert) | Warning explícito + tabla shared abstractions referenciada | skills self-load |

## Penalizaciones

- Builder PR sin Step 0 grep gate → REVERT obligatorio
- Auditor sin Cat 12 check → re-audit
- PM skip architect cuando regla aplica → process-learnings.md case study + retrospective Chris

## Skill loading directive

Cuando se invoca `copilot-expert` o `sales-agent-expert` skill, esta rule debe ser cargada automáticamente en su SKILL.md frontmatter (referenciada).
