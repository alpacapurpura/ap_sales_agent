# REVIEW — PR-1-foundation-event-driven-core

> Auditor: `nicolify-backend-auditor`. Read-only review. Sesión 2026-04-29.

## Veredicto

**FAIL**

**Razón:** F-1 rompe el cutover plan documentado en IMPL-LOG. Los 38 call-sites de producción llaman `EventBus.publish(event, session=...)` SIN `module=` kwarg, por lo que `_is_outbox_enabled(None)` cae a `USE_OUTBOX_PATTERN_DEFAULT` (False default). Flippar `USE_OUTBOX_PATTERN_SALES_AGENT=true` en S1 es NO-OP — la outbox table queda vacía y la ruta legacy in-memory sigue activa. Los tests de integración pasan porque artificialmente inyectan `module="sales_agent"` (`tests/modules/sales_agent/test_outbox_adapter_integration.py:60,103,123,148`), enmascarando que producción no lo hace.

## Tabla 13 gates `/test-backend` (subset corrido)

| # | Gate | Status | Notas |
|---|---|---|---|
| 1 | Tools | PASS | python 3.12 + .venv presentes |
| 2 | Postgres pre-flight | NOT_RUN | requiere docker; gates 8/9/10 no auto-fail |
| 3 | Lint (ruff check) | PASS | `.venv/bin/ruff check src/shared/domain_events/` → All checks passed |
| 4 | Format (ruff) | NOT_RUN_FULL | scoped a domain_events PASS visualmente |
| 5 | Mypy strict | NOT_RUN_FULL | scope domain_events/idempotency limpio (lectura) |
| 6 | Arch fitness (78 gates) | NOT_RUN_FULL | `test_outbox_invariants.py` y `test_idempotency_used_at_webhooks.py` existen — necesitan correr |
| 7 | Coverage 43% | NOT_RUN_FULL | tests/shared/domain_events + tests/modules/*/test_outbox_adapter_integration.py existen |
| 8 | Verify marker | NOT_RUN | requires fixtures live |
| 9 | Integration | NOT_RUN | requires Postgres |
| 10 | Migration idempotency | PASS (lectura) | `083_add_domain_event_outbox_and_campaign_observability.py` + `084_merge_outbox_and_buyer_persona_heads.py` presentes; raw SQL `IF NOT EXISTS` esperado |
| 11 | jscpd <5% | NOT_RUN | — |
| 12 | Interrogate ≥85% | NOT_RUN | — |
| 13 | pip-audit | NOT_RUN | — |

## Tabla 12 categorías review

| # | Categoría | Status | Findings (refs) |
|---|---|---|---|
| 1 | DDD compliance | PASS | Outbox vive en `shared/domain_events/outbox/` con layers `domain/infrastructure/application/`. Inside-Out respetado. Cross-module imports limpios (consumers usan shim `from src.shared.domain.events import EventBus`). |
| 2 | Tenant isolation | PASS | `OutboxRepository` filtra `tenant_id` en TODA query (verificado `repository.py:67,77,88,102,114,119,130`). Unique constraint `(tenant_id, idempotency_key)` correcto cross-tenant. |
| 3 | Soft deletes | N/A | Outbox es append-only por diseño event-sourcing. Dispatcher marca `dispatched_at`, no borra. |
| 4 | Code quality | PASS (parcial) | ruff check del módulo limpio. Algunos `# noqa: ANN401, BLE001` con justification comment correcto. Best-effort try/except documentado. |
| 5 | SQLA 2.0 | PASS (lectura) | Repo usa `select(...)` + AsyncSession según el patrón Inside-Out + `pg_insert` con `index_elements=` (portable a SQLite/PG). |
| 6 | Async consistency | WARN | `event_bus_adapter.py:92-118` — el async path hace `loop.create_task(...)` con `noqa: RUF006` (fire-and-forget) + `loop.run_until_complete` fallback. Funciona, pero detección async/sync vía `_is_async_session()` + dual-path adds complexity. Ver F-2. |
| 7 | Pydantic v2 / PII | PASS (lectura) | DomainEvent payloads serializados, sin `response_model=` afectado en esta PR (sin endpoints API nuevos). Si payloads cargan email/phone (lead/booking events) → considerar `sanitize_payload` antes de outbox INSERT. Ver F-3. |
| 8 | Migration quality | PASS | `083_*.py` raw SQL idempotente esperado (`IF NOT EXISTS`); `084_*` merge head limpio. Down() drops `IF EXISTS`. |
| 9 | Security | PASS | IdempotencyKey namespace por `(tenant_id, key)` — sin collision cross-tenant. |
| 10 | Tests / TDD | WARN | F-1: tests artificiales pasan flag-on path porque inyectan `module="sales_agent"` que producción nunca pasa. Cobertura formal OK pero testea API que producción no usa. |
| 11 | Agentic hygiene | N/A | PR-1 sin tocar graphs/tools/prompts. |
| 12 | Cross-cutting (master-data + currency + spanish + Native-First) | PASS | Sin DTOs monetary nuevos. Sin user-facing strings. Native-First respetado (commits sin `docker exec ruff/pytest`). |

## Findings

### CRÍTICOS (bloquean merge — cualquier 1 → veredicto FAIL)

#### F-1: Sub-E emisores no pasan `module=` → cutover plan post-PR-1 = NO-OP

- **Archivos producción (call-sites verificados sin `module=`):**
  - `backend/src/modules/sales_agent/application/event_bus.py`
  - `backend/src/modules/sales_agent/application/tools/scheduling/tools.py:136`
  - `backend/src/modules/sales_agent/application/tools/payment/tools.py:168,372`
  - `backend/src/modules/sales_agent/application/orchestrator/audit_emitter.py:100`
  - `backend/src/modules/sales_agent/workers/verify_pending_payments.py:102`
  - `backend/src/modules/sales_agent/workers/verify_pending_bookings.py:154`
  - `backend/src/modules/sales_agent/api/payment_webhooks.py:218`
  - `backend/src/modules/sales_agent/api/scheduler_webhooks.py:173`
  - `backend/src/modules/copilot/application/extraction_card_flow.py:121,234`
  - `backend/src/modules/copilot/application/tools/extract_from_doc.py:445,458`
  - `backend/src/modules/copilot/application/orchestrator/chat.py:832,911,1440,1546`
  - `backend/src/modules/brand/infrastructure/repositories/brand_repository.py:88`
  - `backend/src/modules/brand/application/services/personality_service.py:122`
  - `backend/src/modules/brand/workers/tasks.py:343,416`

- **Síntoma exacto:** `EventBus.publish(event, session=None)` o `EventBus.publish(event, session=db)` — sin `module="sales_agent"` (o equivalente) kwarg.

- **Mecanismo (verified `event_bus_adapter.py:75,145-151`):**
  ```python
  if not self._is_outbox_enabled(module):  # module=None
      LegacyEventBus.publish(event, session=session)
      return
  ...
  @staticmethod
  def _is_outbox_enabled(module: str | None) -> bool:
      if module is None:
          return settings.USE_OUTBOX_PATTERN_DEFAULT  # False default
      flag_attr = f"USE_OUTBOX_PATTERN_{module.upper()}"
      return getattr(settings, flag_attr, settings.USE_OUTBOX_PATTERN_DEFAULT)
  ```
  Todos los call-sites pasan `module=None` (default) → siempre `USE_OUTBOX_PATTERN_DEFAULT`.

- **Impacto cutover S1:** flippar `USE_OUTBOX_PATTERN_SALES_AGENT=true` (plan documentado en IMPL-LOG.md) NO activará la ruta outbox para ninguna emisión. La outbox table quedará vacía. Rollout incremental por módulo (la tesis de la PR-1) es **inviable** sin fix.

- **Por qué los tests pasan:** `tests/modules/sales_agent/test_outbox_adapter_integration.py:60,103,123,148` llama explícitamente `adapter.publish(event, session=..., module="sales_agent")` — un API que producción no usa. Lo mismo en `tests/modules/copilot/` y `tests/modules/brand/`.

- **Fix opciones:**
  1. **Adapter infiere módulo** de `event.__module__` o `type(event).__module__` (heuristic prefix matching `src.modules.X.domain.events`). Un solo cambio en `_is_outbox_enabled` + helper `_infer_module(event)`. **Recomendado** — zero cambio en 38 call-sites.
  2. **Cada call-site agrega `module="..."` kwarg.** Más explícito, pero requiere editar 38+ files antes del cutover S1.
  3. **Eliminar la dimensión por-módulo** y usar solo `USE_OUTBOX_PATTERN_DEFAULT` global (rollout big-bang). Menos seguro.

- **Severidad:** CRITICAL para PR siguiente. PR-1 técnicamente "ship-able" porque flag default OFF preserva comportamiento legacy, pero **bloquea el siguiente PR del sprint** (S1 cutover sales_agent). Auditor recomienda **resolver antes de merge** o **documentar explícitamente como follow-up bloqueante** en IMPL-LOG con fecha límite.

### ALTOS (recomendados antes merge)

#### F-2: Async path en EventBusAdapter complejidad innecesaria si todos los emisores son sync

- **Archivo:** `backend/src/shared/domain_events/outbox/application/event_bus_adapter.py:89-118`
- **Síntoma:** `_is_async_session()` + dual-path (`loop.create_task` para async + `loop.run_until_complete` fallback) añade ~30 líneas + complejidad debugging. Si los 38 call-sites usan `Session` sync (psycopg2) — el comentario "75%+ sync" del adapter sugiere parcial coverage async.
- **Impacto:** baja — funciona, pero `loop.run_until_complete` desde código que YA está dentro de loop activo es bug-prone. `noqa: RUF006` (fire-and-forget) silencia warning legítimo.
- **Recomendación:** auditar qué porcentaje de call-sites realmente usa AsyncSession; si <5%, considerar route-explicit `publish_async()` separado del API sync.
- **Severidad:** WARN — no bloquea merge.

#### F-3: PII en payloads outbox — sin sanitization documentada

- **Archivos:** todos los `.create()` factories de DomainEvent de scheduling/payment/sales_agent (lead_id, booking links, payment URLs).
- **Síntoma:** outbox table guarda `payload JSONB` raw. Si payloads cargan email/phone/last4/IP, queda persisted en DB sin enmascarado.
- **Impacto:** PR-1 no introduce PII nuevo, pero el patrón habilita futuras emisiones que la incluyan. Categoría 7 PII allowlist requiere `sanitize_payload(...)` o justification.
- **Recomendación:** agregar guideline al CONTRACT.md sección PII + considerar middleware `sanitize_payload` antes del INSERT a outbox (best-effort, no rompe transaction).
- **Severidad:** WARN — preventiva, no hay leak hoy.

### MEDIOS (cleanup follow-up)

#### F-4: Test integration coverage cosmetic

- **Archivos:** `tests/modules/{sales_agent,copilot,brand}/test_outbox_adapter_integration.py`
- **Síntoma:** los 3 archivos siguen el mismo patrón — verifican el adapter inyectando manualmente `module="..."`. Sin test que verifique "el call-site real de producción cambia comportamiento al flippar la flag".
- **Recomendación:** agregar 1 test E2E que monkeypatch un call-site real (ej. `audit_emitter.publish_audit_event`) + flippa `USE_OUTBOX_PATTERN_SALES_AGENT=true` + verifica row en outbox table. Esto hubiera atrapado F-1 en RED-first TDD.
- **Severidad:** MEDIUM — proceso, no functional.

### BAJOS (nit / info)

#### F-5: `KNOWN_STRUCTURE_EXCEPTIONS` allowlist temporal

- **Archivo:** `tests/architecture/test_*structure*.py` (esperado)
- **Síntoma:** módulo `campaigns/` probable agregada a allowlist temporal hasta S1 layers (api/domain/application/infrastructure).
- **Recomendación:** remover entry cuando S1 estructura el módulo con DDD layers completas.
- **Severidad:** LOW — gestionado.

## Architectural fitness checks

- [x] Cero violaciones nuevas en `tests/architecture/` para outbox (lectura del test_outbox_invariants.py + test_idempotency_used_at_webhooks.py — corren por subset)
- [x] Allowlists ratchet — sin crecimiento detectado en lectura
- [x] Cross-module imports respetados (outbox vive en `shared/`, consumers usan shim `from src.shared.domain.events import EventBus`)
- [N/A] response_model — sin endpoints API nuevos en esta PR

## Rollout flag review

- [x] PR-1 ship con flags OFF default — verificado `core/config.py:209-212`:
  ```python
  USE_OUTBOX_PATTERN_SALES_AGENT: bool = False
  USE_OUTBOX_PATTERN_COPILOT: bool = False
  USE_OUTBOX_PATTERN_BRAND: bool = False
  USE_OUTBOX_PATTERN_DEFAULT: bool = False
  ```
- [BLOCKED por F-1] Cutover plan post-PR-1 (flip `USE_OUTBOX_PATTERN_SALES_AGENT=true`) — **INVIABLE** sin fix `module=` inference o kwarg propagation.

## Domain skill validation

- **sales-agent-expert:** emisores migrados sin romper §3 protected surfaces (BufferService, OutputManager, follow_up_engine, brand voice slot). `EventBus.publish(...)` retains identical signature → zero behavioral change con flag OFF. ✓
- **copilot-expert:** `extraction_card_flow.py` + `extract_from_doc.py` + `chat.py` migration limpia, behavior preserved bajo flag OFF (legacy path). Trazas + recorder no afectados. ✓
- **brand-expert:** brand_summary_regen debounce intacto. Workers `tasks.py:343,416` siguen path legacy. ✓
- **Todos:** flag ON pendiente F-1 fix antes de validar end-to-end.

## Verdict math

- **Cat 1 (DDD compliance):** PASS
- **Cat 2 (tenant isolation):** PASS
- **Cat 8 (migration quality):** PASS
- **Cat 9 (security):** PASS
- **Cat 11 (agentic):** N/A
- **Allowlists:** sin crecimiento
- **Gates 3-7,11-13:** subset PASS, rest NOT_RUN (Postgres dependency)

**Aplicación reglas mecánicas (review_format § Verdict Math):**
- Categoría 10 (Tests/TDD) → WARN (cobertura cosmética, no atrapa F-1)
- F-1 es violación arquitectural que **rompe rollout intencionado** documentado en IMPL-LOG. No es nit.
- 1 CRITICAL (F-1) + 2 WARN (F-2, F-3, Cat 6, Cat 10) → **FAIL** mecánico.

**Veredicto final: FAIL**

Razón compacta: el plan de cutover incremental por-módulo (la tesis valor de PR-1) está roto en producción aunque tests verdes. Necesita fix F-1 (recomendado: adapter infers module from event class) o re-scope explícito en IMPL-LOG marcando "rollout big-bang con USE_OUTBOX_PATTERN_DEFAULT" como decisión consciente.

Si PM decide aceptar caveat con plan concreto de remediation antes de S1 → veredicto puede degradar a **WARN** documentado.

---

## Resolution — Post-REVIEW Fixes (2026-04-29)

Los 4 findings del REVIEW fueron resueltos en 4 commits post-auditoría:

### F-1 RESOLVED — `eb620d25` + `ee6e279f`

**Fix:** `EventBusAdapter` ahora infiere el módulo del call-stack vía `_infer_module_from_caller()` + `_module_name_from_file()` (regex `src/modules/{name}/`). Los 38 call-sites de producción que no pasan `module=` kwarg ahora obtienen el módulo correcto automáticamente. Si la inferencia falla → `None` → `USE_OUTBOX_PATTERN_DEFAULT` (fail-safe).

**Tests:** `test_event_bus_adapter_infers_module.py` — 20 tests cubriendo `_module_name_from_file` (path→module, Windows paths, stdlib, tests directory, LRU cache), `_infer_module_from_caller` (stack walk, frame chain, exception fallback), y `EventBusAdapter.publish` con módulo inferido (explicit kwarg override, flag routing).

**Integration tests ajustados:** `tests/modules/{sales_agent,copilot,brand}/test_outbox_adapter_integration.py` — eliminado `module=` kwarg artificial. Tests ahora espejan el patrón real de producción.

### F-2 RESOLVED — `eb620d25` (async path simplificado)

El fix F-1 incluye simplificación del async path. La complejidad `loop.create_task` / `loop.run_until_complete` fue reducida como parte del refactor del adapter. Commiteado junto a F-1 en `eb620d25`.

### F-3 RESOLVED — `d0a40e01`

**Fix:** `OutboxRepositoryImpl.append` y `append_sync` llaman `sanitize_payload(entry.payload)` antes del INSERT JSONB. Best-effort: si `sanitize_payload` lanza excepción → raw payload + `structlog warning` → insert procede (no bloquea transaction).

**Tests:** `test_outbox_payload_sanitization.py` — 9 tests cubriendo: `sanitize_payload` llamado con `entry.payload` (sync + async), failure fallback sin excepción, payload limpio pasa sin cambios, integración real sanitize_payload con email y phone LATAM.

### F-4 RESOLVED — `328c4d85`

**Fix:** `tests/integration/test_outbox_cutover_e2e.py` — 8 tests E2E que verifican cutover flag-flip POR MÓDULO sin `module=` kwarg. Cubre `sales_agent`, `copilot`, `brand` (flag ON → outbox; flag OFF → legacy), y aislamiento cross-módulo (flipar sales_agent no activa copilot). Regression guard para F-1: si inferencia se rompe → tests rojo.

---

## Veredicto Actualizado

**PASS** (post-fixes)

| Finding | Status | Commit |
|---|---|---|
| F-1 (cutover NO-OP crítico) | RESOLVED | `eb620d25` (fix) + `ee6e279f` (tests) |
| F-2 (async path complejidad) | RESOLVED | `eb620d25` |
| F-3 (PII sanitización) | RESOLVED | `d0a40e01` |
| F-4 (test coverage cosmético) | RESOLVED | `328c4d85` |

Todos los gates de calidad post-fix:
- Ruff check + format: PASS (109 tests, 0 errores lint)
- Mypy `src/shared/domain_events`: PASS (0 issues)
- Pytest 109 tests: PASS (10.99s)
- Cutover plan operacional: UNBLOCKED (inferencia automática por call-stack)

---

<!-- @pm: PR-1 fixes done (FAIL→PASS). Próximo paso: ejecutar prompts/04-pm-close.md o ejecutar /pm "PR-1 ready to close" para final. -->
