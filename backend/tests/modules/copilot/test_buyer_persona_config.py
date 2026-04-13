"""Tests for BuyerPersona interview config registration and structure."""

from src.modules.copilot.domain.interview_config import get_interview_config
from src.modules.copilot.domain.interview_configs.buyer_persona_config import (
    BUYER_PERSONA_INTERVIEW_CONFIG,
)


def test_buyer_persona_config_registered() -> None:
    """Test buyer persona config is registered."""
    config = get_interview_config("buyer_persona")
    assert config.domain == "buyer_persona"


def test_buyer_persona_has_5_blocks() -> None:
    """Test buyer persona has 5 blocks."""
    config = BUYER_PERSONA_INTERVIEW_CONFIG
    assert len(config.bloques) == 5


def test_buyer_persona_block_ids() -> None:
    """Test buyer persona block IDs match expected order."""
    config = BUYER_PERSONA_INTERVIEW_CONFIG
    block_ids = [b.id for b in config.bloques]
    assert block_ids == [
        "demographics",
        "psychographics",
        "pain_desire",
        "objections",
        "channels_journey",
    ]


def test_buyer_persona_has_document_template() -> None:
    """Test buyer persona has document extraction template."""
    config = BUYER_PERSONA_INTERVIEW_CONFIG
    assert config.document_extraction_template == "buyer_persona_doc_extraction"


def test_buyer_persona_all_blocks_have_campos() -> None:
    """Test all buyer persona blocks have campos_objetivo."""
    config = BUYER_PERSONA_INTERVIEW_CONFIG
    for block in config.bloques:
        assert len(block.campos_objetivo) > 0, (
            f"Block {block.id} has no campos_objetivo"
        )


def test_buyer_persona_has_expertise_template() -> None:
    """Test buyer persona has expertise template."""
    config = BUYER_PERSONA_INTERVIEW_CONFIG
    assert config.expertise_template == "buyer_persona_expertise"


def test_buyer_persona_output_schema_path() -> None:
    """Test buyer persona output schema path contains domain."""
    config = BUYER_PERSONA_INTERVIEW_CONFIG
    assert "buyer_persona" in config.output_schema_path.lower()


def test_buyer_persona_datos_previos_fields() -> None:
    """Test buyer persona datos previos fields."""
    config = BUYER_PERSONA_INTERVIEW_CONFIG
    assert "name" in config.datos_previos_fields
    assert "demographics" in config.datos_previos_fields


def test_buyer_persona_no_rag_collection() -> None:
    """BuyerPersona does not use RAG collection."""
    config = BUYER_PERSONA_INTERVIEW_CONFIG
    assert config.rag_collection is None
