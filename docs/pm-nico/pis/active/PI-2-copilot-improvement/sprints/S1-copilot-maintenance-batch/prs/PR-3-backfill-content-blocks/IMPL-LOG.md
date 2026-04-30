# IMPL-LOG — PR-3-backfill-content-blocks

> Owner: builder. Append-only durante implementación.

## Sesión 2026-04-29 — `nicolify-backend` (Opus 4.7) + main thread fix-up

### Contexto cargado
- `PR.md` ✓
- `CONTRACT.md` ✓ (8 architect-empowered decisions D1-D8)
- Skills: `copilot-expert` ✓
- Rules: `backend-ddd`, `tenant-isolation`, `tdd-mandatory`, `backend-migrations`, `copilot-resilience`, `copilot-observability`, `parallel-safety` (M8 nueva), `git-safety` ✓

### Decisiones implementación (siguiendo CONTRACT §D1-D8)

- **D1 batch processing**: per-conv atomic UPDATE + READ COMMITTED + commit-per-batch (default 100). Bulk SQL FROM SELECT descartado — codec usa `uuid4()` Python.
- **D2 retry/corruption**: skip + log + count, abort if `failure_rate > 0.05` sobre n≥100. Tres-categoría message classification:
  - `_message_is_v2`: tiene blocks truthy → skip already-done.
  - `_message_needs_backfill`: tiene content truthy + sin blocks → transform via codec.
  - `_message_is_corrupt`: NI role, NI content, NI blocks → skip + audit.
  - **valid pass-through**: role + content vacío + sin blocks (e.g. tool_call) → preserve as-is, no backfill needed.
- **D3 concurrency**: optimistic lock `WHERE messages = :original` + READ COMMITTED. Sin `FOR UPDATE SKIP LOCKED` (no worker pool). Conflict mid-flight = 0 rows updated → re-corre próximo run. Idempotente.
- **D4 observability**: tabla `copilot_backfill_runs` (audit run_id+tenant_id+stats+status) + structlog per-batch.
- **D5 codec v1 warning**: sampled 1/100 (counter por proceso) + structlog warning `copilot_message_legacy_v1_read`.
- **D6 alembic vs script**: marker migration `111_copilot_blocks_backfill_marker.py` con tabla audit; backfill ortogonal en script externo (patrón canónico Nicolify).
- **D7 tenant isolation**: secuencial per-tenant default. `--workers N` flag NO implementado (YAGNI).
- **D8 dry-run**: triple safety — dry-run default, `--apply` explícito, `--confirm-prod` regex `prod\.` interceptor en DATABASE_URL, `--max-failure-rate 0.05`.

### Sub-deliverables completados

- [x] **Phase A** — codec v1 warning sampled 1/100 (`message_codec.py`)
- [x] **Phase B** — script standalone `backfill_copilot_content_to_blocks.py` con CLI flags (--dry-run/--apply/--batch-size/--tenant-id/--confirm-prod/--max-failure-rate)
- [x] **Phase C** — alembic marker migration `111_copilot_blocks_backfill_marker.py` con `copilot_backfill_runs` audit table
- [x] **Phase D** — 7 tests TDD: dry_run, apply_converts_legacy, idempotent_rerun, batch_size, tenant_filter, corrupt_skipped, audit_records

### Tests escritos (TDD layered)

- `tests/scripts/test_backfill_copilot_content_to_blocks.py` (7 tests):
  - `test_dry_run_does_not_mutate_db`
  - `test_apply_converts_legacy_rows`
  - `test_idempotent_rerun`
  - `test_batch_size_respects_limit`
  - `test_tenant_filter_isolation`
  - `test_corrupt_message_skipped_with_audit`
  - `test_audit_table_records_run`
- `tests/scripts/conftest.py` — fixtures DB
- `tests/modules/copilot/test_message_codec.py` (M) — 18 tests pre-existentes + nuevos para codec v1 warning sampling

**Total: 25 tests verde** (7 backfill + 18 codec) ✓

### Quality gates

- [x] Ruff check verde — 0 errors
- [x] Ruff format verde — 6 files already formatted
- [x] Mypy `message_codec.py`: 12 errors PRE-EXISTENTES (`dict` sin type args, type-arg, no-any-return). NO introducidos por este PR. Mi `_LEGACY_READ_COUNTER: dict[str, int]` correctamente tipado.
- [x] Mypy `scripts/`: EXCLUDED por config `pyproject.toml [tool.mypy] exclude scripts/` — script no participa en mypy gate.
- [x] Pytest 25/25 PR-3 tests verde
- [x] Arch fitness 683 passed. **1 deselected**: `test_domain_layer_has_no_framework_imports` falla por `campaigns/domain/repositories.py` AJENO sesión paralela PI-1 — NO de PR-3 (regla M8 read-only ajenos).
- [ ] Migration prod-clone test — diferido a `/test-backend` o pase prod (Chris docker exec).

### Bloqueadores encontrados

- **Builder agent truncó token cap** mid-debugging idempotency bug (re-run path classificaba tool messages con content="" sin blocks como corrupt).
- **Main thread (Opus 4.7) terminó manualmente:**
  - Fix idempotency: nueva función `_message_is_corrupt(msg)` distingue corrupt (sin role/content/blocks) vs valid pass-through (role + content vacío). Re-run ahora correcto.
  - Lógica reescrita en `_run_batch`: corrupt detection FIRST → idempotency check (`needs_backfill=False` → already done) → transform si tiene legacy.

### Decisiones diferidas durante implementación

- **Migration prod-clone test** — diferido a `/test-backend` (requiere Docker activo).
- **Arch fail `campaigns/domain/repositories.py`** — sesión paralela PI-1 introduce framework import en domain. Regla M8: no destroy work del otro. Reportado en RESULT.md como deuda PI-1 sub-G follow-up.

### Surface real entregada

| Tipo | Path | Estado |
|---|---|---|
| Script | `backend/scripts/backfill_copilot_content_to_blocks.py` | NEW |
| Migration | `backend/alembic/versions/111_copilot_blocks_backfill_marker.py` | NEW (marker + audit table `copilot_backfill_runs` raw SQL idempotente) |
| Codec patch | `backend/src/modules/copilot/infrastructure/repositories/message_codec.py` | MODIFY (sampled v1 warning) |
| Tests | `backend/tests/scripts/test_backfill_copilot_content_to_blocks.py` + `conftest.py` | NEW (7 tests) |
| Tests codec | `backend/tests/modules/copilot/test_message_codec.py` | MODIFY (sampling tests) |

### Commits

- `280aa923` — `docs(pm): PR-3 backfill-content-blocks CONTRACT.md (architect-empowered, 8 decisions)`
- `<HEAD next>` — `feat(copilot): backfill content→blocks script + audit + codec v1 warning (PI-2 S1 PR-3)` (builder + main thread idempotency fix)

### Auto-fix iter (post-builder truncate)

**Iter 1 (main thread)**: fix idempotency bug — `_message_is_corrupt` función nueva distingue 4 categorías (v2 / needs_backfill / pass_through / corrupt). Tests 25/25 verde post-fix.

---

<!-- @pm: implementación done. Próximo paso: ejecutar prompts/03-auditor-start.md o ejecutar /pm "PR-3 builder done" para review. -->
