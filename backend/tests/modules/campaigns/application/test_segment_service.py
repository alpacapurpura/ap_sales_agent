"""Unit tests for SegmentService.

All tests use AsyncMock — no DB needed.
SQL-side filtering contract verified structurally (filter evaluator called).
"""

from __future__ import annotations

import datetime as dt
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from luana_core_campaigns.application.dtos.segment_dtos import (
    SegmentCreate,
    SegmentUpdate,
)
from luana_core_campaigns.application.services.cache import SimpleTTLCache
from luana_core_campaigns.application.services.segment_service import (
    SegmentDuplicateNameError,
    SegmentNotFoundError,
    SegmentService,
)
from luana_core_campaigns.domain.enums import SegmentType
from luana_core_campaigns.domain.segment import Segment, SegmentSnapshot
from luana_core_campaigns.domain.segment_filter import PredefinedSegmentFilter

pytestmark = pytest.mark.asyncio

TENANT = uuid4()
_NOW = dt.datetime(2025, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)


def _make_filter() -> PredefinedSegmentFilter:
    """Build a minimal valid PredefinedSegmentFilter (no fields = match-all)."""
    return PredefinedSegmentFilter()


def _make_segment(
    *,
    tenant_id: UUID | None = None,
    deleted: bool = False,
) -> Segment:
    now = _NOW
    return Segment(
        id=uuid4(),
        tenant_id=tenant_id or TENANT,
        name="Test Segment",
        description="desc",
        segment_type=SegmentType.DYNAMIC,
        filter_dsl=_make_filter(),
        created_at=now,
        updated_at=now,
        deleted_at=now if deleted else None,
    )


def _make_service() -> tuple[
    SegmentService,
    AsyncMock,  # repo
    AsyncMock,  # snapshot_repo
    AsyncMock,  # lead_query_port
    MagicMock,  # filter_evaluator
    AsyncMock,  # outbox_service
    SimpleTTLCache,
]:
    repo = AsyncMock()
    snapshot_repo = AsyncMock()
    lead_query_port = AsyncMock()
    filter_evaluator = MagicMock()
    outbox_service = AsyncMock()
    cache = SimpleTTLCache()

    svc = SegmentService(
        repo=repo,
        snapshot_repo=snapshot_repo,
        lead_query_port=lead_query_port,
        filter_evaluator=filter_evaluator,
        outbox_service=outbox_service,
        cache=cache,
    )
    return svc, repo, snapshot_repo, lead_query_port, filter_evaluator, outbox_service, cache


class TestSegmentServiceCreate:
    """Tests for create() happy path and error paths."""

    async def test_create_happy_path(self) -> None:
        """create() saves segment and emits SegmentCreated event."""
        svc, repo, _, _, _, outbox, _ = _make_service()
        session = AsyncMock()
        dto = SegmentCreate(
            name="Mi Segmento",
            description="desc",
            segment_type=SegmentType.DYNAMIC,
            filter_dsl=_make_filter(),
        )
        with patch(
            "luana_core_campaigns.application.services.segment_service.utc_now",
            return_value=_NOW,
        ):
            seg = await svc.create(TENANT, dto, session=session)

        assert seg.tenant_id == TENANT
        assert seg.name == "Mi Segmento"
        repo.append.assert_awaited_once()
        outbox.enqueue_async_from_sync_caller.assert_awaited_once()

    async def test_create_duplicate_raises(self) -> None:
        """create() raises SegmentDuplicateNameError on unique violation."""
        svc, repo, _, _, _, _, _ = _make_service()
        session = AsyncMock()
        repo.append.side_effect = Exception("duplicate key uq_segment")
        dto = SegmentCreate(
            name="Dup",
            filter_dsl=_make_filter(),
        )
        with pytest.raises(SegmentDuplicateNameError):
            await svc.create(TENANT, dto, session=session)

    async def test_create_other_exception_propagates(self) -> None:
        """create() propagates non-unique exceptions."""
        svc, repo, _, _, _, _, _ = _make_service()
        session = AsyncMock()
        repo.append.side_effect = RuntimeError("db connection lost")
        dto = SegmentCreate(name="X", filter_dsl=_make_filter())
        with pytest.raises(RuntimeError):
            await svc.create(TENANT, dto, session=session)

    async def test_create_invalidates_estimate_cache(self) -> None:
        """create() calls cache.invalidate_pattern for tenant estimates."""
        svc, _, _, _, _, _, cache = _make_service()
        session = AsyncMock()
        dto = SegmentCreate(name="Seg", filter_dsl=_make_filter())
        invalidate_called = []

        async def fake_invalidate(pat: str) -> None:
            invalidate_called.append(pat)

        cache.invalidate_pattern = fake_invalidate  # type: ignore[method-assign]
        await svc.create(TENANT, dto, session=session)
        assert any(str(TENANT) in p for p in invalidate_called)


class TestSegmentServiceRead:
    """Tests for get(), list(), update(), delete()."""

    async def test_get_not_found_raises(self) -> None:
        """get() raises SegmentNotFoundError when repo returns None."""
        svc, repo, _, _, _, _, _ = _make_service()
        session = AsyncMock()
        repo.get_by_id.return_value = None
        with pytest.raises(SegmentNotFoundError):
            await svc.get(TENANT, uuid4(), session=session)

    async def test_get_deleted_raises(self) -> None:
        """get() raises SegmentNotFoundError for soft-deleted segment."""
        svc, repo, _, _, _, _, _ = _make_service()
        session = AsyncMock()
        repo.get_by_id.return_value = _make_segment(deleted=True)
        with pytest.raises(SegmentNotFoundError):
            await svc.get(TENANT, uuid4(), session=session)

    async def test_get_found(self) -> None:
        """get() returns segment when found."""
        svc, repo, _, _, _, _, _ = _make_service()
        session = AsyncMock()
        seg = _make_segment()
        repo.get_by_id.return_value = seg
        result = await svc.get(TENANT, seg.id, session=session)
        assert result.id == seg.id

    async def test_update_calls_repo(self) -> None:
        """update() patches name and calls repo.update."""
        svc, repo, _, _, _, _, _ = _make_service()
        session = AsyncMock()
        seg = _make_segment()
        repo.get_by_id.return_value = seg
        dto = SegmentUpdate(name="Nuevo")
        updated = await svc.update(TENANT, seg.id, dto, session=session)
        assert updated.name == "Nuevo"
        repo.update.assert_awaited_once()

    async def test_update_invalidates_cache(self) -> None:
        """update() invalidates estimate_size cache for segment."""
        svc, repo, _, _, _, _, cache = _make_service()
        session = AsyncMock()
        seg = _make_segment()
        repo.get_by_id.return_value = seg
        invalidated: list[str] = []

        async def fake_invalidate(key: str) -> None:
            invalidated.append(key)

        cache.invalidate = fake_invalidate  # type: ignore[method-assign]
        await svc.update(TENANT, seg.id, SegmentUpdate(name="X"), session=session)
        assert any(str(seg.id) in k for k in invalidated)

    async def test_delete_calls_soft_delete(self) -> None:
        """delete() calls repo.soft_delete (not hard delete)."""
        svc, repo, _, _, _, _, _ = _make_service()
        session = AsyncMock()
        seg = _make_segment()
        repo.get_by_id.return_value = seg
        await svc.delete(TENANT, seg.id, session=session)
        repo.soft_delete.assert_awaited_once()
        # Ensure no hard-delete call
        assert not hasattr(repo, "delete") or not repo.delete.called


class TestSegmentServiceResolve:
    """Tests for resolve() — SQL-side filtering contract."""

    async def test_resolve_uses_sql_predicate(self) -> None:
        """resolve() calls filter_evaluator.to_sql_predicate (SQL-side, not Python)."""
        svc, repo, _, lead_port, evaluator, _, _ = _make_service()
        session = AsyncMock()
        seg = _make_segment()
        repo.get_by_id.return_value = seg
        fake_predicate = MagicMock()
        evaluator.to_sql_predicate.return_value = fake_predicate
        lead_port.list_lead_ids_matching.return_value = ([uuid4(), uuid4()], 2)

        ids, total, truncated = await svc.resolve(TENANT, seg.id, session=session, limit=100)

        evaluator.to_sql_predicate.assert_called_once()
        lead_port.list_lead_ids_matching.assert_awaited_once()
        assert total == 2
        assert not truncated

    async def test_resolve_truncated_when_exceeds_limit(self) -> None:
        """resolve() returns truncated=True when total > limit."""
        svc, repo, _, lead_port, evaluator, _, _ = _make_service()
        session = AsyncMock()
        seg = _make_segment()
        repo.get_by_id.return_value = seg
        evaluator.to_sql_predicate.return_value = MagicMock()
        # total=200 but limit=100 → truncated
        lead_port.list_lead_ids_matching.return_value = ([uuid4()] * 100, 200)

        _, total, truncated = await svc.resolve(TENANT, seg.id, session=session, limit=100)

        assert total == 200
        assert truncated is True

    async def test_resolve_not_found_raises(self) -> None:
        """resolve() raises SegmentNotFoundError if segment not found."""
        svc, repo, _, _, _, _, _ = _make_service()
        session = AsyncMock()
        repo.get_by_id.return_value = None
        with pytest.raises(SegmentNotFoundError):
            await svc.resolve(TENANT, uuid4(), session=session)


class TestSegmentServiceEstimateSize:
    """Tests for estimate_size() caching behavior."""

    async def test_estimate_cache_miss_queries_db(self) -> None:
        """estimate_size() computes via lead_query_port on cache miss."""
        svc, repo, _, lead_port, evaluator, _, _ = _make_service()
        session = AsyncMock()
        seg = _make_segment()
        repo.get_by_id.return_value = seg
        evaluator.to_sql_predicate.return_value = MagicMock()
        lead_port.count_leads_matching.return_value = 42

        size, cached_at, cache_hit = await svc.estimate_size(TENANT, seg.id, session=session)

        assert size == 42
        assert cache_hit is False
        lead_port.count_leads_matching.assert_awaited_once()

    async def test_estimate_cache_hit_skips_db(self) -> None:
        """estimate_size() returns cached value on second call."""
        svc, repo, _, lead_port, evaluator, _, cache = _make_service()
        session = AsyncMock()
        seg = _make_segment()
        repo.get_by_id.return_value = seg
        evaluator.to_sql_predicate.return_value = MagicMock()
        lead_port.count_leads_matching.return_value = 7

        # First call — miss
        await svc.estimate_size(TENANT, seg.id, session=session)
        # Second call — should hit cache
        size, _, cache_hit = await svc.estimate_size(TENANT, seg.id, session=session)

        assert size == 7
        assert cache_hit is True
        # DB queried exactly once
        assert lead_port.count_leads_matching.await_count == 1


class TestSegmentServiceSnapshot:
    """Tests for snapshot() — materializes lead IDs + emits event."""

    async def test_snapshot_persists_and_emits_event(self) -> None:
        """snapshot() appends SegmentSnapshot and emits SegmentSnapshotted event."""
        svc, repo, snapshot_repo, lead_port, evaluator, outbox, _ = _make_service()
        session = AsyncMock()
        seg = _make_segment()
        repo.get_by_id.return_value = seg
        evaluator.to_sql_predicate.return_value = MagicMock()
        lead_ids = [uuid4(), uuid4(), uuid4()]
        lead_port.list_lead_ids_matching.return_value = (lead_ids, 3)

        snap = await svc.snapshot(TENANT, seg.id, session=session)

        assert isinstance(snap, SegmentSnapshot)
        assert snap.lead_count == 3
        assert snap.tenant_id == TENANT
        snapshot_repo.append.assert_awaited_once()
        outbox.enqueue_async_from_sync_caller.assert_awaited_once()
