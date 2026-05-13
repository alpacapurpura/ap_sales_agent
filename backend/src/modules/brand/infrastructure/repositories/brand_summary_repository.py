"""Brand summary repository.

CRUD over ``brand_summary`` (lighthouse table). Tenant-scoped; one row
per tenant. ``upsert`` bumps ``version`` atomically when an existing
row is updated.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from luana_core_brand_studio.infrastructure.models.brand_summary_model import (
    BrandSummaryModel,
)
from luana_core_platform.domain.datetime_utils import utc_now
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger()


class BrandSummaryRepository:
    """Repository for brand summary lighthouse."""

    def __init__(self, db: Session) -> None:
        """Bind a SQLAlchemy session."""
        self.db = db

    def upsert(
        self,
        *,
        tenant_id: UUID,
        summary: str,
        model_used: str,
        last_section_changed: str | None = None,
    ) -> BrandSummaryModel:
        """Insert (version=1) or update (version+1) by ``tenant_id``.

        ``index_elements=["tenant_id"]`` keeps the SQL portable across
        the SQLite test conftest and Postgres prod (named-constraint
        upserts blow up on SQLite — see learnings/F2).
        """
        now = utc_now()
        chars_count = len(summary)
        stmt = (
            pg_insert(BrandSummaryModel)
            .values(
                tenant_id=tenant_id,
                summary=summary,
                version=1,
                model_used=model_used,
                chars_count=chars_count,
                last_section_changed=last_section_changed,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=["tenant_id"],
                set_={
                    "summary": summary,
                    "version": BrandSummaryModel.version + 1,
                    "model_used": model_used,
                    "chars_count": chars_count,
                    "last_section_changed": last_section_changed,
                    "updated_at": now,
                },
            )
            .returning(BrandSummaryModel)
        )
        row = self.db.execute(stmt).scalar_one()
        self.db.flush()
        return row

    def get(self, *, tenant_id: UUID) -> BrandSummaryModel | None:
        """Fetch the single brand summary for ``tenant_id`` (or ``None``)."""
        stmt = select(BrandSummaryModel).where(
            BrandSummaryModel.tenant_id == tenant_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_all(self) -> list[BrandSummaryModel]:
        """Return every summary (admin Streamlit consumer — not tenant-bound)."""
        stmt = select(BrandSummaryModel).order_by(
            BrandSummaryModel.updated_at.desc(),
        )
        return list(self.db.execute(stmt).scalars().all())
