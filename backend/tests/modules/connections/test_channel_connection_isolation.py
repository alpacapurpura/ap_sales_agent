"""Tenant isolation tests for ChannelConnectionRepository.

Proves that Tenant B cannot see or retrieve data belonging to Tenant A.
"""
import uuid

from sqlalchemy.orm import Session

from src.modules.connections.domain.enums import ChannelType
from src.modules.connections.infrastructure.models.channel_connection_model import (
    ChannelConnectionModel,
)
from src.modules.connections.infrastructure.repositories.channel_connection_repository import (
    ChannelConnectionRepository,
)

TENANT_A = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")


def _create_connection(
    db: Session,
    tenant_id: uuid.UUID,
    channel_type: ChannelType = ChannelType.TELEGRAM,
    is_active: bool = True,
) -> ChannelConnectionModel:
    conn = ChannelConnectionModel(
        tenant_id=tenant_id,
        channel_type=channel_type.value,
        credentials={},
        config={"note": f"tenant_{tenant_id}"},
        is_active=is_active,
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


class TestGetActiveTenantIsolation:
    def test_tenant_b_cannot_see_tenant_a_active_connection(self, db: Session):
        _create_connection(db, TENANT_A, ChannelType.TELEGRAM, is_active=True)
        repo = ChannelConnectionRepository(db)

        result = repo.get_active(TENANT_B, ChannelType.TELEGRAM)
        assert result is None

    def test_tenant_a_sees_own_active_connection(self, db: Session):
        _create_connection(db, TENANT_A, ChannelType.TELEGRAM, is_active=True)
        repo = ChannelConnectionRepository(db)

        result = repo.get_active(TENANT_A, ChannelType.TELEGRAM)
        assert result is not None
        assert result.tenant_id == TENANT_A


class TestGetByTenantAndTypeTenantIsolation:
    def test_tenant_b_cannot_get_tenant_a_connection(self, db: Session):
        _create_connection(db, TENANT_A, ChannelType.WHATSAPP)
        repo = ChannelConnectionRepository(db)

        result = repo.get_by_tenant_and_type(TENANT_B, ChannelType.WHATSAPP)
        assert result is None

    def test_tenant_a_can_get_own_connection(self, db: Session):
        _create_connection(db, TENANT_A, ChannelType.WHATSAPP)
        repo = ChannelConnectionRepository(db)

        result = repo.get_by_tenant_and_type(TENANT_A, ChannelType.WHATSAPP)
        assert result is not None
        assert result.tenant_id == TENANT_A


class TestGetAllByTenantTenantIsolation:
    def test_tenant_b_list_returns_empty_when_only_tenant_a_data(self, db: Session):
        _create_connection(db, TENANT_A, ChannelType.TELEGRAM)
        _create_connection(db, TENANT_A, ChannelType.WHATSAPP)
        repo = ChannelConnectionRepository(db)

        results = repo.get_all_by_tenant(TENANT_B)
        assert len(results) == 0

    def test_tenant_a_list_excludes_tenant_b_data(self, db: Session):
        _create_connection(db, TENANT_A, ChannelType.TELEGRAM)
        _create_connection(db, TENANT_B, ChannelType.TELEGRAM)
        repo = ChannelConnectionRepository(db)

        results_a = repo.get_all_by_tenant(TENANT_A)
        assert len(results_a) == 1
        assert all(r.tenant_id == TENANT_A for r in results_a)

        results_b = repo.get_all_by_tenant(TENANT_B)
        assert len(results_b) == 1
        assert all(r.tenant_id == TENANT_B for r in results_b)


class TestGetAllByTenantAndTypesTenantIsolation:
    def test_tenant_b_cannot_see_tenant_a_connections_by_types(self, db: Session):
        _create_connection(db, TENANT_A, ChannelType.META)
        _create_connection(db, TENANT_A, ChannelType.GOOGLE_ANALYTICS)
        repo = ChannelConnectionRepository(db)

        results = repo.get_all_by_tenant_and_types(
            TENANT_B, [ChannelType.META, ChannelType.GOOGLE_ANALYTICS]
        )
        assert len(results) == 0

    def test_tenant_a_sees_only_own_connections_by_types(self, db: Session):
        _create_connection(db, TENANT_A, ChannelType.META)
        _create_connection(db, TENANT_B, ChannelType.META)
        repo = ChannelConnectionRepository(db)

        results = repo.get_all_by_tenant_and_types(TENANT_A, [ChannelType.META])
        assert len(results) == 1
        assert results[0].tenant_id == TENANT_A
