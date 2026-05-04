# PI-11 — Backend Quality Guardrails

> Tipo: **maintenance transversal hardening** (técnico, **bloqueador deploy**).
> Owner: /pm
> Estado: **active, S1 ready (3 PRs builders pendientes)**
> Prioridad: **Now — alta. Bloquea cualquier `/pase-produccion` confiable.**

## Origen

Failed `/pase-produccion` 2026-05-04 (development → main) detectó **25 BE failures + 2 FE failures + 1 snapshot test polluter no identificable** después de 3h bisección sistemática.

**Causa raíz arquitectural:** commit `64738354` (2026-04-29, PR-1 Sub-E PI-2 "switch emisores to outbox event bus adapter") flipeó defaults sin auditar tests:

```python
# backend/src/core/config.py
USE_OUTBOX_PATTERN_SALES_AGENT: bool = True  # antes False
USE_OUTBOX_PATTERN_COPILOT: bool = True       # antes False
USE_OUTBOX_PATTERN_BRAND: bool = True         # antes False
```

Cambió el call path real de eventos de dominio:
```
ANTES (flag=False):  service.save() → EventBus.publish() → handlers in-memory
                                       ↑ tests mockean acá
AHORA (flag=True):   service.save() → adapter_bus.publish() → outbox.enqueue_sync() → DB outbox table
                                       ↑ tests aún mockean EventBus.publish (path muerto)
```

**Consecuencias detectadas:**
1. Snapshot tests (`_chat_flow_snapshot_helpers.py`) capturan `domain_events=[]` siempre — publicaciones reales van por outbox no interceptado.
2. `TestDomainSubscribersRegistration` (`tests/modules/copilot/test_outbox_adapter_integration.py:206-259`) llama `LegacyEventBus.clear()` SIN teardown → leak `EventBus._handlers` cross-test.
3. Singletons class-level (`LLMFactory._instance`, `ChatOrchestrator._instance`, `SemanticRouter._instance`) persisten entre tests con settings monkeypatched.
4. Polluter del snapshot test `test_chat_flow_telegram_new_lead_snapshot` — deterministic order pollution NO identificada en bisección 80+ min.

**Costo invertido como referencia (justificación PI):**
- Sesión 2026-05-04: ~3h en ~50% fixes
- Polluter hunt agente: 80 min sin resolver
- Token spend total: ~500k tokens
- **Sin prevención: cada deploy futuro replica un % de este costo.**

## Outcome esperado (post-S1)

| Outcome | Métrica |
|---|---|
| 0 BE failures, 0 FE failures | `pytest` y `vitest run` sin flags especiales (`--deselect`, `--reruns`) |
| Polluter snapshot test fixed at source | Sin band-aid `@pytest.mark.flaky` final |
| Singletons class-level documentados + reseteados | Autouse fixture exhaustivo en `tests/conftest.py` cubre TODOS los singletons identificables |
| Tests legacy EventBus mocks migrados | 100% tests mockean `adapter_bus` o capturan via outbox table inspection |
| Snapshot helpers outbox-aware | `_chat_flow_snapshot_helpers.py` captura `domain_events` real desde outbox table o adapter_bus probe |
| Arch fitness test bloqueador | `test_no_legacy_eventbus_mock_when_outbox_on.py` — fail si test mockea `LegacyEventBus.publish` solo |
| Regla anti-default-flip cementada | `.claude/rules/anti-default-flip-audit.md` con workflow obligatorio (grep + update mocks + run both flag values + commit body docs) |
| Agents actualizados con default-flip audit | `nicolify-architect`, `nicolify-backend`, `nicolify-backend-auditor` con Step 0/CONTRACT block/Cat review nuevos |
| `pm` skill template extendido | PR.md template incluye bloque "Default flips audited" cuando aplique |
| `tdd-mandatory.md` extendido | Sección "Default flag flips" con regla |
| `LegacyEventBus.publish` deprecado | Runtime warning + considerar eliminación capability mock-only post audit |
| Cobertura P0 ≥75% | `crm`, `scheduling` (PR-2 — sin cambio scope original) |
| Arch fitness 78/78 PASS | Sin allowlist creciente sin justificación |
| `/test-backend` + `/test-frontend` verde | Gate real, no aspiracional |

## Decisión arquitectónica clave (Chris 2026-05-04, escala 1000 clientes)

**Outbox `True` permanente. Tests migran al path nuevo, NO se revierte el flag.**

Justificación robustez escala:
- In-memory `LegacyEventBus` rompe en multi-worker FastAPI/Gunicorn (cada worker = process separado, eventos entre workers se pierden silencioso)
- 1000 clientes proyectados 1 mes = picos concurrencia + multi-worker obligatorio
- Outbox garantiza durabilidad eventos + retry + idempotencia + observabilidad DB-side
- Reverso a `False` = bomba tiempo @ scale; postergar problema costaría 10x

Implicación: `LegacyEventBus.publish` queda como **legacy compat path solo**. Deprecación gradual:
1. Runtime warning si llamado en prod (warn level)
2. Tests migran a `adapter_bus` mock o outbox table probe
3. Auditor flag detecta nuevos tests legacy
4. Eventualmente capability eliminable (post PI-12, fuera scope PI-11)

## Scope

### In scope (S1 expandido — 3 PRs)

**PR-1 EXTENDIDO** — Fix tests + polluter hunt + singleton fixture + EventBus mocks audit + bug fix litellm
- Apply stash 16 archivos (24 de 25 fixes ya validados sesión 2026-05-04)
- Polluter hunt sistemático snapshot test (deterministic order pollution — sin band-aid `@pytest.mark.flaky` final)
- Singleton fixture exhaustivo `tests/conftest.py` — TODOS class-level singletons identificables (`LLMFactory._instance`, `ChatOrchestrator._instance`, `SemanticRouter._instance`, langgraph/deepagents global compilation caches, posibles más detectables via grep)
- Audit TODOS tests que mockean `EventBus.publish` legacy → migrar a `adapter_bus` o outbox table probe
- Audit TODOS `_chat_flow_snapshot_helpers.py` patterns — outbox-aware capture
- Bug fix real `litellm.py` kimi clamp (production bug — temperature=1.0 → Kimi K2.6 HTTP 400 silencioso, mirror del clamp dead-code en `kimi.py`)
- 24 stale tests fix (lista detallada en PR-1/PR.md)
- Deprecation runtime warning `LegacyEventBus.publish`

**PR-3 NEW** — Anti-default-flip enforcement
- Rule `.claude/rules/anti-default-flip-audit.md` con workflow obligatorio
- Arch fitness test `tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py` bloqueador

**PR-4 NEW** — Update agents/skills/rules con default-flip audit
- `nicolify-architect`: Step 0 default-flip detection + CONTRACT.md block "Tests audit"
- `nicolify-backend`: Step 0 grep tests mockean path afectado antes flip
- `nicolify-backend-auditor`: Cat review nueva "Default flip side-effect coverage"
- `pm` skill: PR.md template bloque "Default flips audited"
- `.claude/rules/tdd-mandatory.md`: sección "Default flag flips"

**PR-2 (sin cambio scope original)** — Coverage P0 modules
- `crm` ≥75% + `scheduling` ≥75%

### Out of scope

- Refactor funcional de negocio (sin cambiar comportamiento user-facing)
- Nuevos endpoints o features
- Frontend coverage lift (PI separado si se decide)
- Eliminación final `LegacyEventBus.publish` capability (post PI-12 si decide)
- Cobertura `sales_agent`/`copilot` ≥80% (S2)
- Tests integración con Postgres real (verify/integration markers — gate separado existente)

## Plan macro (sprints)

| Sprint | Tema | PRs | Objetivo |
|---|---|---|---|
| **S1** | Test integrity hardening + anti-default-flip cementado + coverage P0 | PR-1 ext (fixes + polluter + singleton fixture) · PR-3 (rule + arch test) · PR-4 (agents/skills/rules) · PR-2 (coverage P0) | Restaurar CI verde permanentemente + prevenir recurrencia raíz |
| **S2** | Coverage P1 + shared contracts | PR-5 coverage sales_agent/copilot · PR-6 shared/links/ports tests | Cerrar brechas agentic + transversales |

## Decisiones tomadas (2026-05-04)

| # | Decisión | Justificación |
|---|---|---|
| D1 | Outbox `USE_OUTBOX_PATTERN_*` queda `True` permanente | Escala 1000 clientes multi-worker; in-memory bomba tiempo |
| D2 | Tests migran a `adapter_bus` mock o outbox table probe | Path nuevo es prod path; test path debe match |
| D3 | `LegacyEventBus.publish` runtime warning + deprecation gradual | Capability legacy compat solo; eliminación final post PI-12 |
| D4 | Polluter hunt sin band-aid `@pytest.mark.flaky` final | Fix at source obligatorio; band-aid permitido SOLO durante hunt activo, removido pre-cierre PR |
| D5 | Architect Opus 1 ejecución cubre PR-1 + PR-3 (CONTRACT compartido o linkeado) | Acoplamiento técnico singleton fixture + arch fitness; consistencia invariantes; ahorro spawn |
| D6 | PR-4 = PM directo (no builder técnico) | Scope = markdown meta-process (`.claude/agents/*.md` + `.claude/skills/pm/SKILL.md` + `.claude/rules/tdd-mandatory.md`); no requiere code generation |
| D7 | Stash{0} pop ocurre en builder Phase 1 PR-1 (NO antes) | Evita conflicto workflow paralelo; builder revisa cada archivo del stash + commitea como parte de PR-1 |

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Polluter snapshot test no se identifica con presupuesto inicial | Asignar Opus al hunt (no Sonnet); JSON diff exhaustivo baseline vs actual cuando falla en suite completa; bisección de orden + setup-only suite. Sin band-aid final. Si supera 6h Opus → PM escalate Chris para budget extra (NO ship con `@pytest.mark.flaky` permanente) |
| Cross-surface (business + agentic) en mismo PR-1 | 2 builders paralelos (`nicolify-backend` + `nicolify-agentic`) con paths exclusivos por surface; conftest.py compartido = lock prevention via builder negocio (regla M3 SECUENCIAL si conflicto) |
| Tests rotos por refactoring paralelo (otra sesión) | M4 Claim by commit inmediato; CI verde antes push |
| Singleton fixture incompleto (alguno escapa) | Builder PR-1 obliga grep `_instance =` cross-codebase + lista exhaustiva en IMPL-LOG; auditor agentic Cat review valida cobertura |
| Tests legacy EventBus mocks no detectados en grep inicial | Multi-iteration grep: `EventBus.publish`, `LegacyEventBus`, `event_bus.publish`, mock path patterns. Builder documenta lista completa en IMPL-LOG. Auditor Cat 12 detecta omisiones |

## Cierre PI

- Todos los PRs (1, 2, 3, 4) shipped + RESULT.md escritos
- `current-state/` NO se actualiza (sin capacidades user-facing nuevas)
- `retro.md` con learnings:
  - Patrón detect default flip = side-effect call path change
  - Cómo prevenir recurrencia (workflow obligatorio)
  - Polluter hunt methodology (qué funcionó, qué no)
  - Singleton fixture exhaustive pattern
  - Costo total real (3h sesión + ejecución PI-11) vs costo proyectado sin PI (replica per-deploy)
- Re-merge `development → main` clean post-PI cierre
- `/pase-produccion` desde estado limpio

## Historial

| Fecha | Evento |
|---|---|
| 2026-05-01 | Creado por Chris — detectados 10+ tests fallidos + cobertura baja P0/P1 (sesión qwen) |
| 2026-05-04 | **Promoted Next → Now con scope expandido masivo.** Failed `/pase-produccion` reveló causa raíz arquitectural (commit `64738354` outbox flag flip) + polluter no identificable. Decisión Chris escala 1000 clientes: outbox `True` permanente, tests migran al path nuevo, regla anti-default-flip cementada en agents/skills/rules para que NUNCA recurra. PR-1 ext + PR-3 NEW + PR-4 NEW agregados a S1. Stash{0} (16 archivos, 24/25 fixes validados) marcado para apply en builder PR-1 Phase 1. |
