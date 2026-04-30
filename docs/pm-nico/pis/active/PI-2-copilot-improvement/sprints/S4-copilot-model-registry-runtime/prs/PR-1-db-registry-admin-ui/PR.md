# PR-1-db-registry-admin-ui

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-1-db-registry-admin-ui |
| Sprint padre | S4-copilot-model-registry-runtime |
| PI padre | PI-2-copilot-improvement |
| Estado | ready (depends S3 shipped) |
| Tipo | infra (DB registry runtime + admin UI) |
| Esfuerzo | L (~12-15 archivos cohesivos) |
| Owner PM | /pm |

## Problema

Post-S3, swap modelo aún requiere `.env` edit + redeploy = ventana downtime + lento experimentación. A 1000+ tenants, cada deploy = riesgo + tiempo. JTBD Chris: "Cambiar de modelo en cualquier capa rápido y sencillo, sin deploy."

## Outcome esperado

- Tabla `llm_role_binding` SSoT runtime per role (NANO, FAST, REASONING, AGENT, VISION, EMBEDDING).
- Admin Streamlit `/admin/llm-models` CRUD: CREATE, UPDATE, ACTIVATE, DEACTIVATE.
- `LLMConfigService.resolve(role, tenant_id) -> ModelBinding` con cache 60s + Redis pub/sub invalidation.
- Cambio admin UI → backend pods refresh <60s sin restart.
- Audit trail tabla `llm_config_audit` (immutable append-only).

## Walking skeleton

1. **Migration alembic 117**: tabla `llm_role_binding` + `llm_config_audit` (idempotente raw SQL).
   - Schema `llm_role_binding`: `(id UUID, role VARCHAR(32), provider, model, is_active, config JSONB, eval_score, created_at, created_by, activated_at, deactivated_at, notes)` + UNIQUE(role) WHERE is_active.
   - Schema `llm_config_audit`: append-only `(id, role, old_model, new_model, action, admin_user, timestamp, reason)`.
2. **`LLMConfigService`** en `src/shared/infrastructure/llm/config_service.py`:
   - `resolve(role) -> ModelBinding` (default global)
   - `resolve(role, tenant_id) -> ModelBinding` (per-tenant override S4 PR-2)
   - Cache in-memory TTL 60s + Redis pub/sub channel `llm_config_invalidate`
   - Fallback: si DB unavailable → leer `.env` (degraded mode)
3. **Admin Streamlit** `admin/pages/llm_models.py`:
   - List bindings per role + active highlighted
   - Form CREATE: provider + model + role + config JSON
   - Button ACTIVATE → UPDATE active=TRUE WHERE role=X (transactional, only one active per role)
   - Button DEACTIVATE → UPDATE active=FALSE
   - Button "Test ping" → invocar provider con prompt sample → latency + cost real reportados
   - Audit log view (last 50 changes)
4. **Refactor Settings.get_model**: prefer `LLMConfigService.resolve()` if DB binding exists, fallback `.env` AI_MODEL_<ROLE>.
5. **Pub/sub invalidation worker**: `src/workers/llm_config_invalidation_consumer.py` escucha Redis channel + flush in-memory cache.
6. **Migration data seed**: import `.env` actual a tabla (NANO=gpt-4o-mini openai active, FAST=gpt-4o-mini openai active, REASONING=deepseek-reasoner deepseek active, AGENT=kimi-k2.6 moonshot active, etc.).

## Existing systems audit

```bash
grep -rn "settings\.get_model\|settings\.get_provider_for_role" src/
grep -rn "AI_MODEL_\|AI_PROVIDER_" src/ docs/
find src/shared/infrastructure/llm/ -name "*.py"
```

**Sistemas:**
- ✅ Sistema A (EXTEND): `Settings.get_model` → wrap con LLMConfigService.resolve fallback (nuevo) + .env legacy fallback (existente). Cero breaking changes consumers.
- 🆕 Sistema B (NEW DB layer): tabla `llm_role_binding` + service. Justificación: hot-swap requiere DB SSoT runtime, .env-only no soporta sin redeploy.
- ✅ Sistema C (EXTEND admin Streamlit): nueva page sigue patrón `admin/pages/{slug}.py` (rule `admin-panel.md`).

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A — DB registry custom + admin UI Streamlit | Control total + tenant-aware S4 PR-2 | Custom maintenance | **ELEGIDA** |
| B — LiteLLM admin UI nativa | Out-of-box | LiteLLM admin UI no conoce ModelRole semantic Nicolify; tenant-aware débil | descartada (UI complementaria, no sustituto) |
| C — JSON config file en repo + git workflow | Simple | NO hot-swap, requiere PR + deploy | descartada |

## Surface impactada

| Tipo | Path | Cambio |
|---|---|---|
| Migration | `alembic/versions/117_llm_role_binding.py` | NEW |
| BE service | `src/shared/infrastructure/llm/config_service.py` | NEW |
| BE settings refactor | `src/core/config.py::Settings.get_model` | wrap with config_service |
| Worker | `src/workers/llm_config_invalidation_consumer.py` | NEW Redis pub/sub |
| Admin | `admin/pages/llm_models.py` + spec entry | NEW |
| Tests | `tests/shared/infrastructure/llm/test_config_service.py` | NEW |
| Tests | `tests/admin/test_llm_models_page.py` | NEW |
| Migration seed | `alembic/versions/118_llm_role_binding_seed_from_env.py` | NEW idempotente |
| current-state | `current-state/copilot.md` | append cap "LLM model registry runtime hot-swap" |

## Tests requeridos

- `test_config_service.py` — resolve global, cache hit/miss, pub/sub invalidation, DB fallback to .env
- `test_llm_models_page.py` — CRUD smoke, ACTIVATE only-one-active invariant, audit log row
- Migration tests idempotente

## Aceptación

- [ ] Tests verde
- [ ] Lint/type strict verde
- [ ] Admin UI funcional (manual test: cambiar NANO=gpt-4o → verify backend resolve nuevo en <60s)
- [ ] Audit log row present por cada cambio
- [ ] current-state/copilot.md updated
- [ ] Decisions appendadas

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Cache stale entre pods (race condition) | Pub/sub Redis con timestamp + version on each request |
| DB down → fallback .env, pero seed table puede estar desincronizado de .env real | Migration seed idempotente periódico (worker) |
| Admin user activa modelo broken → all turns fail | Admin UI "Test ping" obligatorio antes ACTIVATE; rollback button MTTR <30s |
