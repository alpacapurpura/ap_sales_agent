"""Tests for Interview Engine domain entities and value objects."""

from dataclasses import FrozenInstanceError, asdict
from uuid import uuid4

import pytest

from src.modules.copilot.domain.interview_config import InterviewBlock, InterviewConfig
from src.modules.copilot.domain.interview_configs.brand_config import (
    BRAND_INTERVIEW_CONFIG,
)
from src.modules.copilot.domain.interview_session import (
    InterviewSession,
    InterviewStatus,
)


class TestInterviewStatus:
    def test_all_statuses_exist(self):
        assert InterviewStatus.ACTIVE == "active"
        assert InterviewStatus.PAUSED == "paused"
        assert InterviewStatus.COMPLETED == "completed"
        assert InterviewStatus.ABANDONED == "abandoned"


class TestInterviewBlock:
    def test_frozen_dataclass(self):
        block = InterviewBlock(
            id="identidad",
            label="Tu Identidad",
            campos_objetivo=["story.origin_story", "story.mission"],
            prompt_context="Explora el origen de la marca.",
        )
        assert block.id == "identidad"
        assert block.coverage_threshold == 0.8
        with pytest.raises((FrozenInstanceError, AttributeError)):
            block.id = "other"


class TestInterviewConfig:
    def test_frozen_dataclass(self):
        config = InterviewConfig(
            domain="brand",
            objetivo="Completar Brand Studio",
            bloques=[
                InterviewBlock(
                    id="b1",
                    label="B1",
                    campos_objetivo=["f1"],
                    prompt_context="ctx",
                ),
            ],
            output_schema_path="modules.brand.domain.BrandSettings",
            datos_previos_fields=["identity.brand_name"],
            tono="consultor senior",
            expertise_template="brand_expertise",
        )
        assert config.domain == "brand"
        assert config.max_mensajes == 60
        assert config.rag_collection is None

    def test_serializable_to_dict(self):
        config = InterviewConfig(
            domain="brand",
            objetivo="Test",
            bloques=[],
            output_schema_path="test.Path",
            datos_previos_fields=[],
            tono="test",
            expertise_template="test",
        )
        d = asdict(config)
        assert d["domain"] == "brand"
        assert isinstance(d["bloques"], list)


class TestInterviewSession:
    def test_create_new_session(self):
        tenant_id = uuid4()
        session = InterviewSession.create(
            tenant_id=tenant_id,
            domain="brand",
            config=BRAND_INTERVIEW_CONFIG,
            conversation_id=uuid4(),
        )
        assert session.tenant_id == tenant_id
        assert session.status == InterviewStatus.ACTIVE
        assert session.bloque_actual == BRAND_INTERVIEW_CONFIG.bloques[0].id
        assert session.bloques_completados == []
        assert session.messages_count == 0
        assert session.mapa_global == {}

    def test_advance_block(self):
        session = InterviewSession.create(
            tenant_id=uuid4(),
            domain="brand",
            config=BRAND_INTERVIEW_CONFIG,
            conversation_id=uuid4(),
        )
        first_block = session.bloque_actual
        session.advance_block(first_block)
        assert first_block in session.bloques_completados
        assert session.bloque_actual == BRAND_INTERVIEW_CONFIG.bloques[1].id

    def test_advance_last_block_completes(self):
        session = InterviewSession.create(
            tenant_id=uuid4(),
            domain="brand",
            config=BRAND_INTERVIEW_CONFIG,
            conversation_id=uuid4(),
        )
        for block in BRAND_INTERVIEW_CONFIG.bloques:
            session.advance_block(block.id)
        assert session.status == InterviewStatus.COMPLETED

    def test_pause_and_resume(self):
        session = InterviewSession.create(
            tenant_id=uuid4(),
            domain="brand",
            config=BRAND_INTERVIEW_CONFIG,
            conversation_id=uuid4(),
        )
        session.pause()
        assert session.status == InterviewStatus.PAUSED
        session.resume()
        assert session.status == InterviewStatus.ACTIVE

    def test_update_mapa_global_merge(self):
        session = InterviewSession.create(
            tenant_id=uuid4(),
            domain="brand",
            config=BRAND_INTERVIEW_CONFIG,
            conversation_id=uuid4(),
        )
        session.update_mapa_global({"story.origin_story": "Test origin"})
        assert session.mapa_global["story.origin_story"] == "Test origin"
        session.update_mapa_global({"story.mission": "Test mission"})
        assert session.mapa_global["story.origin_story"] == "Test origin"
        assert session.mapa_global["story.mission"] == "Test mission"

    def test_coverage_for_block(self):
        session = InterviewSession.create(
            tenant_id=uuid4(),
            domain="brand",
            config=BRAND_INTERVIEW_CONFIG,
            conversation_id=uuid4(),
        )
        assert session.coverage_for_block("identidad") == 0.0
        campos = BRAND_INTERVIEW_CONFIG.bloques[0].campos_objetivo
        for field in campos[:3]:
            session.update_mapa_global({field: "value"})
        coverage = session.coverage_for_block("identidad")
        assert coverage == pytest.approx(3 / len(campos), rel=0.01)

    def test_increment_messages(self):
        session = InterviewSession.create(
            tenant_id=uuid4(),
            domain="brand",
            config=BRAND_INTERVIEW_CONFIG,
            conversation_id=uuid4(),
        )
        session.increment_messages()
        assert session.messages_count == 1


class TestBrandInterviewConfig:
    def test_has_5_blocks(self):
        assert len(BRAND_INTERVIEW_CONFIG.bloques) == 5

    def test_block_ids(self):
        ids = [b.id for b in BRAND_INTERVIEW_CONFIG.bloques]
        assert ids == [
            "identidad",
            "posicionamiento",
            "narrativa",
            "publico",
            "identidad_creativa",
        ]

    def test_all_blocks_have_campos(self):
        for block in BRAND_INTERVIEW_CONFIG.bloques:
            assert len(block.campos_objetivo) > 0
            assert block.label != ""
            assert block.prompt_context != ""

    def test_domain_is_brand(self):
        assert BRAND_INTERVIEW_CONFIG.domain == "brand"
        assert BRAND_INTERVIEW_CONFIG.expertise_template == "brand_expertise"
