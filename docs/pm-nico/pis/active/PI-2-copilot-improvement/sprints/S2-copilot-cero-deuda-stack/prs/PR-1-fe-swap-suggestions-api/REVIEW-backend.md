# REVIEW-backend — PR-1-fe-swap-suggestions-api

**Auditor:** nicolify-backend-auditor (skill: backend-expert + copilot-expert + tessl__fastapi + tessl__pytest-api-testing + tessl__graceful-degradation)
**Fecha:** 2026-04-30
**Commit auditado:** `e53b7ef6 feat(copilot): add suggestions API endpoints + DTOs (PR-1 PI-2 S2)`
**Scope:** SOLO archivos BE de PR-1 (3 fuente + 3 test). Frontend → REVIEW-frontend.md (auditor independiente).
**Iteración:** 1

## Score (1-5 cada categoría)

| Categoría | Score | Comentario |
|---|---|---|
| DDD compliance | 5 | API thin (delega engine + bus). Sin lógica de negocio en routes. Imports respetan capas y ratchet copilot→módulo (22 frozen). |
| Tenant isolation | 5 | Ambos endpoints derivan `tenant_id` de `Depends(get_tenant_context)` + 401 explícito si None. `tenant_id` se propaga a `SuggestionContext` y a ambos eventos. Engine ya enforza tenant_id en providers (verificado engine.py:90). |
| PII / response_model | 5 | `response_model=` declarado en ambos endpoints (gate `test_api_contracts.py` verde). DTOs excluyen `metadata` (D-6) y dejan `source_module` justificado en docstring (slug interno público, no PII). |
| Test coverage scope PR | 5 | 13/13 unit verde + 3 integration recogidos (`@pytest.mark.integration`). Coverage scoped: **97.44%** (suggestions.py 95% — solo logger.warning lines 106-107 no cubiertas; suggestions_dto.py 100%). RED-first declarado en docstrings y respetado por IMPL-LOG. |
| Code quality (ruff/mypy) | 5 | ruff check `All checks passed!` + ruff format `5 files already formatted` + mypy strict `Success: no issues found` + interrogate **100%** (≥85% requerido). |
| Migration safety | n/a | PR no introduce migrations (D-5: persistencia vía `copilot_trace_event` existente). |
| Architectural ratchet | 5 | Anchor `[COPILOT-SUGGESTIONS-ENGINE]` reusado (cap 36/37 NO bumpeado, D-15). Ratchet copilot→módulo 22 frozen (test_no_new_copilot_module_imports verde). Imports nuevos: `iam` + `shared.domain_events` + `copilot.*` (todos en `ALLOWED_TARGETS`). Sin nuevos cross-module imports a otros dominios. |
| Observability (best-effort) | 5 | Doble try/except independiente (engine + EventBus.publish), `# noqa: BLE001` justificado. structlog warning con `tenant_id=str(...)` (no PII raw). El handler nunca lanza 5xx por fallos de telemetría/engine (D-10/D-11). El subscriber `on_suggestion_shown`/`on_suggestion_accepted` ya wired en `domain_subscribers.py:106-107` (verificado). |
| Idempotencia | 5 | At-least-once OK (D-5), sin Idempotency-Key. `suggestion_id` UUID es la natural-key; subscriber escribe `copilot_trace_event` con `event_type='suggestion_accepted'` y métricas usan `COUNT(DISTINCT)`. Documentado en CONTRACT §1 D-5. |
| Spanish neutro | 5 | grep voseo (vos/sos/tenés/podés/elegí/agregá/etc.) en ambos archivos = 0 hits. summaries y descriptions son tuteo neutro ("Obtener smart-chips", "Reportar que el usuario clickeó"). HTTPException detail "Tenant ID requerido" = neutro. |
| Documentation | 5 | Docstrings Google-style en módulo + cada función + cada DTO. Anchor `[COPILOT-SUGGESTIONS-ENGINE]` linkeado en headers. Todas las decisiones (D-1..D-16) referenciadas inline donde aplica. interrogate 100%. |
| Risk vs CONTRACT | 5 | Implementación matchea CONTRACT 1:1 (D-1..D-16). Override D-6 final (incluir `source_module` en SuggestionDTO) está en CONTRACT y respetado en código. main.py wiring matchea contrato literal. Sin drift. |

## Findings

### CRÍTICOS
Ninguno.

### ALTOS
Ninguno.

### MEDIOS
Ninguno.

### BAJOS

**B-1 — `Annotated[object, Depends(get_current_user)]` en lugar de `User`**
- **Archivo:** `backend/src/modules/copilot/api/suggestions.py:55,139`
- **Issue:** El handler tipa `current_user: Annotated[object, Depends(get_current_user)]` y luego usa `getattr(current_user, "id", None)`. CONTRACT §4 ejemplifica `Annotated[User, Depends(get_current_user)]` con import `from src.modules.iam.domain.user import User`.
- **Por qué BAJO:** funcionalmente correcto (mypy strict pasa, runtime OK porque `User` tiene `.id`). Defensivo pero pierde tipado fuerte.
- **Recomendación (no bloqueante, próximo PR):** importar `User` desde `iam.domain.user` y tipar `Annotated[User, Depends(get_current_user)]` + reemplazar `getattr(current_user, "id", None)` por `current_user.id`. Sin impact en ratchet (`iam` ya en `ALLOWED_TARGETS`). NO bloquea merge.

**B-2 — Coverage 95% en `suggestions.py` (lines 106-107 sin cubrir)**
- **Archivo:** `backend/src/modules/copilot/api/suggestions.py:106-107`
- **Issue:** El branch `except Exception as exc: logger.warning("suggestion_shown_publish_failed", ...)` no tiene un test dedicado (sólo `suggestion_accepted_publish_failed` en `test_accept_event_publish_failure_returns_ok_false`).
- **Por qué BAJO:** símetrico al accept-failure test que sí existe. Cobertura conjunta del PR es 97.44% (>>43% gate). Ramas de logging son baja prioridad.
- **Recomendación (próximo PR/iter, no bloqueante):** agregar `test_suggestions_event_publish_failure_logs_warning` que mockee `EventBus.publish.side_effect = RuntimeError(...)` y verifique `logger.warning.assert_called()` con event_name `suggestion_shown_publish_failed`.

## Quality gates results

| Gate | Resultado | Detalle |
|---|---|---|
| ruff check (PR-1 files) | PASS | `All checks passed!` (suggestions.py + suggestions_dto.py + 3 test files) |
| ruff format --check (PR-1 files) | PASS | `5 files already formatted` |
| mypy --strict (PR-1 source) | PASS | `Success: no issues found in 2 source files` |
| pytest unit (PR-1) | PASS | 13/13 verde en 10.59s — 8 endpoint + 5 accept |
| pytest integration (PR-1) | COLLECT-OK | 3 tests recogidos con `@pytest.mark.integration` (no corren sin Postgres en este audit; gate 9 SKIP-aceptable) |
| pytest arch (suite completa) | PASS PR-1 | 21/21 verde en gates críticos PR-1: `test_copilot_anchors`, `test_no_new_copilot_module_imports` (ratchet 22 frozen), `test_api_contracts` (response_model=), `test_copilot_provider_compliance`, `test_copilot_registry`. Suite completa: 725/731 (6 deselected = pre-existing parallel-session campaigns failures: master_data USD default, folder_naming `_*.py`, ddd_boundaries `_service_factories.py`. NO PR-1 — confirmado en IMPL-LOG §"Pre-existing failures") |
| interrogate (PR-1 files) | PASS 100% | (≥85% requerido) |
| jscpd (PR-1 files) | PASS 0% | 0 clones, 299 lines, 1649 tokens analizados (<5% requerido) |
| pip-audit | n/a | PR no modifica `pyproject.toml`/`requirements.txt` |
| Coverage scope PR | PASS 97.44% | suggestions.py 95% (43/45 stmts) + suggestions_dto.py 100% (35/35 stmts). Lines no cubiertas: 106-107 (logger.warning del fallo bus en `/suggestions`, ver B-2) |

## /test-backend Gate Status (mapeo a 13 gates)

| # | Gate | Resultado | Detalle |
|---|---|---|---|
| 1 | Tools | PASS | Python 3.12.3, ruff/mypy/pytest/interrogate/jscpd OK |
| 2 | Postgres pre-flight | n/a | Auditor no levantó DB; gates 8/9/10 dependen de DB |
| 3 | Lint (ruff check) | PASS | 0 errors |
| 4 | Format (ruff format) | PASS | 0 reformats |
| 5 | Type check (mypy strict) | PASS | 0 errors en 2 source files PR-1 |
| 6 | Architecture fitness | PASS PR-1 | 725/731 verde; 6 fallos NO son PR-1 (campaigns sesión paralela, documentado IMPL-LOG) |
| 7 | Tests + coverage | PASS | 13/13 unit verde, coverage scope PR 97.44% (≥43%) |
| 8 | Verify-marker | n/a | PR-1 sin analytics |
| 9 | Integration | SKIP-aceptable | 3 tests `@pytest.mark.integration` recogidos OK; requieren Postgres para correr (no fallan, no PASS) |
| 10 | Migration idempotency | n/a | Sin migrations |
| 11 | jscpd <5% | PASS | 0% en archivos PR-1 |
| 12 | interrogate ≥85% | PASS 100% | |
| 13 | pip-audit | n/a | Sin cambios en deps |

## Cross-references — Skills/Rules consultados

- `copilot-expert`: anchor reusado (cap 36/37 sin bump, D-15), ratchet copilot→módulo 22 frozen verificado, best-effort double try/except cumplido, subscribers `on_suggestion_shown`/`on_suggestion_accepted` wired (domain_subscribers.py:106-107).
- `backend-expert`: Pydantic v2 `ConfigDict(from_attributes=True, extra="forbid")` ✓, async route handlers ✓, `response_model=` mandatory ✓, structlog (no print) ✓, `tenant_id` filter en CADA query (engine ya tenant-isolated) ✓.
- `tessl__fastapi`: `Annotated[..., Depends(...)]` style ✓, `response_model=` declarado ✓, una operación HTTP por función ✓, sin `RootModel` ✓, `extra="forbid"` evita drift de payload (CONTRACT §3) ✓.
- `tessl__pytest-api-testing`: factory `_build_client` con `dependency_overrides` ✓, parametrize implícito en helper ✓, error responses cubiertas (401/422/RuntimeError) ✓, response shape verificada (no solo status code) ✓.
- `tessl__graceful-degradation`: doble fallback (engine fallback `[], {}, 0` + bus publish fallback `ok=False`) ✓, structured logging con contexto (tenant_id, error) ✓, dependencias aisladas (engine fail no impide event publish) ✓. Engine NO es external HTTP call (es in-process), aplica solo "best-effort" semantics — cumplido.
- `pii-sanitisation`: `response_model=` allowlist ✓, `metadata` excluido ✓, `source_module` justificado ✓.
- `tdd-mandatory`: docstrings declaran "Tests written RED first per `tdd-mandatory.md`" + IMPL-LOG declara "TDD estricto: Tests RED escritos antes de implementación" ✓.

## Contract Compliance

- [x] D-1: 2 endpoints POST con body context ✓
- [x] D-2: nuevo file `copilot/api/suggestions.py` con APIRouter ✓
- [x] D-3: `await asyncio.to_thread(engine.get_suggestions, ctx)` ✓
- [x] D-4: `/accept` flat (no nested) ✓
- [x] D-5: at-least-once OK, sin Idempotency-Key ✓
- [x] D-6 (override final): SuggestionDTO incluye `source_module`, excluye `metadata` ✓
- [x] D-7: `confidence` se expone ✓
- [x] D-8: `locale="es"` server-side, no en request DTO ✓
- [x] D-9: aplica solo a FE (out of scope BE)
- [x] D-10: best-effort engine — 200 + suggestions=[] en fallo ✓
- [x] D-11: SuggestionShown emitido SIEMPRE (incluso 0 chips) ✓
- [x] D-12,D-13: aplica solo a FE
- [x] D-14: aplica solo a FE
- [x] D-15: anchor `[COPILOT-SUGGESTIONS-ENGINE]` reusado (cap 36/37 sin bump) ✓
- [x] D-16: 0 nuevos cross-module imports (ratchet 22 frozen) ✓

## Allowlist Movement
- Allowlist `KNOWN_COPILOT_TO_MODULE_IMPORTS` — **sin cambio** (22 entries, todas las usadas son `iam` + `shared` + `copilot` que están en `ALLOWED_TARGETS`).
- Allowlist anchors `ANCHOR_REGISTRY` — **sin cambio** (cap 36/37 mantenido, D-15).
- Sin allowlist growth → no requiere justificación de commit.

## Native-First Audit
- [x] Auditor corrió todos los gates con `cd backend && .venv/bin/{ruff,mypy,pytest,interrogate}` (NUNCA `docker exec`).
- [x] Commit `e53b7ef6` muestra `git diff --stat` con scope acotado a archivos PR-1 (BE + FE) — sin `git add .` / `git add -A` accidental visible en mensaje.
- [x] PR no pushea a `main` — branch `development`. `make ci-parity` no aplica.

## Verdict Math
- Categorías 1/2/8/9/11 sin FAIL → no auto-FAIL.
- Allowlist sin growth → no auto-FAIL.
- Gates `/test-backend` 3-7/11-13: PASS donde aplica, n/a donde no aplica.
- 0 WARN de categoría → no overall WARN.
- 2 BAJOS no bloqueantes (B-1 typing defensivo, B-2 1 branch logger sin test).
- → **PASS**

## Veredicto
**PASS**

Razón: Implementación matchea CONTRACT 1:1 (las 16 decisiones D-1..D-16 verificadas). Todos los gates `/test-backend` aplicables verde sobre archivos PR-1. Tenant isolation correcta vía `Depends(get_tenant_context)` con 401 explícito. PII allowlist respetada (`response_model=` + `metadata` excluido). Best-effort observability con doble try/except independiente cumple `tessl__graceful-degradation` y `copilot-expert` rule "trace recorder writes never break turn". Anchor reusado, ratchet copilot→módulo 22 frozen sin agregados. Cobertura 97.44% sobre archivos del PR. Spanish neutro confirmado (0 hits voseo). 2 findings BAJOS no bloqueantes para mejora futura.

---

<!-- @pm: audit done. verdict=PASS, iter=1 -->
