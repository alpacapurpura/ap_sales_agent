"""Tests for enhanced Mailerlite provider extraction."""

import asyncio
import uuid
from datetime import date
from unittest.mock import AsyncMock

from luana_core_analytics_engine.domain.extraction_result import ExtractionResult
from luana_core_analytics_engine.infrastructure.providers.base import ExtractedMetric
from luana_core_analytics_engine.infrastructure.providers.mailerlite_provider import (
    MAILERLITE_METRIC_MAP,
    MailerLiteProvider,
    classify_campaign_type,
)

TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestMailerliteMetricMap:
    def test_opens_count_mapped(self):
        assert "opens_count" in MAILERLITE_METRIC_MAP

    def test_clicks_count_mapped(self):
        assert "clicks_count" in MAILERLITE_METRIC_MAP

    def test_opens_count_canonical_name(self):
        name, unit = MAILERLITE_METRIC_MAP["opens_count"]
        assert name == "opens_count"
        assert unit == "count"

    def test_clicks_count_canonical_name(self):
        name, unit = MAILERLITE_METRIC_MAP["clicks_count"]
        assert name == "clicks_count"
        assert unit == "count"


class TestCampaignTypeClassification:
    def test_newsletter_from_name(self):
        assert classify_campaign_type("Newsletter Semanal #12", "") == "newsletter"

    def test_newsletter_from_subject(self):
        assert classify_campaign_type("Edicion 5", "Novedades de la semana") == "newsletter"

    def test_newsletter_digest(self):
        assert classify_campaign_type("Digest mensual", "") == "newsletter"

    def test_launch_from_name(self):
        assert classify_campaign_type("Lanzamiento Curso Premium", "") == "lanzamiento"

    def test_launch_exclusivo(self):
        assert classify_campaign_type("Acceso exclusivo", "Estreno del programa") == "lanzamiento"

    def test_promo_from_name(self):
        assert classify_campaign_type("Promo Black Friday -40%", "") == "promocion"

    def test_promo_from_discount(self):
        assert classify_campaign_type("Oferta especial", "50% de descuento") == "promocion"

    def test_promo_free(self):
        assert classify_campaign_type("Recurso gratis", "") == "promocion"

    def test_content_default(self):
        assert classify_campaign_type("5 Tips de Fotografia", "Aprende mas") == "contenido"

    def test_reengagement(self):
        assert classify_campaign_type("Te extranamos", "Vuelve") == "reengagement"

    def test_reengagement_miss_you(self):
        assert classify_campaign_type("We miss you", "Come back") == "reengagement"

    def test_case_insensitive(self):
        assert classify_campaign_type("NEWSLETTER SEMANAL", "") == "newsletter"

    def test_empty_strings(self):
        assert classify_campaign_type("", "") == "contenido"

    def test_first_match_wins(self):
        """When multiple types match, the first in iteration order wins."""
        # "newsletter" is checked before "lanzamiento"
        result = classify_campaign_type("Newsletter de lanzamiento", "")
        assert result == "newsletter"


class TestCampaignMetadataInExtra:
    """Test that _aggregate_campaign_metrics includes campaign metadata."""

    def test_aggregate_includes_campaign_metadata(self):
        """Campaign metrics should include per-campaign metadata list in extra."""
        from datetime import date

        from luana_core_analytics_engine.infrastructure.providers.mailerlite_provider import (
            MailerLiteProvider,
        )

        provider = MailerLiteProvider()

        campaigns = [
            {
                "name": "Newsletter Semanal #5",
                "emails": [{"subject": "Novedades de abril"}],
                "stats": {
                    "sent": 100,
                    "unique_opens_count": 40,
                    "open_rate": 0.4,
                },
            },
            {
                "name": "Lanzamiento Curso AI",
                "emails": [{"subject": "Nuevo curso disponible"}],
                "stats": {
                    "sent": 200,
                    "unique_opens_count": 80,
                    "open_rate": 0.4,
                },
            },
        ]

        metrics = provider._aggregate_campaign_metrics(
            campaigns,
            slug="email-nurture",
            metric_date=date(2026, 4, 1),
            known_groups_set=set(),
        )

        # Find a count metric to check its extra
        sent_metric = next((m for m in metrics if m.metric_name == "emails_sent"), None)
        assert sent_metric is not None
        assert "campaigns" in sent_metric.extra

        campaign_list = sent_metric.extra["campaigns"]
        assert len(campaign_list) == 2

        first = campaign_list[0]
        assert first["campaign_name"] == "Newsletter Semanal #5"
        assert first["campaign_subject"] == "Novedades de abril"
        assert first["campaign_type"] == "newsletter"

        second = campaign_list[1]
        assert second["campaign_name"] == "Lanzamiento Curso AI"
        assert second["campaign_subject"] == "Nuevo curso disponible"
        assert second["campaign_type"] == "lanzamiento"

    def test_aggregate_emits_per_campaign_rows_with_campaign_id(self):
        """BUG REGRESSION: _aggregate_campaign_metrics must emit per-campaign
        metric rows with campaign_id set, so the Campañas tab can query them.

        Root cause: the function only emitted daily aggregates (campaign_id=None),
        but _get_campaign_list() filters WHERE campaign_id IS NOT NULL.
        """
        from datetime import date

        from luana_core_analytics_engine.infrastructure.providers.mailerlite_provider import (
            MailerLiteProvider,
        )

        provider = MailerLiteProvider()

        campaigns = [
            {
                "id": "camp_001",
                "name": "Newsletter Semanal #5",
                "emails": [{"subject": "Novedades de abril"}],
                "stats": {
                    "sent": 100,
                    "unique_opens_count": 40,
                    "open_rate": 0.4,
                    "click_rate": 0.1,
                },
            },
            {
                "id": "camp_002",
                "name": "Lanzamiento Curso AI",
                "emails": [{"subject": "Nuevo curso disponible"}],
                "stats": {
                    "sent": 200,
                    "unique_opens_count": 80,
                    "open_rate": 0.4,
                    "click_rate": 0.2,
                },
            },
        ]

        metrics = provider._aggregate_campaign_metrics(
            campaigns,
            slug="email-nurture",
            metric_date=date(2026, 4, 1),
            known_groups_set=set(),
        )

        # Per-campaign rows must exist with campaign_id set
        per_campaign = [m for m in metrics if m.campaign_id is not None]
        assert len(per_campaign) > 0, "No per-campaign metrics emitted — Campañas tab will be empty"

        # Check campaign_001 has emails_sent metric
        camp1_sent = [m for m in per_campaign if m.campaign_id == "camp_001" and m.metric_name == "emails_sent"]
        assert len(camp1_sent) == 1
        assert camp1_sent[0].value == 100

        # Check campaign_002 has emails_sent metric
        camp2_sent = [m for m in per_campaign if m.campaign_id == "camp_002" and m.metric_name == "emails_sent"]
        assert len(camp2_sent) == 1
        assert camp2_sent[0].value == 200

        # Per-campaign rows must include metadata in extra
        camp1_metric = camp1_sent[0]
        assert camp1_metric.extra.get("campaign_name") == "Newsletter Semanal #5"
        assert camp1_metric.extra.get("campaign_subject") == "Novedades de abril"
        assert camp1_metric.extra.get("campaign_type") == "newsletter"

        # Daily aggregates (campaign_id=None) should still exist
        daily_agg = [m for m in metrics if m.campaign_id is None]
        assert len(daily_agg) > 0, "Daily aggregate metrics must still be emitted"

    def test_campaign_without_emails_field(self):
        """Campaign without emails field should default to empty subject."""
        from datetime import date

        from luana_core_analytics_engine.infrastructure.providers.mailerlite_provider import (
            MailerLiteProvider,
        )

        provider = MailerLiteProvider()

        campaigns = [
            {
                "name": "Simple campaign",
                "stats": {"sent": 50},
            },
        ]

        metrics = provider._aggregate_campaign_metrics(
            campaigns,
            slug="email-nurture",
            metric_date=date(2026, 4, 1),
            known_groups_set=set(),
        )

        sent_metric = next((m for m in metrics if m.metric_name == "emails_sent"), None)
        assert sent_metric is not None
        campaign_meta = sent_metric.extra["campaigns"][0]
        assert campaign_meta["campaign_name"] == "Simple campaign"
        assert campaign_meta["campaign_subject"] == ""
        assert campaign_meta["campaign_type"] == "contenido"


class TestExtractMetricsDailyOptimized:
    """extract_metrics_daily must batch the full range, not loop day-by-day."""

    def test_calls_extract_metrics_once_for_multiday_range(self):
        """For a 7-day range, extract_metrics should be called ONCE with the
        full range, not 7 times with single-day ranges.

        The base class default loops day-by-day (7 calls). The override
        should call extract_metrics once with (start_date, end_date).
        """
        provider = MailerLiteProvider()

        mock_result = ExtractionResult(
            metrics=[
                ExtractedMetric(
                    provider="mailerlite",
                    channel_slug="email-nurture",
                    metric_name="emails_sent",
                    value=100,
                    unit="count",
                    date=date(2026, 4, 1),
                ),
            ],
        )
        provider.extract_metrics = AsyncMock(return_value=mock_result)

        result = _run(
            provider.extract_metrics_daily(
                tenant_id=TENANT_ID,
                credentials={"api_key": "test"},
                start_date=date(2026, 4, 1),
                end_date=date(2026, 4, 7),
                stage="nurture",
            ),
        )

        # Must be called ONCE with the full range, not 7 times
        assert provider.extract_metrics.call_count == 1, (
            f"Expected 1 call (batched), got {provider.extract_metrics.call_count} "
            f"(day-by-day). Override extract_metrics_daily to batch."
        )
        call_kwargs = provider.extract_metrics.call_args.kwargs
        assert call_kwargs["start_date"] == date(2026, 4, 1)
        assert call_kwargs["end_date"] == date(2026, 4, 7)

        # Metrics from the single call must be returned
        assert len(result.metrics) == 1
        assert result.metrics[0].metric_name == "emails_sent"

    def test_passes_all_parameters_through(self):
        """The override must forward tenant_id, credentials, and stage."""
        provider = MailerLiteProvider()
        provider.extract_metrics = AsyncMock(return_value=ExtractionResult())

        creds = {"api_key": "key123", "stage_group_mapping": {"nurture": ["g1"]}}

        _run(
            provider.extract_metrics_daily(
                tenant_id=TENANT_ID,
                credentials=creds,
                start_date=date(2026, 4, 1),
                end_date=date(2026, 4, 3),
                stage="capture",
            ),
        )

        call_kwargs = provider.extract_metrics.call_args.kwargs
        assert call_kwargs["tenant_id"] == TENANT_ID
        assert call_kwargs["credentials"] == creds
        assert call_kwargs["stage"] == "capture"

    def test_propagates_failures(self):
        """Failures from extract_metrics must propagate through."""
        from luana_core_analytics_engine.domain.extraction_result import SubExtractorFailure

        provider = MailerLiteProvider()
        failure = SubExtractorFailure(
            extractor_name="mailerlite_campaigns",
            error="API timeout",
            error_type="timeout",
        )
        provider.extract_metrics = AsyncMock(
            return_value=ExtractionResult(failures=[failure]),
        )

        result = _run(
            provider.extract_metrics_daily(
                tenant_id=TENANT_ID,
                credentials={"api_key": "test"},
                start_date=date(2026, 4, 1),
                end_date=date(2026, 4, 7),
                stage="nurture",
            ),
        )

        assert len(result.failures) == 1
        assert result.failures[0].extractor_name == "mailerlite_campaigns"


# ---------------------------------------------------------------------------
# Automation type classification
# ---------------------------------------------------------------------------


class TestAutomationTypeClassification:
    def test_welcome_from_bienvenida(self):
        from luana_core_analytics_engine.infrastructure.providers.mailerlite_provider import (
            classify_automation_type,
        )

        assert classify_automation_type("BIENVENIDA: nuevas inscritas") == "welcome"

    def test_welcome_from_english(self):
        from luana_core_analytics_engine.infrastructure.providers.mailerlite_provider import (
            classify_automation_type,
        )

        assert classify_automation_type("Welcome new subscribers") == "welcome"

    def test_nurture_from_nutricion(self):
        from luana_core_analytics_engine.infrastructure.providers.mailerlite_provider import (
            classify_automation_type,
        )

        assert classify_automation_type("Nutrición de leads") == "nurture"

    def test_reengagement(self):
        from luana_core_analytics_engine.infrastructure.providers.mailerlite_provider import (
            classify_automation_type,
        )

        assert classify_automation_type("Re-engagement campaña") == "reengagement"

    def test_post_compra(self):
        from luana_core_analytics_engine.infrastructure.providers.mailerlite_provider import (
            classify_automation_type,
        )

        assert classify_automation_type("Post-compra seguimiento") == "post_compra"

    def test_default_is_workflow(self):
        from luana_core_analytics_engine.infrastructure.providers.mailerlite_provider import (
            classify_automation_type,
        )

        assert classify_automation_type("Visionaras Linktree Workflow") == "workflow"

    def test_case_insensitive(self):
        from luana_core_analytics_engine.infrastructure.providers.mailerlite_provider import (
            classify_automation_type,
        )

        assert classify_automation_type("bienvenida suscriptores") == "welcome"


# ---------------------------------------------------------------------------
# Automation extraction — per-automation rows
# ---------------------------------------------------------------------------


class TestExtractAutomationsPerRow:
    """_extract_automations must emit per-automation rows like campaigns do."""

    MOCK_AUTOMATIONS_RESPONSE = {
        "data": [
            {
                "id": "auto_001",
                "name": "BIENVENIDA: nuevas inscritas",
                "enabled": True,
                "steps_count": 2,
                "stats": {
                    "sent": 11,
                    "completed_subscribers_count": 11,
                    "subscribers_in_queue_count": 0,
                    "open_rate": {"float": 1.0, "string": "100%"},
                    "click_rate": {"float": 0.3636, "string": "36.36%"},
                    "click_to_open_rate": {"float": 0.3636, "string": "36.36%"},
                    "unsubscribes_count": 0,
                },
                "triggers": [{}],
                "steps": [{}, {}],
            },
            {
                "id": "auto_002",
                "name": "LISTA DE ESPERA WORKFLOW",
                "enabled": True,
                "steps_count": 11,
                "stats": {
                    "sent": 16,
                    "completed_subscribers_count": 0,
                    "subscribers_in_queue_count": 9,
                    "open_rate": {"float": 0.625, "string": "62.5%"},
                    "click_rate": {"float": 0.25, "string": "25%"},
                    "click_to_open_rate": {"float": 0.4, "string": "40%"},
                    "unsubscribes_count": 1,
                },
                "triggers": [{}],
                "steps": [{} for _ in range(11)],
            },
        ],
    }

    def _run_extract(self, automations_response=None):
        """Run _extract_automations with mocked _api_get."""
        from unittest.mock import MagicMock, patch

        if automations_response is None:
            automations_response = self.MOCK_AUTOMATIONS_RESPONSE

        mock_response = MagicMock()
        mock_response.json.return_value = automations_response
        mock_response.status_code = 200

        async def fake_api_get(*args, **kwargs):
            return mock_response

        provider = MailerLiteProvider()
        client = AsyncMock()  # not used directly — _api_get is patched

        with patch(
            "luana_core_analytics_engine.infrastructure.providers.mailerlite_provider._api_get",
            side_effect=fake_api_get,
        ):
            return _run(
                provider._extract_automations(
                    client,
                    {},
                    {},
                    date(2026, 4, 1),
                    date(2026, 4, 10),
                    "email-nurture",
                ),
            )

    def test_emits_per_automation_rows_with_campaign_id(self):
        metrics = self._run_extract()

        per_auto = [m for m in metrics if m.campaign_id is not None]
        assert len(per_auto) > 0, "Must emit per-automation rows with campaign_id"

        auto_001_metrics = [m for m in per_auto if m.campaign_id == "auto_001"]
        assert len(auto_001_metrics) > 0

        sent = next(
            (m for m in auto_001_metrics if m.metric_name == "emails_sent"),
            None,
        )
        assert sent is not None
        assert sent.value == 11

    def test_per_automation_rows_have_source_in_extra(self):
        metrics = self._run_extract()
        per_auto = [m for m in metrics if m.campaign_id is not None]
        for m in per_auto:
            assert m.extra.get("source") == "automation", (
                f"Metric {m.metric_name} for {m.campaign_id} missing source=automation"
            )

    def test_per_automation_rows_have_metadata(self):
        metrics = self._run_extract()
        auto_001 = [m for m in metrics if m.campaign_id == "auto_001"]
        first = auto_001[0]
        assert first.extra["automation_name"] == "BIENVENIDA: nuevas inscritas"
        assert first.extra["automation_status"] == "active"
        assert first.extra["automation_type"] == "welcome"
        assert first.extra["completed_subscribers"] == 11
        assert first.extra["subscribers_in_queue"] == 0

    def test_rates_converted_to_percentage(self):
        metrics = self._run_extract()
        auto_001_open = next(
            (m for m in metrics if m.campaign_id == "auto_001" and m.metric_name == "open_rate"),
            None,
        )
        assert auto_001_open is not None
        assert auto_001_open.value == 100.0  # 1.0 * 100
        assert auto_001_open.unit == "percentage"

    def test_channel_slug_is_email_nurture(self):
        metrics = self._run_extract()
        for m in metrics:
            assert m.channel_slug == "email-nurture"

    def test_empty_automations_returns_empty(self):
        metrics = self._run_extract(automations_response={"data": []})
        assert metrics == []


class TestAutomationStepExtraction:
    """Tests for per-step email data extraction in _extract_automations."""

    def _build_mock_automation(self) -> dict:
        """Build a mock MailerLite /automations response object with steps."""
        return {
            "id": "auto-123",
            "name": "BIENVENIDA: nuevas inscritas",
            "enabled": True,
            "stats": {
                "sent": 18,
                "completed_subscribers_count": 4,
                "subscribers_in_queue_count": 5,
                "open_rate": {"float": 0.85, "string": "85.0%"},
                "click_rate": {"float": 0.42, "string": "42.0%"},
                "click_to_open_rate": {"float": 0.49, "string": "49.0%"},
                "unsubscribes_count": 1,
            },
            "steps": [
                {
                    "id": "step-1",
                    "type": "email",
                    "subject": "¡Bienvenida!",
                    "from_name": "Visionarias",
                    "email": {
                        "screenshot_url": "https://img.example/1.png",
                        "preview_url": "https://preview.example/1",
                        "stats": {
                            "sent": 9,
                            "unique_opens_count": 9,
                            "open_rate": {"float": 1.0, "string": "100%"},
                            "unique_clicks_count": 9,
                            "click_rate": {"float": 1.0, "string": "100%"},
                            "unsubscribes_count": 0,
                            "hard_bounces_count": 0,
                            "soft_bounces_count": 0,
                        },
                    },
                },
                {
                    "id": "step-2",
                    "type": "delay",
                    "unit": "days",
                    "value": 2,
                },
                {
                    "id": "step-3",
                    "type": "email",
                    "subject": "Próximos pasos",
                    "from_name": "Visionarias",
                    "email": {
                        "screenshot_url": None,
                        "preview_url": "https://preview.example/3",
                        "stats": {
                            "sent": 4,
                            "unique_opens_count": 3,
                            "open_rate": {"float": 0.75, "string": "75%"},
                            "unique_clicks_count": 1,
                            "click_rate": {"float": 0.25, "string": "25%"},
                            "unsubscribes_count": 1,
                            "hard_bounces_count": 0,
                            "soft_bounces_count": 0,
                        },
                    },
                },
            ],
        }

    def test_extracts_steps_into_extra(self):
        """Provider extra must contain steps array with per-email data."""
        from unittest.mock import MagicMock, patch

        from luana_core_analytics_engine.infrastructure.providers.mailerlite_provider import (
            MailerLiteProvider,
        )

        provider = MailerLiteProvider()
        mock_auto = self._build_mock_automation()

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": [mock_auto]}
        mock_response.status_code = 200

        async def fake_api_get(*args, **kwargs):
            return mock_response

        mock_client = AsyncMock()

        with patch(
            "luana_core_analytics_engine.infrastructure.providers.mailerlite_provider._api_get",
            side_effect=fake_api_get,
        ):
            metrics = _run(
                provider._extract_automations(
                    mock_client,
                    {},
                    {},
                    date(2026, 4, 1),
                    date(2026, 4, 10),
                    "email-nurture",
                ),
            )

        assert len(metrics) > 0
        first = metrics[0]
        assert first.extra["source"] == "automation"
        assert "steps" in first.extra
        steps = first.extra["steps"]
        assert len(steps) == 3
        assert steps[0]["type"] == "email"
        assert steps[0]["subject"] == "¡Bienvenida!"
        assert steps[0]["emails_sent"] == 9
        assert steps[0]["open_rate"] == 100.0
        assert steps[0]["click_rate"] == 100.0
        assert steps[0]["screenshot_url"] == "https://img.example/1.png"
        assert steps[0]["preview_url"] == "https://preview.example/1"
        assert steps[1]["type"] == "delay"
        assert steps[1]["delay_value"] == 2
        assert steps[1]["delay_unit"] == "days"
        assert steps[2]["unsubscribes"] == 1

    def test_reads_enabled_flag_for_status(self):
        """automation_status must read the enabled flag, not hardcoded."""
        from unittest.mock import MagicMock, patch

        from luana_core_analytics_engine.infrastructure.providers.mailerlite_provider import (
            MailerLiteProvider,
        )

        provider = MailerLiteProvider()
        paused_auto = self._build_mock_automation()
        paused_auto["enabled"] = False

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": [paused_auto]}
        mock_response.status_code = 200

        async def fake_api_get(*args, **kwargs):
            return mock_response

        mock_client = AsyncMock()

        with patch(
            "luana_core_analytics_engine.infrastructure.providers.mailerlite_provider._api_get",
            side_effect=fake_api_get,
        ):
            metrics = _run(
                provider._extract_automations(
                    mock_client,
                    {},
                    {},
                    date(2026, 4, 1),
                    date(2026, 4, 10),
                    "email-nurture",
                ),
            )

        assert metrics[0].extra["automation_status"] == "paused"
