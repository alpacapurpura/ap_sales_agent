# PR-1 — Fix Broken Tests, Polluter Hunt, Singleton Fixture, EventBus Migration

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-1-fix-broken-tests-and-arch-snapshots |
| Sprint padre | S1-test-integrity-and-coverage |
| PI padre | PI-11-backend-quality-guardrails |
| Estado | ready |
| Tipo | refactor + bug fix |
| Esfuerzo | XL |
| Owner PM | /pm |
| Claimed by session | — |
| Expanded | 2026-05-04 |

## Problema

Failed `/pase-produccion` 2026-05-04 reveló **25 BE failures + 2 FE failures + 1 polluter snapshot test no identificable** después de 3h bisección. Causa raíz arquitectural: commit `64738354` (PR-1 Sub-E PI-2, 2026-04-29) flipeó defaults `USE_OUTBOX_PATTERN_*` False→True sin auditar tests que mockean path legacy `EventBus.publish`.

**Síntomas:**
1. ~24 tests stale (defaults outbox + arch snapshots + endpoint legacy 410 + temperature clamp + import paths)
2. 1 test polluter deterministic (`test_chat_flow_telegram_new_lead_snapshot`) que solo falla en suite completa, NO en isolation
3. Singletons class-level (`LLMFactory._instance`, `ChatOrchestrator._instance`, `SemanticRouter._instance`) leak entre tests
4. `_chat_flow_snapshot_helpers.py` captura `domain_events=[]` siempre (publicaciones reales van por outbox no interceptado)
5. 1 bug real producción: `litellm.py` no clampea kimi temperature (=1.0) → Kimi K2.6 HTTP 400 silencioso (mirror del clamp dead-code en `kimi.py`)
6. 2 FE tests stale: URL slug `/campañas/` (ñ no URL-encoded en Next.js routes — debe ser `/campanas/`)

**Costo invertido referencia:** ~3h sesión + 80min polluter hunt agente + ~500k tokens.

## Outcome esperado

| Outcome | Métrica |
|---|---|
| `pytest` 100% sin flags | 0 failed, 0 deselected, 0 `@pytest.mark.flaky` permanentes |
| `vitest run` 100% | 0 failed |
| Polluter fixed at source | Sin band-aid; root cause identificado + documentado en IMPL-LOG |
| Singleton fixture exhaustivo | TODOS class-level singletons identificados via grep `_instance =` cross-codebase, documentados + reseteados en autouse fixture |
| EventBus mocks migrated | 100% tests legacy `EventBus.publish` mocks → `adapter_bus` mock o outbox table probe |
| Snapshot helpers outbox-aware | `_chat_flow_snapshot_helpers.py` captura `domain_events` real desde outbox table (no return `[]` falso) |
| litellm.py kimi clamp aplicado | Production bug fixed |
| Arch fitness 78/78 PASS | Sin allowlist creciente sin justificación |
| `LegacyEventBus.publish` deprecated | Runtime warning emitted |
| Stash{0} aplicado + revisado + commiteado | 16 archivos integrados en PR-1 commits |

## Walking skeleton

Implementación dividida en 5 fases. Builders business + agentic ejecutan en paralelo (regla M1). PM coordina paths exclusivos.

### Fase 1 — Apply stash + scope baseline

Builder PR-1 (business surface owns) hace `cd /home/chris/AISALESHT && git stash pop` en Step 1 Phase 1 después de leer CONTRACT.md y CONTEXT-BRIEF.md. Revisa cada archivo (lista abajo) y verifica que el fix aplicado coincide con scope expandido. Si fix incompleto/desactualizado vs scope nuevo → re-aplica + extiende.

**Lista 16 archivos del stash (24/25 fixes ya validados sesión 2026-05-04):**

**Backend tests (15) — fixes a tests stale:**
- `backend/tests/architecture/test_ddd_boundaries.py` — 3 entries a `KNOWN_CROSS_MODULE_IMPORTS` (campaigns→sales_agent adapter, crm→campaigns x2)
- `backend/tests/architecture/test_folder_naming.py` — `copilot/api/_dependencies.py` a `KNOWN_PRIVATE_FILE_EXCEPTIONS`
- `backend/tests/architecture/test_sales_agent_anchors.py` — `SALES-AGENT-OUTBOUND-PR7` a `ANCHOR_REGISTRY`
- `backend/tests/architecture/test_sales_agent_system_prompt_order.py` — `CAMPAIGN_CONTEXT` a `EXPECTED_CACHEABLE`
- `backend/tests/conftest.py` — autouse fixture `_reset_singletons_between_tests` (versión inicial — **EXTENDER exhaustivo en PR-1 nueva fase 3**)
- `backend/tests/integration/test_outbound_orchestrator_e2e.py` — fix mock target (`build_sales_agent_callback_handler` → `build_sales_agent_observability_context`)
- `backend/tests/modules/brand/test_brand_section_updated_event.py` — autouse `monkeypatch.setattr(USE_OUTBOX_PATTERN_BRAND=False)` **REVISAR** vs scope nuevo (decisión D1 outbox True permanente — el approach correcto es **migrar test al path nuevo**, NO `False` monkeypatch)
- `backend/tests/modules/brand/test_outbox_adapter_integration.py` — `monkeypatch.setattr` settings con MagicMock USE_OUTBOX_PATTERN_BRAND=False — **REVISAR** mismo
- `backend/tests/modules/copilot/test_offer_section_tools.py` — `test_missing_brand` actualizado a `next_step_hint` contract
- `backend/tests/modules/copilot/test_outbox_adapter_integration.py` — `monkeypatch.setattr` USE_OUTBOX_PATTERN_COPILOT=False — **REVISAR** mismo
- `backend/tests/modules/copilot/test_voice_api.py` — actualizado a esperar 410 Gone
- `backend/tests/modules/copilot/test_voice_combined.py` — `test_legacy_transcribe_endpoint_still_works` esperar 410
- `backend/tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py` — `@pytest.mark.flaky(reruns=2)` + comment **(BAND-AID — REMOVER en PR-1 Phase 4 polluter hunt)**
- `backend/tests/modules/sales_agent/prompts/test_compose_system_prompt.py` — `CAMPAIGN_CONTEXT` a expected
- `backend/tests/shared/domain_events/test_event_bus_adapter.py` — `monkeypatch.setattr` settings con USE_OUTBOX_PATTERN_SALES_AGENT=False — **REVISAR** mismo

**Backend source (1) — REAL BUG FIX:**
- `backend/src/shared/infrastructure/llm/providers/litellm.py` — kimi clamp logic (production bug — temperature=1.0 → Kimi K2.6 HTTP 400 silencioso). Mirror del clamp adapter legacy `kimi.py` dead code post `LITELLM_PROXY_ENABLED=True` default.

**Frontend (1):**
- `frontend/src/features/closer-studio/components/inbox/__tests__/CampaignTag.test.tsx` — URL slug `/campañas/` → `/campanas/` (ASCII URLs Next.js)

### Fase 2 — Tests EventBus mock migration (decisión D2)

Audit sistemático tests que mockean `EventBus.publish` legacy. Migración:

**Approach correcto (escala 1000 clientes):** outbox `True` permanente. Tests deben **mockear `adapter_bus` directamente** o **probar via outbox table inspection**. NO usar `monkeypatch.setattr(USE_OUTBOX_PATTERN_*=False)` como en stash inicial — eso es band-aid temporal.

Workflow:
1. Grep cross-codebase: `EventBus.publish`, `LegacyEventBus`, `event_bus.publish`, mock paths del path legacy
2. Cada test detectado → migrar:
   - Si test asserts EVENT FUE PUBLICADO → switch a probe `adapter_bus.publish` mock o query DB outbox table
   - Si test asserts HANDLER FUE INVOCADO → switch a inspection outbox enqueue + simulación dispatcher
3. Documentar lista completa migrated en IMPL-LOG.md sección "EventBus migration audit"
4. Auditor Cat 12 valida cobertura + 0 omisiones

### Fase 3 — Singleton fixture exhaustivo

Grep cross-codebase patterns:
- `_instance = None` (class-level)
- `_instance: Optional[`
- `cls._instance`
- LangGraph compilation cache patterns (`compiled_graph`, `_compiled`)
- deepagents global state patterns
- Module-level mock targets de `uuid.uuid4`, `datetime.now`, etc.

Lista mínima conocida:
- `LLMFactory._instance`
- `ChatOrchestrator._instance`
- `SemanticRouter._instance`

Builder PR-1 produce lista exhaustiva validada por architect CONTRACT § Singleton inventory. Autouse fixture `tests/conftest.py::_reset_singletons_between_tests`:
1. Documenta CADA singleton con comment `# {ClassName}._instance — reset reason: {why}`
2. Resetea pre-test (yield)
3. Resetea post-test (cleanup)
4. Si singleton tiene cleanup específico (close connections, etc.) → invocar antes reset

Fixture extiende versión stash (que es initial). Auditor agentic Cat review valida exhaustividad.

### Fase 4 — Polluter hunt sistemático snapshot test

Target: `test_chat_flow_telegram_new_lead_snapshot` que falla en suite completa pero pasa en isolation.

Methodology obligatoria (sin band-aid `@pytest.mark.flaky` final):
1. **Bisección de orden** — `pytest --collect-only > order.txt` → ejecutar suite hasta target con ordenes parciales (binary search) hasta identificar tests previos que mutan estado
2. **JSON diff exhaustivo** — capturar baseline snapshot (test isolation) vs snapshot suite-completa cuando falla → diff campo a campo
3. **Setup-only suite** — pytest --setup-only para identificar fixtures cargadas
4. **Sospechosos primarios** (en orden investigación):
   - LangGraph global compilation cache (graphs compiled once, reused; mutación cross-test posible)
   - deepagents subagent state cache
   - Módulo-level `uuid.uuid4` patches (tests previos patchean uuid module-wide → leak)
   - LLM router/factory state leak
   - Settings mutation persistente (settings cached, monkeypatch restore falla)
   - `langgraph.checkpoint` state shared
   - Mocks de `httpx.AsyncClient` que persisten cross-test
5. Documentar hipótesis + experimento + resultado en IMPL-LOG sección "Polluter hunt log"
6. **Fix at source** una vez identificado: NO marker, NO `xfail`. Si polluter es módulo del sistema → fixearlo de raíz aunque requiera refactor (LangGraph compilation cache reset, deepagents global state isolation, mock module-level uuid scoping)
7. **Pre-PR-1 ship:** REMOVER `@pytest.mark.flaky(reruns=2)` del stash. Test debe pasar 1.0 sin reruns

Sin budget cap explícito (decisión Chris 2026-05-04). Si supera 6h Opus → escalate PM Chris budget extra. **NO ship con band-aid permanente.**

### Fase 5 — Snapshot helpers outbox-aware

`backend/tests/modules/sales_agent/orchestrator/_chat_flow_snapshot_helpers.py` (y similares) capturan `domain_events=[]` siempre porque mockean `EventBus.publish` legacy.

Migración:
1. Helper consume outbox table directamente: `select(DomainEventOutbox).where(tenant_id=...).order_by(created_at)`
2. O instala `adapter_bus.publish` probe que captura events real
3. Snapshot ahora refleja realidad post-flag-flip
4. Tests usando helpers: actualizar assertions si snapshot cambia (revisar baseline)

### Fase 6 — LegacyEventBus runtime warning (deprecation gradual D3)

`backend/src/shared/domain_events/legacy_event_bus.py` (o equivalente):
1. Llamar `LegacyEventBus.publish` cuando outbox flag `True` → emit `warnings.warn(DeprecationWarning, ...)` + `structlog.warning("legacy_event_bus_called_outside_test_context", ...)`
2. Excepción: tests internos que prueban LegacyEventBus mismo (capability test) → suppress warning
3. Production runtime: warning visible en logs (alerta debug)

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A — Revertir flags `USE_OUTBOX_PATTERN_*` a False | Tests pasan inmediato; mínimo blast radius | Bomba tiempo @ scale 1000 clientes multi-worker; eventos perdidos in-memory; postergar problema 10x cost | **descartada** — decisión Chris D1 |
| B — Outbox `True` permanente + tests migran al path nuevo + regla anti-default-flip cementada | Robusto escala; CI permanente verde; previene recurrencia | Scope grande PR-1 + PR-3 + PR-4; investigación polluter sin budget cap | **ELEGIDA** — robustez @ 1000 clientes |
| C — Outbox `True` + tests usan `monkeypatch False` por test | Simple; preserva isolation per-test | NO migra tests al path real; futuro flip de otra flag replicará bug; band-aid del band-aid | **descartada** — síntoma no causa |

## Validación técnica preliminar

- Modules afectados: `brand`, `copilot`, `sales_agent`, `shared`, `campaigns`, `crm`, `core`, `frontend/closer-studio`
- Blockers: ninguno (decisiones D1-D7 tomadas)
- Tiempo estimado: 1 architect Opus (compartido PR-1+PR-3) + 2 builders paralelos + audit cruzado + fix-loop max 3 iter cada surface

## Existing systems audit

| Sistema | Path | Decisión |
|---|---|---|
| `LegacyEventBus` (in-memory dispatcher) | `backend/src/shared/domain_events/legacy_event_bus.py` | EXTEND con runtime deprecation warning. NO eliminar capability todavía (tests internos lo necesitan) |
| `event_bus_adapter` (outbox dispatcher) | `backend/src/shared/domain_events/outbox/application/event_bus_adapter.py` | Path canónico — tests migran acá |
| `_reset_singletons_between_tests` (stash) | `backend/tests/conftest.py` | EXTEND a exhaustivo (versión stash es initial) |
| `_chat_flow_snapshot_helpers.py` | `backend/tests/modules/sales_agent/orchestrator/` | EXTEND outbox-aware |
| `LLMFactory._instance` | `backend/src/shared/infrastructure/llm/factory.py` | NO touch source — solo fixture reset en conftest |

## Decisiones (cementadas en PI.md)

D1, D2, D3, D4, D5, D6, D7 — ver `PI-11/PI.md` § Decisión arquitectónica clave.

## Out of scope

- Coverage P0/P1 lift (PR-2)
- Eliminación final `LegacyEventBus.publish` capability (post PI-12 si decide)
- Refactor funcional negocio
- Nuevos endpoints/features
- FE coverage threshold cambio
- Cobertura sales_agent/copilot ≥80% (S2)

## Copilot-first checklist

- [x] No aplica — PR infraestructura calidad, no operable desde copilot.

## Agentes / skills recomendados

| Fase | Agente/skill | Modelo | Prompt | Entregable |
|---|---|---|---|---|
| Pre-flight | `nicolify-context-builder` | Haiku | `prompts/00-context-prep.md` | CONTEXT-BRIEF.md |
| Architect (compartido PR-1 + PR-3) | `nicolify-architect` | Opus | `prompts/01-architect-start.md` | CONTRACT.md (PR-1 + PR-3 cross-linked) |
| Build business | `nicolify-backend` | Sonnet | `prompts/02-builder-start.md` | code + IMPL-LOG.md |
| Build agentic | `nicolify-agentic` | Opus | `prompts/02-builder-start-agentic.md` | code + IMPL-LOG.md |
| Audit business | `nicolify-backend-auditor` | Opus | `prompts/03-auditor-start.md` (auto-spawned) | REVIEW-backend.md |
| Audit agentic | `nicolify-agentic-auditor` | Opus | `prompts/03-auditor-start-agentic.md` (auto-spawned) | REVIEW-agentic.md |
| Cierre | `/pm` | — | `prompts/04-pm-close.md` | RESULT.md |

## Surface impactada

### Business surface (`nicolify-backend`)

| Tipo | Path | Cambio |
|---|---|---|
| Tests conftest | `backend/tests/conftest.py` | EXTEND singleton fixture exhaustivo |
| Tests | `backend/tests/architecture/test_ddd_boundaries.py` | Allowlist 3 entries (stash) |
| Tests | `backend/tests/architecture/test_folder_naming.py` | Exception `_dependencies.py` (stash) |
| Tests | `backend/tests/modules/brand/test_outbox_adapter_integration.py` | Migración mock legacy → adapter_bus |
| Tests | `backend/tests/modules/brand/test_brand_section_updated_event.py` | Outbox table fixture + migración mock |
| Tests | `backend/tests/shared/domain_events/test_event_bus_adapter.py` | Migración mock |
| Source | `backend/src/shared/domain_events/legacy_event_bus.py` | Runtime DeprecationWarning emit |
| Source | `backend/src/shared/infrastructure/llm/providers/litellm.py` | Kimi clamp (stash + REVISAR) |

### Agentic surface (`nicolify-agentic`)

| Tipo | Path | Cambio |
|---|---|---|
| Tests | `backend/tests/architecture/test_sales_agent_anchors.py` | `SALES-AGENT-OUTBOUND-PR7` (stash) |
| Tests | `backend/tests/architecture/test_sales_agent_system_prompt_order.py` | `CAMPAIGN_CONTEXT` (stash) |
| Tests | `backend/tests/modules/sales_agent/prompts/test_compose_system_prompt.py` | `CAMPAIGN_CONTEXT` (stash) |
| Tests | `backend/tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py` | **REMOVER** `@pytest.mark.flaky` post polluter fix |
| Tests | `backend/tests/modules/sales_agent/orchestrator/_chat_flow_snapshot_helpers.py` | EXTEND outbox-aware |
| Tests | `backend/tests/modules/copilot/test_outbox_adapter_integration.py` | Migración mock |
| Tests | `backend/tests/modules/copilot/test_offer_section_tools.py` | `next_step_hint` (stash) |
| Tests | `backend/tests/modules/copilot/test_voice_api.py` | 410 Gone (stash) |
| Tests | `backend/tests/modules/copilot/test_voice_combined.py` | 410 Gone (stash) |
| Tests | `backend/tests/integration/test_outbound_orchestrator_e2e.py` | Mock target rename (stash) |
| Source (polluter fix) | TBD según hunt | Fix at source — sin band-aid |

### Frontend surface (sin agente builder dedicado — fix mecánico stash)

| Tipo | Path | Cambio |
|---|---|---|
| Tests | `frontend/src/features/closer-studio/components/inbox/__tests__/CampaignTag.test.tsx` | URL slug `/campañas/` → `/campanas/` (stash) |

**Decisión:** business builder hace stash pop que ya incluye este FE fix. Vitest run nativo confirma. Sin builder FE separado.

## Tests requeridos (TDD)

Solo fix de tests existentes + extender singleton fixture. 0 tests nuevos de feature (puro hardening).

Excepción: si polluter hunt revela bug real código → tests regresión RED → fix GREEN.

## Aceptación

- [ ] Stash{0} aplicado, revisado, commiteado dentro PR-1
- [ ] `pytest` 0 failed, 0 deselected, 0 `flaky` permanentes
- [ ] `vitest run` 0 failed
- [ ] Polluter `test_chat_flow_telegram_new_lead_snapshot` fixed at source (no marker)
- [ ] Singleton fixture exhaustivo + lista validada en IMPL-LOG
- [ ] EventBus mocks migration audit completo en IMPL-LOG
- [ ] Snapshot helpers outbox-aware (no `domain_events=[]` falso)
- [ ] `LegacyEventBus.publish` runtime warning emit
- [ ] litellm.py kimi clamp activo + test cubre regression
- [ ] Arch fitness 78/78 PASS
- [ ] `IMPL-LOG.md` business + agentic completos
- [ ] `REVIEW-backend.md` + `REVIEW-agentic.md` verdict PASS
- [ ] `RESULT.md` escrito por PM

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Polluter hunt sin resolución | Methodology sistemática Phase 4; sin budget cap (decisión Chris); escalate Chris si supera 6h Opus |
| Fix de test revela bug real producto adicional | Documentar IMPL-LOG; si trivial fix in-PR; si scope expansion → escalate PM mini-PI hotfix paralelo |
| Builders paralelos tocan `tests/conftest.py` | Business builder owns conftest. Agentic NO modifica. PR-3 builder NO modifica (solo lee como referencia arch fitness new file) |
| Builders paralelos tocan `tests/architecture/` | Paths exclusivos: business owns DDD/naming; agentic owns sales_agent_anchors/system_prompt_order |
| EventBus migration omisión (test con mock no detectado en grep) | Multi-pattern grep IMPL-LOG documentado; auditor Cat 12 valida 0 omisiones |
| Singleton fixture omisión | Grep `_instance =` cross-codebase obligatorio; lista exhaustiva en IMPL-LOG; auditor agentic Cat review |
| Stash apply conflicta con commits intermedios | `git stash list` antes pop + `git status` clean check; si conflict → resolución manual file-by-file (NO descartar stash) |

## Notas operativas

- Stash apply en builder Phase 1 Step 1 (NO antes — workflow paralelo)
- Builder business owns conftest.py + business surface
- Builder agentic owns agentic surface + snapshot helpers + polluter hunt
- Architect Opus 1 ejecución produce CONTRACT.md PR-1 + CONTRACT.md PR-3 (cross-linked)
- PR-3 builder corre en paralelo a PR-1 después architect
- PR-4 = PM directo (no builder técnico)
