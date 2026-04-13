"""Tests for InterviewSession.revert_to_block."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.modules.copilot.domain.interview_config import InterviewBlock, InterviewConfig
from src.modules.copilot.domain.interview_session import InterviewSession, InterviewStatus

_CONFIG = InterviewConfig(
    domain="offer",
    objetivo="Test offer interview",
    bloques=[
        InterviewBlock(
            id="strategy",
            label="Estrategia",
            campos_objetivo=["strategy.offer_name"],
            prompt_context="Explora la estrategia.",
        ),
        InterviewBlock(
            id="promise",
            label="Promesa",
            campos_objetivo=["promise.headline"],
            prompt_context="Explora la promesa.",
        ),
        InterviewBlock(
            id="pricing",
            label="Precios",
            campos_objetivo=["pricing.total"],
            prompt_context="Explora el pricing.",
        ),
    ],
    output_schema_path="modules.offer.domain.OfferSettings",
    datos_previos_fields=[],
    tono="consultor",
    expertise_template="offer_expertise",
)


def _make_session() -> InterviewSession:
    session = InterviewSession.create(
        tenant_id=uuid4(),
        domain="offer",
        config=_CONFIG,
        conversation_id=uuid4(),
    )
    session.advance_block("strategy")
    session.advance_block("promise")
    return session


class TestRevertToBlock:
    def test_revert_to_earlier_block(self) -> None:
        session = _make_session()
        assert session.bloque_actual == "pricing"
        assert "strategy" in session.bloques_completados
        assert "promise" in session.bloques_completados

        session.revert_to_block("strategy")

        assert session.bloque_actual == "strategy"
        assert session.bloques_completados == []

    def test_revert_to_middle_block(self) -> None:
        session = _make_session()
        session.revert_to_block("promise")

        assert session.bloque_actual == "promise"
        assert session.bloques_completados == ["strategy"]

    def test_revert_to_invalid_block_raises(self) -> None:
        session = _make_session()
        with pytest.raises(ValueError, match="not found"):
            session.revert_to_block("nonexistent")

    def test_revert_keeps_mapa_global(self) -> None:
        session = _make_session()
        session.update_mapa_global({"strategy.offer_name": "Test"})
        session.revert_to_block("strategy")
        assert session.mapa_global["strategy.offer_name"] == "Test"

    def test_revert_sets_status_active(self) -> None:
        session = _make_session()
        session.pause()
        assert session.status == InterviewStatus.PAUSED
        session.revert_to_block("strategy")
        assert session.status == InterviewStatus.ACTIVE
