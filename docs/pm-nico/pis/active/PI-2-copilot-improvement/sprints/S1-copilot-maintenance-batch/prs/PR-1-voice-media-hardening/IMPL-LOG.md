# IMPL-LOG — PR-1-voice-media-hardening

> Owner: builders. Append-only durante implementación. Diario de decisiones.

## Sesión 2026-04-29 — `nicolify-backend` (Opus 4.7) + main thread fix-up

### Contexto cargado
- `PR.md` ✓
- `CONTRACT.md` ✓ (PI-2 S1 PR-1, post 5 PM answers Q1-Q5)
- Skills: `copilot-expert` ✓
- Rules: `backend-ddd`, `tenant-isolation`, `tdd-mandatory`, `backend-migrations`, `admin-panel`, `copilot-resilience`, `copilot-observability` ✓

### Decisiones implementación
- **Reuse `core/rate_limit.py` (no `shared/rate_limit/` nuevo)** — CONTRACT decisión §0. Helper Redis sliding-window ya in-use por `copilot/api/chat.py`. Extender via env settings + DI resolver.
- **Tabla audit separada `copilot_tenant_limits_audit`** (Q2 PM) — append-only, FK lógico a tenant. Atomic write con upsert/soft_delete en misma transacción (sync repo).
- **Domain `CopilotTenantLimits` frozen dataclass** — invariantes en `__post_init__` (tenant_id required, voice_rpm ∈ [1,1000], media_bytes ∈ [1 MiB, 100 MiB]). No framework deps.
- **Sync + Async repos** — async para FastAPI handlers, sync wrapper para Streamlit admin (Streamlit no soporta async event loop limpio).
- **Migration 085 raw SQL idempotente** — `CREATE TABLE IF NOT EXISTS`, `CHECK` constraints (cap upper editable), `CREATE INDEX IF NOT EXISTS`, `CREATE UNIQUE INDEX IF NOT EXISTS ... WHERE deleted_at IS NULL` (partial unique tenant_id viva).
- **Default voice 6 RPM** (Q3 PM) — cost-based ($0.006/min Whisper × 6 = $0.036/min/tenant cap).
- **Cap upper media 100 MiB** (Q4 PM) — industry standard SaaS microempresarios; CHECK constraint editable cuando aterricen planes per-tenant.
- **Rate limit `/media/upload` bucket separado** (Q5 PM) — `copilot-media-upload` scope, default 30 RPM. Storage R2 confirmado vía `AssetsService.upload_asset` (independiente de cap bytes).
- **Legacy `/voice/transcribe` removido** (Q1 PM) — cliente pequeño, barato corregir ahora. Test `test_legacy_transcribe_endpoint_still_responds` valida 404 + import scan.

### Sub-deliverables completados
- [x] **A — Domain**: `tenant_limits.py` aggregate + invariantes (commit pending HEAD)
- [x] **B — Infrastructure**: 2 models (main + audit) + sync/async repo (commit pending HEAD)
- [x] **C — Application**: `limits_resolver.py` (env defaults + per-tenant override + DB-error fallback) (commit pending HEAD)
- [x] **D — API**: DTO `tenant_limits_dto.py` + integración `voice.py` + `media.py` con rate limit por bucket + DI hook (commit pending HEAD)
- [x] **E — Migration**: `085_copilot_tenant_limits.py` raw SQL idempotente, 2 tablas + 4 índices + 3 CHECKs (commit pending HEAD)
- [x] **F — Admin**: Streamlit `pages/copilot-limits.py` + `modules/copilot_limits.py` (list overrides, upsert, soft-delete) (commit pending HEAD)

### Tests escritos (TDD layered)
- `tests/modules/copilot/test_tenant_limits_invariants.py` — 11 tests domain (frozen, caps, sentinels, required fields)
- `tests/modules/copilot/test_tenant_limits_repository.py` — 10 tests repo (upsert create/update, soft_delete, get_by_tenant, list_overrides, model→domain mapping)
- `tests/modules/copilot/test_limits_resolver.py` — 4 tests resolver (no override, voice only, both, DB error fallback)
- `tests/modules/copilot/test_voice_rate_limit.py` — 5 tests endpoint (legacy 404, 413 max_bytes, 429 rate limit, scope correcto, pasa under limit)
- `tests/modules/copilot/test_voice_rate_limit_per_tenant_override.py` — 3 tests (override 20 RPM, 7 reqs no rate limit, resolver vs env)
- `tests/modules/copilot/test_media_max_bytes_env.py` — 5 tests endpoint (override 50 MiB, 11 MiB falla con 10 MiB env, empty 400, buckets independientes voice vs media, 429)
- `tests/modules/copilot/test_media_db_roundtrip.py` — 2 tests (asset_id válido, response sin secrets)
- `tests/admin/test_copilot_limits_smoke.py` — 2 tests (módulo expone `render_*`, render no crashea)

**Total: 42 tests verdes** ✓

### Quality gates
- [x] Ruff verde — `cd backend && .venv/bin/ruff check src/modules/copilot/ src/admin/modules/copilot_limits.py src/admin/pages/copilot-limits.py src/core/config.py tests/modules/copilot/ tests/admin/test_copilot_limits_smoke.py`
- [x] Ruff format verde — 385 files already formatted
- [x] Mypy verde (PR-1 files only) — 9 archivos, 0 errors. **Mypy strict global del módulo copilot tiene 354 errors pre-existentes en `chat.py`/`streaming.py` etc — NO introducidos por este PR**.
- [x] Pytest verde — 42/42 PR-1 + 649/649 arch fitness
- [x] Arch fitness verde — `tests/architecture/` 649 passed
- [ ] Migration prod-clone test — **PENDIENTE** (requiere `docker exec` Postgres con prod schema clone). Recomendado correr en `/test-backend` o manualmente antes de pase prod.

### Bloqueadores encontrados
- **Builder agent truncó dos veces (token cap)**:
  1. Sesión 1: completó código + tests pero no llegó a quality gates ni IMPL-LOG.
  2. Sesión 2: arregló mayor parte de ruff (12 errors auto-fix + 7 manuales), pero quedaron 10 mypy errors mid-fix.
- **Main thread (Opus 4.7) terminó manualmente:**
  - Fix `_get_repo()` return type `tuple[object, ...]` → `tuple[Session, ...]` con `TYPE_CHECKING` import.
  - `# type: ignore[misc]` en `CopilotTenantLimitsModel(Base)` y `CopilotTenantLimitsAuditModel(Base)` — consistente con codebase pre-existente (Base typed Any).
  - Quitar `# type: ignore[comparison-overlap]` unused en `tenant_limits.py:40`.
  - Refactor `_media_default_bytes` para evitar E501 line-too-long.
  - None-guard en lectura `current.media_max_bytes_override` para satisfacer mypy union-attr.

### Decisiones diferidas durante implementación
- **Migration prod-clone test** — diferido a `/test-backend` o pase prod (requiere Docker activo).
- **Builder agent contaminó trabajo paralelo PI-1 (5 commits ajenos)** — `5fc7169f`, `a1696b3f`, `8a4968a1`, `3b4180b1`, `d5b9d373`. Decisión Chris: no revert (preservar info), aceptar contaminación, comunicarse manualmente con sesión PI-1 al cierre. **Lección**: builder agents no distinguen `PR-1 PI-1` vs `PR-1 PI-2` cuando ambas activas — necesita restricción explícita por path en futuras sesiones paralelas.

### Surface real entregada

| Tipo | Path | Estado |
|---|---|---|
| Domain | `backend/src/modules/copilot/domain/tenant_limits.py` | NEW |
| Model | `backend/src/modules/copilot/infrastructure/models/tenant_limits_model.py` | NEW |
| Audit Model | `backend/src/modules/copilot/infrastructure/models/tenant_limits_audit_model.py` | NEW |
| Repo (sync+async) | `backend/src/modules/copilot/infrastructure/repositories/tenant_limits_repository.py` | NEW |
| Service | `backend/src/modules/copilot/application/services/limits_resolver.py` | NEW |
| DTO | `backend/src/modules/copilot/api/tenant_limits_dto.py` | NEW |
| API voice | `backend/src/modules/copilot/api/voice.py` | MODIFIED (rate limit + per-tenant override + legacy removed) |
| API media | `backend/src/modules/copilot/api/media.py` | MODIFIED (rate limit bucket + tenant-scoped max_bytes) |
| Settings | `backend/src/core/config.py` | MODIFIED (3 env settings COPILOT_*) |
| Migration | `backend/alembic/versions/085_copilot_tenant_limits.py` | NEW |
| Admin module | `backend/src/admin/modules/copilot_limits.py` | NEW |
| Admin page | `backend/src/admin/pages/copilot-limits.py` | NEW |
| Admin app reg | `backend/src/admin/app.py` | MODIFIED (PageSpec + nav entry) |
| Tests | `backend/tests/modules/copilot/test_*.py` × 7 | NEW |
| Tests admin | `backend/tests/admin/test_copilot_limits_smoke.py` | NEW |

### Commits
- `ebf25d4c` — `docs(pm): PI-2 S1 PR-1 voice-media-hardening CONTRACT.md complete` (architect output)
- `<HEAD next>` — `feat(copilot): tenant-configurable voice/media limits + rate limiting (PI-2 S1 PR-1)` (builder + main thread fix-up)

### Contaminación paralela (info para PM)
Agent builder commiteó 5 cambios sobre archivos PI-1 sub-G activo. Listado para coordinación con sesión paralela:
- `5fc7169f` `fix(tests): retention scaling 7 * n_agents` (PI-1)
- `a1696b3f` `docs(pm): PI-1 CONTRACT.md PR-1 final` (PI-1) — 1488 líneas insertadas
- `8a4968a1` `chore(lint): ruff format scripts/ + per-file-ignores` (cosmético)
- `3b4180b1` `docs(pm): current-state PR-1 caps — outbox + campaigns observability` (PI-1, 4 archivos)
- `d5b9d373` `docs(pm): IMPL-LOG PI-1 PR-1 final` (PI-1 IMPL-LOG)

---

<!-- @pm: implementación done. Próximo paso: ejecutar prompts/03-auditor-start.md o ejecutar /pm "PR-1 builder done" para review. -->
