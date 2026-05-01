"""Forward-compat invariant: ContactFilterParams MUST contain ALL canonical filters.

Ratchet shrink-only: futuro adds OK; remove FAIL test. Origen: PR-10 PI-1 S4.
Cuando PI-3 agrega filter nuevo → DEBE actualizar CANONICAL_FILTER_FIELDS aquí.
"""

from src.modules.crm.api.dto.contact_filters import ContactFilterParams

CANONICAL_FILTER_FIELDS: frozenset[str] = frozenset(
    {
        "lifecycle_stage_in",
        "score_min",
        "score_max",
        "source_in",
        "has_email",
        "has_phone",
        "has_telegram_id",
        "has_whatsapp_id",
        "has_instagram_id",
        "has_tiktok_id",
        "created_after",
        "created_before",
        "last_activity_after",
        "last_activity_before",
        "is_inactive",
        "has_campaign_engagement",
        "country_in",
        "q",
    }
)


def test_contact_filter_params_includes_all_canonical_fields() -> None:
    """ContactFilterParams DEBE contener todos los campos canónicos.

    Ratchet shrink-only: futuro adds OK; remove FAIL test.
    Cuando PI-3 agrega filter nuevo → actualizar CANONICAL_FILTER_FIELDS aquí.
    """
    actual = frozenset(ContactFilterParams.model_fields.keys())
    missing = CANONICAL_FILTER_FIELDS - actual
    assert not missing, (
        f"ContactFilterParams MISSING canonical fields: {missing}. Forward-compat invariant violated. PR-10 PI-1 S4."
    )


def test_contact_filter_params_no_extra_undocumented_fields() -> None:
    """Si se agrega un field nuevo → DEBE sumarse a CANONICAL_FILTER_FIELDS aquí."""
    actual = frozenset(ContactFilterParams.model_fields.keys())
    extra = actual - CANONICAL_FILTER_FIELDS
    assert not extra, (
        f"ContactFilterParams has UNDOCUMENTED fields: {extra}. Update CANONICAL_FILTER_FIELDS in this test."
    )
