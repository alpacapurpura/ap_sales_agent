"""Tests for pure domain helpers (text matching + expected metric resolver)."""

from src.modules.advertising.domain.enums import (
    OfferExpectedMetric,
    expected_metric_for_objective,
    expected_metric_label_es,
    objective_label_es,
    resolve_expected_metric,
)
from src.modules.advertising.domain.text_matching import (
    jaccard_similarity,
    normalize_url,
    tokenize_es,
    urls_match,
)


class TestNormalizeUrl:
    def test_strips_scheme_and_www_and_trailing_slash(self):
        assert (
            normalize_url("https://www.Visionarias.com/masterclass/")
            == "visionarias.com/masterclass"
        )

    def test_strips_query_string(self):
        assert (
            normalize_url("https://visionarias.com/masterclass/?utm_source=fb")
            == "visionarias.com/masterclass"
        )

    def test_empty_input(self):
        assert normalize_url(None) == ""
        assert normalize_url("") == ""
        assert normalize_url("   ") == ""

    def test_no_scheme(self):
        assert normalize_url("visionarias.com/foo") == "visionarias.com/foo"


class TestUrlsMatch:
    def test_symmetric_contains(self):
        assert urls_match(
            "https://visionarias.com/masterclass",
            "https://www.visionarias.com/masterclass?x=1",
        )

    def test_ad_longer_than_offer(self):
        # Ad URL includes offer URL path.
        assert urls_match(
            "https://visionarias.com/masterclass/lp-v2",
            "visionarias.com/masterclass",
        )

    def test_no_match_different_domains(self):
        assert not urls_match(
            "https://visionarias.com/a",
            "https://otrasite.com/a",
        )

    def test_empty_inputs(self):
        assert not urls_match("", "https://x.com")
        assert not urls_match(None, None)


class TestTokenizeEs:
    def test_removes_stopwords_and_short_tokens(self):
        assert tokenize_es("Curso de Marketing para creadores") == {
            "curso",
            "marketing",
            "creadores",
        }

    def test_lowercases_and_strips_punctuation(self):
        assert tokenize_es("¡Promoción! Masterclass - 2024") == {
            "promoción",
            "masterclass",
            "2024",
        }

    def test_empty(self):
        assert tokenize_es(None) == set()
        assert tokenize_es("") == set()


class TestJaccard:
    def test_basic(self):
        assert jaccard_similarity({"a", "b"}, {"a", "b"}) == 1.0
        assert jaccard_similarity({"a", "b"}, {"c", "d"}) == 0.0
        assert abs(jaccard_similarity({"a", "b", "c"}, {"a", "b"}) - 2 / 3) < 1e-9

    def test_empty(self):
        assert jaccard_similarity(set(), {"a"}) == 0.0
        assert jaccard_similarity({"a"}, set()) == 0.0


class TestResolveExpectedMetric:
    def test_lead_magnet_wins(self):
        assert (
            resolve_expected_metric(
                archetype="PRODUCTO",
                onboarding_action=None,
                is_lead_magnet=True,
                has_checkout_url=True,
            )
            == OfferExpectedMetric.LEAD
        )

    def test_servicio_with_kickoff_call(self):
        assert (
            resolve_expected_metric(
                archetype="SERVICIO",
                onboarding_action="BOOK_KICKOFF_CALL",
                is_lead_magnet=False,
                has_checkout_url=False,
            )
            == OfferExpectedMetric.CALL_BOOKED
        )

    def test_servicio_with_intake_form(self):
        assert (
            resolve_expected_metric(
                archetype="SERVICIO",
                onboarding_action="FILL_INTAKE_FORM",
                is_lead_magnet=False,
                has_checkout_url=False,
            )
            == OfferExpectedMetric.FORM_SUBMIT
        )

    def test_producto_with_checkout(self):
        assert (
            resolve_expected_metric(
                archetype="PRODUCTO",
                onboarding_action=None,
                is_lead_magnet=False,
                has_checkout_url=True,
            )
            == OfferExpectedMetric.PURCHASE
        )

    def test_membresia_with_checkout_is_subscription(self):
        assert (
            resolve_expected_metric(
                archetype="MEMBRESIA",
                onboarding_action=None,
                is_lead_magnet=False,
                has_checkout_url=True,
            )
            == OfferExpectedMetric.SUBSCRIPTION
        )

    def test_servicio_fallback_message(self):
        assert (
            resolve_expected_metric(
                archetype="SERVICIO",
                onboarding_action=None,
                is_lead_magnet=False,
                has_checkout_url=False,
            )
            == OfferExpectedMetric.MESSAGE
        )

    def test_default_fallback_lead(self):
        assert (
            resolve_expected_metric(
                archetype="PROGRAMA",
                onboarding_action=None,
                is_lead_magnet=False,
                has_checkout_url=False,
            )
            == OfferExpectedMetric.LEAD
        )


class TestExpectedMetricForObjective:
    def test_sales_maps_to_purchase(self):
        assert (
            expected_metric_for_objective("OUTCOME_SALES")
            == OfferExpectedMetric.PURCHASE
        )

    def test_messages_maps_to_message(self):
        assert (
            expected_metric_for_objective("OUTCOME_MESSAGES")
            == OfferExpectedMetric.MESSAGE
        )

    def test_leads_maps_to_lead(self):
        assert (
            expected_metric_for_objective("OUTCOME_LEADS") == OfferExpectedMetric.LEAD
        )

    def test_traffic_is_none(self):
        assert expected_metric_for_objective("OUTCOME_TRAFFIC") is None

    def test_none_input(self):
        assert expected_metric_for_objective(None) is None


class TestLabels:
    def test_expected_metric_labels_es_in_spanish(self):
        assert expected_metric_label_es("lead") == "Lead"
        assert expected_metric_label_es("call_booked") == "Llamada agendada"
        assert expected_metric_label_es("subscription") == "Suscripción"

    def test_objective_labels_es(self):
        assert objective_label_es("OUTCOME_SALES") == "Ventas"
        assert objective_label_es("OUTCOME_MESSAGES") == "Mensajes"
        assert objective_label_es(None) == "Sin objetivo"
