# Runtime Quality Checklist (Backend)

> Checklist OBLIGATORIO antes de marcar PR BE shipped o REVIEW.md PASS.
> Origen: S4 PI-1 PR-10 audit failure 2026-04-30 — 7 bugs CRITICAL pasaron tests inicialmente porque builder Sonnet pause + PM fallback solo gates mecánicos.
>
> Tests verde + lint verde + mypy verde NO es suficiente para FastAPI. Pydantic schema gen + dependency resolution + async lifecycle hide bugs runtime.

## FastAPI dependency injection — Annotated patterns

❌ **PROHIBIDO:** Type alias para dep complejo con AsyncSession dentro:

```python
# ANTI-PATTERN — FastAPI resolution falla con "AsyncSession not valid Pydantic field"
async def _get_service(session: Annotated[AsyncSession, Depends(get_session)]) -> Service:
    return Service(session)

ServiceDep = Annotated[Service, Depends(_get_service)]  # ← FastAPI confused

@router.get("/", response_model=Response)
async def endpoint(svc: ServiceDep, ...):  # ← schema gen recurses into AsyncSession → fail
    ...
```

✅ **CORRECTO:** Annotated inline per call site:

```python
async def _get_service(session: Annotated[AsyncSession, Depends(get_session)]) -> Service:
    return Service(session)

@router.get("/", response_model=Response)
async def endpoint(
    svc: Annotated[Service, Depends(_get_service)],  # ← inline, FastAPI resolves OK
    ...
):
    ...
```

---

## Test fixture override — bare params son Pydantic field

❌ **PROHIBIDO:** override factory con param sin `Depends()`:

```python
# ANTI-PATTERN — `session` sin Depends → FastAPI introspects AsyncSession como Pydantic field → 500 error
async def _fake_svc(session: AsyncSession = None) -> Service:
    return Service(session=db_session, ...)  # session unused — closure captura db_session

app.dependency_overrides[_get_service] = _fake_svc  # ← request fails
```

✅ **CORRECTO:** factory sin params (closure captura state externo):

```python
async def _fake_svc() -> Service:  # ← no params
    return Service(session=db_session, ...)

app.dependency_overrides[_get_service] = _fake_svc
```

---

## Multi-tenant test fixture — header-based dispatch

❌ **PROHIBIDO:** múltiples fixtures sobrescriben `app.dependency_overrides` global:

```python
# ANTI-PATTERN — 2 client fixtures, segundo wins (tenant isolation broken in tests)
@pytest.fixture()
async def client_a(db_session):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(tenant_id=TENANT_A)
    yield AsyncClient(...)

@pytest.fixture()
async def client_b(db_session):
    app.dependency_overrides[get_current_user] = lambda: FakeUser(tenant_id=TENANT_B)  # overrides A!
    yield AsyncClient(...)

# Test que usa ambos clients ve solo TENANT_B data en BOTH
```

✅ **CORRECTO:** single override con header-based dispatch:

```python
@pytest.fixture()
async def app_with_overrides(db_session):
    def _fake_user(x_tenant_id: str | None = Header(None, alias="X-Tenant-ID")) -> FakeUser:
        tid = UUID(x_tenant_id) if x_tenant_id else TENANT_A
        return FakeUser(tenant_id=tid)

    app.dependency_overrides[get_current_user] = _fake_user
    yield app
    app.dependency_overrides.pop(get_current_user, None)

@pytest.fixture()
async def client_a(app_with_overrides):
    async with AsyncClient(transport=ASGITransport(app=app_with_overrides),
                           base_url="http://test",
                           headers={"X-Tenant-ID": str(TENANT_A)}) as ac:
        yield ac

@pytest.fixture()
async def client_b(app_with_overrides):
    async with AsyncClient(...,
                           headers={"X-Tenant-ID": str(TENANT_B)}) as ac:
        yield ac
```

---

## 501 / 404 stub endpoints — `response: Response` causa Pydantic introspection fail

❌ **PROHIBIDO:** `response: Response` para set headers en stubs:

```python
# ANTI-PATTERN — 422 Unprocessable Entity (Pydantic introspects Response como field)
@router.get("/{id}/journey", response_model=DeferredResponse, status_code=501)
async def stub_journey(contact_id: UUID, response: Response) -> DeferredResponse:
    response.headers["Retry-After"] = "PI-3"
    return DeferredResponse(...)
```

✅ **CORRECTO:** retornar `JSONResponse` directo:

```python
from fastapi.responses import JSONResponse

@router.get("/{id}/journey", response_model=DeferredResponse, status_code=501,
            responses={501: {"model": DeferredResponse, "headers": {"Retry-After": {"schema": {"type": "string"}}}}})
async def stub_journey(contact_id: UUID) -> JSONResponse:
    payload = DeferredResponse(detail="...", deferred_until="PI-3", ...)
    return JSONResponse(
        status_code=501,
        content=payload.model_dump(),
        headers={"Retry-After": "PI-3"},
    )
```

---

## Datetime query params — usar `datetime` directo, no `str + parse manual`

❌ **PROHIBIDO:** `str` + manual `_parse_datetime` helper:

```python
# ANTI-PATTERN — URL `?created_after=2026-04-21T01:21:23+00:00` falla porque httpx no encoda `+`
@router.get("/")
async def list_x(
    created_after: Annotated[str | None, Query()] = None,
):
    parsed = _parse_datetime(created_after, "created_after")  # rejects raw "+00:00"
    ...
```

✅ **CORRECTO:** `datetime | None` direct (FastAPI parsea ISO 8601 nativo):

```python
@router.get("/")
async def list_x(
    created_after: Annotated[datetime | None, Query(description="ISO 8601 datetime.")] = None,
):
    # datetime ya parseado por FastAPI/Pydantic
    ...
```

Tests httpx también deben usar `params={...}` (NO f-string raw URL) — httpx encoda `+` correctamente:

```python
# ❌ raw URL — `+00:00` interpretado como espacio
await client.get(f"/contacts/?created_after={cutoff.isoformat()}")

# ✅ httpx params encoda `+` → `%2B`
await client.get("/contacts/", params={"created_after": cutoff.isoformat()})
```

---

## SQLA legacy `Column[T]` types con mypy strict

Cuando módulo CRM/legacy usa `Column()` (no `Mapped[]`), mypy strict reporta `Column[UUID]` instead of `UUID` en attribute access.

❌ **PROHIBIDO:** `Any` widespread sin razón:

```python
def _helper(self, col: Any) -> ...:  # ANN401 ESLint reject
    ...
```

✅ **CORRECTO:** `# noqa: ANN401` con razón documentada + targeted `# type: ignore`:

```python
def _apply_channel_exists(
    self,
    q: _SelectQuery,
    tenant_id: UUID,
    channel_col: Any,  # noqa: ANN401  # SQLA legacy Column — typed as Any pragmatically
    flag: bool | None,
) -> _SelectQuery:
    ...

# Per-call line ignores cuando access stale:
profile_ids: list[UUID] = [p.id for p in page_rows]  # type: ignore[misc]
presence[lead.customer_id] = lead  # type: ignore[index]
```

Cleanup futuro: migrar Column → Mapped[T] (track deuda).

---

## Cross-module reads via Port (DDD)

❌ **PROHIBIDO:** import directo de otro módulo:

```python
# ANTI-PATTERN — viola DDD boundary
from src.modules.campaigns.application.services.campaign_service import CampaignService
```

✅ **CORRECTO:** Port en `shared/links/ports/` + factory:

```python
from src.shared.links.ports.campaigns import (
    create_campaigns_lookup_port,
    CampaignsLookupPort,
)

port = create_campaigns_lookup_port()
result = await port.find_recent_campaign_tasks_for_leads(
    tenant_id=tenant_id, lead_ids=ids, window_hours=2160, session=session
)
```

Si port no soporta tu use case → EXTEND port (add method) en mismo PR. NO bypass.

---

## Pydantic v2 ConfigDict strict

✅ **OBLIGATORIO** en TODOS los DTOs (request + response):

```python
class MyDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")  # rechaza fields no declarados
    # Si lee de SQLA model:
    model_config = ConfigDict(extra="forbid", from_attributes=True)
```

❌ **PROHIBIDO:** `class Config:` inner (Pydantic v1 legacy)
❌ **PROHIBIDO:** `extra="allow"` o no especificar (silently allows typos)

---

## Tenant isolation — cada query, sin excepción

✅ **OBLIGATORIO:** `WHERE tenant_id == :tenant_id` en CADA query (incluso `get_by_id`):

```python
stmt = select(Model).where(
    Model.tenant_id == tenant_id,  # ← PRIMER predicate
    Model.id == entity_id,
    Model.deleted_at.is_(None),
)
```

✅ **404 vs 403:** si entity_id existe pero tenant no match → return `None` desde repo → 404 desde API. NO leak existencia con 403.

```python
async def get(self, *, tenant_id: UUID, contact_id: UUID) -> ContactDetail | None:
    q = select(Model).where(Model.id == contact_id, Model.tenant_id == tenant_id)
    profile = (await session.execute(q)).scalars().first()
    if profile is None:
        return None  # ← API maps a 404, NO 403
    return profile
```

---

## Async patterns — SQLA 2.0 only

❌ `Session.query()` / `session.query()` / `model.query` — SQLA 1.x legacy
❌ `datetime.utcnow()` — naive datetime
❌ `DateTime()` sin `timezone=True`
❌ `Column()` para nuevo código — usar `mapped_column(...)` + `Mapped[T]`

✅ `select(Model).where(...)` async via `await session.execute(stmt)`
✅ `utc_now()` from `src.shared.domain.datetime_utils`
✅ `DateTime(timezone=True)` siempre
✅ `Mapped[T]` + `mapped_column()` para todo nuevo código

---

## response_model + JSONB shape contract

✅ **OBLIGATORIO** `response_model=` en CADA endpoint (PII allowlist enforce):

```python
@router.get("/{id}", response_model=ContactDetail)  # ← obligatorio
async def get_contact(contact_id: UUID, ...) -> ContactDetail:
    ...
```

JSONB shape contract pattern (cuando reusas existing column con shape nuevo):

```python
# Storage: filter_dsl JSONB existing column
# Shape new: {"_static": true, "lead_ids": [UUID, UUID, ...]}
# Resolve(): if dsl.get("_static") is True → return dsl["lead_ids"] sin SQL
# Documenta shape en domain/segment.py + service docstring
```

NO migration necesaria. Pero documenta shape signature explícitamente.

---

## Async test fixture race + closure captures

❌ **PROHIBIDO:** factory hook capture state que cambia post-mount:

```python
# ANTI-PATTERN — `id` capturado en closure constructor; caller lo cambia after
def use_x(id_param: UUID):
    async def call():
        await client.post(f"/x/{id_param}/...")  # ← `id_param` stale si caller cambió
    return call
```

✅ **CORRECTO:** pasar `id` per-call payload, NO en factory:

```python
def use_x():
    async def call(id_param: UUID, ...):
        await client.post(f"/x/{id_param}/...")  # ← per-call
    return call
```

(Equivalente FE de useAddCampaignStepMutation pattern aplicado a Python async helpers.)

---

## Auditor invocation checklist (read source + grep)

Cuando builder Sonnet spawnea auditor o auditor agent paused/killed → resume Opus auditor (NO PM fallback). Auditor MUST execute en orden:

1. ✅ Run gates locales nativo (ruff/mypy/pytest/pytest-arch) — necesario pero NO suficiente
2. ✅ **Read full source de cada archivo PR-touched** — buscar anti-patterns:
   - Type alias `Annotated[X, Depends(...)]` para dep complejo con AsyncSession dentro → flag CRITICAL
   - Override factory con bare param sin `Depends()` → flag CRITICAL
   - 501 stubs con `response: Response` param → flag CRITICAL
   - `str` + manual `_parse_datetime` para query params datetime → flag HIGH
   - Cross-module direct imports (no port) → flag CRITICAL (DDD violation)
   - Missing `tenant_id` filter en query → flag CRITICAL
   - Missing `response_model=` en endpoint → flag CRITICAL (PII rule)
   - `Session.query()` / `Column()` legacy en código nuevo → flag HIGH
   - `class Config:` inner Pydantic v1 → flag MEDIUM
   - Multiple test fixtures sobreescribiendo `app.dependency_overrides` → flag HIGH (tenant isolation broken in tests)
   - Migration `op.create_table()` / `op.add_column()` no idempotente → flag CRITICAL
3. ✅ Verify `IMPL-LOG.md § Skills Consulted` filled — si vacío → REVIEW FAIL "skills not invoked"
4. ✅ Solo si pasos 1-3 verde → REVIEW.md PASS
5. Si CUALQUIER finding flag CRITICAL/HIGH/MEDIUM → REVIEW.md WARN o FAIL + builder fix loop O escalate PM si fix > 30 LOC

---

## Skill invocation REPORT obligatorio en IMPL-LOG.md

Builder MUST escribir en `IMPL-LOG.md § Skills Consulted` lista verbatim de skills invocadas:

```md
## Skills Consulted

- `backend-expert` — invoked Step 3 SOP routing. Loaded `runtime-quality-checklist.md` antes commit.
- `tessl__fastapi` — invoked para FastAPI Annotated dep patterns + response_model
- `tessl__pytest-api-testing` — invoked para httpx AsyncClient + fixture scoping
- `metrics-expert` — invoked porque PR toca `modules/analytics/` ETL pipeline
```

❌ Vacío o "skipped" sin razón → auditor FAIL automatic.
❌ "I knew the patterns already" no es excusa — invoke + cite decision tomada.
✅ "skill X invoked, decision: Y, citation: skill_path:line_or_section"

---

## Cuándo invocar este checklist

- ✅ `nicolify-backend` builder Step 4 (antes implement) + Step 7 (antes commit + spawn auditor)
- ✅ `nicolify-backend-auditor` Phase audit (antes producir REVIEW.md)
- ✅ Bug fix BE (un check rápido pre-commit)
- ✅ Cualquier cambio que toca `api/`, `application/services/`, repos, migrations, tests integration
