"""Tests for BuyerPersona SQLAlchemy model."""

from src.modules.brand.infrastructure.models.buyer_persona_model import (
    BuyerPersonaModel,
)


def test_buyer_persona_model_tablename() -> None:
    """Test table name is buyer_personas."""
    assert BuyerPersonaModel.__tablename__ == "buyer_personas"


def test_buyer_persona_model_has_required_columns() -> None:
    """Test all required columns exist in the model."""
    columns = {c.name for c in BuyerPersonaModel.__table__.columns}
    expected = {
        "id",
        "tenant_id",
        "user_id",
        "name",
        "tagline",
        "scope",
        "offer_id",
        "is_primary",
        "demographics",
        "psychographics",
        "pain_points",
        "desires",
        "buyer_journey",
        "purchase_triggers",
        "anti_patterns",
        "completeness_score",
        "is_active",
        "deleted_at",
        "created_at",
        "updated_at",
    }
    assert expected.issubset(columns)


def test_buyer_persona_model_tenant_id_indexed() -> None:
    """Test tenant_id column has an index for performance."""
    tenant_indexed = False
    for idx in BuyerPersonaModel.__table__.indexes:
        col_names = {c.name for c in idx.columns}
        if "tenant_id" in col_names:
            tenant_indexed = True
            break
    assert tenant_indexed, "tenant_id must be indexed"


def test_buyer_persona_model_has_composite_index() -> None:
    """Test composite index on (tenant_id, scope) exists."""
    indexes = {idx.name for idx in BuyerPersonaModel.__table__.indexes}
    assert "ix_buyer_personas_tenant_scope" in indexes
