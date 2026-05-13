"""Tests for Segment and SegmentSnapshot domain entities."""

from __future__ import annotations

import datetime as dt
from uuid import uuid4

import pytest
from pydantic import ValidationError

from luana_core_campaigns.domain.enums import SegmentType
from luana_core_campaigns.domain.segment import Segment, SegmentSnapshot
from luana_core_campaigns.domain.segment_filter import PredefinedSegmentFilter


NOW = dt.datetime.now(dt.timezone.utc)
EMPTY_FILTER = PredefinedSegmentFilter()


def make_segment(**overrides) -> dict:
    """Factory for valid Segment data."""
    base = {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "name": "Active Leads",
        "filter_dsl": EMPTY_FILTER,
        "created_at": NOW,
        "updated_at": NOW,
    }
    base.update(overrides)
    return base


def make_snapshot(**overrides) -> dict:
    """Factory for valid SegmentSnapshot data."""
    base = {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "segment_id": uuid4(),
        "snapshotted_at": NOW,
        "lead_ids": [uuid4(), uuid4()],
        "lead_count": 2,
        "created_at": NOW,
    }
    base.update(overrides)
    return base


class TestSegmentBasicInvariants:
    """Test basic Segment entity invariants."""

    def test_valid_dynamic_segment(self):
        """A minimal dynamic segment should be valid."""
        seg = Segment(**make_segment())
        assert seg.segment_type == SegmentType.DYNAMIC
        assert seg.deleted_at is None
        assert seg.estimated_size is None

    def test_tenant_id_required(self):
        """tenant_id is mandatory."""
        data = make_segment()
        del data["tenant_id"]
        with pytest.raises(ValidationError):
            Segment(**data)

    def test_name_required(self):
        """name is mandatory."""
        data = make_segment()
        del data["name"]
        with pytest.raises(ValidationError):
            Segment(**data)

    def test_name_cannot_be_empty(self):
        """Empty name should fail."""
        with pytest.raises(ValidationError):
            Segment(**make_segment(name=""))

    def test_name_max_length(self):
        """Name over 128 chars should fail."""
        with pytest.raises(ValidationError):
            Segment(**make_segment(name="x" * 129))

    def test_filter_dsl_required(self):
        """filter_dsl is mandatory."""
        data = make_segment()
        del data["filter_dsl"]
        with pytest.raises(ValidationError):
            Segment(**data)

    def test_filter_dsl_accepts_predefined_filter(self):
        """filter_dsl accepts PredefinedSegmentFilter."""
        seg = Segment(**make_segment(filter_dsl=EMPTY_FILTER))
        assert isinstance(seg.filter_dsl, PredefinedSegmentFilter)

    def test_segment_type_default_dynamic(self):
        """Default segment_type is DYNAMIC."""
        seg = Segment(**make_segment())
        assert seg.segment_type == SegmentType.DYNAMIC

    def test_static_segment_type(self):
        """STATIC segment_type is valid."""
        seg = Segment(**make_segment(segment_type=SegmentType.STATIC))
        assert seg.segment_type == SegmentType.STATIC

    def test_estimated_size_non_negative(self):
        """estimated_size must be >= 0."""
        with pytest.raises(ValidationError):
            Segment(**make_segment(estimated_size=-1))

    def test_estimated_size_zero_ok(self):
        """estimated_size=0 is valid."""
        seg = Segment(**make_segment(estimated_size=0))
        assert seg.estimated_size == 0

    def test_extra_fields_forbidden(self):
        """Extra fields should be forbidden."""
        with pytest.raises(ValidationError):
            Segment(**make_segment(unknown="value"))


class TestSegmentSnapshotInvariants:
    """Test SegmentSnapshot invariants."""

    def test_valid_snapshot(self):
        """A valid snapshot should be created successfully."""
        snap = SegmentSnapshot(**make_snapshot())
        assert snap.lead_count == 2
        assert len(snap.lead_ids) == 2
        assert snap.deleted_at is None

    def test_tenant_id_required(self):
        """tenant_id is mandatory."""
        data = make_snapshot()
        del data["tenant_id"]
        with pytest.raises(ValidationError):
            SegmentSnapshot(**data)

    def test_segment_id_required(self):
        """segment_id is mandatory."""
        data = make_snapshot()
        del data["segment_id"]
        with pytest.raises(ValidationError):
            SegmentSnapshot(**data)

    def test_snapshotted_at_required(self):
        """snapshotted_at is mandatory."""
        data = make_snapshot()
        del data["snapshotted_at"]
        with pytest.raises(ValidationError):
            SegmentSnapshot(**data)

    def test_lead_count_non_negative(self):
        """lead_count must be >= 0."""
        with pytest.raises(ValidationError):
            SegmentSnapshot(**make_snapshot(lead_count=-1))

    def test_empty_lead_ids_valid(self):
        """Empty lead_ids is valid (zero-resolved segment)."""
        snap = SegmentSnapshot(**make_snapshot(lead_ids=[], lead_count=0))
        assert snap.lead_ids == []
        assert snap.lead_count == 0

    def test_soft_delete_optional(self):
        """deleted_at defaults to None."""
        snap = SegmentSnapshot(**make_snapshot())
        assert snap.deleted_at is None
