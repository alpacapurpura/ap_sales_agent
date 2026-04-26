"""TP5-B7 regression: ``_check_offer_completion`` must use real product columns.

Bug context (TP5 2026-04-26 S5.6):
- Tool ``get_module_completion_status`` in ``/brand-studio`` chat turn raised
  ``UndefinedColumn: column "is_active" does not exist``. The ``products``
  table tracks lifecycle via ``status`` + ``deleted_at`` + ``archived_at``;
  ``is_active`` was never a column. The narrow ``except (TypeError, ValueError)``
  could not catch ``SQLAlchemyError`` so the chat turn 500'd.

Fix invariants:
1. SQL filter aligns with the partial index ``ix_products_active_by_tenant``
   semantics: ``deleted_at IS NULL AND archived_at IS NULL``.
2. Any SQLAlchemy error returns a graceful ``configured=False`` dict instead
   of bubbling up — chat turns must NOT 500 on schema drift.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import text

from src.modules.copilot.application.tools.awareness import _check_offer_completion


@pytest.fixture
def tenant_id():
    return uuid4()


def _insert_product(db, tenant_id, *, deleted_at=None, archived_at=None, name="P"):
    db.execute(
        text(
            """
            INSERT INTO products (id, tenant_id, name, archetype, status, deleted_at, archived_at)
            VALUES (:id, :tid, :name, 'service', 'active', :deleted_at, :archived_at)
            """
        ),
        {
            "id": str(uuid4()),
            "tid": str(tenant_id),
            "name": name,
            "deleted_at": deleted_at,
            "archived_at": archived_at,
        },
    )
    db.commit()


class TestCheckOfferCompletion:
    def test_counts_only_alive_unarchived_products(self, db, tenant_id):
        # 1 alive (counts), 1 archived (skipped), 1 soft-deleted (skipped).
        _insert_product(db, tenant_id, name="alive")
        _insert_product(db, tenant_id, name="archived", archived_at="2026-01-01")
        _insert_product(db, tenant_id, name="deleted", deleted_at="2026-01-01")

        result = _check_offer_completion(db, tenant_id)

        assert result["configured"] is True
        assert "1 oferta" in result["markdown"]

    def test_zero_products_returns_unconfigured(self, db, tenant_id):
        result = _check_offer_completion(db, tenant_id)

        assert result["configured"] is False
        assert "Sin ofertas" in result["markdown"]

    def test_only_soft_deleted_returns_unconfigured(self, db, tenant_id):
        _insert_product(db, tenant_id, deleted_at="2026-01-01")

        result = _check_offer_completion(db, tenant_id)

        assert result["configured"] is False

    def test_handles_sqlalchemy_error_gracefully(self, db, tenant_id, monkeypatch):
        """Schema drift / undefined column must NOT 500 the chat turn."""
        from sqlalchemy.exc import SQLAlchemyError

        msg = "simulated schema drift"

        def boom(*args, **kwargs):
            raise SQLAlchemyError(msg)

        monkeypatch.setattr(db, "execute", boom)
        result = _check_offer_completion(db, tenant_id)

        assert result["configured"] is False
        assert "markdown" in result
