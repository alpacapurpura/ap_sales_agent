"""Soft-delete tests for ChannelConnectionRepository.

Verifies that deleted_at filtering works correctly across all query methods,
and that the delete() method performs a soft-delete (not hard-delete).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.modules.connections.domain.enums import ChannelType
from src.modules.connections.infrastructure.models.channel_connection_model import (
    ChannelConnectionModel,
)
from src.modules.connections.infrastructure.repositories.channel_connection_repository import (
    ChannelConnectionRepository,
)

TENANT = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")


def _create_connection(
    db: Session,
    tenant_id: uuid.UUID,
    channel_type: ChannelType = ChannelType.TELEGRAM,
    is_active: bool = True,
    deleted_at: datetime | None = None,
) -> ChannelConnectionModel:
    conn = ChannelConnectionModel(
        tenant_id=tenant_id,
        channel_type=channel_type.value,
        credentials={},
        config={"note": f"tenant_{tenant_id}"},
        is_active=is_active,
        deleted_at=deleted_at,
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


class TestSoftDeleteExclusion:
    def test_soft_deleted_excluded_from_get_by_tenant_and_type(self, db: Session):
        _create_connection(
            db,
            TENANT,
            ChannelType.WHATSAPP,
            deleted_at=datetime.now(timezone.utc),
        )
        repo = ChannelConnectionRepository(db)

        result = repo.get_by_tenant_and_type(TENANT, ChannelType.WHATSAPP)
        assert result is None

    def test_soft_deleted_excluded_from_get_all_by_tenant(self, db: Session):
        _create_connection(db, TENANT, ChannelType.TELEGRAM)
        _create_connection(
            db,
            TENANT,
            ChannelType.WHATSAPP,
            deleted_at=datetime.now(timezone.utc),
        )
        repo = ChannelConnectionRepository(db)

        results = repo.get_all_by_tenant(TENANT)
        assert len(results) == 1
        assert results[0].channel_type == ChannelType.TELEGRAM.value

    def test_soft_deleted_excluded_from_get_all_by_tenant_and_types(self, db: Session):
        _create_connection(db, TENANT, ChannelType.META)
        _create_connection(
            db,
            TENANT,
            ChannelType.GOOGLE_ANALYTICS,
            deleted_at=datetime.now(timezone.utc),
        )
        repo = ChannelConnectionRepository(db)

        results = repo.get_all_by_tenant_and_types(
            TENANT,
            [ChannelType.META, ChannelType.GOOGLE_ANALYTICS],
        )
        assert len(results) == 1
        assert results[0].channel_type == ChannelType.META.value


class TestDeleteMethod:
    def test_delete_sets_deleted_at_and_deactivates(self, db: Session):
        conn = _create_connection(db, TENANT, ChannelType.TELEGRAM)
        repo = ChannelConnectionRepository(db)

        repo.delete(conn)
        db.commit()
        db.refresh(conn)

        assert conn.deleted_at is not None
        assert conn.is_active is False

    def test_delete_preserves_row(self, db: Session):
        conn = _create_connection(db, TENANT, ChannelType.TELEGRAM)
        conn_id = conn.id
        repo = ChannelConnectionRepository(db)

        repo.delete(conn)
        db.commit()

        row = db.get(ChannelConnectionModel, conn_id)
        assert row is not None

    def test_get_active_excludes_soft_deleted(self, db: Session):
        conn = _create_connection(db, TENANT, ChannelType.TELEGRAM, is_active=True)
        repo = ChannelConnectionRepository(db)

        repo.delete(conn)
        db.commit()

        result = repo.get_active(TENANT, ChannelType.TELEGRAM)
        assert result is None
