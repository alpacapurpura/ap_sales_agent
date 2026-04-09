"""Tests for enhanced Mailerlite provider extraction."""

from src.modules.analytics.infrastructure.providers.mailerlite_provider import (
    MAILERLITE_METRIC_MAP,
    classify_campaign_type,
)


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
        assert (
            classify_campaign_type("Edicion 5", "Novedades de la semana")
            == "newsletter"
        )

    def test_newsletter_digest(self):
        assert classify_campaign_type("Digest mensual", "") == "newsletter"

    def test_launch_from_name(self):
        assert classify_campaign_type("Lanzamiento Curso Premium", "") == "lanzamiento"

    def test_launch_exclusivo(self):
        assert (
            classify_campaign_type("Acceso exclusivo", "Estreno del programa")
            == "lanzamiento"
        )

    def test_promo_from_name(self):
        assert classify_campaign_type("Promo Black Friday -40%", "") == "promocion"

    def test_promo_from_discount(self):
        assert (
            classify_campaign_type("Oferta especial", "50% de descuento") == "promocion"
        )

    def test_promo_free(self):
        assert classify_campaign_type("Recurso gratis", "") == "promocion"

    def test_content_default(self):
        assert (
            classify_campaign_type("5 Tips de Fotografia", "Aprende mas") == "contenido"
        )

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

        from src.modules.analytics.infrastructure.providers.mailerlite_provider import (
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

    def test_campaign_without_emails_field(self):
        """Campaign without emails field should default to empty subject."""
        from datetime import date

        from src.modules.analytics.infrastructure.providers.mailerlite_provider import (
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
