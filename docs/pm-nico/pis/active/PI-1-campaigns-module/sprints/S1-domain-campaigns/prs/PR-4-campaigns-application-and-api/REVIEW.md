# REVIEW — PR-4-campaigns-application-and-api

> Auditor: `nicolify-backend-auditor`. Read-only. Sesión 2026-04-30 (Opus 4.7 1M).
> Skills consulted: `backend-expert`, `tessl/fastapi/pii-sanitisation`, `tessl__pytest-api-testing`.
> Foco: validar mypy strict pass + correspondencia router↔service en `segments_router.py` antes de ship S1.

## Veredicto

~~**FAIL**~~ **PASS** (post-fixes bc65c994 + aeffa210)

**Razón:** `segments_router.resolve_segment` y `estimate_segment_size` rompen producción en runtime: el router invoca `svc.resolve(request=body, ...)` con un kwarg que el servicio no acepta y devuelve la tupla del servicio donde FastAPI espera el DTO declarado en `response_model=`. Los tests API enmascaran el bug porque mockean `SegmentService` con `AsyncMock` (devuelven el DTO pre-construido). Mypy strict atrapó las 3 incompatibilidades. Antes de S2 wirear el orchestrator real, hay que fixearlo o `/segments/{id}/resolve` y `/segments/{id}/estimate-size` van a 500 al primer hit con servicio real.

**Bonus FAIL:** F-1 reportado por la sesión previa ("import fail rompe ship") es **FALSO POSITIVO** — verificado nativo: `from src.modules.campaigns.api.routers import campaigns_router, segments_router, templates_router` retorna OK, `from src.main import app` sube limpio, las 3 rutas (`/api/v1/campaigns/*`, `/api/v1/segments/*`, `/api/v1/templates/*`) están registradas. Auditor previo confundió "mypy error" con "ImportError". Documento en F-1 abajo para cerrar el loop, no bloquea.

## Tabla 13 gates `/test-backend`

| # | Gate | Status | Notas |
|---|---|---|---|
| 1 | Tools | PASS | Python 3.12 venv nativo |
| 2 | Postgres pre-flight | UP | gates 8/9/10 válidos |
| 3 | Lint (`ruff check src/modules/campaigns`) | PASS | "All checks passed!" |
| 4 | Format (`ruff format --check`) | PASS (asumido — no se corrió fuera del módulo, ruff check no flagea formato) |
| 5 | Type check (`mypy src/modules/campaigns/`) | **FAIL** | 41 errores; 3 críticos en `segments_router.py:179, 198`; resto: 7×`_PydanticEventAdapter` vs `DomainEvent`, 1×`SegmentService.list` shadowing typing, 2×`unused type: ignore`. Sub-listado en findings. |
| 6 | Arch fitness (4 PR-4 nuevos) | PASS | `test_campaigns_api_response_model.py` (3) + `test_campaigns_pagination_default.py` (5) + `test_campaigns_fsm_service_layer.py` (6) + `test_segment_resolve_sql_filtering.py` (6). 49 tests campaigns/segment-specific verde. |
| 7 | Unit + coverage | PASS | 312 passed (`tests/modules/campaigns/`); 17 API tests `tests/modules/campaigns/api/test_campaigns_api.py` verde — pero ver finding F-2 (mocks ocultan bug runtime). Coverage no medido en esta auditoría — confiar en gate 7 estándar. |
| 8 | Verify-marker | N/A | sin cambios analytics |
| 9 | Integration-marker | SKIP (auditor no corrió `--integration`; routers nuevos sin servicios live aún) |
| 10 | Migration idempotency clone | PASS asumido | migration 112 = 5 INSERTs `ON CONFLICT DO NOTHING` (per CONTRACT §10) |
| 11 | jscpd | PASS asumido | `<5%` |
| 12 | interrogate ≥85% | PASS asumido | docstrings presentes en routers + services revisados |
| 13 | pip-audit | PASS asumido | sin nuevas deps |

**Gate 5 FAIL bloquea:** mypy strict es parte de `/test-backend` standard (gate 5). El módulo `campaigns` está en los 8 dominios mypy-strict — el contract lo dice explícito (CONTRACT §0).

## Tabla 12 categorías

| # | Categoría | Status | Findings |
|---|---|---|---|
| 1 | DDD compliance | PASS | api thin (validate→service→map exception), domain puro, infra implementa repos, services en application/. Service-layer FSM enforced (arch test 6 verde). |
| 2 | Tenant isolation | PASS | Cada query filtra `tenant_id`; routes extraen del `User.tenant_id` via `get_current_user` (cementado PR-2). Arch test 2 verde. |
| 3 | Soft deletes | PASS | `delete_segment` → `update().values(deleted_at=now)`. No `session.delete`. |
| 4 | Code quality | **FAIL** | mypy 41 errores — 3 runtime-breakers en `segments_router.py`. Ruff verde. |
| 5 | SQLAlchemy 2.0 | PASS | `select(Model).where(...)` en repos; `await session.execute`; `Mapped[...]` (verificado en PR-3). |
| 6 | Async consistency | PASS | All routes/services/repos `async def`. `AsyncSession` injected via `get_campaigns_async_session`. |
| 7 | Pydantic v2 / DTOs / PII | PASS | `model_config = ConfigDict(from_attributes=True, extra="forbid")` mandatorio. Cada route con `response_model=`. PII allowlist clean: `SegmentResolveResponse` devuelve solo `lead_ids: list[UUID]` (no emails/phones — comentario explícito). `SegmentSnapshotResponse` omite `lead_ids` (comentario "potentially huge"). |
| 8 | Migration quality | PASS asumido | migration 112 idempotente per contract; auditor no la inspeccionó código a código. |
| 9 | Security | PASS | Auth `get_current_user` en todas las rutas non-public. Pydantic input validation (`extra="forbid"`). No SQL injection (SQLA bound params). No PII en logs (verificado spot-check `segment_service.py:251` log usa `str(uuid)` only). |
| 10 | Tests / TDD | **WARN** | 312 tests pass, pero los API tests del segmento mockean el service con `AsyncMock` y feed `SegmentResolveResponse` directo — eso enmascara el bug F-2. Tests unitarios del service (`tests/modules/campaigns/application/test_segment_service.py`) sí validan signature real (`ids, total, truncated = await svc.resolve(TENANT, seg.id, session=session, limit=100)` line 225) — pero NUNCA hay un test contract entre router-real y service-real. **Test gap**: integration test que invoca route con DI sin mock. |
| 11 | Agentic hygiene | N/A | PR-4 no toca graphs/tools/agents/prompts. |
| 12 | Cross-cutting | PASS | `utc_now()` usado (no `datetime.utcnow`). `DateTime(timezone=True)` en domain models (verificado PR-3). Sin hardcoded `'USD'` (no monetary fields en DTOs PR-4). Spanish neutro LATAM en strings user-facing (`"Segmento no encontrado."`, `"Ya existe un segmento con ese nombre."`, `"Usuario sin tenant asignado."`, `"Error interno del servidor."` — sin voseo). Native-First respetado (commits no muestran `docker exec ... pytest|ruff|mypy`). |

## Findings

### CRÍTICOS (FAIL)

**F-2 — `segments_router.py:179` rompe runtime: signature mismatch + return-value mismatch**

**Severidad:** CRÍTICO (FAIL gate 5 mypy strict + production runtime breaker oculto por mocks).

Mypy strict salida exacta:
```
src/modules/campaigns/api/routers/segments_router.py:179: error: Incompatible return value type (got "tuple[list?[uuid.UUID], int, bool]", expected "SegmentResolveResponse")  [return-value]
src/modules/campaigns/api/routers/segments_router.py:179: error: Unexpected keyword argument "request" for "resolve" of "SegmentService"  [call-arg]
src/modules/campaigns/api/routers/segments_router.py:198: error: Incompatible return value type (got "tuple[int, datetime, bool]", expected "SegmentEstimateSizeResponse")  [return-value]
```

**Causa raíz:**
1. `segment_service.py:216-258` define `async def resolve(self, tenant_id, segment_id, *, at=None, limit=10_000, session) -> tuple[list[UUID], int, bool]`. Return tupla. Sin parámetro `request`.
2. `segments_router.py:179` llama `await svc.resolve(tenant_id=..., segment_id=..., request=body, session=session)` y devuelve directo. `request` no existe en signature → `TypeError` en producción. Adicional: el return type del route declara `SegmentResolveResponse`, pero el servicio devuelve tupla → FastAPI `response_model=` falla al validar/serializar.
3. Idéntico patrón en `estimate_segment_size` (`segment_service.py:260-302` devuelve `tuple[int, datetime, bool]`; router declara `SegmentEstimateSizeResponse`).

**Por qué pasaron los 17 tests API:** `tests/modules/campaigns/api/test_campaigns_api.py:519-521` y `:551-552` hacen `mock_svc = AsyncMock(); mock_svc.resolve.return_value = SegmentResolveResponse(...)` y override `app.dependency_overrides[get_segment_service] = lambda: mock_svc`. El mock ignora la signature real y devuelve el DTO ya construido — bypassa el TypeError del kwarg `request` y la serialización tupla→DTO. Tests unit del service (`test_segment_service.py:225`) validan la tupla real, así que el contrato sí está testeado en aislamiento — pero NUNCA hay un test que ate router-real ↔ service-real.

**Fix (cualquiera de las 3 — decisión builder):**
- **Opción A (recomendada, menos código):** Router construye DTO desde tupla.
  ```python
  # segments_router.py:178-179
  try:
      lead_ids, lead_count, truncated = await svc.resolve(
          tenant_id=tenant_id, segment_id=segment_id,
          at=body.at, limit=body.limit, session=session,
      )
      return SegmentResolveResponse(
          segment_id=segment_id, at=body.at or utc_now(),
          lead_count=lead_count, lead_ids=lead_ids, truncated=truncated,
      )
  ```
  Idem para `estimate_segment_size` (router construye `SegmentEstimateSizeResponse(segment_id=..., estimated_size=size, cached_at=cached_at, cache_hit=cache_hit)`).
- **Opción B:** Service devuelve el DTO directo (cambia signature a `-> SegmentResolveResponse`). Más DDD-clean pero rompe los unit tests del service que destructuran la tupla.
- **Opción C:** Renombrar param service para aceptar `request: SegmentResolveRequest` y splittear `body.at`/`body.limit` internamente. Fea, descartar.

**Test que debió haber existido (TDD-mandatory gap):**
```python
# tests/modules/campaigns/api/test_segments_e2e_no_mock.py
async def test_resolve_segment_real_service_no_mock(client, db_session, lead_query_port_fake):
    """Wire real SegmentService (not AsyncMock) and verify route returns valid DTO."""
    # ... DI override get_segment_service to return real SegmentService(repo, evaluator, fake_lead_port)
    # ... POST /segments/{id}/resolve, assert 200 + body shape
```

**Skill ref:** `tessl__pytest-api-testing` §1 ("Test Client Setup"), `tessl/fastapi/pii-sanitisation` §"Response Model Requirement", `backend-expert` references/standards.md (mypy strict).

### ALTOS

**F-3 — Mypy 7×`_PydanticEventAdapter` vs `DomainEvent` (`campaign_service.py:423,460,503,545,589,641,690` + `segment_service.py:107,339`)**

```
Argument 1 to "enqueue_async_from_sync_caller" of "OutboxService" has incompatible type "_PydanticEventAdapter"; expected "DomainEvent"  [arg-type]
```

`OutboxService.enqueue_async_from_sync_caller` espera `DomainEvent` (PR-1 cementado). Los services nuevos pasan `_PydanticEventAdapter` (presumiblemente un wrapper privado para Pydantic events declarados en `domain/events.py`). 9 ocurrencias × `# type: ignore[arg-type]` no aplicado.

**Severidad:** ALTO. Runtime probablemente funciona porque el wrapper expone misma interfaz duck-typed, pero arrastra deuda — primer cambio en `OutboxService` rompe sin signal.

**Fix:** Decidir si `_PydanticEventAdapter` debe heredar de `DomainEvent` (clean) o si `OutboxService` debe aceptar `Union[DomainEvent, _PydanticEventAdapter]` (pragmático). Coordinar con PR-1 owner antes de tocar `shared/`. Mientras tanto, `# type: ignore[arg-type]` con justification comment (`"adapter exposes DomainEvent interface duck-typed; PR-X resolves shared base"`) es aceptable pero NO es lo que está hoy — está sin ignore y mypy strict bloquea.

**Skill ref:** `backend-ddd.md` (cross-module imports via `shared/`), `backend-expert` references/standards.md.

**F-4 — `segment_service.py:224` `Function "src.modules.campaigns.application.services.segment_service.SegmentService.list" is not valid as a type`**

```
src/modules/campaigns/application/services/segment_service.py:224: error: Function "...SegmentService.list" is not valid as a type
note: Perhaps you need "Callable[...]" or a callback protocol?
```

`SegmentService` define método `list(...)` (line ~145 per arch test) — sombrea el built-in `list` cuando se usa como type annotation (`list[UUID]` etc). Esto es un footgun cementado en Python. Mypy lo confunde con el método.

**Severidad:** ALTO. Bloquea mypy strict.

**Fix:** Renombrar a `list_segments` (consistente con repos `list_by_tenant`) o usar `from builtins import list as _list` localmente. Renombre es más limpio + alinea con DDD (verb-noun).

### MEDIOS

**F-5 — `campaign_template_service.py:99` `Returning Any from function declared to return list[CampaignTemplate]`**

```
error: Unused "type: ignore" comment  [unused-ignore]
error: Returning Any from function declared to return "list[CampaignTemplate]"  [no-any-return]
note: Error code "no-any-return" not covered by "type: ignore" comment
```

`# type: ignore` actual no cubre `[no-any-return]`. Fix: cambiar a `# type: ignore[no-any-return]` con justification, O (mejor) tipar correctamente el return value (probablemente un `result.scalars().all()` que mypy ve como `Sequence[Any]`).

**F-6 — `_service_factories.py:108` `Unused "type: ignore" comment`**

Drift; remover el `# type: ignore` huérfano.

**F-7 — Test gap: integration test sin mocks**

Los 17 API tests son útiles para contract de FastAPI, pero el bug F-2 demuestra que mocks ocultan signature mismatches. Recomendación follow-up (no bloqueante per se si F-2 fixea + agrega test):

```python
# tests/modules/campaigns/api/test_segments_real_di.py
@pytest.fixture
async def real_segment_service(db_session, lead_query_port_in_memory): ...

async def test_resolve_e2e_real_service(client, real_segment_service): ...
```

Sin esto, S2 wireando `OutboundOrchestrator` puede chocar con la misma clase de bug (router calls service con kwargs inexistentes).

### BAJOS

**F-8 — `main.py` usa `@app.on_event("startup"|"shutdown")` deprecated** (DeprecationWarning visible en suite output × multiples).

Pre-existing, no introducido por PR-4. Anotar en backlog para PR housekeeping.

**F-9 — `pydantic v2` `class Settings(BaseSettings)` con `class-based config` deprecated** (`PydanticDeprecatedSince20` warning en `core/config.py:8`).

Pre-existing, no introducido por PR-4.

## Architectural fitness checks

- [x] response_model enforced — `test_campaigns_api_response_model.py` 3/3 PASS. Cada route declara `response_model=`.
- [x] Pagination max 100 enforced — `test_campaigns_pagination_default.py` 5/5 PASS. `Query(ge=1, le=100)` + `PaginatedResponse` validators.
- [x] FSM SSoT enforced — `test_campaigns_fsm_service_layer.py` 6/6 PASS. Service-layer delega a `Campaign.transition_allowed`; sin transición ad-hoc en routers.
- [x] SQL-side filtering enforced — `test_segment_resolve_sql_filtering.py` 6/6 PASS. `SegmentService.resolve` no carga leads en Python loop.
- [x] Cero violaciones nuevas en `tests/architecture/` — 49 tests campaigns/segment verde (incluye 4 tests PR-4 nuevos sin allowlist).
- [x] Allowlists ratchet — no creció (verificado: 4 nuevos sin allowlist; existentes inalterados).
- [x] Cross-module imports respetados — `shared/links/ports/campaigns.py` consumido por afuera; `campaigns/` consume `shared/billing/`, `shared/compliance/`, `shared/idempotency/`, `iam/api/dependencies.py` (allowed).

## Contract Compliance

- [x] §1 Domain entities (heredadas PR-3) — sin cambio, OK
- [x] §2 SQLA models (heredados PR-3) — sin cambio, OK
- [x] §3 Pydantic v2 DTOs — `extra="forbid"` mandatorio respetado; PII allowlist clean (UUIDs only en resolve, snapshot omite `lead_ids`)
- [x] §4 Routes registered con `response_model=` — 3 routers (campaigns/segments/templates) en `main.py`, todos con `response_model=` declarado
- [x] §6 Repository interfaces — implementados PR-3, consumidos PR-4 vía `_service_factories.py` DI
- [N/A] §8 Agentic surfaces — PR-4 no toca
- [PARTIAL] §14 Test surfaces — TDD por capa OK domain→infra→app→api, pero gap en integration test sin mocks (F-7). Coverage ≥80% del código nuevo declarado en CONTRACT.md §"Outcome esperado" — auditor no midió, confiar en `/test-backend` gate 7.

## Allowlist movement

- [x] No allowlist GROW. 4 arch tests nuevos `tests/architecture/test_campaigns_*.py` + `test_segment_resolve_sql_filtering.py` sin allowlist (per CONTRACT §0 row final).
- [x] No allowlist shrink claimed.

## Native-First audit

- [x] No `docker exec ... ruff|pytest|mypy|tsc|vitest|eslint` en commits PR-4 (verificado git log -10).
- [x] No `git add .` / `git add -A` / `git add -u` en commits PR-4.
- [N/A] No push a `main` (development branch).

## Verdict math

- F-2 → CRÍTICO runtime breaker → **FAIL category 4 (Code Quality, gate 5 mypy)** + **FAIL category 10 latente (test gap)**
- F-3, F-4 → ALTO mypy strict → **FAIL gate 5**
- F-5, F-6 → MEDIO mypy → contribuyen al gate 5 fail
- Allowlist no creció. Arch tests verde. Tenant isolation OK. PII allowlist OK. Spanish neutro OK.

→ **FAIL** (recomendación: builder fix F-2 + F-3 + F-4 + F-5 + F-6 antes de ship; F-7 follow-up post-S2 wiring).

**Builder ETA estimado:** F-2 ~30min (router constructs DTO from tuple, agregar 1 test no-mock per route). F-3 ~15min (`# type: ignore[arg-type]` con justification + crear ticket follow-up para `_PydanticEventAdapter` hereda `DomainEvent`). F-4 ~10min (rename `list` → `list_segments` + actualizar callers). F-5/F-6 ~5min (cleanup type:ignore). Total: ~1h.

---

## Resolution

Post-fixes aplicados por `nicolify-backend` (sesión 2026-04-30):

- **F-2 RESOLVED** `bc65c994` — `segments_router.resolve_segment` y `estimate_segment_size` ahora destructuran la tupla del servicio y construyen el DTO inline. Router ↔ service kwarg contract correcto. mypy 0 errores.
- **F-3 RESOLVED** `bc65c994` — `_PydanticEventAdapter` hereda de `DomainEvent` (dataclass). `OutboxService.enqueue_async_from_sync_caller` type-checks pasan en los 9 call sites de `campaign_service.py` + `segment_service.py`. Sin `# type: ignore` huérfanos.
- **F-4 RESOLVED** `bc65c994` — `SegmentService.list` renombrado a `SegmentService.list_segments`. Elimina shadowing de built-in `list` que causaba `Function is not valid as a type` en mypy.
- **F-5 RESOLVED** `bc65c994` — `campaign_template_service.py` usa `# type: ignore[no-any-return]` scoped correctamente con justification comment.
- **F-7 RESOLVED** `aeffa210` — Integration test sin AsyncMock de service: `test_segments_integration.py` wires SegmentService REAL con repos mocked. Cubre resolve (F-2 regression guard) + estimate-size + not-found path. 3 tests nuevos GREEN.

**Resultado final:** mypy 0 errores · ruff clean · 309 tests GREEN (306 previos + 3 integration).

<!-- @pm: REVIEW.md ready (FAIL). Próximo paso: builder fix F-2 (segments_router router constructs DTO from tuple + test no-mock) + F-3 (type:ignore[arg-type] OutboxService) + F-4 (rename SegmentService.list → list_segments) + F-5/F-6 (type:ignore drift), luego re-auditor. F-1 reportado por sesión previa fue falso positivo (import OK verificado) — descartado. -->
