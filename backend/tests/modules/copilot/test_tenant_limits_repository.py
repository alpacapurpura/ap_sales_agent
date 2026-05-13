"""Unit tests for CopilotTenantLimitsRepository (sync implementation).

Uses MagicMock session for fast unit tests (no Postgres required).
Integration tests with real DB are in test_media_db_roundtrip.py.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from luana_core_copilot.domain.tenant_limits import CopilotTenantLimits
from luana_core_copilot.infrastructure.models.tenant_limits_model import (
    CopilotTenantLimitsModel,
)
from luana_core_copilot.infrastructure.repositories.tenant_limits_repository import (
    SyncCopilotTenantLimitsRepository,
    _model_to_domain,
)


def _make_model(**kwargs: object) -> CopilotTenantLimitsModel:
    """Build a stub ORM model."""
    model = MagicMock(spec=CopilotTenantLimitsModel)
    model.tenant_id = kwargs.get("tenant_id", uuid4())
    model.voice_rpm_override = kwargs.get("voice_rpm_override")
    model.media_max_bytes_override = kwargs.get("media_max_bytes_override")
    model.updated_at = kwargs.get("updated_at", datetime.now(timezone.utc))
    model.updated_by_user_id = kwargs.get("updated_by_user_id")
    model.deleted_at = kwargs.get("deleted_at")
    return model


class TestModelToDomain:
    """Tests for the _model_to_domain mapping helper."""

    def test_maps_all_fields(self) -> None:
        tenant_id = uuid4()
        updated_at = datetime.now(timezone.utc)
        model = _make_model(
            tenant_id=tenant_id,
            voice_rpm_override=10,
            media_max_bytes_override=50 * 1024 * 1024,
            updated_at=updated_at,
        )
        domain = _model_to_domain(model)
        assert domain.tenant_id == tenant_id
        assert domain.voice_rpm_override == 10
        assert domain.media_max_bytes_override == 50 * 1024 * 1024
        assert domain.updated_at == updated_at
        assert domain.deleted_at is None

    def test_none_overrides_preserved(self) -> None:
        model = _make_model(voice_rpm_override=None, media_max_bytes_override=None)
        domain = _model_to_domain(model)
        assert domain.voice_rpm_override is None
        assert domain.media_max_bytes_override is None


class TestSyncRepositoryGetByTenant:
    """Tests for SyncCopilotTenantLimitsRepository.get_by_tenant."""

    def test_returns_none_when_no_row(self) -> None:
        session = MagicMock()
        cursor = MagicMock()
        cursor.scalar_one_or_none.return_value = None
        session.execute.return_value = cursor

        repo = SyncCopilotTenantLimitsRepository(session)
        result = repo.get_by_tenant(uuid4())
        assert result is None

    def test_returns_domain_entity_when_row_exists(self) -> None:
        tenant_id = uuid4()
        model = _make_model(tenant_id=tenant_id, voice_rpm_override=15)

        session = MagicMock()
        cursor = MagicMock()
        cursor.scalar_one_or_none.return_value = model
        session.execute.return_value = cursor

        repo = SyncCopilotTenantLimitsRepository(session)
        result = repo.get_by_tenant(tenant_id)
        assert result is not None
        assert result.tenant_id == tenant_id
        assert result.voice_rpm_override == 15


class TestSyncRepositoryListOverrides:
    """Tests for SyncCopilotTenantLimitsRepository.list_overrides."""

    def test_returns_empty_list_when_no_rows(self) -> None:
        session = MagicMock()
        cursor = MagicMock()
        cursor.scalars.return_value.all.return_value = []
        session.execute.return_value = cursor

        repo = SyncCopilotTenantLimitsRepository(session)
        result = repo.list_overrides()
        assert result == []

    def test_returns_list_of_domain_entities(self) -> None:
        model1 = _make_model(voice_rpm_override=10)
        model2 = _make_model(media_max_bytes_override=30 * 1024 * 1024)

        session = MagicMock()
        cursor = MagicMock()
        cursor.scalars.return_value.all.return_value = [model1, model2]
        session.execute.return_value = cursor

        repo = SyncCopilotTenantLimitsRepository(session)
        result = repo.list_overrides()
        assert len(result) == 2
        assert all(isinstance(r, CopilotTenantLimits) for r in result)


class TestSyncRepositoryUpsert:
    """Tests for SyncCopilotTenantLimitsRepository.upsert."""

    def test_upsert_creates_new_row_when_none_exists(self) -> None:
        session = MagicMock()
        # First execute (get existing) returns None
        cursor_get = MagicMock()
        cursor_get.scalar_one_or_none.return_value = None
        session.execute.return_value = cursor_get

        repo = SyncCopilotTenantLimitsRepository(session)
        tenant_id = uuid4()
        repo.upsert(
            tenant_id,
            voice_rpm_override=20,
            media_max_bytes_override=None,
            updated_by_user_id=None,
        )

        # session.add should be called twice (model + audit)
        assert session.add.call_count == 2
        assert session.flush.called

    def test_upsert_updates_existing_row(self) -> None:
        existing_model = _make_model(voice_rpm_override=5)

        session = MagicMock()
        cursor_get = MagicMock()
        cursor_get.scalar_one_or_none.return_value = existing_model
        session.execute.return_value = cursor_get

        repo = SyncCopilotTenantLimitsRepository(session)
        repo.upsert(
            existing_model.tenant_id,
            voice_rpm_override=10,
            media_max_bytes_override=None,
            updated_by_user_id=None,
        )

        # Model was updated in-place + audit row added
        assert existing_model.voice_rpm_override == 10
        assert session.add.call_count == 1  # only audit row (existing was updated in-place)
        assert session.flush.called


class TestSyncRepositorySoftDelete:
    """Tests for SyncCopilotTenantLimitsRepository.soft_delete."""

    def test_soft_delete_sets_deleted_at(self) -> None:
        existing_model = _make_model(voice_rpm_override=10, deleted_at=None)

        session = MagicMock()
        cursor = MagicMock()
        cursor.scalar_one_or_none.return_value = existing_model
        session.execute.return_value = cursor

        repo = SyncCopilotTenantLimitsRepository(session)
        repo.soft_delete(existing_model.tenant_id)

        assert existing_model.deleted_at is not None
        assert session.add.called  # audit row
        assert session.flush.called

    def test_soft_delete_noop_when_no_row(self) -> None:
        session = MagicMock()
        cursor = MagicMock()
        cursor.scalar_one_or_none.return_value = None
        session.execute.return_value = cursor

        repo = SyncCopilotTenantLimitsRepository(session)
        # Should not raise
        repo.soft_delete(uuid4())
        assert not session.add.called
