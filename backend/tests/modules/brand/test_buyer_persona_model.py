"""Tests for BuyerPersona SQLAlchemy model."""

from src.modules.brand.infrastructure.models.buyer_persona_model import (
    BuyerPersonaModel,
)


def test_buyer_persona_model_tablename():
    assert BuyerPersonaModel.__tablename__ == "buyer_personas"


def test_buyer_persona_model_has_required_columns():
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
        "objections",
        "preferred_channels",
        "buyer_journey",
        "purchase_triggers",
        "anti_patterns",
        "completeness_score",
        "interview_session_id",
        "is_active",
        "deleted_at",
        "created_at",
        "updated_at",
    }
    assert expected.issubset(columns)


def test_buyer_persona_model_tenant_id_indexed():
    """tenant_id column must have an index for performance."""
    # Check there's an index on tenant_id (either single or composite)
    tenant_indexed = False
    for idx in BuyerPersonaModel.__table__.indexes:
        col_names = {c.name for c in idx.columns}
        if "tenant_id" in col_names:
            tenant_indexed = True
            break
    assert tenant_indexed, "tenant_id must be indexed"


def test_buyer_persona_model_has_composite_index():
    """Composite index on (tenant_id, scope) should exist."""
    indexes = {idx.name for idx in BuyerPersonaModel.__table__.indexes}
    assert "ix_buyer_personas_tenant_scope" in indexes
