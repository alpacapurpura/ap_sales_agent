"""Tests for the Offer interview configuration."""

from src.modules.copilot.domain.interview_config import get_interview_config
from src.modules.copilot.domain.interview_configs.offer_config import (
    OFFER_INTERVIEW_CONFIG,
)


def test_offer_config_registered():
    config = get_interview_config("offer")
    assert config.domain == "offer"


def test_offer_has_6_blocks():
    config = OFFER_INTERVIEW_CONFIG
    assert len(config.bloques) == 6


def test_offer_block_ids():
    config = OFFER_INTERVIEW_CONFIG
    block_ids = [b.id for b in config.bloques]
    assert block_ids == [
        "identity_strategy",
        "promise",
        "psychology",
        "pricing",
        "value_stack",
        "closing",
    ]


def test_offer_has_research_enabled():
    config = OFFER_INTERVIEW_CONFIG
    assert config.initial_research_enabled is True


def test_offer_has_context_loader():
    config = OFFER_INTERVIEW_CONFIG
    assert config.context_loader == "offer_context"


def test_offer_has_document_template():
    config = OFFER_INTERVIEW_CONFIG
    assert config.document_extraction_template == "offer_doc_extraction"


def test_offer_campos_objetivo_are_real_offer_fields():
    """Verify that campos_objetivo map to real Offer entity fields."""
    from src.modules.offer.domain.offer import Offer

    offer_fields = set(Offer.model_fields.keys())
    config = OFFER_INTERVIEW_CONFIG

    for block in config.bloques:
        for campo in block.campos_objetivo:
            # Top-level field name (no dot notation for Offer since it's flat)
            assert campo in offer_fields, (
                f"Campo '{campo}' in block '{block.id}' does not exist in Offer entity. "
                f"Available fields: {sorted(offer_fields)}"
            )


def test_offer_datos_previos_fields_are_real():
    """datos_previos_fields must map to real Offer fields."""
    from src.modules.offer.domain.offer import Offer

    offer_fields = set(Offer.model_fields.keys())

    for field in OFFER_INTERVIEW_CONFIG.datos_previos_fields:
        assert field in offer_fields, (
            f"datos_previos field '{field}' not found in Offer entity"
        )


def test_offer_expertise_template_name():
    config = OFFER_INTERVIEW_CONFIG
    assert config.expertise_template == "offer_expertise"


def test_offer_output_schema_path():
    config = OFFER_INTERVIEW_CONFIG
    assert config.output_schema_path == "modules.offer.domain.offer.Offer"
