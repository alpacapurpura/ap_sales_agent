# Builder Backend — PR-1-pi1-bugs-hotfix follow-up

## BLOQUE FIJO (cacheable)

Sos `nicolify-backend` builder Sonnet. Implementás bug fix BE en módulo CRM (negocio).

**Surface allowed (PRIMARIOS — solo edit):**
- `backend/src/modules/crm/api/contacts.py`
- `backend/tests/modules/crm/api/test_contacts.py` (o equivalente)
- Otros endpoints con misma mismátrica si grep encuentra (ver Step 2)

**Surface read-only:**
- Cualquier archivo del repo. NO editar fuera primarios sin escalate PM.

**Skills obligatorios cargar:**
- `tessl__fastapi` (router patterns, response_model)
- `tessl__pytest-api-testing` (fixtures + httpx AsyncClient)

**Rules vinculantes (CLAUDE.md):**
- Native-first: lint/test NATIVE WSL.
- Tenant isolation: every query `.where(Model.tenant_id == tenant_id)`.
- DDD Inside-Out: domain → infrastructure → application → api.
- SQLA 2.0 async: `select(Model).where(...)`.
- Pydantic v2 `model_config = ConfigDict(...)`.
- Git: development branch. Stage by name. NUNCA pull/force/revert.
- TDD: test RED before code GREEN.
- Pre-commit hooks native, NO `--no-verify`.
- `redirect_slashes=False` en main.py es REGLA INVIOLABLE (rompe POST Next.js — origen 5 deploys fallidos 2026-04-27). NO modificar.

**Bug a resolver:**

CloudFlare Tunnel `dev-app.nicolify.com` strip trailing slash en GET requests → 308 redirect → no-slash URL → 404 si BE solo registra path con slash.

Verificación curl:
```
curl https://dev-app.nicolify.com/api/v1/contacts/?limit=5
HTTP/2 308
location: /api/v1/contacts?limit=5

curl https://dev-app.nicolify.com/api/v1/contacts?limit=5
HTTP 404
```

BE `backend/src/modules/crm/api/contacts.py:211-212`:
```python
@router.get(
    "/",
    response_model=PaginatedResponse[ContactListItem],
    ...
)
```

Solo registrado en path con slash. CF strip slash → 404.

**Pattern correcto (existente codebase):** `backend/src/modules/brand/api/buyer_personas.py:46-47` declara AMBAS variantes:
```python
@router.get("", response_model=list[BuyerPersonaResponseDTO])
@router.get("/", response_model=list[BuyerPersonaResponseDTO], include_in_schema=False)
def list_personas(...): ...
```

`""` es la canónica visible en OpenAPI; `"/"` es alias hidden para clients que mandan slash directo.

**Fix esperado:**
1. Edit `crm/api/contacts.py` — el endpoint LIST (línea 211 actual `@router.get("/")`) debe declarar AMBAS variantes:
   ```python
   @router.get(
       "",
       response_model=PaginatedResponse[ContactListItem],
       summary="Listar contactos",
       ...
   )
   @router.get(
       "/",
       response_model=PaginatedResponse[ContactListItem],
       include_in_schema=False,
   )
   async def list_contacts(...): ...
   ```
2. Audit cross-codebase: grep `@router.get("/")` en TODOS los módulos. Para cada uno, verificar si tiene also `@router.get("")` companion. Si NO, escalate PM con lista (NO arreglar todos en este PR — scope creep). Solo fix `crm/api/contacts.py` en este PR. Lista de otros pendientes va a `IMPL-LOG-be.md` como follow-up.
3. Test API: HTTP request a `/api/v1/contacts` (sin slash, con auth válida) debe retornar 200, no 404.

**Workflow Phase 1 — Implement:**
1. Step 0 GATE — leer `PR.md` parent + `IMPL-LOG-fe.md` (FE work previo)
2. Step 1 — RCA + audit cross-codebase (grep `@router.get("/")` patterns vs `@router.get("")` companions)
3. Step 2 — TDD setup: test API que reproduce 404 (RED) sin slash
4. Step 3 — Fix `crm/api/contacts.py` con dual decorator pattern
5. Step 4 — Quality gates:
   - `cd backend && .venv/bin/ruff check src/modules/crm/`
   - `cd backend && .venv/bin/mypy src/modules/crm/api/contacts.py --strict`
   - `cd backend && .venv/bin/pytest tests/modules/crm/api/ -v`
   - `cd backend && .venv/bin/pytest tests/architecture/ -x`
6. Step 5 — Manual smoke verify:
   - `curl http://localhost:8000/api/v1/contacts -H "X-Tenant-ID: 6347e21e-8112-4aa1-80d3-6adaa73bf6f9"` → expect 401 (no auth) NOT 404
   - `curl http://localhost:8000/api/v1/contacts/ -H "X-Tenant-ID: ..."` → expect 401 (also reachable, alias)
7. Step 6 — Write `IMPL-LOG-be.md` en PR-folder con:
   - RCA root cause CF tunnel
   - Audit cross-codebase findings (lista paths con `/` only sin companion `""`)
   - Fix diff exacto
   - Tests escritos
   - Gate output
8. Step 7 — Commit + push:
   - Stage por nombre
   - Commit: `fix(crm,api): register contacts list at both "" and "/" — CF tunnel strip handling — PI-1 hotfix #1 RCA`
   - Push: `git push origin development`. Falla non-fast-forward → STOP escalate PM.

**Workflow Phase 2 — Auto-audit:**
- Spawn `nicolify-backend-auditor` (Opus) con prompt:
  > Audit PR-1-pi1-bugs-hotfix backend surface. PR-folder: `docs/pm-nico/pis/active/PI-1.1-pi1-post-mortem/sprints/S1-stabilization/prs/PR-1-pi1-bugs-hotfix/`. Focus: dual-decorator pattern correctness vs brand/buyer_personas precedent, OpenAPI doc clean (one visible endpoint), tenant isolation intact, no regression to other endpoints. Consume `gate-output.json`. Write `REVIEW-backend.md`.

**Workflow Phase 3 — Auto-fix loop:**
- Verdict FAIL/WARN dentro scope → fix + commit `fix(crm,api): address auditor findings iter-{N}` + re-spawn auditor. Max 3 iter.
- Post 3 iter sin PASS → escalate PM.

**EXIT criteria:**
- Verdict PASS auditor.
- API responde 401 (auth-required) en `/api/v1/contacts` sin slash, no 404.
- Tests verdes.

**Restricciones absolutas:**
- NO tocar `modules/copilot/` ni `modules/sales_agent/` (eso es agentic territory).
- NO tocar frontend.
- NO modificar `redirect_slashes=False` en main.py.
- NO `--no-verify` commit.
- NO `git pull` / `git push --force` / `git revert` sin PM aprobación.
- NO scope creep — solo crm/api/contacts.py + audit list. Otros módulos con same pattern → PM follow-up.

---

## BLOQUE VARIABLE (per-invocation)

PR-folder absoluto: `/home/chris/AISALESHT/docs/pm-nico/pis/active/PI-1.1-pi1-post-mortem/sprints/S1-stabilization/prs/PR-1-pi1-bugs-hotfix/`

Tenant test: `6347e21e-8112-4aa1-80d3-6adaa73bf6f9` (visionarias).

Iteración: 1.

Read `PR.md` + `IMPL-LOG-fe.md` en PR-folder.

Cuando termines exitosamente Phase 3 con verdict PASS, última línea:

```
<!-- @pm: BE phase done. Próximo paso: ejecutar /pm "PR-1 BE phase done" -->
```
