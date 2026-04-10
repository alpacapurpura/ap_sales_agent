"""Domain enums for the advertising module (offer-campaign association)."""

from enum import Enum


class AssociationTargetType(str, Enum):
    """Level at which an association targets a Meta object."""

    CAMPAIGN = "campaign"
    AD_SET = "ad_set"


class AssociationType(str, Enum):
    """How the association was produced."""

    MANUAL = "manual"
    AUTO_LANDING_URL = "auto_landing_url"
    AUTO_KEYWORD = "auto_keyword"
    AUTO_OBJECTIVE = "auto_objective"
    EXCLUDED_BRANDING = "excluded_branding"
    SUGGESTED = "suggested"  # auto-detected but pending user confirmation


class AssociationConfidence(str, Enum):
    """Confidence level for auto-detected associations."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class OfferExpectedMetric(str, Enum):
    """Primary outcome metric expected for an offer.

    Derived from the offer archetype + onboarding_action + is_lead_magnet.
    Used to interpret ad performance naturally (CPL vs ROAS vs cost-per-message).
    """

    LEAD = "lead"
    MESSAGE = "message"
    PURCHASE = "purchase"
    SUBSCRIPTION = "subscription"
    CALL_BOOKED = "call_booked"
    FORM_SUBMIT = "form_submit"


_EXPECTED_METRIC_LABELS_ES: dict[str, str] = {
    OfferExpectedMetric.LEAD.value: "Lead",
    OfferExpectedMetric.MESSAGE.value: "Mensaje",
    OfferExpectedMetric.PURCHASE.value: "Compra",
    OfferExpectedMetric.SUBSCRIPTION.value: "Suscripción",
    OfferExpectedMetric.CALL_BOOKED.value: "Llamada agendada",
    OfferExpectedMetric.FORM_SUBMIT.value: "Formulario enviado",
}

_OBJECTIVE_LABELS_ES: dict[str, str] = {
    "OUTCOME_SALES": "Ventas",
    "OUTCOME_LEADS": "Clientes potenciales",
    "OUTCOME_ENGAGEMENT": "Interacción",
    "OUTCOME_AWARENESS": "Reconocimiento",
    "OUTCOME_TRAFFIC": "Tráfico",
    "OUTCOME_APP_PROMOTION": "Promoción de app",
    "CONVERSIONS": "Conversiones",
    "LEAD_GENERATION": "Generación de leads",
    "MESSAGES": "Mensajes",
    "OUTCOME_MESSAGES": "Mensajes",
    "LINK_CLICKS": "Clicks al enlace",
    "REACH": "Alcance",
    "BRAND_AWARENESS": "Reconocimiento de marca",
}


def expected_metric_label_es(metric: str) -> str:
    """Return Spanish label for a given expected-metric value."""
    return _EXPECTED_METRIC_LABELS_ES.get(metric, metric)


def objective_label_es(objective: str | None) -> str:
    """Return Spanish label for a Meta campaign objective."""
    if not objective:
        return "Sin objetivo"
    return _OBJECTIVE_LABELS_ES.get(objective.upper(), objective)


def resolve_expected_metric(
    archetype: str | None,
    onboarding_action: str | None,
    is_lead_magnet: bool,
    has_checkout_url: bool,
) -> OfferExpectedMetric:
    """Derive the primary outcome metric expected for an offer.

    The rules follow the spec in the contract — lead magnets always
    optimise for LEAD, onboarding actions pin specific metrics, and
    the presence of a checkout URL differentiates PURCHASE vs lead-like
    outcomes.
    """
    normalized_archetype = (archetype or "").strip().upper()
    normalized_action = (onboarding_action or "").strip().upper() or None

    if is_lead_magnet:
        return OfferExpectedMetric.LEAD
    if normalized_action == "BOOK_KICKOFF_CALL":
        return OfferExpectedMetric.CALL_BOOKED
    if normalized_action == "FILL_INTAKE_FORM":
        return OfferExpectedMetric.FORM_SUBMIT
    if normalized_action == "JOIN_COMMUNITY" and not has_checkout_url:
        return OfferExpectedMetric.LEAD
    if has_checkout_url:
        if normalized_archetype == "MEMBRESIA":
            return OfferExpectedMetric.SUBSCRIPTION
        return OfferExpectedMetric.PURCHASE
    if normalized_archetype == "SERVICIO":
        return OfferExpectedMetric.MESSAGE
    return OfferExpectedMetric.LEAD


def expected_metric_for_objective(
    objective: str | None,
) -> OfferExpectedMetric | None:
    """Return the metric a Meta campaign objective is optimising for."""
    if not objective:
        return None
    obj = objective.upper()
    if obj in {"OUTCOME_SALES", "CONVERSIONS"}:
        return OfferExpectedMetric.PURCHASE
    if obj in {"OUTCOME_LEADS", "LEAD_GENERATION"}:
        return OfferExpectedMetric.LEAD
    if obj in {"OUTCOME_MESSAGES", "MESSAGES"}:
        return OfferExpectedMetric.MESSAGE
    return None
