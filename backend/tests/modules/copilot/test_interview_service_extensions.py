"""Tests for InterviewSession extensions.

Covers entity_id and initial_mapa behavior.
"""

from uuid import uuid4

from src.modules.copilot.domain.interview_config import (
    InterviewBlock,
    InterviewConfig,
)
from src.modules.copilot.domain.interview_session import (
    InterviewSession,
    InterviewStatus,
)
from src.modules.copilot.infrastructure.models.interview_session_model import (
    InterviewSessionModel,
)


def test_interview_session_accepts_entity_id() -> None:
    """Test session accepts entity_id parameter."""
    config = InterviewConfig(
        domain="offer",
        objetivo="test",
        bloques=[
            InterviewBlock(
                id="b1",
                label="B1",
                campos_objetivo=["f1"],
                prompt_context="ctx",
            ),
        ],
        output_schema_path="test",
        datos_previos_fields=[],
        tono="test",
        expertise_template="test",
    )

    entity_id = uuid4()
    session = InterviewSession.create(
        tenant_id=uuid4(),
        domain="offer",
        config=config,
        conversation_id=uuid4(),
        entity_id=entity_id,
        initial_mapa={"public_name": "Test Offer"},
    )

    assert session.entity_id == entity_id
    assert session.mapa_global == {
        "public_name": "Test Offer",
    }
    assert session.status == InterviewStatus.ACTIVE
    assert session.bloque_actual == "b1"


def test_interview_session_entity_id_defaults_to_none() -> None:
    """Test entity_id defaults to None."""
    config = InterviewConfig(
        domain="brand",
        objetivo="test",
        bloques=[
            InterviewBlock(
                id="b1",
                label="B1",
                campos_objetivo=["f1"],
                prompt_context="ctx",
            ),
        ],
        output_schema_path="test",
        datos_previos_fields=[],
        tono="test",
        expertise_template="test",
    )

    session = InterviewSession.create(
        tenant_id=uuid4(),
        domain="brand",
        config=config,
        conversation_id=uuid4(),
    )

    assert session.entity_id is None
    assert session.mapa_global == {}


def test_interview_session_initial_mapa_defaults_to_empty() -> None:
    """Test initial_mapa defaults to empty dict."""
    config = InterviewConfig(
        domain="offer",
        objetivo="test",
        bloques=[
            InterviewBlock(
                id="b1",
                label="B1",
                campos_objetivo=["f1"],
                prompt_context="ctx",
            ),
        ],
        output_schema_path="test",
        datos_previos_fields=[],
        tono="test",
        expertise_template="test",
    )

    session = InterviewSession.create(
        tenant_id=uuid4(),
        domain="offer",
        config=config,
        conversation_id=uuid4(),
        entity_id=uuid4(),
    )

    assert session.mapa_global == {}


def test_interview_session_entity_id_preserved_after_operations() -> None:
    """Test entity_id persists through session operations."""
    config = InterviewConfig(
        domain="offer",
        objetivo="test",
        bloques=[
            InterviewBlock(
                id="b1",
                label="B1",
                campos_objetivo=["f1"],
                prompt_context="ctx",
            ),
            InterviewBlock(
                id="b2",
                label="B2",
                campos_objetivo=["f2"],
                prompt_context="ctx2",
            ),
        ],
        output_schema_path="test",
        datos_previos_fields=[],
        tono="test",
        expertise_template="test",
    )

    entity_id = uuid4()
    session = InterviewSession.create(
        tenant_id=uuid4(),
        domain="offer",
        config=config,
        conversation_id=uuid4(),
        entity_id=entity_id,
        initial_mapa={"name": "Test"},
    )

    session.advance_block("b1")

    assert session.entity_id == entity_id
    assert session.bloque_actual == "b2"
    assert session.mapa_global == {"name": "Test"}


def test_interview_session_model_has_entity_id() -> None:
    """Verify the SQLAlchemy model has entity_id column."""
    columns = {c.name for c in InterviewSessionModel.__table__.columns}
    assert "entity_id" in columns
