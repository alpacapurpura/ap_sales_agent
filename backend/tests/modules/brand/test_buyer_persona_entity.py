"""Tests for BuyerPersona domain entity."""

from uuid import uuid4

from src.modules.brand.domain.buyer_persona import BuyerPersona


def test_create_buyer_persona() -> None:
    """Test creating a buyer persona with minimal fields."""
    persona = BuyerPersona(
        id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        name="Maria",
        tagline="Quiere escalar sin perder autenticidad",
    )
    assert persona.name == "Maria"
    assert persona.scope == "GLOBAL"
    assert persona.is_primary is False
    assert persona.demographics == {}
    assert persona.pain_points == []
    assert persona.completeness_score == 0.0


def test_buyer_persona_with_full_profile() -> None:
    """Test buyer persona with demographics and pain points."""
    persona = BuyerPersona(
        id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        name="Carlos",
        demographics={"age_range": "30-40", "location": "LATAM"},
        pain_points=[
            {"description": "No puede escalar", "intensity": "high"},
        ],
        desires=[
            {"description": "Automatizar ventas", "priority": "high"},
        ],
        completeness_score=45.0,
    )
    assert persona.demographics["age_range"] == "30-40"
    assert len(persona.pain_points) == 1
    assert persona.completeness_score == 45.0


def test_buyer_persona_offer_scope() -> None:
    """Test buyer persona with OFFER scope."""
    offer_id = uuid4()
    persona = BuyerPersona(
        id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        name="Offer Persona",
        scope="OFFER",
        offer_id=offer_id,
    )
    assert persona.scope == "OFFER"
    assert persona.offer_id == offer_id


def test_buyer_persona_defaults() -> None:
    """Test default values for optional fields."""
    persona = BuyerPersona(
        id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        name="Default Test",
    )
    assert persona.tagline is None
    assert persona.psychographics == {}
    assert persona.buyer_journey == {}
    assert persona.purchase_triggers == []
    assert persona.anti_patterns == []
    assert persona.is_active is True
    assert persona.deleted_at is None


def test_buyer_persona_from_attributes() -> None:
    """Verify from_attributes=True (ORM mode) works via model_config."""
    persona = BuyerPersona(
        id=uuid4(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        name="ORM Test",
    )
    assert persona.model_config.get("from_attributes") is True
