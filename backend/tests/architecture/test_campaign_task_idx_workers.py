"""Architectural fitness — worker queue partial index exists in migration DDL.

Lee el archivo de migración ``112_campaigns_domain.py`` y verifica:
1. Contiene ``CREATE INDEX IF NOT EXISTS ix_campaign_task_worker_queue``
   con ``WHERE status IN ('pending','scheduled')`` (partial idx worker queue).
2. Contiene constraint ``uq_campaign_task_tenant_idem`` UNIQUE sobre
   ``(tenant_id, idempotency_key)``.
3. El orden de columnas en el worker queue idx es
   ``(tenant_id, status, scheduled_at)`` — crítico para query plan.

Rationale: con 1000 tenants y 10k tareas/tenant, sin el partial idx el
worker poll degrada O(N) full scan sobre ``campaign_task``. El índice reduce
el scan a solo las filas pendientes/scheduled (típicamente <5% del total).

Sin el unique constraint ``(tenant_id, idempotency_key)``, bulk inserts en
el launch orchestrator pueden crear duplicados en condición de race.

# [CAMPAIGNS-WORKER-IDX-PR3-S1]
"""

from __future__ import annotations

from pathlib import Path

# parents[2] = REPO root when running from backend/ (tests/architecture/ -> tests/ -> backend/)
# parents[3] = workspace root when running from project root
_THIS_DIR = Path(__file__).resolve()
_CANDIDATE_PATHS = [
    _THIS_DIR.parents[2] / "alembic" / "versions" / "112_campaigns_domain.py",
    _THIS_DIR.parents[3] / "backend" / "alembic" / "versions" / "112_campaigns_domain.py",
]
MIGRATION_FILE = next((p for p in _CANDIDATE_PATHS if p.exists()), _CANDIDATE_PATHS[0])


def _get_migration_content() -> str:
    for candidate in _CANDIDATE_PATHS:
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
    msg = "Migration 112_campaigns_domain.py no encontrada. Verificar que el commit de migración existe."
    raise FileNotFoundError(msg)


class TestCampaignTaskWorkerQueueIndex:
    """Verifica que el migration DDL incluye índices críticos para el worker."""

    def test_worker_queue_partial_index_exists(self) -> None:
        """DDL debe crear el partial index para el worker queue."""
        content = _get_migration_content()
        assert "ix_campaign_task_worker_queue" in content, (
            "Migration 112_campaigns_domain.py debe crear el índice "
            "ix_campaign_task_worker_queue. Este índice es crítico para performance "
            "del worker con 1000+ tenants."
        )

    def test_worker_queue_index_has_where_clause(self) -> None:
        """Partial index debe filtrar solo status pending/scheduled."""
        content = _get_migration_content()
        # Buscar la combinación: el índice + la cláusula WHERE
        assert "WHERE status IN ('pending','scheduled')" in content, (
            "El índice ix_campaign_task_worker_queue DEBE ser un partial index "
            "con WHERE status IN ('pending','scheduled'). Sin esta cláusula, "
            "el índice crece O(N) con todos los tasks históricos."
        )

    def test_worker_queue_index_column_order(self) -> None:
        """El worker query ordena por (tenant_id, status, scheduled_at)."""
        content = _get_migration_content()
        # El índice debe tener las 3 columnas en el orden correcto
        # para soportar el query: WHERE status IN (...) AND scheduled_at <= :now
        assert "tenant_id, status, scheduled_at" in content, (
            "El índice ix_campaign_task_worker_queue debe tener columnas en orden "
            "(tenant_id, status, scheduled_at). Este orden es crítico para el "
            "query plan del worker poll."
        )

    def test_idempotency_unique_constraint_exists(self) -> None:
        """DDL debe crear el unique constraint para idempotency."""
        content = _get_migration_content()
        assert "uq_campaign_task_tenant_idem" in content, (
            "Migration debe crear constraint uq_campaign_task_tenant_idem "
            "UNIQUE (tenant_id, idempotency_key). Sin este constraint, "
            "bulk inserts en campaign launch pueden crear tasks duplicados."
        )

    def test_idempotency_constraint_covers_correct_columns(self) -> None:
        """Unique constraint debe cubrir (tenant_id, idempotency_key)."""
        content = _get_migration_content()
        assert "tenant_id, idempotency_key" in content, (
            "Unique constraint uq_campaign_task_tenant_idem debe cubrir "
            "(tenant_id, idempotency_key) para deduplicación cross-tenant safe."
        )

    def test_migration_revision_is_correct(self) -> None:
        """Verifica que el archivo es la revisión esperada."""
        content = _get_migration_content()
        assert 'revision: str = "112_campaigns_domain"' in content, (
            "Archivo de migración debe declarar revision = '112_campaigns_domain'"
        )

    def test_migration_down_revision_chains_correctly(self) -> None:
        """La migración debe encadenarse correctamente desde el head anterior."""
        content = _get_migration_content()
        assert "111_copilot_blocks_backfill_marker" in content, (
            "down_revision debe apuntar a '111_copilot_blocks_backfill_marker' para cadena de migraciones correcta."
        )

    def test_six_tables_created(self) -> None:
        """DDL debe crear las 6 tablas del dominio campaigns."""
        content = _get_migration_content()
        tables = [
            "CREATE TABLE IF NOT EXISTS campaign (",
            "CREATE TABLE IF NOT EXISTS campaign_step (",
            "CREATE TABLE IF NOT EXISTS campaign_task (",
            "CREATE TABLE IF NOT EXISTS segment (",
            "CREATE TABLE IF NOT EXISTS segment_snapshot (",
            "CREATE TABLE IF NOT EXISTS campaign_template (",
        ]
        missing = [t for t in tables if t not in content]
        assert not missing, "Migration debe crear las 6 tablas del dominio campaigns. Faltantes: " + str(missing)
