"""Tests for marketing webhook route functions and helpers.

Covers pure helpers (_tag_to_metric, _flow_to_metric, _field_to_metric,
_event_to_metric_name, _event_to_stage, _event_to_channel_suffix,
_build_manychat_event_properties) and route handlers via direct call
with mocked Request + DB.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from luana_core_connections.api.marketing_webhooks import (
    _build_manychat_event_properties,
    _event_to_channel_suffix,
    _event_to_metric_name,
    _event_to_stage,
    _field_to_metric,
    _flow_to_metric,
    _tag_to_metric,
    handle_mailerlite_webhook,
    handle_manychat_webhook,
    mailerlite_webhook_legacy,
    shopify_webhook,
)

TENANT_ID = uuid4()


def _mock_request(json_data: dict, headers: dict | None = None) -> MagicMock:
    req = MagicMock()
    req.json = AsyncMock(return_value=json_data)
    req.headers = headers or {}
    return req


def _mock_db() -> MagicMock:
    db = MagicMock()
    db.execute.return_value.scalar_one_or_none.return_value = None
    db.execute.return_value.all.return_value = []
    db.execute.return_value.scalars.return_value.all.return_value = []
    return db


# ---------------------------------------------------------------------------
# _tag_to_metric
# ---------------------------------------------------------------------------


class TestTagToMetric:
    def test_known_tag_solicito_reunion(self):
        assert _tag_to_metric({"tag_name": "Solicito_reunion"}) == "meetings_requested"

    def test_known_tag_link_clicked(self):
        assert _tag_to_metric({"tag_name": "link_clicked"}) == "link_clicks"

    def test_known_tag_quiz_started(self):
        assert _tag_to_metric({"tag_name": "quiz_started"}) == "qualified_leads"

    def test_unknown_tag_defaults_to_tag_applied(self):
        assert _tag_to_metric({"tag_name": "SomeOtherTag"}) == "tag_applied"

    def test_missing_tag_defaults_to_tag_applied(self):
        assert _tag_to_metric({}) == "tag_applied"


# ---------------------------------------------------------------------------
# _flow_to_metric
# ---------------------------------------------------------------------------


class TestFlowToMetric:
    def test_bofu_flow_returns_bofu_triggered(self):
        assert _flow_to_metric({"flow_name": "BOFU_Webinar"}) == "bofu_flows_triggered"

    def test_followup_flow_returns_sequences_sent(self):
        assert _flow_to_metric({"flow_name": "FollowUpEmail"}) == "sequences_sent"

    def test_sequence_flow_returns_sequences_sent(self):
        assert _flow_to_metric({"flow_name": "SequenceNurture"}) == "sequences_sent"

    def test_generic_flow_returns_flows_triggered(self):
        assert _flow_to_metric({"flow_name": "SomeOtherFlow"}) == "flows_triggered"

    def test_empty_flow_name_returns_flows_triggered(self):
        assert _flow_to_metric({}) == "flows_triggered"


# ---------------------------------------------------------------------------
# _field_to_metric
# ---------------------------------------------------------------------------


class TestFieldToMetric:
    def test_consultas_field_returns_consultations(self):
        assert _field_to_metric({"custom_field_name": "Consultas"}) == "consultations"

    def test_other_field_returns_none(self):
        assert _field_to_metric({"custom_field_name": "OtrosCampos"}) is None

    def test_empty_returns_none(self):
        assert _field_to_metric({}) is None


# ---------------------------------------------------------------------------
# _event_to_metric_name
# ---------------------------------------------------------------------------


class TestEventToMetricName:
    def test_subscriber_new_returns_new_subscribers(self):
        assert _event_to_metric_name("subscriber.new", {}) == "new_subscribers"

    def test_comment_trigger_returns_comment_triggers(self):
        assert _event_to_metric_name("comment.trigger", {}) == "comment_triggers"

    def test_tag_applied_routes_to_tag_handler(self):
        result = _event_to_metric_name("tag.applied", {"tag_name": "link_clicked"})
        assert result == "link_clicks"

    def test_flow_triggered_routes_to_flow_handler(self):
        result = _event_to_metric_name("flow.triggered", {"flow_name": "BOFU_Close"})
        assert result == "bofu_flows_triggered"

    def test_unknown_event_returns_none(self):
        assert _event_to_metric_name("unknown.event", {}) is None


# ---------------------------------------------------------------------------
# _event_to_stage
# ---------------------------------------------------------------------------


class TestEventToStage:
    def test_comment_trigger_is_attraction(self):
        assert _event_to_stage("comment.trigger", {}) == "attraction"

    def test_subscriber_new_is_capture(self):
        assert _event_to_stage("subscriber.new", {}) == "capture"

    def test_solicito_reunion_tag_is_opportunity(self):
        assert _event_to_stage("tag.applied", {"tag_name": "Solicito_reunion"}) == "opportunity"

    def test_other_tag_is_nurture(self):
        assert _event_to_stage("tag.applied", {"tag_name": "link_clicked"}) == "nurture"

    def test_bofu_flow_is_opportunity(self):
        assert _event_to_stage("flow.triggered", {"flow_name": "BOFU_Close"}) == "opportunity"

    def test_other_flow_is_nurture(self):
        assert _event_to_stage("flow.triggered", {"flow_name": "FollowUp"}) == "nurture"

    def test_unknown_event_returns_none(self):
        assert _event_to_stage("unknown.event", {}) is None


# ---------------------------------------------------------------------------
# _event_to_channel_suffix
# ---------------------------------------------------------------------------


class TestEventToChannelSuffix:
    def test_comment_trigger_is_comments(self):
        assert _event_to_channel_suffix("comment.trigger", {}) == "comments"

    def test_tag_applied_solicito_reunion_is_bofu(self):
        assert _event_to_channel_suffix("tag.applied", {"tag_name": "Solicito_reunion"}) == "bofu"

    def test_tag_applied_other_is_sequences(self):
        assert _event_to_channel_suffix("tag.applied", {"tag_name": "quiz_started"}) == "sequences"

    def test_flow_triggered_bofu_is_bofu(self):
        assert _event_to_channel_suffix("flow.triggered", {"flow_name": "BOFU_Final"}) == "bofu"

    def test_flow_triggered_other_is_sequences(self):
        assert _event_to_channel_suffix("flow.triggered", {"flow_name": "FollowUp"}) == "sequences"

    def test_subscriber_new_defaults_to_ig(self):
        assert _event_to_channel_suffix("subscriber.new", {}) == "ig"


# ---------------------------------------------------------------------------
# _build_manychat_event_properties
# ---------------------------------------------------------------------------


class TestBuildManychatEventProperties:
    def test_minimal_payload(self):
        props = _build_manychat_event_properties({}, "sub_123", "instagram", "subscriber.new")
        assert props["source"] == "manychat_webhook"
        assert props["manychat_subscriber_id"] == "sub_123"
        assert props["channel"] == "instagram"
        assert props["event_type"] == "subscriber.new"

    def test_tag_name_included(self):
        payload = {"tag_name": "link_clicked"}
        props = _build_manychat_event_properties(payload, "sub_1", "instagram", "tag.applied")
        assert props["tag_name"] == "link_clicked"

    def test_flow_fields_included(self):
        payload = {"flow_ns": "ns123", "flow_name": "FollowUpEmail"}
        props = _build_manychat_event_properties(payload, "sub_1", "instagram", "flow.triggered")
        assert props["flow_ns"] == "ns123"
        assert props["flow_name"] == "FollowUpEmail"

    def test_custom_field_included(self):
        payload = {"custom_field_name": "Consultas", "custom_field_value": "2"}
        props = _build_manychat_event_properties(payload, "sub_1", "instagram", "field.updated")
        assert props["custom_field_name"] == "Consultas"
        assert props["custom_field_value"] == "2"

    def test_custom_fields_snapshot_included(self):
        payload = {"custom_fields": {"field1": "val1"}}
        props = _build_manychat_event_properties(payload, "sub_1", "instagram", "subscriber.new")
        assert props["custom_fields_snapshot"] == {"field1": "val1"}


# ---------------------------------------------------------------------------
# shopify_webhook
# ---------------------------------------------------------------------------


class TestShopifyWebhook:
    @pytest.mark.asyncio
    async def test_unknown_tenant_returns_ignored(self):
        req = _mock_request(
            {"email": "test@test.com"},
            headers={"X-Shopify-Topic": "checkouts/create", "X-Shopify-Shop-Domain": "unknown.myshopify.com"},
        )
        db = _mock_db()
        db.execute.return_value.all.return_value = []

        result = await shopify_webhook(req, verified=True, db=db)
        assert result["status"] == "ignored"

    @pytest.mark.asyncio
    async def test_unhandled_topic_returns_processed(self):
        req = _mock_request(
            {},
            headers={"X-Shopify-Topic": "products/update", "X-Shopify-Shop-Domain": "mystore.myshopify.com"},
        )
        db = _mock_db()

        with patch(
            "luana_core_connections.api.marketing_webhooks._resolve_tenant",
            new_callable=AsyncMock,
            return_value=TENANT_ID,
        ):
            result = await shopify_webhook(req, verified=True, db=db)
        assert result["status"] == "processed"

    @pytest.mark.asyncio
    async def test_checkouts_create_dispatches_to_handler(self):
        payload = {"email": "buyer@test.com", "total_price": "99.00", "currency": "USD", "line_items": []}
        req = _mock_request(
            payload,
            headers={"X-Shopify-Topic": "checkouts/create", "X-Shopify-Shop-Domain": "shop.myshopify.com"},
        )
        db = _mock_db()

        with (
            patch(
                "luana_core_connections.api.marketing_webhooks._resolve_tenant",
                new_callable=AsyncMock,
                return_value=TENANT_ID,
            ),
            patch(
                "luana_core_connections.api.marketing_webhooks._handle_checkout_created", new_callable=AsyncMock
            ) as mock_handler,
        ):
            result = await shopify_webhook(req, verified=True, db=db)

        mock_handler.assert_called_once()
        assert result["status"] == "processed"

    @pytest.mark.asyncio
    async def test_orders_create_dispatches_to_handler(self):
        payload = {"email": "buyer@test.com", "total_price": "99.00", "currency": "USD", "line_items": []}
        req = _mock_request(
            payload,
            headers={"X-Shopify-Topic": "orders/create", "X-Shopify-Shop-Domain": "shop.myshopify.com"},
        )
        db = _mock_db()

        with (
            patch(
                "luana_core_connections.api.marketing_webhooks._resolve_tenant",
                new_callable=AsyncMock,
                return_value=TENANT_ID,
            ),
            patch(
                "luana_core_connections.api.marketing_webhooks._handle_order_created", new_callable=AsyncMock
            ) as mock_handler,
        ):
            result = await shopify_webhook(req, verified=True, db=db)

        mock_handler.assert_called_once()
        assert result["status"] == "processed"

    @pytest.mark.asyncio
    async def test_exception_returns_error_status(self):
        req = _mock_request(
            {}, headers={"X-Shopify-Topic": "checkouts/create", "X-Shopify-Shop-Domain": "shop.myshopify.com"}
        )
        req.json = AsyncMock(side_effect=Exception("parse error"))
        db = _mock_db()

        result = await shopify_webhook(req, verified=True, db=db)
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# handle_mailerlite_webhook
# ---------------------------------------------------------------------------


class TestHandleMailerliteWebhook:
    @pytest.mark.asyncio
    async def test_invalid_json_raises_400(self):
        req = _mock_request({})
        req.json = AsyncMock(side_effect=ValueError("bad json"))
        db = _mock_db()

        with pytest.raises(HTTPException) as exc_info:
            await handle_mailerlite_webhook(TENANT_ID, req, db)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_no_email_returns_ignored(self):
        req = _mock_request({"type": "campaign.open", "subscriber": {}})
        db = _mock_db()

        result = await handle_mailerlite_webhook(TENANT_ID, req, db)
        assert result["status"] == "ignored"
        assert result["reason"] == "no_email"

    @pytest.mark.asyncio
    async def test_unknown_subscriber_returns_ignored(self):
        req = _mock_request({"type": "campaign.open", "subscriber": {"email": "x@test.com"}})
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None

        result = await handle_mailerlite_webhook(TENANT_ID, req, db)
        assert result["status"] == "ignored"
        assert result["reason"] == "unknown_subscriber"

    @pytest.mark.asyncio
    async def test_email_opened_creates_journey_event(self):
        profile = MagicMock()
        profile.id = uuid4()
        req = _mock_request(
            {
                "type": "campaign.open",
                "subscriber": {"email": "user@test.com"},
                "campaign": {"id": "camp_1", "name": "Newsletter"},
            }
        )
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = profile

        with patch("luana_core_platform.links.ports.crm_repos.get_lifecycle_service") as mock_lc:
            mock_lc.return_value.recalculate_score.return_value = None
            result = await handle_mailerlite_webhook(TENANT_ID, req, db)

        assert result["status"] == "processed"
        assert result["event"] == "email_opened"
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_email_clicked_creates_journey_event(self):
        profile = MagicMock()
        profile.id = uuid4()
        req = _mock_request(
            {
                "type": "campaign.click",
                "subscriber": {"email": "user@test.com"},
                "campaign": {"id": "camp_1", "name": "Newsletter"},
            }
        )
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = profile

        with patch("luana_core_platform.links.ports.crm_repos.get_lifecycle_service") as mock_lc:
            mock_lc.return_value.recalculate_score.return_value = None
            result = await handle_mailerlite_webhook(TENANT_ID, req, db)

        assert result["status"] == "processed"
        assert result["event"] == "email_clicked"

    @pytest.mark.asyncio
    async def test_unsupported_event_returns_ignored(self):
        profile = MagicMock()
        req = _mock_request({"type": "campaign.unsubscribe", "subscriber": {"email": "user@test.com"}})
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = profile

        result = await handle_mailerlite_webhook(TENANT_ID, req, db)
        assert result["status"] == "ignored"
        assert "unsupported_event" in result["reason"]


# ---------------------------------------------------------------------------
# mailerlite_webhook_legacy
# ---------------------------------------------------------------------------


class TestMailerliteLegacy:
    @pytest.mark.asyncio
    async def test_returns_received(self):
        req = _mock_request({"type": "campaign.open", "data": "x"})
        db = _mock_db()

        result = await mailerlite_webhook_legacy(req, db)
        assert result["status"] == "received"
        assert result["source"] == "mailerlite"

    @pytest.mark.asyncio
    async def test_invalid_json_raises_400(self):
        req = _mock_request({})
        req.json = AsyncMock(side_effect=Exception("parse error"))
        db = _mock_db()

        with pytest.raises(HTTPException) as exc_info:
            await mailerlite_webhook_legacy(req, db)
        assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# handle_manychat_webhook
# ---------------------------------------------------------------------------


class TestHandleManychatWebhook:
    @pytest.mark.asyncio
    async def test_invalid_json_raises_400(self):
        req = _mock_request({})
        req.json = AsyncMock(side_effect=ValueError("bad json"))
        db = _mock_db()

        with pytest.raises(HTTPException) as exc_info:
            await handle_manychat_webhook(TENANT_ID, req, db)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_missing_event_type_raises_422(self):
        req = _mock_request({"subscriber_id": "sub_1", "channel": "instagram"})
        db = _mock_db()

        with pytest.raises(HTTPException) as exc_info:
            await handle_manychat_webhook(TENANT_ID, req, db)
        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_no_manychat_connection_returns_ignored(self):
        payload = {"event_type": "subscriber.new", "subscriber_id": "sub_1", "channel": "instagram"}
        req = _mock_request(payload)
        db = _mock_db()
        db.execute.return_value.scalar_one_or_none.return_value = None

        result = await handle_manychat_webhook(TENANT_ID, req, db)
        assert result["status"] == "ignored"
        assert result["reason"] == "no_manychat_connection"

    @pytest.mark.asyncio
    async def test_valid_event_dispatches_to_handler(self):
        payload = {"event_type": "subscriber.new", "subscriber_id": "sub_1", "channel": "instagram"}
        req = _mock_request(payload)
        db = _mock_db()
        connection = MagicMock()
        db.execute.return_value.scalar_one_or_none.return_value = connection

        with patch(
            "luana_core_connections.api.marketing_webhooks._handle_manychat_event", new_callable=AsyncMock
        ) as mock_handler:
            result = await handle_manychat_webhook(TENANT_ID, req, db)

        mock_handler.assert_called_once()
        assert result["status"] == "processed"
        assert result["event"] == "subscriber.new"
