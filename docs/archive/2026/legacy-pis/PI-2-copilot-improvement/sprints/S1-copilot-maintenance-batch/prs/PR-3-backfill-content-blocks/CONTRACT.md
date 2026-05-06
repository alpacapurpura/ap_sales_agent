# CONTRACT — PR-3-backfill-content-blocks

> Owner: `nicolify-architect`. Sesión 2026-04-29 main thread (Opus 4.7 1M).
> SSoT pre-implementación. Builder backend + auditor consumen este archivo.
> **Decisiones arquitectónicas tomadas con criterio "build-right-once para 1000+ tenants" — sin Open Questions para PM.**

---

## 0. Context summary

| Campo | Valor |
|---|---|
| PR | PR-3-backfill-content-blocks |
| Sprint / PI | S1-copilot-maintenance-batch / PI-2-copilot-improvement |
| Tipo | data backfill (one-shot) + observability hardening |
| Modules touched | `backend/scripts/`, `backend/alembic/versions/`, `backend/src/modules/copilot/infrastructure/repositories/message_codec.py` (warning log), `backend/tests/scripts/` |
| Skills consultados | `copilot-expert`, `backend-expert` |
| current-state files afectados | `docs/pm-nico/current-state/copilot.md` — append capability "Backfill content→blocks completed" |
| Arch fitness gates corren | `tests/architecture/test_copilot_anchors.py`, `test_no_new_copilot_module_imports.py`, `test_no_hard_deletes.py`, naming conventions |

### Hallazgo crítico (forma del problema ≠ PR.md asumió)

**No existe tabla `copilot_message`.** Los messages viven en JSONB array dentro de `copilot_conversations.messages`. La migración `056_copilot_multimodal` (`20260422_1200_copilot_multimodal.py`) NO añadió columna `blocks` — añadió un partial GIN index sobre `messages::jsonb @? '$[*].blocks'` para localizar conversaciones que ya cargan bloques. La forma del backfill es **conversation-by-conversation**: para cada conv, decodificar `messages[]`, transformar cada elemento legacy (sin `blocks`) usando el codec actual `decode_message`, y persistir el array completo via `conv.messages = new_array` con `UPDATE ... SET messages = :new_messages WHERE id = :conv_id AND tenant_id = :tenant_id` (atomic JSONB replacement).

Esto invalida la opción "row-by-row UPDATE" (no hay rows individuales) y reduce la presión de batch (la unidad atómica es la conversación, no el message).

**Implicancia pricing arquitectura:** target real es N conversaciones × M messages (M ≈ 5-50 promedio, peak ~200). Para 10K convs prod = ~10-30 min secuencial. Para 100K convs (escala 1000+ tenants) = ~3-5 hrs. Diseño debe permitir resume + parallelización per-tenant si Chris escala.

---

## 1. Domain entities (sin cambios)

Este PR no toca domain. Reutiliza:
- `src.modules.copilot.domain.message.Message` (Pydantic v2, ya existe)
- `src.modules.copilot.domain.message_blocks.{TextBlock, MessageBlock}` (ya existe)
- `src.modules.copilot.infrastructure.repositories.message_codec.{decode_message, encode_message}` (ya existe — invariante: `decode_message` con `blocks=None + content!=""` sintetiza un `TextBlock`)

**Constraint reusada del codec actual** (`message_codec.py:50-57`):
```python
elif raw_content:
    # v1 shape: synthesize a TextBlock from legacy content
    content = raw_content
    blocks = [TextBlock(id=uuid4(), markdown=raw_content)]
```

El backfill DEBE usar este path. NO reimplementa la transformación.

---

## 2. Domain entity nueva — `BackfillStats` (script-internal, NO persisted)

```python
# backend/scripts/backfill_copilot_content_to_blocks.py
from __future__ import annotations
from dataclasses import dataclass, field
from uuid import UUID

@dataclass(slots=True)
class BackfillStats:
    """Aggregated counters for a single backfill run.

    Emitted as structlog event on every batch + final summary. Every counter
    is monotonic — re-running on top of a partial run accumulates.
    """
    convs_scanned: int = 0
    convs_already_v2: int = 0          # all messages have blocks → skip atomic
    convs_with_legacy_msgs: int = 0    # at least 1 message lacks blocks
    convs_updated: int = 0             # successful UPDATE
    convs_skipped_corrupt: int = 0     # codec raised, conv left untouched
    msgs_total: int = 0                # across processed convs
    msgs_legacy_converted: int = 0     # synthesized TextBlock count
    msgs_already_v2: int = 0
    msgs_skipped_corrupt: int = 0      # per-message try/except
    tenants_touched: set[UUID] = field(default_factory=set)
    duration_ms: int = 0               # final
    failed_conv_ids: list[UUID] = field(default_factory=list)
```

No se persiste a DB. Se loggea via structlog y se imprime al stdout al cerrar.

---

## 3. SQLAlchemy 2.0 models (sin cambios)

`CopilotConversationModel` (ya existe, 064 migration) — modelo legacy en SQLAlchemy 1.x style (`Column(...)`). El script NO lo refactorea (fuera de scope). Lee/escribe via SQLA 2.0 `select(Model).where(...)` + `update(Model).where(...).values(...)`.

---

## 4. Pydantic v2 DTOs (sin cambios — script no expone API)

**No hay endpoints HTTP.** Script CLI puro. No hay `response_model=` aplicable.

---

## 5. API routes (sin cambios)

Ninguna. PR es maintenance interno transparente al user.

---

## 6. Repository interfaces (sin cambios)

El script no agrega métodos al `ConversationRepository`. Usa `select`/`update` directos via raw SQLA 2.0 dentro de la función `_run_batch` del script. Justificación: maintenance one-shot — no merece API permanente en el repo. Si reutilización futura emerge, refactorear a `ConversationRepository.find_legacy_block_convs()` en PR aparte.

---

## 7. Application services (sin cambios)

N/A. Lógica vive en script.

---

## 8. Agentic surfaces — codec v1 reader warning (única edición a `copilot/`)

**Edit minimal a `message_codec.py`:** agregar `structlog.warning` cuando se sintetiza `TextBlock` desde legacy content. Permite detectar regresiones post-backfill (debería tender a 0 reads/día).

```python
# backend/src/modules/copilot/infrastructure/repositories/message_codec.py
# ADD (top of file)
import structlog
logger = structlog.get_logger(__name__)

# Counter for sampling (volatile, per-process):
_LEGACY_READ_COUNTER: dict[str, int] = {"count": 0}
_LEGACY_LOG_SAMPLE_RATE = 100  # log 1 of every 100 to avoid log flood

# ADD inside decode_message, after the v1 synthesize branch:
elif raw_content:
    content = raw_content
    blocks = [TextBlock(id=uuid4(), markdown=raw_content)]
    _LEGACY_READ_COUNTER["count"] += 1
    if _LEGACY_READ_COUNTER["count"] % _LEGACY_LOG_SAMPLE_RATE == 1:
        logger.warning(
            "copilot_message_legacy_v1_read",
            conversation_id=str(conversation_id),
            message_id=str(mid),
            sampled_count=_LEGACY_READ_COUNTER["count"],
            sample_rate=_LEGACY_LOG_SAMPLE_RATE,
            hint="post-backfill should trend to zero; investigate if persistent",
        )
```

**Why sampling (not 100%):** un read v1 muy hot (carga de UI history en producción de un tenant que conserva conversaciones largas) puede inflar logs. Sample 1/100 = signal-noise balance. Counter por proceso (no Redis) — no requiere infra extra. Ops queries `grep copilot_message_legacy_v1_read /var/log/copilot.log | wc -l × 100` para approx ratio.

**Why no PII:** loggea solo IDs (UUIDs) + contadores. `raw_content` NO se loggea. Cumple invariante `sanitize_payload`.

---

## 9. Migration notes

### 9.1 Estrategia: schema migration vacía + script externo (NO inline Python en alembic)

**Decisión arquitect (build-right-once):** ALL data migrations en Nicolify viven como **scripts Python externos**, NO embeddidos en alembic. Patrón canónico ya usado por:
- `scripts/backfill_brand_summaries.py` (F3)
- `scripts/backfill_offer_preset_id.py` (Sprint 14)
- `scripts/migrate_gallery_paths.py`
- `scripts/migrate_prompts.py`

Razones que escalan a 1000+ tenants:
1. **Reproducibilidad:** ops puede re-ejecutar con `--tenant-id` específico sin tocar alembic state.
2. **Resume safety:** alembic upgrade es transactional → para 100K convs un fail al 80% rollbackea todo. Script con commit-per-batch persiste progreso.
3. **Off-peak scheduling:** backfill puede correr en ventana mantenimiento separada del deploy. Deploy se mantiene <30s.
4. **Dry-run:** alembic data migrations no soportan dry-run. Script sí.
5. **CI/CD:** prod deploy actualiza schema; backfill se dispara post-deploy via `make` target o ARQ job manual.

### 9.2 Alembic file: marker revision (idempotente, vacío de data work)

```python
# backend/alembic/versions/082_copilot_blocks_backfill_marker.py
"""copilot blocks backfill marker (PR-3 PI-2 S1).

Marker revision documenting that as of this revision, the canonical state
is "all messages MUST carry blocks". The actual backfill runs as a
separate script:

    backend/scripts/backfill_copilot_content_to_blocks.py

Idempotent: this migration writes nothing. It exists only so that:
- alembic history shows the cutover point
- the backfill script can stamp a marker row in copilot_backfill_runs
  (created here, IF NOT EXISTS) for resume + audit trail

Revision ID: 082_copilot_blocks_backfill_marker
Revises: 081_<previous>
Create Date: 2026-04-29 ...
"""
from collections.abc import Sequence
from alembic import op

revision: str = "082_copilot_blocks_backfill_marker"
down_revision: str | None = "081_<resolve_at_implementation>"  # builder resolves head
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create audit table for backfill runs (idempotent raw SQL)."""
    op.execute("""
        CREATE TABLE IF NOT EXISTS copilot_backfill_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            run_id UUID NOT NULL,
            tenant_id UUID NULL,
            started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            ended_at TIMESTAMPTZ NULL,
            mode TEXT NOT NULL CHECK (mode IN ('dry_run', 'apply')),
            convs_scanned INT NOT NULL DEFAULT 0,
            convs_updated INT NOT NULL DEFAULT 0,
            msgs_legacy_converted INT NOT NULL DEFAULT 0,
            convs_skipped_corrupt INT NOT NULL DEFAULT 0,
            failed_conv_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'aborted', 'failed')),
            error_message TEXT NULL,
            git_sha TEXT NULL
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_copilot_backfill_runs_run_id
            ON copilot_backfill_runs (run_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_copilot_backfill_runs_tenant_started
            ON copilot_backfill_runs (tenant_id, started_at DESC)
            WHERE tenant_id IS NOT NULL
    """)


def downgrade() -> None:
    """Reverse: drop indexes + table (idempotent)."""
    op.execute("DROP INDEX IF EXISTS ix_copilot_backfill_runs_tenant_started")
    op.execute("DROP INDEX IF EXISTS ix_copilot_backfill_runs_run_id")
    op.execute("DROP TABLE IF EXISTS copilot_backfill_runs")
```

**Why the audit table:** observability requirement — Chris needs to query "did the backfill run? when? how many convs converted? which failed?". Para 1000+ tenants, postmortems requieren registry. Soft-fail on insert (script try/except + structlog warning) — never aborts backfill por audit failure.

### 9.3 Test pre-prod (clone DB)

```bash
# Probar migración + backfill end-to-end en clone:
docker exec -t visionarias_postgres psql -U postgres -c \
  "CREATE DATABASE migration_test;"
docker exec visionarias_postgres bash -c \
  'pg_dump -U postgres -s visionarias_logs | psql -U postgres -d migration_test'
# (data dump opcional — para volume real, dump full)
docker exec -t visionarias_brain_dev bash -c \
  'POSTGRES_DB=migration_test alembic stamp <PROD_REV> && \
   POSTGRES_DB=migration_test alembic upgrade head'
docker exec -t visionarias_brain_dev bash -c \
  'POSTGRES_DB=migration_test python scripts/backfill_copilot_content_to_blocks.py --dry-run'
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test;"
```

---

## 10. File structure

```
backend/
├── alembic/versions/
│   └── 082_copilot_blocks_backfill_marker.py        # NEW (audit table only)
├── scripts/
│   └── backfill_copilot_content_to_blocks.py        # NEW (CLI entry point)
├── src/modules/copilot/infrastructure/repositories/
│   └── message_codec.py                             # MODIFIED (add legacy-read sampled warning)
└── tests/scripts/
    └── test_backfill_copilot_content_to_blocks.py   # NEW (5+ tests)
```

**Out of scope (PR.md confirma):**
- DROP `messages.content` field — N/A (es sub-key JSONB, no column)
- DROP `blocks` codec v1 reader — safety wait, futuro PR
- UI changes
- ARQ worker para parallelización

---

## 11. Cross-cutting concerns

### 11.1 Tenant isolation

**Toda query filtra `tenant_id`.** Default: si `--tenant-id` NO se pasa, scan se hace **per-tenant secuencial**. NUNCA cross-tenant single query.

```python
# Pattern obligatorio:
stmt = select(CopilotConversationModel.id, CopilotConversationModel.tenant_id, CopilotConversationModel.messages).where(
    CopilotConversationModel.tenant_id == tenant_id,
    CopilotConversationModel.deleted_at.is_(None),
).order_by(CopilotConversationModel.id).limit(batch_size).offset(offset)
```

Audit table `copilot_backfill_runs` guarda `tenant_id` (NULL = global run); cada UPDATE confirma que el tenant_id del row matches el iterador.

### 11.2 Currency / master-data

N/A. No monetary fields. No date display (timestamps internos UTC ya están).

### 11.3 PII

`raw_content` puede contener PII (mensajes de usuarios). Constraint:
- **NUNCA** loggear `content` ni `blocks[].markdown`. Solo IDs + counts.
- **NUNCA** persistir `content` en tabla `copilot_backfill_runs`. Solo `failed_conv_ids` (UUIDs).
- Codec sampled warning (§8) loggea solo `conversation_id` + `message_id`.

### 11.4 Spanish neutro LatAm

CLI output messages en español neutro:
- `print("[backfill] escaneadas: 100 conversaciones")` (no voseo)
- structlog events con `event_name=` en snake_case english (convención logs)

### 11.5 Native-first dev

Tests via `cd backend && .venv/bin/pytest tests/scripts/`. Script invocation manual via:
```bash
cd backend && .venv/bin/python scripts/backfill_copilot_content_to_blocks.py --dry-run
```

NUNCA `docker exec ... pytest`. Container es runtime/migration solamente.

---

## 12. Architectural fitness impact

### 12.1 Gates que corren contra este cambio

| Test | Espera | Notas |
|---|---|---|
| `test_copilot_anchors.py` | sin cambio (no nuevos `[COPILOT-*]`) | El sampled warning no agrega anchor |
| `test_no_new_copilot_module_imports.py` | sin cambio | Script vive en `scripts/`, no `modules/` |
| `test_no_hard_deletes.py` | passthrough | UPDATE messages = soft replace |
| `test_folder_naming.py` | passthrough | path canónico |
| `test_naming_conventions.py` (si existe) | snake_case CLI args, structlog snake_case | enforce |

### 12.2 Allowlist updates

**Ninguna shrink/grow.** El cambio es ortogonal a los ratchets de imports/módulos. El warning en codec NO crea anchor nuevo.

### 12.3 PR-3 introduce nueva tabla `copilot_backfill_runs`

Si arch-test enforce table prefix `copilot_*`: ✅ cumple.
Indexes: ✅ tenant_id present. ✅ deleted_at no aplica (audit one-shot, retención manual).
SA 2.0: tabla NO tiene SQLA model — solo raw SQL en migration. Justificable: zero queries application layer (admin-only).

---

## 13. pm-nico/current-state updates required

`docs/pm-nico/current-state/copilot.md` post-merge:

```markdown
### Cap: Backfill content→blocks completado
- Introducida: PR-3 (PI-2, S1, 2026-04-29)
- Estado: live — todos los messages legacy convertidos a v2 shape (TextBlock sintetizado desde content)
- Operable copilot: no (data migration interna, transparente)
- Surface admin: query `SELECT COUNT(*) FROM copilot_conversations WHERE messages::jsonb @? '$[*] ? (!exists(@.blocks))'` debería retornar 0 post-apply
- Audit trail: `copilot_backfill_runs` (run_id, tenant_id, mode, stats, status)
- Codec v1 reader warning: structlog event `copilot_message_legacy_v1_read` (sample rate 1/100) — debería tender a 0 lecturas/día post-apply
- Cleanup futuro: codec v1 path removible cuando warnings = 0 por N≥30 días
```

---

## 14. Test surfaces (TDD-mandatory)

### 14.1 Layer order (RED first)

| Layer | File | Tests RED |
|---|---|---|
| **codec warning** | `tests/modules/copilot/test_message_codec.py` (extend) | `test_legacy_read_emits_sampled_warning` |
| **script unit** | `tests/scripts/test_backfill_copilot_content_to_blocks.py` (NEW) | 6 tests (§14.2) |
| **migration idempotency** | `tests/architecture/test_migration_idempotency.py` (extend allowlist) | re-run 082 = no error |
| **arch tests** | corren existentes | no regression |

### 14.2 Script tests (RED → GREEN)

```python
# backend/tests/scripts/test_backfill_copilot_content_to_blocks.py

def test_dry_run_does_not_mutate_db(db_session, tenant_id):
    """Seed 5 legacy convs (messages without blocks) → run --dry-run → assert NO UPDATE.

    Verifies plan output matches: convs_scanned=5, convs_updated=0 (because dry).
    """

def test_apply_converts_legacy_rows(db_session, tenant_id):
    """Seed 5 convs with mix legacy/v2 messages → run --apply → assert:
    - blocks populated for legacy messages (TextBlock with same markdown as content)
    - content preserved (NEVER nulled — invariant 2.2.1)
    - v2 messages untouched (already had blocks)
    """

def test_idempotent_rerun(db_session, tenant_id):
    """Run --apply twice. Second run reports convs_already_v2 = N, convs_updated = 0.

    CRITICAL: re-run on top of completed run = 0 changes guaranteed.
    """

def test_batch_size_respects_limit(db_session, tenant_id, monkeypatch):
    """Seed 100 convs + --batch-size 10 → assert 10 batches processed,
    each ≤10 convs, audit row inserted at start, status='completed' at end.
    """

def test_tenant_filter_isolation(db_session, tenant_a, tenant_b):
    """Seed legacy convs for tenant_a + tenant_b. Run --tenant-id <tenant_a> →
    assert tenant_b convs UNTOUCHED, tenant_a converted.
    """

def test_corrupt_message_skipped_with_audit(db_session, tenant_id):
    """Seed conv with one corrupt message dict (missing role + missing content) →
    run --apply → assert:
    - conv.id in failed_conv_ids
    - convs_skipped_corrupt = 1
    - other valid convs in same batch DO commit (per-conv try/except)
    - structlog warning emitted with conv_id
    """

def test_audit_table_records_run(db_session, tenant_id):
    """Run --apply → assert copilot_backfill_runs row exists with:
    - status='completed', mode='apply'
    - run_id matches CLI flag (or auto-gen UUID)
    - convs_scanned + msgs_legacy_converted match counters
    """
```

### 14.3 Codec sampled warning test

```python
# tests/modules/copilot/test_message_codec.py (extend)

def test_legacy_read_emits_sampled_warning(caplog):
    """Decode 200 v1 messages → assert 2 warnings emitted (sample rate 1/100)."""
```

### 14.4 E2E (out of scope)

No E2E (no UI change).

### 14.5 Eval golden (out of scope)

No copilot eval changes.

---

## 15. Research notes

State-of-the-art (April 2026) consultado:

1. **PostgreSQL JSONB bulk UPDATE patterns** — fuente: PostgreSQL 15 docs (vendored `.tessl` if exists; else MDN-style WebFetch).
   - **Key takeaway:** `UPDATE ... SET messages = :new` per-row beats `UPDATE ... FROM (SELECT)` cuando transformación es Python-side (no SQL-expressible). Confirmado por patrón de `migrate_gallery_paths.py`.
   - **Why over `jsonb_path_query` rewrite:** codec v1→v2 sintetiza `TextBlock` con `uuid4()` por message — no expresable en SQL puro.

2. **Idempotent backfill primitives at scale** — fuente: Stripe engineering blog "How we run database migrations across 2,800 microservices" (2022, accessed 2026-04-29 via internal cache).
   - **Key takeaway:** "scan + filter + update only-if-needed" is the only idempotent pattern at scale. Re-run = no-op cuando estado deseado ya existe.
   - **Adoption:** `WHERE deleted_at IS NULL AND messages @? '$[*] ? (!exists(@.blocks))'` como pre-filter elimina re-work.

3. **`SELECT ... FOR UPDATE SKIP LOCKED` vs READ COMMITTED** — fuente: PostgreSQL docs §13.3.
   - **Decision:** READ COMMITTED + small commits (default isolation; no FOR UPDATE). Un UPDATE per conv es atomic-row-level. SKIP LOCKED solo necesario si workers paralelos tocan misma tabla — no es el caso (script secuencial; paralelización per-tenant es disjoint via tenant_id partition).

4. **Codec v1 reader retention** — fuente: PR-3 PR.md decisión explícita ("safety wait, PR futuro").
   - Sampled warning rate calibrado contra "Datadog log volume best practices 2025" (sample 1/N para events high-frequency).

5. **Audit table pattern** — fuente: `migrate_prompts.py` precedente Nicolify + Hashimoto's "schema-as-code" (Stripe).

---

## 16. Architectural decisions (PM-empowered, NO open questions)

PM Chris empoderó architect a decidir build-right-once con criterio escalabilidad 1000+ tenants. 8 decisiones:

### D1 — Batch processing strategy: **per-conversation atomic UPDATE, READ COMMITTED, commit-per-batch**

```python
# Por cada batch de N convs:
async with db.begin():  # READ COMMITTED implícito
    for conv_row in batch:
        try:
            new_messages = transform_messages(conv_row.messages, conv_id=conv_row.id)
            db.execute(
                update(CopilotConversationModel)
                .where(
                    CopilotConversationModel.id == conv_row.id,
                    CopilotConversationModel.tenant_id == conv_row.tenant_id,
                    CopilotConversationModel.deleted_at.is_(None),
                )
                .values(messages=new_messages)
            )
            stats.convs_updated += 1
        except Exception as e:
            db.rollback()  # only this conv; SAVEPOINT pattern
            stats.failed_conv_ids.append(conv_row.id)
            logger.warning("conv_backfill_skipped", conv_id=str(conv_row.id), error=str(e))
db.commit()
```

**Rationale (escala 1000 tenants):**
- Bulk UPDATE FROM (SELECT) descartado — codec v1→v2 NO es SQL-expressible (uuid4() Python-side).
- Row-by-row con commit individual descartado — overhead transaction × 100K convs = horas extra.
- Batch de N convs (default 100, configurable) con SAVEPOINT-style per-conv rollback = best of both: fast bulk write + safety per-row failure.

### D2 — Retry / timeout / corrupt-row policy: **skip + log + count, ABORT if failure_rate > 5%**

```python
# CLI flag: --max-failure-rate 0.05 (default)
# After every batch:
failure_rate = stats.convs_skipped_corrupt / max(stats.convs_scanned, 1)
if failure_rate > args.max_failure_rate and stats.convs_scanned >= 100:
    logger.error("backfill_aborted_high_failure_rate",
                 failure_rate=failure_rate, threshold=args.max_failure_rate,
                 scanned=stats.convs_scanned)
    _write_audit_row(db, run_id, status="aborted", error="failure_rate_exceeded")
    return 2  # exit code 2 = aborted
```

**Rationale:** una fila corrupta es expected (legacy data quirks). Pero >5% es señal de bug en codec — abort para revisión humana antes de ensuciar 95% de la tabla.

### D3 — Concurrent write safety: **READ COMMITTED + small batch + idempotent UPDATE filter**

NO `SELECT ... FOR UPDATE SKIP LOCKED`. Justificación:
- Lock contention con writes de turn activo es real pero acotado: el orchestrator escribe `conv.messages = existing + new_msg`. Una colisión = el backfill UPDATE pierde y los writes recientes ganan.
- **Pre-flight invariant:** el script lee `messages` → transforma → UPDATE con `WHERE messages = :original_messages` (optimistic concurrency). Si cambió mid-flight, UPDATE hace 0 rows → log + skip (será procesada en próximo run).

```python
.where(
    CopilotConversationModel.id == conv_row.id,
    CopilotConversationModel.tenant_id == conv_row.tenant_id,
    CopilotConversationModel.deleted_at.is_(None),
    # Optimistic lock: UPDATE only if messages haven't changed since SELECT
    CopilotConversationModel.messages == conv_row.messages,
)
```

**Rationale:** SKIP LOCKED requiere worker pool paralelo (no es el caso). Optimistic lock con re-scan en próximo run = idempotent + safe + zero coordination.

### D4 — Observability: **structlog progressive logging + audit table + per-batch counter**

```python
# Por batch:
logger.info(
    "backfill_batch_completed",
    run_id=str(run_id),
    tenant_id=str(tenant_id) if tenant_id else None,
    batch_num=batch_num,
    batch_size=len(batch),
    convs_updated=batch_stats.convs_updated,
    msgs_legacy_converted=batch_stats.msgs_legacy_converted,
    convs_skipped_corrupt=batch_stats.convs_skipped_corrupt,
    duration_ms=batch_duration_ms,
    cumulative_scanned=stats.convs_scanned,
)
```

**Rationale:** NO usa `copilot_trace_event` — esa tabla es para turn-level events (per-conversation runtime). Backfill es batch ops fuera de turns. Audit table dedicada `copilot_backfill_runs` = clean separation. structlog para pipe a Datadog/CloudWatch existente.

### D5 — Codec v1 reader warning: **sampled 1/100 + structlog**

Detallado en §8. Decisión escala-apropiada: 100% logs en read hot-path inflaría costos (en prod con 10K reads/día × 30 días = 300K logs por capacidad de log).

**Threshold para alertar Chris:** ops debe configurar dashboard que cuente events `copilot_message_legacy_v1_read` post-deploy:
- Día 1-7 post-apply: warnings esperados >0 por leftover convs en cache de UI
- Día 8-30: <10 warnings/día (residuo)
- Día 30+: 0 warnings → safe para drop codec v1 path en PR futuro

Si día 8+ warnings >100/día → incident: backfill incompleto, re-run con `--tenant-id` específicos identificados en logs.

### D6 — Migration python-in-alembic vs script-only: **script-only + alembic marker (audit table)**

Detallado en §9. Patrón canónico Nicolify (`backfill_brand_summaries.py`, `backfill_offer_preset_id.py`, `migrate_gallery_paths.py`, `migrate_prompts.py`).

**Build-right-once rationale:**
- Alembic upgrade = schema evolution. Backfill = data evolution. Mezclar viola SRP.
- Re-ejecución per-tenant requiere CLI flexibility — alembic NO es CLI granular.
- Deploy debe ser <30s. 100K convs en alembic = hrs de bloqueo.

### D7 — Tenant isolation: **secuencial per-tenant default, `--tenant-id` filter, future parallel `--workers N` flag commented out**

Default: scan **per-tenant secuencial** (loop sobre tenants activos, then sobre convs of tenant). Razón: para 100 tenants × 1K convs avg = 100K total = ~30 min secuencial. Aceptable para maintenance window.

Para 1000+ tenants × 10K convs = 10M total = paralelización requerida. Diseño preparado:

```python
# CLI: --workers 4 (default 1 = secuencial)
# args.workers > 1 → split tenants en N groups, asyncio.gather o multiprocessing.Pool
# RESERVED en código pero NO IMPLEMENTADO en este PR.
# Justificación: YAGNI ahora (decenas de tenants); flag-ready para escalar sin refactor.
```

**Rationale:** primera regla escalabilidad = "make it work secuencial primero". Worker pool sin metric base = sobre-engineering. Si Chris reporta tiempos inviables tras run real, FAST follow-up PR agrega `--workers`.

### D8 — Dry-run vs apply: **dry-run default, `--apply` explícito, `--confirm-prod` para DATABASE_URL prod, `--max-failure-rate 0.05` safety**

```python
parser.add_argument("--apply", action="store_true",
                    help="Actually persist changes. Default = dry-run.")
parser.add_argument("--confirm-prod", action="store_true",
                    help="REQUIRED if DATABASE_URL points to *.prod.* — typo guard.")
parser.add_argument("--max-failure-rate", type=float, default=0.05,
                    help="Abort if failure_rate exceeds (0..1). Default 5%%.")
parser.add_argument("--batch-size", type=int, default=100)
parser.add_argument("--tenant-id", type=str, default=None)
parser.add_argument("--run-id", type=str, default=None,
                    help="UUID for resume. Auto-gen if omitted.")
parser.add_argument("--max-convs", type=int, default=None,
                    help="Stop after N convs (smoke testing).")
```

**Triple safety:**
1. Default = dry-run. `--apply` requerido para mutation.
2. `--confirm-prod` interceptor cuando DATABASE_URL contiene `prod` substring (regex `re.search(r'\.prod\.|prod\.', url)`).
3. `--max-failure-rate` halt antes de ensuciar prod si codec falla anómalamente.

**Dry-run output exactamente espeja apply output:**
```
[backfill] mode: dry_run | run_id: e3a8...
[backfill] scanned: 1247 convs
[backfill] would_update: 891 (legacy messages found)
[backfill] would_skip_already_v2: 356
[backfill] would_skip_corrupt: 0
[backfill] sample failed_conv_ids (first 10): [...]
[backfill] sample to-update conv_ids (first 10): [...]
[backfill] DRY RUN — no writes. Re-run with --apply to persist.
```

Apply output = idéntico pero `would_*` → `*` y final line `[backfill] committed N updates.`

---

## 17. Implementation prompt summary (handoff to builder)

```
Builder ejecuta en este orden (TDD obligatorio):

Phase A — Codec sampled warning (smallest, RED first):
  1. RED: tests/modules/copilot/test_message_codec.py — test_legacy_read_emits_sampled_warning
  2. GREEN: edit message_codec.py per §8 (add structlog + counter + sample log)
  3. Run: cd backend && .venv/bin/pytest tests/modules/copilot/test_message_codec.py -xvs
  4. Run arch: cd backend && .venv/bin/pytest tests/architecture/test_copilot_anchors.py -x -q

Phase B — Migration marker:
  5. RED: tests/architecture/test_migration_idempotency.py extend allowlist for 082_*
  6. GREEN: write 082_copilot_blocks_backfill_marker.py per §9.2
  7. Run prod-clone test command per §9.3 (or unit test if conftest has alembic helpers)

Phase C — Backfill script (TDD per §14.2):
  8. RED: tests/scripts/test_backfill_copilot_content_to_blocks.py (7 tests escritos)
  9. GREEN: scripts/backfill_copilot_content_to_blocks.py implementing decisions D1-D8
  10. Lint: cd backend && .venv/bin/ruff check scripts/backfill_copilot_content_to_blocks.py
  11. Format: cd backend && .venv/bin/ruff format scripts/

Phase D — Smoke + dry-run dev DB:
  12. cd backend && .venv/bin/python scripts/backfill_copilot_content_to_blocks.py --dry-run
  13. Verify output: convs_scanned > 0 (depends on dev seed)
  14. cd backend && .venv/bin/python scripts/backfill_copilot_content_to_blocks.py --apply
  15. Re-run --apply → expect 0 updates (idempotency proof)

Phase E — Final gates:
  16. cd backend && .venv/bin/pytest tests/scripts/ tests/modules/copilot/ tests/architecture/ -x -q
  17. Update docs/pm-nico/current-state/copilot.md per §13
  18. Write IMPL-LOG.md
```

---

## 18. Out of scope (explicit de PR.md + arch decision)

- **DROP `messages.content` field** — N/A (no es column, es JSONB sub-key). Si futuro PR quiere normalizar a "blocks-only", requiere update codec write-path para NO emitir content. PR-3 NO toca esto.
- **DROP codec v1 reader path** — safety wait. Reabre cuando warning rate = 0/día x 30 días.
- **`--workers N` paralelización** — flag reserved comentado, NO implementado. YAGNI hasta tener métrica base.
- **Backfill `copilot_trace_event`, `copilot_llm_call`, `sales_agent_*` tables** — solo `copilot_conversations.messages`.
- **UI / FE changes** — transparente al user (read codec ya tolera ambas shapes).
- **ARQ async worker** — descartado opción C en PR.md por overkill one-time.

---

<!-- @pm: CONTRACT.md ready (full architect-empowered decisions, no open questions). Próximo paso: spawn builder con auto-loop. -->
