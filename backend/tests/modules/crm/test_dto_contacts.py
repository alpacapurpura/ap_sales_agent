"""Tests for CRM contacts DTOs — validation, serialization, edge cases.

CRM-15: ContactListItem, ContactIdentity, ContactDetail, DeferredEndpointResponse,
FilterFieldMeta, FilterSchemaResponse, ContactFilterParams.
"""

import uuid
from datetime import datetime, timezone

import pytest

from luana_core_platform.domain.enums import LifecycleStage

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAMPLE_UUID = uuid.uuid4()
_NOW = datetime.now(timezone.utc)


def _make_contact_list_data(**overrides):
    """Build minimal valid dict for ContactListItem."""
    defaults = {
        "id": _SAMPLE_UUID,
        "full_name": "Test User",
        "primary_email": "test@example.com",
        "primary_phone": "+5491112345678",
        "lifecycle_stage": LifecycleStage.LEAD,
        "lead_score": 25.0,
        "is_inactive": False,
        "last_activity_at": _NOW,
        "lead_source": "organic",
        "country": "ar",
        "has_telegram_id": False,
        "has_whatsapp_id": True,
        "has_instagram_id": False,
        "has_tiktok_id": False,
        "has_email": True,
        "has_phone": True,
        "has_recent_campaign_engagement": None,
        "created_at": _NOW,
    }
    defaults.update(overrides)
    return defaults


def _make_contact_detail_data(**overrides):
    """Build minimal valid dict for ContactDetail."""
    defaults = {
        "id": _SAMPLE_UUID,
        "full_name": "Test User",
        "primary_email": "test@example.com",
        "primary_phone": "+5491112345678",
        "lifecycle_stage": LifecycleStage.CUSTOMER,
        "lead_score": 80.0,
        "rfm_segment": "champion",
        "lifetime_value": 150.0,
        "is_inactive": False,
        "first_conversion_at": _NOW,
        "first_seen_at": _NOW,
        "last_activity_at": _NOW,
        "lead_source": "paid",
        "lead_source_detail": "google-ads",
        "traits": {"interest": "marketing"},
        "computed_traits": {"engagement": "high"},
        "created_at": _NOW,
        "updated_at": _NOW,
        "lead_id": _SAMPLE_UUID,
        "telegram_id": "tg-123",
        "whatsapp_id": "wa-456",
        "instagram_id": "ig-789",
        "tiktok_id": None,
        "api_id": None,
        "fit_score": 7,
        "intent_score": 8,
        "temperature": "warm",
        "is_blacklisted": False,
        "last_interaction_date": _NOW,
        "country": "mx",
        "conversation_summary": "Interested in course",
        "identities": [],
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# ContactListItem
# ---------------------------------------------------------------------------


class TestContactListItem:
    """ContactListItem DTO validation and serialization."""

    def test_valid_construction(self):
        from luana_core_crm.api.dto.contacts import ContactListItem

        data = _make_contact_list_data()
        item = ContactListItem(**data)

        assert item.id == _SAMPLE_UUID
        assert item.full_name == "Test User"
        assert item.lifecycle_stage == LifecycleStage.LEAD
        assert item.lead_score == 25.0
        assert item.has_recent_campaign_engagement is None

    def test_all_lifecycle_stages_accepted(self):
        from luana_core_crm.api.dto.contacts import ContactListItem

        for stage in LifecycleStage:
            data = _make_contact_list_data(lifecycle_stage=stage)
            item = ContactListItem(**data)
            assert item.lifecycle_stage == stage

    def test_none_optional_fields(self):
        from luana_core_crm.api.dto.contacts import ContactListItem

        data = _make_contact_list_data(
            full_name=None,
            primary_email=None,
            primary_phone=None,
            last_activity_at=None,
            lead_source=None,
            country=None,
        )
        item = ContactListItem(**data)

        assert item.full_name is None
        assert item.primary_email is None
        assert item.primary_phone is None
        assert item.last_activity_at is None
        assert item.lead_source is None
        assert item.country is None

    def test_extra_fields_forbidden(self):
        from pydantic import ValidationError

        from luana_core_crm.api.dto.contacts import ContactListItem

        data = _make_contact_list_data(extra_field="should fail")

        with pytest.raises(ValidationError):
            ContactListItem(**data)

    def test_missing_required_field_raises(self):
        from pydantic import ValidationError

        from luana_core_crm.api.dto.contacts import ContactListItem

        data = _make_contact_list_data()
        del data["id"]

        with pytest.raises(ValidationError):
            ContactListItem(**data)

    def test_model_dump_serialization(self):
        from luana_core_crm.api.dto.contacts import ContactListItem

        data = _make_contact_list_data()
        item = ContactListItem(**data)
        dumped = item.model_dump()

        assert dumped["id"] == _SAMPLE_UUID
        assert dumped["lifecycle_stage"] == LifecycleStage.LEAD
        assert dumped["has_telegram_id"] is False
        assert dumped["has_whatsapp_id"] is True

    def test_channel_presence_booleans(self):
        from luana_core_crm.api.dto.contacts import ContactListItem

        data = _make_contact_list_data(
            has_telegram_id=True,
            has_whatsapp_id=False,
            has_instagram_id=True,
            has_tiktok_id=True,
            has_email=True,
            has_phone=False,
        )
        item = ContactListItem(**data)

        assert item.has_telegram_id is True
        assert item.has_whatsapp_id is False
        assert item.has_instagram_id is True
        assert item.has_tiktok_id is True
        assert item.has_email is True
        assert item.has_phone is False


# ---------------------------------------------------------------------------
# ContactIdentity
# ---------------------------------------------------------------------------


class TestContactIdentity:
    """ContactIdentity DTO validation and serialization."""

    def test_valid_construction(self):
        from luana_core_crm.api.dto.contacts import ContactIdentity

        identity = ContactIdentity(
            type="email",
            value="test@example.com",
            is_primary=True,
            verification_status="verified",
            last_seen_at=_NOW,
        )

        assert identity.type == "email"
        assert identity.value == "test@example.com"
        assert identity.is_primary is True
        assert identity.verification_status == "verified"

    def test_extra_fields_forbidden(self):
        from pydantic import ValidationError

        from luana_core_crm.api.dto.contacts import ContactIdentity

        with pytest.raises(ValidationError):
            ContactIdentity(
                type="email",
                value="test@example.com",
                is_primary=True,
                verification_status="verified",
                last_seen_at=_NOW,
                extra="nope",
            )

    def test_missing_required_field_raises(self):
        from pydantic import ValidationError

        from luana_core_crm.api.dto.contacts import ContactIdentity

        with pytest.raises(ValidationError):
            ContactIdentity(
                type="email",
                value="test@example.com",
                is_primary=True,
                verification_status="verified",
            )


# ---------------------------------------------------------------------------
# ContactDetail
# ---------------------------------------------------------------------------


class TestContactDetail:
    """ContactDetail DTO validation and serialization."""

    def test_valid_construction(self):
        from luana_core_crm.api.dto.contacts import ContactDetail

        data = _make_contact_detail_data()
        detail = ContactDetail(**data)

        assert detail.id == _SAMPLE_UUID
        assert detail.lifetime_value == 150.0
        assert detail.rfm_segment == "champion"
        assert len(detail.identities) == 0

    def test_with_identities(self):
        from luana_core_crm.api.dto.contacts import ContactDetail, ContactIdentity

        identities = [
            ContactIdentity(
                type="email",
                value="test@example.com",
                is_primary=True,
                verification_status="verified",
                last_seen_at=_NOW,
            ),
            ContactIdentity(
                type="whatsapp",
                value="+5491112345678",
                is_primary=False,
                verification_status="unverified",
                last_seen_at=_NOW,
            ),
        ]
        data = _make_contact_detail_data(identities=identities)
        detail = ContactDetail(**data)

        assert len(detail.identities) == 2
        assert detail.identities[0].type == "email"
        assert detail.identities[1].type == "whatsapp"

    def test_none_optional_lead_fields(self):
        from luana_core_crm.api.dto.contacts import ContactDetail

        data = _make_contact_detail_data(
            lead_id=None,
            telegram_id=None,
            whatsapp_id=None,
            instagram_id=None,
            fit_score=None,
            intent_score=None,
            temperature=None,
            is_blacklisted=None,
            last_interaction_date=None,
            conversation_summary=None,
        )
        detail = ContactDetail(**data)

        assert detail.lead_id is None
        assert detail.telegram_id is None
        assert detail.fit_score is None
        assert detail.temperature is None
        assert detail.is_blacklisted is None

    def test_extra_fields_forbidden(self):
        from pydantic import ValidationError

        from luana_core_crm.api.dto.contacts import ContactDetail

        data = _make_contact_detail_data(extra="nope")

        with pytest.raises(ValidationError):
            ContactDetail(**data)

    def test_model_dump_serialization(self):
        from luana_core_crm.api.dto.contacts import ContactDetail

        data = _make_contact_detail_data()
        detail = ContactDetail(**data)
        dumped = detail.model_dump()

        assert dumped["lifetime_value"] == 150.0
        assert dumped["traits"] == {"interest": "marketing"}
        assert dumped["computed_traits"] == {"engagement": "high"}

    def test_updated_at_none(self):
        from luana_core_crm.api.dto.contacts import ContactDetail

        data = _make_contact_detail_data(updated_at=None)
        detail = ContactDetail(**data)

        assert detail.updated_at is None


# ---------------------------------------------------------------------------
# DeferredEndpointResponse
# ---------------------------------------------------------------------------


class TestDeferredEndpointResponse:
    """DeferredEndpointResponse for 501 deferred endpoints."""

    def test_valid_construction(self):
        from luana_core_crm.api.dto.contacts import DeferredEndpointResponse

        resp = DeferredEndpointResponse(
            detail="Endpoint deferred to PI-3",
            deferred_until="PI-3",
            canonical_path="/api/v1/crm/contacts/advanced-search",
            expected_response_model="ContactSearchResponse",
        )

        assert resp.detail == "Endpoint deferred to PI-3"
        assert resp.deferred_until == "PI-3"
        assert resp.canonical_path == "/api/v1/crm/contacts/advanced-search"

    def test_extra_fields_forbidden(self):
        from pydantic import ValidationError

        from luana_core_crm.api.dto.contacts import DeferredEndpointResponse

        with pytest.raises(ValidationError):
            DeferredEndpointResponse(
                detail="test",
                deferred_until="PI-3",
                canonical_path="/test",
                expected_response_model="Test",
                extra="nope",
            )

    def test_missing_required_field_raises(self):
        from pydantic import ValidationError

        from luana_core_crm.api.dto.contacts import DeferredEndpointResponse

        with pytest.raises(ValidationError):
            DeferredEndpointResponse(
                detail="test",
                deferred_until="PI-3",
                canonical_path="/test",
            )


# ---------------------------------------------------------------------------
# FilterFieldMeta
# ---------------------------------------------------------------------------


class TestFilterFieldMeta:
    """FilterFieldMeta for dynamic filter UI construction."""

    def test_valid_construction(self):
        from luana_core_crm.api.dto.contacts import FilterFieldMeta

        meta = FilterFieldMeta(
            name="lifecycle_stage_in",
            type="enum_list",
            enum_values=["subscriber", "lead", "mql"],
            description="Filter by lifecycle stage",
        )

        assert meta.name == "lifecycle_stage_in"
        assert meta.type == "enum_list"
        assert len(meta.enum_values) == 3

    def test_none_enum_values(self):
        from luana_core_crm.api.dto.contacts import FilterFieldMeta

        meta = FilterFieldMeta(
            name="q",
            type="string",
            enum_values=None,
            description="Search query",
        )

        assert meta.enum_values is None

    def test_none_description(self):
        from luana_core_crm.api.dto.contacts import FilterFieldMeta

        meta = FilterFieldMeta(
            name="score_min",
            type="int_range",
            enum_values=None,
            description=None,
        )

        assert meta.description is None

    def test_extra_fields_forbidden(self):
        from pydantic import ValidationError

        from luana_core_crm.api.dto.contacts import FilterFieldMeta

        with pytest.raises(ValidationError):
            FilterFieldMeta(
                name="test",
                type="string",
                enum_values=None,
                description=None,
                extra="nope",
            )


# ---------------------------------------------------------------------------
# FilterSchemaResponse
# ---------------------------------------------------------------------------


class TestFilterSchemaResponse:
    """FilterSchemaResponse for filter metadata endpoint."""

    def test_valid_construction(self):
        from luana_core_crm.api.dto.contacts import FilterFieldMeta, FilterSchemaResponse

        fields = [
            FilterFieldMeta(name="q", type="string", enum_values=None, description="Search"),
            FilterFieldMeta(name="score_min", type="int_range", enum_values=None, description=None),
        ]
        resp = FilterSchemaResponse(version="1.0", fields=fields)

        assert resp.version == "1.0"
        assert len(resp.fields) == 2

    def test_empty_fields_list(self):
        from luana_core_crm.api.dto.contacts import FilterSchemaResponse

        resp = FilterSchemaResponse(version="2.0", fields=[])

        assert resp.version == "2.0"
        assert resp.fields == []

    def test_extra_fields_forbidden(self):
        from pydantic import ValidationError

        from luana_core_crm.api.dto.contacts import FilterSchemaResponse

        with pytest.raises(ValidationError):
            FilterSchemaResponse(version="1.0", fields=[], extra="nope")


# ---------------------------------------------------------------------------
# ContactFilterParams
# ---------------------------------------------------------------------------


class TestContactFilterParams:
    """ContactFilterParams validation — all fields default to None."""

    def test_all_defaults_none(self):
        from luana_core_crm.api.dto.contact_filters import ContactFilterParams

        params = ContactFilterParams()

        assert params.lifecycle_stage_in is None
        assert params.score_min is None
        assert params.score_max is None
        assert params.source_in is None
        assert params.has_email is None
        assert params.has_phone is None
        assert params.has_telegram_id is None
        assert params.has_whatsapp_id is None
        assert params.has_instagram_id is None
        assert params.has_tiktok_id is None
        assert params.created_after is None
        assert params.created_before is None
        assert params.last_activity_after is None
        assert params.last_activity_before is None
        assert params.is_inactive is None
        assert params.has_campaign_engagement is None
        assert params.country_in is None
        assert params.q is None

    def test_lifecycle_stage_filter(self):
        from luana_core_crm.api.dto.contact_filters import ContactFilterParams

        params = ContactFilterParams(
            lifecycle_stage_in=[LifecycleStage.LEAD, LifecycleStage.MQL],
        )

        assert params.lifecycle_stage_in == [LifecycleStage.LEAD, LifecycleStage.MQL]

    def test_score_range_validation_valid(self):
        from luana_core_crm.api.dto.contact_filters import ContactFilterParams

        params = ContactFilterParams(score_min=10, score_max=90)

        assert params.score_min == 10
        assert params.score_max == 90

    def test_score_min_below_zero_raises(self):
        from pydantic import ValidationError

        from luana_core_crm.api.dto.contact_filters import ContactFilterParams

        with pytest.raises(ValidationError):
            ContactFilterParams(score_min=-1)

    def test_score_max_above_100_raises(self):
        from pydantic import ValidationError

        from luana_core_crm.api.dto.contact_filters import ContactFilterParams

        with pytest.raises(ValidationError):
            ContactFilterParams(score_max=101)

    def test_source_filter(self):
        from luana_core_crm.api.dto.contact_filters import ContactFilterParams

        params = ContactFilterParams(source_in=["google", "facebook", "organic"])

        assert params.source_in == ["google", "facebook", "organic"]

    def test_identity_presence_filters(self):
        from luana_core_crm.api.dto.contact_filters import ContactFilterParams

        params = ContactFilterParams(
            has_email=True,
            has_phone=True,
            has_telegram_id=False,
            has_whatsapp_id=True,
            has_instagram_id=False,
            has_tiktok_id=False,
        )

        assert params.has_email is True
        assert params.has_phone is True
        assert params.has_telegram_id is False
        assert params.has_whatsapp_id is True

    def test_temporal_filters(self):
        from luana_core_crm.api.dto.contact_filters import ContactFilterParams

        after = datetime(2024, 1, 1, tzinfo=timezone.utc)
        before = datetime(2024, 12, 31, tzinfo=timezone.utc)

        params = ContactFilterParams(
            created_after=after,
            created_before=before,
            last_activity_after=after,
            last_activity_before=before,
        )

        assert params.created_after == after
        assert params.created_before == before

    def test_is_inactive_filter(self):
        from luana_core_crm.api.dto.contact_filters import ContactFilterParams

        params_active = ContactFilterParams(is_inactive=False)
        params_inactive = ContactFilterParams(is_inactive=True)

        assert params_active.is_inactive is False
        assert params_inactive.is_inactive is True

    def test_campaign_engagement_filter(self):
        from luana_core_crm.api.dto.contact_filters import ContactFilterParams

        params = ContactFilterParams(has_campaign_engagement=True)

        assert params.has_campaign_engagement is True

    def test_country_filter(self):
        from luana_core_crm.api.dto.contact_filters import ContactFilterParams

        params = ContactFilterParams(country_in=["mx", "pe", "co"])

        assert params.country_in == ["mx", "pe", "co"]

    def test_search_query_valid(self):
        from luana_core_crm.api.dto.contact_filters import ContactFilterParams

        params = ContactFilterParams(q="john doe")

        assert params.q == "john doe"

    def test_search_query_max_length(self):
        from luana_core_crm.api.dto.contact_filters import ContactFilterParams

        long_q = "a" * 120
        params = ContactFilterParams(q=long_q)

        assert len(params.q) == 120

    def test_search_query_exceeds_max_length_raises(self):
        from pydantic import ValidationError

        from luana_core_crm.api.dto.contact_filters import ContactFilterParams

        with pytest.raises(ValidationError):
            ContactFilterParams(q="a" * 121)

    def test_extra_fields_forbidden(self):
        from pydantic import ValidationError

        from luana_core_crm.api.dto.contact_filters import ContactFilterParams

        with pytest.raises(ValidationError):
            ContactFilterParams(q="test", extra_field="nope")

    def test_combined_filters(self):
        from luana_core_crm.api.dto.contact_filters import ContactFilterParams

        params = ContactFilterParams(
            lifecycle_stage_in=[LifecycleStage.CUSTOMER],
            score_min=50,
            has_email=True,
            country_in=["ar", "mx"],
            q="premium",
        )

        assert params.lifecycle_stage_in == [LifecycleStage.CUSTOMER]
        assert params.score_min == 50
        assert params.has_email is True
        assert params.country_in == ["ar", "mx"]
        assert params.q == "premium"
