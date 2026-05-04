# Interview Engine Phase 2 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable AI Interview Engine (chat-based, consultant-style) integrated into Brand Studio as the first domain, enabling co-creation of brand identity through guided conversation.

**Architecture:** Extends existing Copilot infrastructure (LangGraph ReAct, SSE streaming, tool system) with a new "interview" tool group, dedicated `interview_sessions` table, and a full-takeover split-view page. Backend DDD layers in `modules/copilot/`. Frontend route at `/brand-studio/interview`.

**Tech Stack:** FastAPI + SQLAlchemy 2.0 (sync Session), LangGraph + LangChain tools, Jinja2 prompts, React + Zustand + React Query, Tailwind CSS + Shadcn UI.

**Spec:** `docs/superpowers/specs/2026-04-12-interview-engine-phase2-design.md`

---

## File Structure

### Backend — New Files

| File | Responsibility |
|------|---------------|
| `backend/src/modules/copilot/domain/interview_session.py` | InterviewSession entity + InterviewStatus enum |
| `backend/src/modules/copilot/domain/interview_config.py` | InterviewConfig + InterviewBlock frozen dataclasses |
| `backend/src/modules/copilot/domain/interview_configs/brand_config.py` | Brand-specific InterviewConfig instance (5 blocks) |
| `backend/src/modules/copilot/infrastructure/models/interview_session_model.py` | SQLAlchemy model |
| `backend/src/modules/copilot/infrastructure/repositories/interview_session_repository.py` | CRUD with tenant isolation |
| `backend/src/modules/copilot/infrastructure/persisters/brand_persister.py` | Writes mapa_global → BrandSettings |
| `backend/src/modules/copilot/infrastructure/persisters/persister_registry.py` | DOMAIN_PERSISTERS dict |
| `backend/src/modules/copilot/infrastructure/prompts/templates/interview/system_base.j2` | Base persona template |
| `backend/src/modules/copilot/infrastructure/prompts/templates/interview/brand_expertise.j2` | StoryBrand + BLK frameworks |
| `backend/src/modules/copilot/application/tools/interview/__init__.py` | Tool group export |
| `backend/src/modules/copilot/application/tools/interview/extract_structured.py` | Silent extraction tool |
| `backend/src/modules/copilot/application/tools/interview/offer_alternatives.py` | Alternatives card tool |
| `backend/src/modules/copilot/application/tools/interview/clarify.py` | Clarify card tool |
| `backend/src/modules/copilot/application/tools/interview/checkpoint.py` | Block summary tool |
| `backend/src/modules/copilot/application/tools/interview/advance_block.py` | Persist + advance tool |
| `backend/src/modules/copilot/application/tools/interview/complete_interview.py` | Close session tool |
| `backend/src/modules/copilot/application/services/interview_service.py` | Orchestration service |
| `backend/src/modules/copilot/api/interview.py` | REST endpoints |
| `backend/src/modules/copilot/api/dto/interview_dto.py` | Request/Response DTOs |
| `backend/alembic/versions/xxxx_add_interview_sessions.py` | Idempotent migration |

### Backend — Modified Files

| File | Change |
|------|--------|
| `backend/src/modules/copilot/application/tools/registry.py` | Add `"interview"` tool group + route mapping |
| `backend/src/modules/copilot/api/__init__.py` | Register interview router |

### Frontend — New Files

| File | Responsibility |
|------|---------------|
| `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/interview/page.tsx` | Route entry (Server Component) |
| `frontend/src/features/brand/components/interview/interview-split-view.tsx` | Main split layout |
| `frontend/src/features/brand/components/interview/interview-header.tsx` | Header with progress dots |
| `frontend/src/features/brand/components/interview/session-restore-modal.tsx` | Continue/restart modal |
| `frontend/src/features/copilot/components/interview/interview-chat-panel.tsx` | Chat panel (right side) |
| `frontend/src/features/copilot/components/interview/interview-message.tsx` | Message renderer |
| `frontend/src/features/copilot/components/interview/interview-input.tsx` | Text input + mic placeholder |
| `frontend/src/features/copilot/components/cards/alternatives-card.tsx` | Alternatives selection card |
| `frontend/src/features/copilot/components/cards/clarify-card.tsx` | Contradiction/ambiguity card |
| `frontend/src/features/copilot/components/cards/checkpoint-card.tsx` | Block summary + confirm card |
| `frontend/src/features/copilot/components/cards/interview-complete-card.tsx` | Completion redirect |
| `frontend/src/features/copilot/hooks/useInterviewChat.ts` | Interview-specific chat hook |
| `frontend/src/features/copilot/api/interview-api.ts` | API client functions |
| `frontend/src/components/shared/interview-banner.tsx` | Global sticky banner |

### Frontend — Modified Files

| File | Change |
|------|--------|
| `frontend/src/features/copilot/store/copilot-store.ts` | Add interview mode fields |
| `frontend/src/features/brand/components/onboarding/step-source-picker.tsx` | Enable interview option |
| `frontend/src/features/brand/hooks/useOnboardingWizard.ts` | Route to interview page |
| `frontend/src/app/(main)/[tenantId]/(dashboard)/layout.tsx` | Mount InterviewBanner |

### Tests

| File | What it tests |
|------|--------------|
| `backend/tests/modules/copilot/test_interview_session_domain.py` | Domain entities + VOs |
| `backend/tests/modules/copilot/test_interview_session_repository.py` | Repository CRUD |
| `backend/tests/modules/copilot/test_interview_tools.py` | All 6 tools |
| `backend/tests/modules/copilot/test_interview_service.py` | Service orchestration |
| `backend/tests/modules/copilot/test_interview_api.py` | API endpoints |
| `backend/tests/modules/copilot/test_brand_persister.py` | Brand persistence |
| `frontend/src/features/copilot/components/cards/__tests__/alternatives-card.test.tsx` | Card rendering + interactions |
| `frontend/src/features/copilot/components/cards/__tests__/clarify-card.test.tsx` | Card rendering |
| `frontend/src/features/copilot/components/cards/__tests__/checkpoint-card.test.tsx` | Card rendering + confirm/revise |
| `frontend/src/features/copilot/hooks/__tests__/useInterviewChat.test.ts` | Hook logic |
| `frontend/src/features/brand/components/interview/__tests__/interview-split-view.test.tsx` | Split view layout |

---

## Task 1: Database Migration

**Files:**
- Create: `backend/alembic/versions/20260412_add_interview_sessions.py`

- [ ] **Step 1: Generate migration file**

```bash
cd backend && .venv/bin/alembic revision --autogenerate -m "add_interview_sessions"
```

Replace the autogenerated content with idempotent SQL:

- [ ] **Step 2: Write idempotent migration**

```python
"""add_interview_sessions

Revision ID: <auto>
Revises: <auto>
"""
from alembic import op


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS interview_sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            domain VARCHAR(50) NOT NULL DEFAULT 'brand',
            config_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
            conversation_id UUID REFERENCES copilot_conversations(id) ON DELETE SET NULL,
            mapa_global JSONB NOT NULL DEFAULT '{}'::jsonb,
            bloque_actual VARCHAR(100) NOT NULL DEFAULT '',
            bloques_completados JSONB NOT NULL DEFAULT '[]'::jsonb,
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            messages_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            deleted_at TIMESTAMPTZ
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_interview_sessions_tenant_id
        ON interview_sessions (tenant_id);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_interview_sessions_tenant_domain_status
        ON interview_sessions (tenant_id, domain)
        WHERE status = 'active' AND deleted_at IS NULL;
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_interview_sessions_one_active_per_domain
        ON interview_sessions (tenant_id, domain)
        WHERE status = 'active' AND deleted_at IS NULL;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS interview_sessions;")
```

- [ ] **Step 3: Apply migration**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && alembic upgrade head"
```

- [ ] **Step 4: Verify migration applied**

```bash
docker exec -t visionarias_postgres psql -U postgres -d visionarias_logs -c "\d interview_sessions"
```

Expected: Table with all columns listed above.

- [ ] **Step 5: Commit**

```bash
git add backend/alembic/versions/*interview_sessions*
git commit -m "feat(copilot): add interview_sessions table migration"
```

---

## Task 2: Domain Layer — Entities & Value Objects

**Files:**
- Create: `backend/src/modules/copilot/domain/interview_session.py`
- Create: `backend/src/modules/copilot/domain/interview_config.py`
- Create: `backend/src/modules/copilot/domain/interview_configs/__init__.py`
- Create: `backend/src/modules/copilot/domain/interview_configs/brand_config.py`
- Test: `backend/tests/modules/copilot/test_interview_session_domain.py`

- [ ] **Step 1: Write domain tests**

```python
"""Tests for Interview Engine domain entities and value objects."""
import pytest
from uuid import uuid4

from src.modules.copilot.domain.interview_config import InterviewBlock, InterviewConfig
from src.modules.copilot.domain.interview_configs.brand_config import BRAND_INTERVIEW_CONFIG
from src.modules.copilot.domain.interview_session import InterviewSession, InterviewStatus


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
        with pytest.raises(Exception):  # frozen
            block.id = "other"


class TestInterviewConfig:
    def test_frozen_dataclass(self):
        config = InterviewConfig(
            domain="brand",
            objetivo="Completar Brand Studio",
            bloques=[
                InterviewBlock(id="b1", label="B1", campos_objetivo=["f1"], prompt_context="ctx"),
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
        from dataclasses import asdict
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
        # Initially 0%
        assert session.coverage_for_block("identidad") == 0.0
        # Fill some fields
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
        assert ids == ["identidad", "posicionamiento", "narrativa", "publico", "identidad_creativa"]

    def test_all_blocks_have_campos(self):
        for block in BRAND_INTERVIEW_CONFIG.bloques:
            assert len(block.campos_objetivo) > 0
            assert block.label != ""
            assert block.prompt_context != ""

    def test_domain_is_brand(self):
        assert BRAND_INTERVIEW_CONFIG.domain == "brand"
        assert BRAND_INTERVIEW_CONFIG.expertise_template == "brand_expertise"
```

- [ ] **Step 2: Run tests — verify RED**

```bash
cd backend && .venv/bin/pytest tests/modules/copilot/test_interview_session_domain.py -v
```

Expected: ImportError (modules don't exist yet).

- [ ] **Step 3: Implement InterviewStatus + InterviewSession entity**

```python
# backend/src/modules/copilot/domain/interview_session.py
"""Interview Session domain entity."""
from __future__ import annotations

from dataclasses import asdict
from enum import StrEnum
from uuid import UUID, uuid4

from src.modules.copilot.domain.interview_config import InterviewConfig


class InterviewStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class InterviewSession:
    """Represents an ongoing interview session with a tenant."""

    def __init__(
        self,
        *,
        id: UUID,
        tenant_id: UUID,
        domain: str,
        config_snapshot: dict,
        conversation_id: UUID,
        mapa_global: dict,
        bloque_actual: str,
        bloques_completados: list[str],
        status: InterviewStatus,
        messages_count: int,
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.domain = domain
        self.config_snapshot = config_snapshot
        self.conversation_id = conversation_id
        self.mapa_global = mapa_global
        self.bloque_actual = bloque_actual
        self.bloques_completados = bloques_completados
        self.status = status
        self.messages_count = messages_count

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        domain: str,
        config: InterviewConfig,
        conversation_id: UUID,
    ) -> InterviewSession:
        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            domain=domain,
            config_snapshot=asdict(config),
            conversation_id=conversation_id,
            mapa_global={},
            bloque_actual=config.bloques[0].id,
            bloques_completados=[],
            status=InterviewStatus.ACTIVE,
            messages_count=0,
        )

    def advance_block(self, block_id: str) -> None:
        if block_id not in self.bloques_completados:
            self.bloques_completados.append(block_id)
        bloques = self.config_snapshot["bloques"]
        block_ids = [b["id"] for b in bloques]
        current_idx = block_ids.index(block_id)
        if current_idx + 1 >= len(block_ids):
            self.status = InterviewStatus.COMPLETED
            self.bloque_actual = ""
        else:
            self.bloque_actual = block_ids[current_idx + 1]

    def pause(self) -> None:
        self.status = InterviewStatus.PAUSED

    def resume(self) -> None:
        self.status = InterviewStatus.ACTIVE

    def abandon(self) -> None:
        self.status = InterviewStatus.ABANDONED

    def update_mapa_global(self, delta: dict) -> None:
        self.mapa_global.update(delta)

    def coverage_for_block(self, block_id: str) -> float:
        bloques = self.config_snapshot["bloques"]
        block = next((b for b in bloques if b["id"] == block_id), None)
        if not block:
            return 0.0
        campos = block["campos_objetivo"]
        if not campos:
            return 1.0
        filled = sum(1 for f in campos if f in self.mapa_global and self.mapa_global[f])
        return filled / len(campos)

    def increment_messages(self) -> None:
        self.messages_count += 1
```

- [ ] **Step 4: Implement InterviewConfig + InterviewBlock**

```python
# backend/src/modules/copilot/domain/interview_config.py
"""Interview configuration value objects (frozen, immutable)."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class InterviewBlock:
    id: str
    label: str
    campos_objetivo: list[str]
    prompt_context: str
    coverage_threshold: float = 0.8


@dataclass(frozen=True)
class InterviewConfig:
    domain: str
    objetivo: str
    bloques: list[InterviewBlock]
    output_schema_path: str
    datos_previos_fields: list[str]
    tono: str
    expertise_template: str
    max_mensajes: int = 60
    rag_collection: str | None = None
```

- [ ] **Step 5: Implement BrandInterviewConfig**

```python
# backend/src/modules/copilot/domain/interview_configs/__init__.py
"""Interview configuration instances per domain."""

# backend/src/modules/copilot/domain/interview_configs/brand_config.py
"""Brand Studio interview configuration — 5 thematic blocks."""
from src.modules.copilot.domain.interview_config import InterviewBlock, InterviewConfig

BRAND_INTERVIEW_CONFIG = InterviewConfig(
    domain="brand",
    objetivo="Completar Brand Studio",
    bloques=[
        InterviewBlock(
            id="identidad",
            label="Tu Identidad",
            campos_objetivo=[
                "story.origin_story",
                "story.mission",
                "story.vision",
                "identity.brand_name",
                "identity.industry",
                "positioning.values",
            ],
            prompt_context=(
                "Explora el origen del negocio, la motivación del fundador, y los valores "
                "que guían las decisiones. Pregunta qué problema vieron que nadie resolvía. "
                "Redacta origin_story como narrativa en tercera persona (problema→epifanía→acción). "
                "Misión: verbo + beneficiario + resultado transformador."
            ),
        ),
        InterviewBlock(
            id="posicionamiento",
            label="Tu Posicionamiento",
            campos_objetivo=[
                "positioning.uvp",
                "positioning.discriminator",
                "positioning.competitors",
                "positioning.consumer_insight",
                "positioning.benefits_functional",
                "positioning.benefits_emotional",
            ],
            prompt_context=(
                "Descubre qué hace diferente al negocio. ¿Contra quién compite? "
                "¿Qué dicen los clientes que hace distinto? Usa Brand Love Key: "
                "beneficio funcional, emocional, character, reason to believe. "
                "UVP formato: Para [quién] que [necesita], [producto] es [categoría] que [beneficio]."
            ),
        ),
        InterviewBlock(
            id="narrativa",
            label="Tu Narrativa",
            campos_objetivo=[
                "narrative.hero",
                "narrative.problem",
                "narrative.guide",
                "narrative.plan",
                "narrative.cta",
                "narrative.outcome",
            ],
            prompt_context=(
                "Aplica StoryBrand de Donald Miller. El cliente es el héroe, "
                "la marca es el guía. Identifica el problema externo, interno y filosófico. "
                "El plan son 3-4 pasos simples. CTA directo. Success/failure outcome."
            ),
        ),
        InterviewBlock(
            id="publico",
            label="Tu Público",
            campos_objetivo=[
                "avatars.primary_demographics",
                "avatars.pain_points",
                "avatars.desires",
                "avatars.objections",
                "avatars.channels",
            ],
            prompt_context=(
                "Descubre quién es el cliente ideal. No pedir datos demográficos como encuesta — "
                "preguntar historias: ¿quién te compra? ¿qué les duele? ¿qué sueñan lograr? "
                "¿qué les frena de comprar? ¿dónde pasan tiempo online?"
            ),
        ),
        InterviewBlock(
            id="identidad_creativa",
            label="Tu Identidad Creativa",
            campos_objetivo=[
                "identity.archetype",
                "identity.tone_of_voice",
                "identity.personality_traits",
                "visuals.visual_direction",
                "visuals.mood_keywords",
            ],
            prompt_context=(
                "Explora personalidad y tono de marca. Usa arquetipos de Jung — "
                "ofrecer alternativas con recomendación basada en lo ya capturado. "
                "Tono: cercano/formal, retador/cálido, etc. Dirección visual: keywords de mood."
            ),
        ),
    ],
    output_schema_path="modules.brand.domain.aggregates.BrandSettings",
    datos_previos_fields=[
        "identity.brand_name",
        "identity.website",
        "identity.industry",
        "story.origin_story",
        "story.mission",
    ],
    tono="consultor senior, cercano, directo, experto en branding",
    expertise_template="brand_expertise",
    rag_collection="brand_examples",
)
```

- [ ] **Step 6: Run tests — verify GREEN**

```bash
cd backend && .venv/bin/pytest tests/modules/copilot/test_interview_session_domain.py -v
```

Expected: All tests PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/src/modules/copilot/domain/interview_session.py backend/src/modules/copilot/domain/interview_config.py backend/src/modules/copilot/domain/interview_configs/__init__.py backend/src/modules/copilot/domain/interview_configs/brand_config.py backend/tests/modules/copilot/test_interview_session_domain.py
git commit -m "feat(copilot): add Interview Engine domain entities and value objects"
```

---

## Task 3: Infrastructure — Model + Repository

**Files:**
- Create: `backend/src/modules/copilot/infrastructure/models/interview_session_model.py`
- Create: `backend/src/modules/copilot/infrastructure/repositories/interview_session_repository.py`
- Test: `backend/tests/modules/copilot/test_interview_session_repository.py`

- [ ] **Step 1: Write repository tests**

```python
"""Tests for InterviewSessionRepository."""
import pytest
from uuid import uuid4

from src.modules.copilot.domain.interview_session import InterviewSession, InterviewStatus
from src.modules.copilot.domain.interview_configs.brand_config import BRAND_INTERVIEW_CONFIG
from src.modules.copilot.infrastructure.repositories.interview_session_repository import (
    InterviewSessionRepository,
)


@pytest.fixture
def repo(db):
    return InterviewSessionRepository(db)


@pytest.fixture
def sample_session():
    return InterviewSession.create(
        tenant_id=uuid4(),
        domain="brand",
        config=BRAND_INTERVIEW_CONFIG,
        conversation_id=uuid4(),
    )


class TestInterviewSessionRepository:
    def test_save_and_get(self, repo, sample_session, db):
        repo.save(sample_session)
        db.commit()
        loaded = repo.get_by_id(sample_session.id, sample_session.tenant_id)
        assert loaded is not None
        assert loaded.id == sample_session.id
        assert loaded.domain == "brand"
        assert loaded.status == InterviewStatus.ACTIVE

    def test_get_by_id_wrong_tenant_returns_none(self, repo, sample_session, db):
        repo.save(sample_session)
        db.commit()
        loaded = repo.get_by_id(sample_session.id, uuid4())
        assert loaded is None

    def test_get_active_by_domain(self, repo, sample_session, db):
        repo.save(sample_session)
        db.commit()
        active = repo.get_active_by_domain(sample_session.tenant_id, "brand")
        assert active is not None
        assert active.id == sample_session.id

    def test_get_active_returns_none_when_paused(self, repo, sample_session, db):
        sample_session.pause()
        repo.save(sample_session)
        db.commit()
        active = repo.get_active_by_domain(sample_session.tenant_id, "brand")
        assert active is None

    def test_update_mapa_global(self, repo, sample_session, db):
        repo.save(sample_session)
        db.commit()
        sample_session.update_mapa_global({"story.origin_story": "Test"})
        repo.save(sample_session)
        db.commit()
        loaded = repo.get_by_id(sample_session.id, sample_session.tenant_id)
        assert loaded.mapa_global["story.origin_story"] == "Test"

    def test_soft_delete(self, repo, sample_session, db):
        repo.save(sample_session)
        db.commit()
        repo.soft_delete(sample_session.id, sample_session.tenant_id)
        db.commit()
        loaded = repo.get_by_id(sample_session.id, sample_session.tenant_id)
        assert loaded is None
```

- [ ] **Step 2: Run tests — verify RED**

```bash
cd backend && .venv/bin/pytest tests/modules/copilot/test_interview_session_repository.py -v
```

- [ ] **Step 3: Implement SQLAlchemy model**

```python
# backend/src/modules/copilot/infrastructure/models/interview_session_model.py
"""SQLAlchemy model for interview_sessions table."""
import uuid

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class InterviewSessionModel(Base):
    __tablename__ = "interview_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    domain = Column(String(50), nullable=False, default="brand")
    config_snapshot = Column(JSONB, nullable=False, default=dict)
    conversation_id = Column(UUID(as_uuid=True), nullable=True)
    mapa_global = Column(JSONB, nullable=False, default=dict)
    bloque_actual = Column(String(100), nullable=False, default="")
    bloques_completados = Column(JSONB, nullable=False, default=list)
    status = Column(String(20), nullable=False, default="active")
    messages_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
```

- [ ] **Step 4: Implement repository**

```python
# backend/src/modules/copilot/infrastructure/repositories/interview_session_repository.py
"""Repository for InterviewSession persistence."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from src.modules.copilot.domain.interview_session import InterviewSession, InterviewStatus
from src.modules.copilot.infrastructure.models.interview_session_model import InterviewSessionModel
from src.shared.domain.datetime_utils import utc_now


class InterviewSessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, session: InterviewSession) -> None:
        existing = self.db.execute(
            select(InterviewSessionModel).where(
                InterviewSessionModel.id == session.id,
                InterviewSessionModel.deleted_at.is_(None),
            )
        ).scalars().first()

        if existing:
            existing.mapa_global = session.mapa_global
            existing.bloque_actual = session.bloque_actual
            existing.bloques_completados = session.bloques_completados
            existing.status = session.status.value
            existing.messages_count = session.messages_count
            existing.updated_at = utc_now()
            flag_modified(existing, "mapa_global")
            flag_modified(existing, "bloques_completados")
        else:
            model = InterviewSessionModel(
                id=session.id,
                tenant_id=session.tenant_id,
                domain=session.domain,
                config_snapshot=session.config_snapshot,
                conversation_id=session.conversation_id,
                mapa_global=session.mapa_global,
                bloque_actual=session.bloque_actual,
                bloques_completados=session.bloques_completados,
                status=session.status.value,
                messages_count=session.messages_count,
            )
            self.db.add(model)

    def get_by_id(self, session_id: UUID, tenant_id: UUID) -> InterviewSession | None:
        model = self.db.execute(
            select(InterviewSessionModel).where(
                InterviewSessionModel.id == session_id,
                InterviewSessionModel.tenant_id == tenant_id,
                InterviewSessionModel.deleted_at.is_(None),
            )
        ).scalars().first()
        return self._to_entity(model) if model else None

    def get_active_by_domain(self, tenant_id: UUID, domain: str) -> InterviewSession | None:
        model = self.db.execute(
            select(InterviewSessionModel).where(
                InterviewSessionModel.tenant_id == tenant_id,
                InterviewSessionModel.domain == domain,
                InterviewSessionModel.status == InterviewStatus.ACTIVE.value,
                InterviewSessionModel.deleted_at.is_(None),
            )
        ).scalars().first()
        return self._to_entity(model) if model else None

    def soft_delete(self, session_id: UUID, tenant_id: UUID) -> None:
        model = self.db.execute(
            select(InterviewSessionModel).where(
                InterviewSessionModel.id == session_id,
                InterviewSessionModel.tenant_id == tenant_id,
            )
        ).scalars().first()
        if model:
            model.deleted_at = utc_now()

    def _to_entity(self, model: InterviewSessionModel) -> InterviewSession:
        return InterviewSession(
            id=model.id,
            tenant_id=model.tenant_id,
            domain=model.domain,
            config_snapshot=model.config_snapshot,
            conversation_id=model.conversation_id,
            mapa_global=model.mapa_global,
            bloque_actual=model.bloque_actual,
            bloques_completados=model.bloques_completados,
            status=InterviewStatus(model.status),
            messages_count=model.messages_count,
        )
```

- [ ] **Step 5: Run tests — verify GREEN**

```bash
cd backend && .venv/bin/pytest tests/modules/copilot/test_interview_session_repository.py -v
```

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/copilot/infrastructure/models/interview_session_model.py backend/src/modules/copilot/infrastructure/repositories/interview_session_repository.py backend/tests/modules/copilot/test_interview_session_repository.py
git commit -m "feat(copilot): add InterviewSession SQLAlchemy model and repository"
```

---

## Task 4: Interview Tools — extract_structured + offer_alternatives

**Files:**
- Create: `backend/src/modules/copilot/application/tools/interview/__init__.py`
- Create: `backend/src/modules/copilot/application/tools/interview/extract_structured.py`
- Create: `backend/src/modules/copilot/application/tools/interview/offer_alternatives.py`
- Test: `backend/tests/modules/copilot/test_interview_tools.py`

- [ ] **Step 1: Write tool tests (extract_structured + offer_alternatives)**

```python
"""Tests for Interview Engine tools."""
import json
import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from src.modules.copilot.application.tools.interview.extract_structured import extract_structured
from src.modules.copilot.application.tools.interview.offer_alternatives import offer_alternatives


class TestExtractStructured:
    def test_returns_preview_update_action(self):
        result = extract_structured.invoke({
            "session_id": str(uuid4()),
            "extractions": [
                {"field_path": "story.origin_story", "value": "Test origin", "confidence": 0.9, "source": "user_explicit"},
            ],
        })
        parsed = json.loads(result) if isinstance(result, str) else result
        assert parsed["ui_action"]["type"] == "preview_update"
        assert "story.origin_story" in parsed["ui_action"]["delta"]

    def test_empty_extractions_returns_empty_delta(self):
        result = extract_structured.invoke({
            "session_id": str(uuid4()),
            "extractions": [],
        })
        parsed = json.loads(result) if isinstance(result, str) else result
        assert parsed["ui_action"]["delta"] == {}

    def test_low_confidence_in_confidence_map(self):
        result = extract_structured.invoke({
            "session_id": str(uuid4()),
            "extractions": [
                {"field_path": "positioning.competitors", "value": ["A", "B"], "confidence": 0.6, "source": "inferred"},
            ],
        })
        parsed = json.loads(result) if isinstance(result, str) else result
        assert "positioning.competitors" in parsed["ui_action"]["confidence_map"]
        assert parsed["ui_action"]["confidence_map"]["positioning.competitors"] == 0.6

    def test_text_is_empty_silent(self):
        result = extract_structured.invoke({
            "session_id": str(uuid4()),
            "extractions": [
                {"field_path": "story.mission", "value": "Test", "confidence": 1.0, "source": "user_explicit"},
            ],
        })
        parsed = json.loads(result) if isinstance(result, str) else result
        assert parsed["text"] == ""


class TestOfferAlternatives:
    def test_returns_alternatives_card(self):
        result = offer_alternatives.invoke({
            "field_path": "identity.archetype",
            "question": "Which archetype fits?",
            "alternatives": [
                {"id": "a", "title": "The Magician", "description": "Transforms complex into simple", "recommended": True, "recommendation_reason": "Matches your pitch"},
                {"id": "b", "title": "The Hero", "description": "Empowers users", "recommended": False},
            ],
            "allow_custom": True,
        })
        parsed = json.loads(result) if isinstance(result, str) else result
        assert parsed["ui_action"]["type"] == "alternatives_card"
        assert len(parsed["ui_action"]["alternatives"]) == 2
        assert parsed["ui_action"]["allow_custom"] is True

    def test_text_is_empty(self):
        result = offer_alternatives.invoke({
            "field_path": "identity.tone",
            "question": "Tone?",
            "alternatives": [
                {"id": "a", "title": "A", "description": "Desc", "recommended": False},
                {"id": "b", "title": "B", "description": "Desc", "recommended": True, "recommendation_reason": "Fits better"},
            ],
            "allow_custom": False,
        })
        parsed = json.loads(result) if isinstance(result, str) else result
        assert parsed["text"] == ""
```

- [ ] **Step 2: Run tests — verify RED**

```bash
cd backend && .venv/bin/pytest tests/modules/copilot/test_interview_tools.py::TestExtractStructured -v
cd backend && .venv/bin/pytest tests/modules/copilot/test_interview_tools.py::TestOfferAlternatives -v
```

- [ ] **Step 3: Implement extract_structured tool**

```python
# backend/src/modules/copilot/application/tools/interview/__init__.py
"""Interview tool group for the Interview Engine."""
from src.modules.copilot.application.tools.interview.extract_structured import extract_structured
from src.modules.copilot.application.tools.interview.offer_alternatives import offer_alternatives
from src.modules.copilot.application.tools.interview.clarify import clarify
from src.modules.copilot.application.tools.interview.checkpoint import checkpoint
from src.modules.copilot.application.tools.interview.advance_block import advance_block
from src.modules.copilot.application.tools.interview.complete_interview import complete_interview

INTERVIEW_TOOLS = [
    extract_structured,
    offer_alternatives,
    clarify,
    checkpoint,
    advance_block,
    complete_interview,
]
```

```python
# backend/src/modules/copilot/application/tools/interview/extract_structured.py
"""Silent extraction tool — captures structured data from user messages."""
import json

from langchain_core.tools import tool


@tool
def extract_structured(session_id: str, extractions: list[dict]) -> str:
    """Extract structured data from the user's last message into the mapa_global.

    INVOKE THIS ON EVERY TURN. It is silent — the user does not see any text output.
    Use field_path with dot notation to place data in the correct section regardless of current block.

    Args:
        session_id: The interview session UUID.
        extractions: List of extracted data items. Each has:
            - field_path: Dot-notation path (e.g., "story.origin_story", "positioning.competitors")
            - value: The extracted value (string, list, or dict) — redacted with expert frameworks
            - confidence: Float 0.0-1.0. Below 0.8 means pending clarification.
            - source: "user_explicit" | "inferred" | "recommended"

    Returns:
        JSON with empty text and a preview_update ui_action containing the delta.
    """
    delta = {}
    confidence_map = {}

    for item in extractions:
        field_path = item.get("field_path", "")
        value = item.get("value")
        confidence = item.get("confidence", 1.0)

        if not field_path or value is None:
            continue

        delta[field_path] = value
        if confidence < 0.8:
            confidence_map[field_path] = confidence

    return json.dumps({
        "text": "",
        "ui_action": {
            "type": "preview_update",
            "session_id": session_id,
            "delta": delta,
            "confidence_map": confidence_map,
        },
    })
```

- [ ] **Step 4: Implement offer_alternatives tool**

```python
# backend/src/modules/copilot/application/tools/interview/offer_alternatives.py
"""Offers 2-4 alternatives with recommendation when user is unsure."""
import json

from langchain_core.tools import tool


@tool
def offer_alternatives(
    field_path: str,
    question: str,
    alternatives: list[dict],
    allow_custom: bool = True,
) -> str:
    """Present 2-4 options with your expert recommendation when the user is unsure.

    Use this instead of plain text when offering choices. The frontend renders an interactive card.
    Exactly ONE alternative should have recommended=true.

    Args:
        field_path: The mapa_global field this selection will fill.
        question: Brief context for the user (1-2 sentences max).
        alternatives: 2-4 options. Each has:
            - id: Short identifier ("a", "b", "c")
            - title: Option name
            - description: 1-2 sentence explanation
            - recommended: Boolean (exactly one should be true)
            - recommendation_reason: Why you recommend this (only if recommended=true)
        allow_custom: Whether user can type a custom answer instead.

    Returns:
        JSON with empty text and an alternatives_card ui_action.
    """
    return json.dumps({
        "text": "",
        "ui_action": {
            "type": "alternatives_card",
            "field_path": field_path,
            "question": question,
            "alternatives": alternatives,
            "allow_custom": allow_custom,
        },
    })
```

- [ ] **Step 5: Run tests — verify GREEN**

```bash
cd backend && .venv/bin/pytest tests/modules/copilot/test_interview_tools.py::TestExtractStructured tests/modules/copilot/test_interview_tools.py::TestOfferAlternatives -v
```

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/copilot/application/tools/interview/__init__.py backend/src/modules/copilot/application/tools/interview/extract_structured.py backend/src/modules/copilot/application/tools/interview/offer_alternatives.py backend/tests/modules/copilot/test_interview_tools.py
git commit -m "feat(copilot): add extract_structured and offer_alternatives interview tools"
```

---

## Task 5: Interview Tools — clarify + checkpoint + advance_block + complete_interview

**Files:**
- Create: `backend/src/modules/copilot/application/tools/interview/clarify.py`
- Create: `backend/src/modules/copilot/application/tools/interview/checkpoint.py`
- Create: `backend/src/modules/copilot/application/tools/interview/advance_block.py`
- Create: `backend/src/modules/copilot/application/tools/interview/complete_interview.py`
- Modify: `backend/tests/modules/copilot/test_interview_tools.py` (add more test classes)

- [ ] **Step 1: Add tests for remaining tools**

Append to `backend/tests/modules/copilot/test_interview_tools.py`:

```python
from src.modules.copilot.application.tools.interview.clarify import clarify
from src.modules.copilot.application.tools.interview.checkpoint import checkpoint
from src.modules.copilot.application.tools.interview.advance_block import advance_block
from src.modules.copilot.application.tools.interview.complete_interview import complete_interview


class TestClarify:
    def test_returns_clarify_card(self):
        result = clarify.invoke({
            "items": [
                {"field_path": "positioning.competitors", "issue": "Contradiction detected", "options": ["Option A", "Option B"]},
            ],
        })
        parsed = json.loads(result) if isinstance(result, str) else result
        assert parsed["ui_action"]["type"] == "clarify_card"
        assert len(parsed["ui_action"]["items"]) == 1
        assert parsed["text"] != ""  # clarify HAS visible text

    def test_max_2_items(self):
        result = clarify.invoke({
            "items": [
                {"field_path": "f1", "issue": "Issue 1", "options": ["A"]},
                {"field_path": "f2", "issue": "Issue 2", "options": ["B"]},
                {"field_path": "f3", "issue": "Issue 3", "options": ["C"]},
            ],
        })
        parsed = json.loads(result) if isinstance(result, str) else result
        assert len(parsed["ui_action"]["items"]) <= 2


class TestCheckpoint:
    def test_returns_checkpoint_card(self):
        result = checkpoint.invoke({
            "block_id": "identidad",
            "block_label": "Tu Identidad",
            "summary": {"story.origin_story": "Founded in 2019...", "story.mission": "Democratize sales..."},
            "health_score": 85,
            "blocks_completed": 1,
            "blocks_total": 5,
        })
        parsed = json.loads(result) if isinstance(result, str) else result
        assert parsed["ui_action"]["type"] == "checkpoint_card"
        assert parsed["ui_action"]["block_id"] == "identidad"
        assert parsed["ui_action"]["health_score"] == 85
        assert parsed["text"] != ""


class TestAdvanceBlock:
    def test_returns_preview_update_persisted(self):
        result = advance_block.invoke({
            "block_id": "identidad",
            "persisted_fields": ["story.origin_story", "story.mission"],
            "next_block_id": "posicionamiento",
            "next_block_label": "Tu Posicionamiento",
        })
        parsed = json.loads(result) if isinstance(result, str) else result
        assert parsed["ui_action"]["type"] == "preview_update"
        assert parsed["ui_action"]["persisted"] is True
        assert parsed["metadata"]["next_block"] == "posicionamiento"
        assert parsed["text"] != ""


class TestCompleteInterview:
    def test_returns_interview_complete(self):
        result = complete_interview.invoke({
            "session_id": str(uuid4()),
            "health_score": 92,
            "redirect_path": "/brand-studio",
        })
        parsed = json.loads(result) if isinstance(result, str) else result
        assert parsed["ui_action"]["type"] == "interview_complete"
        assert parsed["ui_action"]["health_score"] == 92
        assert parsed["ui_action"]["redirect"] == "/brand-studio"
```

- [ ] **Step 2: Run tests — verify RED**

```bash
cd backend && .venv/bin/pytest tests/modules/copilot/test_interview_tools.py -v -k "Clarify or Checkpoint or AdvanceBlock or CompleteInterview"
```

- [ ] **Step 3: Implement clarify tool**

```python
# backend/src/modules/copilot/application/tools/interview/clarify.py
"""Clarify tool — surfaces contradictions or ambiguities for user resolution."""
import json

from langchain_core.tools import tool


@tool
def clarify(items: list[dict]) -> str:
    """Present contradictions or ambiguities to the user for quick resolution.

    ONLY use when you detect a real contradiction or ambiguity. NOT for confirming data.
    Max 2 items per invocation. Each item should have 2-4 quick-resolution options.

    Args:
        items: List of ambiguous/contradictory items. Each has:
            - field_path: The field with the issue
            - issue: Brief description of the contradiction (1-2 sentences)
            - options: 2-4 quick resolution options (strings)

    Returns:
        JSON with brief visible text and a clarify_card ui_action.
    """
    # Enforce max 2 items
    capped_items = items[:2]

    return json.dumps({
        "text": "Noté algo que quiero aclarar rápido:",
        "ui_action": {
            "type": "clarify_card",
            "items": capped_items,
        },
    })
```

- [ ] **Step 4: Implement checkpoint tool**

```python
# backend/src/modules/copilot/application/tools/interview/checkpoint.py
"""Checkpoint tool — presents block summary for user confirmation."""
import json

from langchain_core.tools import tool


@tool
def checkpoint(
    block_id: str,
    block_label: str,
    summary: dict,
    health_score: int,
    blocks_completed: int,
    blocks_total: int,
) -> str:
    """Present a compact summary of the current block for user confirmation.

    Use when block coverage > 80%. Keep summary brief — 1 line per field, not paragraphs.
    The user will either confirm (triggers advance_block) or ask to revise.

    Args:
        block_id: ID of the block being closed.
        block_label: Human-readable block name.
        summary: Dict of field_path → short value summary (max 60 chars each).
        health_score: Overall brand health percentage after this block.
        blocks_completed: Number of blocks completed (including this one).
        blocks_total: Total number of blocks.

    Returns:
        JSON with brief text and a checkpoint_card ui_action.
    """
    return json.dumps({
        "text": f"Tengo lo que necesito de {block_label}. Mira cómo quedó:",
        "ui_action": {
            "type": "checkpoint_card",
            "block_id": block_id,
            "block_label": block_label,
            "summary": summary,
            "health_score": health_score,
            "blocks_progress": {"completed": blocks_completed, "total": blocks_total},
        },
    })
```

- [ ] **Step 5: Implement advance_block tool**

```python
# backend/src/modules/copilot/application/tools/interview/advance_block.py
"""Advance block tool — persists confirmed data and moves to next block."""
import json

from langchain_core.tools import tool


@tool
def advance_block(
    block_id: str,
    persisted_fields: list[str],
    next_block_id: str | None = None,
    next_block_label: str | None = None,
) -> str:
    """Persist the confirmed block data to the domain model and advance to next block.

    Invoke ONLY after user confirms a checkpoint. This triggers actual persistence to
    BrandSettings (or equivalent domain model). The frontend uses persisted=true to
    show green highlights.

    Args:
        block_id: The block that was confirmed.
        persisted_fields: List of field_paths that were persisted.
        next_block_id: ID of the next block (None if this was the last).
        next_block_label: Human label of next block.

    Returns:
        JSON with confirmation text and preview_update with persisted=true.
    """
    text = "¡Guardado!"
    if next_block_label:
        text += f" Pasemos a {next_block_label}."
    else:
        text += " Todos los bloques completados."

    return json.dumps({
        "text": text,
        "ui_action": {
            "type": "preview_update",
            "persisted_fields": persisted_fields,
            "persisted": True,
        },
        "metadata": {
            "block_completed": block_id,
            "next_block": next_block_id,
        },
    })
```

- [ ] **Step 6: Implement complete_interview tool**

```python
# backend/src/modules/copilot/application/tools/interview/complete_interview.py
"""Complete interview tool — closes the session and redirects."""
import json

from langchain_core.tools import tool


@tool
def complete_interview(
    session_id: str,
    health_score: int,
    redirect_path: str = "/brand-studio",
) -> str:
    """Close the interview session. All blocks must be completed or the message limit reached.

    This marks the session as COMPLETED, returns copilot to chat mode, and redirects
    the user to the studio page.

    Args:
        session_id: The interview session UUID.
        health_score: Final health percentage of the domain model.
        redirect_path: Where to redirect the user after completion.

    Returns:
        JSON with celebration text and interview_complete ui_action.
    """
    return json.dumps({
        "text": f"¡Tu marca está lista! {health_score}% completa.",
        "ui_action": {
            "type": "interview_complete",
            "session_id": session_id,
            "health_score": health_score,
            "redirect": redirect_path,
        },
    })
```

- [ ] **Step 7: Run tests — verify GREEN**

```bash
cd backend && .venv/bin/pytest tests/modules/copilot/test_interview_tools.py -v
```

- [ ] **Step 8: Commit**

```bash
git add backend/src/modules/copilot/application/tools/interview/clarify.py backend/src/modules/copilot/application/tools/interview/checkpoint.py backend/src/modules/copilot/application/tools/interview/advance_block.py backend/src/modules/copilot/application/tools/interview/complete_interview.py backend/tests/modules/copilot/test_interview_tools.py
git commit -m "feat(copilot): add clarify, checkpoint, advance_block, complete_interview tools"
```

---

## Task 6: Tool Registry + Persister + Prompts

**Files:**
- Modify: `backend/src/modules/copilot/application/tools/registry.py`
- Create: `backend/src/modules/copilot/infrastructure/persisters/persister_registry.py`
- Create: `backend/src/modules/copilot/infrastructure/persisters/brand_persister.py`
- Create: `backend/src/modules/copilot/infrastructure/prompts/templates/interview/system_base.j2`
- Create: `backend/src/modules/copilot/infrastructure/prompts/templates/interview/brand_expertise.j2`
- Test: `backend/tests/modules/copilot/test_brand_persister.py`

- [ ] **Step 1: Write persister test**

```python
"""Tests for BrandPersister."""
import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from src.modules.copilot.infrastructure.persisters.brand_persister import BrandPersister
from src.modules.copilot.infrastructure.persisters.persister_registry import get_persister


class TestBrandPersister:
    def test_persist_partial_data(self):
        db = MagicMock()
        persister = BrandPersister(db)
        tenant_id = uuid4()
        mapa_global = {
            "story.origin_story": "Founded in 2019...",
            "story.mission": "Democratize sales...",
            "identity.brand_name": "Nicolify",
        }
        fields_to_persist = ["story.origin_story", "story.mission", "identity.brand_name"]

        with patch("src.modules.copilot.infrastructure.persisters.brand_persister.BrandRepository") as repo_cls:
            repo_instance = MagicMock()
            repo_instance.get_settings.return_value = MagicMock(
                model_dump=MagicMock(return_value={"identity": {}, "story": {}})
            )
            repo_cls.return_value = repo_instance

            persister.persist(tenant_id, mapa_global, fields_to_persist)
            repo_instance.save_settings.assert_called_once()


class TestPersisterRegistry:
    def test_get_brand_persister(self):
        db = MagicMock()
        persister = get_persister("brand", db)
        assert isinstance(persister, BrandPersister)

    def test_unknown_domain_raises(self):
        db = MagicMock()
        with pytest.raises(ValueError, match="No persister"):
            get_persister("unknown_domain", db)
```

- [ ] **Step 2: Run tests — verify RED**

```bash
cd backend && .venv/bin/pytest tests/modules/copilot/test_brand_persister.py -v
```

- [ ] **Step 3: Implement persister registry + brand persister**

```python
# backend/src/modules/copilot/infrastructure/persisters/persister_registry.py
"""Registry of domain persisters for the Interview Engine."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from src.modules.copilot.infrastructure.persisters.brand_persister import BrandPersister


def get_persister(domain: str, db: "Session") -> "BrandPersister":
    """Get the appropriate persister for a domain."""
    from src.modules.copilot.infrastructure.persisters.brand_persister import BrandPersister

    registry = {
        "brand": BrandPersister,
    }
    persister_cls = registry.get(domain)
    if not persister_cls:
        raise ValueError(f"No persister registered for domain '{domain}'")
    return persister_cls(db)
```

```python
# backend/src/modules/copilot/infrastructure/persisters/brand_persister.py
"""Persists interview mapa_global data into BrandSettings."""
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.brand.infrastructure.repositories.brand_repository import BrandRepository


class BrandPersister:
    """Writes confirmed interview data to BrandSettings (Tenant.config_json)."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = BrandRepository(db)

    def persist(self, tenant_id: UUID, mapa_global: dict, fields_to_persist: list[str]) -> None:
        """Persist specific fields from mapa_global to BrandSettings.

        Args:
            tenant_id: The tenant.
            mapa_global: Full mapa_global dict (flat keys with dot notation).
            fields_to_persist: Which field_paths to actually persist.
        """
        settings = self.repo.get_settings(tenant_id)
        if not settings:
            return

        current = settings.model_dump(mode="json")

        for field_path in fields_to_persist:
            if field_path not in mapa_global:
                continue
            value = mapa_global[field_path]
            parts = field_path.split(".")
            if len(parts) == 2:
                section, key = parts
                if section not in current:
                    current[section] = {}
                if current[section] is None:
                    current[section] = {}
                current[section][key] = value

        from src.modules.brand.domain.aggregates import BrandSettings
        updated_settings = BrandSettings.model_validate(current)
        self.repo.save_settings(tenant_id, updated_settings)
```

- [ ] **Step 4: Register interview tool group in registry.py**

Add to `backend/src/modules/copilot/application/tools/registry.py`:

```python
# Add import at top
from src.modules.copilot.application.tools.interview import INTERVIEW_TOOLS

# Add to TOOL_GROUPS dict
TOOL_GROUPS = {
    ...existing groups,
    "interview": INTERVIEW_TOOLS,
}

# Add to ROUTE_TOOL_MAP
ROUTE_TOOL_MAP = {
    ...existing routes,
    "brand-studio/interview": ["interview", "knowledge"],
}
```

- [ ] **Step 5: Create Jinja2 templates**

```jinja2
{# backend/src/modules/copilot/infrastructure/prompts/templates/interview/system_base.j2 #}
Eres un consultor senior de {{ domain_label }} trabajando con el dueño de un negocio.
Tu rol es COCREAR, no encuestar. Eres el experto — el usuario tiene el conocimiento de su negocio, tú tienes el conocimiento de {{ domain_label }}.

REGLAS ABSOLUTAS:
1. UNA pregunta por mensaje. Breve. Directa. Que invite reflexión profunda.
2. NUNCA preguntes campo por campo como formulario. Preguntas estratégicas abiertas.
3. NUNCA repitas algo que el usuario ya mencionó — revisa el MAPA GLOBAL antes de preguntar.
4. Invoca extract_structured SIEMPRE después de cada mensaje del usuario. Es silencioso.
5. Si el usuario duda o dice "no sé" → usa offer_alternatives con tu recomendación.
6. Si detectas contradicción real → usa clarify (max 2 items). NO para confirmar datos correctos.
7. Cuando el bloque tiene coverage > 80% → usa checkpoint. No te extiendas innecesariamente.
8. Tu texto visible es BREVE. 1-3 oraciones max. La profundidad va en los cards y la extracción.
9. Redacta con expertise los valores que extraes. No copies literal lo que dice el usuario.
10. Da tu recomendación cuando aplica. Eres el experto. El usuario espera tu opinión.

{{ expertise_content }}

CONTROL DE FLUJO:
- Mensajes restantes: {{ messages_remaining }}
{% if messages_remaining <= 10 %}
- ⚠️ QUEDAN {{ messages_remaining }} MENSAJES. Prioriza cerrar bloques pendientes con checkpoint.
{% endif %}
{% if messages_remaining <= 2 %}
- 🚨 ÚLTIMOS MENSAJES. Ejecuta checkpoint del bloque actual AHORA.
{% endif %}

BLOQUE ACTUAL: {{ bloque_actual }} ({{ bloque_label }})
CAMPOS OBJETIVO: {{ campos_objetivo | join(", ") }}
COVERAGE ACTUAL: {{ coverage_percent }}%

MAPA GLOBAL (todo lo capturado — NO preguntar lo que ya está aquí):
{{ mapa_global_json }}

BLOQUES COMPLETADOS: {{ bloques_completados | join(", ") if bloques_completados else "Ninguno aún" }}
BLOQUES PENDIENTES: {{ bloques_pendientes | join(", ") }}
```

```jinja2
{# backend/src/modules/copilot/infrastructure/prompts/templates/interview/brand_expertise.j2 #}
FRAMEWORKS QUE APLICAS AL REDACTAR:

STORYBRAND (Donald Miller):
- Hero: El cliente es el protagonista, NO la marca
- Problem: Externo (situación), Interno (frustración), Filosófico (injusticia)
- Guide: La marca muestra empatía + autoridad
- Plan: 3-4 pasos simples que eliminan confusión
- CTA: Directo y claro
- Success: Transformación específica y medible
- Failure: Lo que pasa si no actúan

BRAND LOVE KEY:
- Beneficio Funcional: Qué problema resuelve concretamente
- Beneficio Emocional: Cómo se SIENTE el cliente después
- Brand Character: Personalidad (3-5 adjetivos)
- Reason to Believe: Prueba concreta de que funciona

ARQUETIPOS DE JUNG (ofrecer con offer_alternatives cuando toque personalidad):
- El Mago: Transforma lo complejo en simple
- El Héroe: Empodera a superar obstáculos
- El Cuidador: Protege y guía
- El Rebelde: Rompe reglas obsoletas
- El Explorador: Descubre nuevas posibilidades
- El Sabio: Comparte conocimiento profundo

REGLAS DE REDACCIÓN POR CAMPO:
- origin_story: Narrativa en tercera persona. Estructura: problema que vio → epifanía → acción.
- mission: Verbo de acción + beneficiario + resultado transformador. Max 1 oración.
- uvp: "Para [quién] que [necesita], [producto] es [categoría] que [beneficio único]."
- values: 3-5 sustantivos abstractos que guían decisiones diarias.
- tone_of_voice: 2-3 adjetivos + ejemplo de frase característica.
- competitors: Nombres reales + categoría (directos vs indirectos vs aspiracionales).
- discriminator: UNA frase que solo TÚ puedes decir. Test: ¿un competidor podría decir lo mismo?

{% if rag_examples %}
EJEMPLOS RELEVANTES DE TU INDUSTRIA:
{{ rag_examples }}
{% endif %}
```

- [ ] **Step 6: Run tests — verify GREEN**

```bash
cd backend && .venv/bin/pytest tests/modules/copilot/test_brand_persister.py -v
```

- [ ] **Step 7: Run full backend tests to verify no regression**

```bash
cd backend && .venv/bin/pytest -x -q --tb=short
```

- [ ] **Step 8: Commit**

```bash
git add backend/src/modules/copilot/application/tools/registry.py backend/src/modules/copilot/infrastructure/persisters/ backend/src/modules/copilot/infrastructure/prompts/templates/interview/ backend/tests/modules/copilot/test_brand_persister.py
git commit -m "feat(copilot): add tool registry, brand persister, and Jinja2 prompt templates"
```

---

## Task 7: Interview Service + API Endpoints

**Files:**
- Create: `backend/src/modules/copilot/application/services/interview_service.py`
- Create: `backend/src/modules/copilot/api/interview.py`
- Create: `backend/src/modules/copilot/api/dto/interview_dto.py`
- Modify: `backend/src/modules/copilot/api/__init__.py`
- Test: `backend/tests/modules/copilot/test_interview_api.py`

- [ ] **Step 1: Write API tests**

```python
"""Tests for Interview API endpoints."""
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.database import get_db
from src.modules.copilot.api.interview import router
from src.modules.iam.api.dependencies import get_current_user, get_tenant_context


def _build_client(tenant_id):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/copilot/interview")
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_tenant_context] = lambda: tenant_id
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4(), tenant_id=tenant_id)
    return TestClient(app), mock_db


class TestStartInterview:
    def test_start_creates_session(self):
        tenant_id = uuid4()
        client, mock_db = _build_client(tenant_id)
        session_id = uuid4()
        conv_id = uuid4()

        with patch("src.modules.copilot.api.interview.InterviewService") as svc_cls:
            svc = MagicMock()
            svc.start_interview.return_value = {
                "session_id": session_id,
                "conversation_id": conv_id,
                "config": {"domain": "brand", "bloques": []},
                "initial_message": "¡Hola! Vamos a construir tu marca juntos.",
            }
            svc_cls.return_value = svc

            response = client.post("/api/v1/copilot/interview/start", json={"domain": "brand"})

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == str(session_id)
        assert data["initial_message"] != ""

    def test_start_returns_409_if_active_exists(self):
        tenant_id = uuid4()
        client, mock_db = _build_client(tenant_id)

        with patch("src.modules.copilot.api.interview.InterviewService") as svc_cls:
            svc = MagicMock()
            svc.start_interview.side_effect = ValueError("Active session exists")
            svc_cls.return_value = svc

            response = client.post("/api/v1/copilot/interview/start", json={"domain": "brand"})

        assert response.status_code == 409


class TestGetActive:
    def test_returns_active_session(self):
        tenant_id = uuid4()
        client, _ = _build_client(tenant_id)

        with patch("src.modules.copilot.api.interview.InterviewService") as svc_cls:
            svc = MagicMock()
            svc.get_active.return_value = {
                "session_id": uuid4(),
                "domain": "brand",
                "domain_label": "Brand Studio",
                "bloque_actual": "identidad",
                "bloques_completados": [],
                "total_bloques": 5,
            }
            svc_cls.return_value = svc

            response = client.get("/api/v1/copilot/interview/active")

        assert response.status_code == 200
        assert response.json()["domain"] == "brand"

    def test_returns_204_when_no_active(self):
        tenant_id = uuid4()
        client, _ = _build_client(tenant_id)

        with patch("src.modules.copilot.api.interview.InterviewService") as svc_cls:
            svc = MagicMock()
            svc.get_active.return_value = None
            svc_cls.return_value = svc

            response = client.get("/api/v1/copilot/interview/active")

        assert response.status_code == 204


class TestGetState:
    def test_returns_full_state(self):
        tenant_id = uuid4()
        session_id = uuid4()
        client, _ = _build_client(tenant_id)

        with patch("src.modules.copilot.api.interview.InterviewService") as svc_cls:
            svc = MagicMock()
            svc.get_state.return_value = {
                "session_id": session_id,
                "mapa_global": {"story.origin_story": "Test"},
                "bloque_actual": "identidad",
                "bloques_completados": [],
                "config": {"bloques": []},
                "messages_count": 5,
            }
            svc_cls.return_value = svc

            response = client.get(f"/api/v1/copilot/interview/{session_id}/state")

        assert response.status_code == 200
        assert response.json()["mapa_global"]["story.origin_story"] == "Test"


class TestPause:
    def test_pause_session(self):
        tenant_id = uuid4()
        session_id = uuid4()
        client, _ = _build_client(tenant_id)

        with patch("src.modules.copilot.api.interview.InterviewService") as svc_cls:
            svc = MagicMock()
            svc.pause.return_value = True
            svc_cls.return_value = svc

            response = client.post(f"/api/v1/copilot/interview/{session_id}/pause")

        assert response.status_code == 200


class TestAbandon:
    def test_abandon_session(self):
        tenant_id = uuid4()
        session_id = uuid4()
        client, _ = _build_client(tenant_id)

        with patch("src.modules.copilot.api.interview.InterviewService") as svc_cls:
            svc = MagicMock()
            svc.abandon.return_value = True
            svc_cls.return_value = svc

            response = client.post(f"/api/v1/copilot/interview/{session_id}/abandon")

        assert response.status_code == 200
```

- [ ] **Step 2: Run tests — verify RED**

```bash
cd backend && .venv/bin/pytest tests/modules/copilot/test_interview_api.py -v
```

- [ ] **Step 3: Implement DTOs**

```python
# backend/src/modules/copilot/api/dto/interview_dto.py
"""Request and response DTOs for Interview API."""
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StartInterviewRequest(BaseModel):
    domain: str = "brand"
    resume_session_id: UUID | None = None


class StartInterviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    session_id: UUID
    conversation_id: UUID
    config: dict
    initial_message: str


class ActiveInterviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    session_id: UUID
    domain: str
    domain_label: str
    bloque_actual: str
    bloques_completados: list[str]
    total_bloques: int


class InterviewStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    session_id: UUID
    mapa_global: dict
    bloque_actual: str
    bloques_completados: list[str]
    config: dict
    messages_count: int


class InterviewMessageRequest(BaseModel):
    message: str
    context: dict | None = None
```

- [ ] **Step 4: Implement InterviewService**

```python
# backend/src/modules/copilot/application/services/interview_service.py
"""Interview Engine orchestration service."""
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from src.modules.copilot.domain.interview_session import InterviewSession, InterviewStatus
from src.modules.copilot.domain.interview_configs.brand_config import BRAND_INTERVIEW_CONFIG
from src.modules.copilot.infrastructure.repositories.interview_session_repository import (
    InterviewSessionRepository,
)
from src.modules.copilot.infrastructure.repositories.conversation_repository import (
    ConversationRepository,
)

DOMAIN_CONFIGS = {
    "brand": BRAND_INTERVIEW_CONFIG,
}

DOMAIN_LABELS = {
    "brand": "Brand Studio",
}


class InterviewService:
    def __init__(self, db: Session):
        self.db = db
        self.session_repo = InterviewSessionRepository(db)
        self.conversation_repo = ConversationRepository(db)

    def start_interview(self, *, tenant_id: UUID, user_id: UUID, domain: str, resume_session_id: UUID | None = None) -> dict:
        if resume_session_id:
            session = self.session_repo.get_by_id(resume_session_id, tenant_id)
            if not session or session.status != InterviewStatus.PAUSED:
                raise ValueError("Session not found or not paused")
            session.resume()
            self.session_repo.save(session)
            self.db.commit()
            return {
                "session_id": session.id,
                "conversation_id": session.conversation_id,
                "config": session.config_snapshot,
                "initial_message": f"¡Bienvenido de vuelta! Continuemos donde quedamos — estábamos en {session.bloque_actual}.",
            }

        existing = self.session_repo.get_active_by_domain(tenant_id, domain)
        if existing:
            raise ValueError("Active session exists for this domain")

        config = DOMAIN_CONFIGS.get(domain)
        if not config:
            raise ValueError(f"No config for domain '{domain}'")

        conversation_id = uuid4()
        self.conversation_repo.create(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            title=f"Entrevista {DOMAIN_LABELS.get(domain, domain)}",
        )

        session = InterviewSession.create(
            tenant_id=tenant_id,
            domain=domain,
            config=config,
            conversation_id=conversation_id,
        )
        self.session_repo.save(session)
        self.db.commit()

        return {
            "session_id": session.id,
            "conversation_id": session.conversation_id,
            "config": session.config_snapshot,
            "initial_message": f"¡Hola! Vamos a construir tu {DOMAIN_LABELS.get(domain, 'proyecto')} juntos. Cuéntame, ¿cómo nació tu negocio?",
        }

    def get_active(self, tenant_id: UUID) -> dict | None:
        for domain in DOMAIN_CONFIGS:
            session = self.session_repo.get_active_by_domain(tenant_id, domain)
            if session:
                config = session.config_snapshot
                return {
                    "session_id": session.id,
                    "domain": session.domain,
                    "domain_label": DOMAIN_LABELS.get(session.domain, session.domain),
                    "bloque_actual": session.bloque_actual,
                    "bloques_completados": session.bloques_completados,
                    "total_bloques": len(config.get("bloques", [])),
                }
        return None

    def get_state(self, session_id: UUID, tenant_id: UUID) -> dict | None:
        session = self.session_repo.get_by_id(session_id, tenant_id)
        if not session:
            return None
        return {
            "session_id": session.id,
            "mapa_global": session.mapa_global,
            "bloque_actual": session.bloque_actual,
            "bloques_completados": session.bloques_completados,
            "config": session.config_snapshot,
            "messages_count": session.messages_count,
        }

    def pause(self, session_id: UUID, tenant_id: UUID) -> bool:
        session = self.session_repo.get_by_id(session_id, tenant_id)
        if not session or session.status != InterviewStatus.ACTIVE:
            return False
        session.pause()
        self.session_repo.save(session)
        self.db.commit()
        return True

    def abandon(self, session_id: UUID, tenant_id: UUID) -> bool:
        session = self.session_repo.get_by_id(session_id, tenant_id)
        if not session or session.status not in (InterviewStatus.ACTIVE, InterviewStatus.PAUSED):
            return False
        session.abandon()
        self.session_repo.save(session)
        self.db.commit()
        return True
```

- [ ] **Step 5: Implement API router**

```python
# backend/src/modules/copilot/api/interview.py
"""Interview Engine REST API endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.copilot.api.dto.interview_dto import (
    ActiveInterviewResponse,
    InterviewStateResponse,
    StartInterviewRequest,
    StartInterviewResponse,
)
from src.modules.copilot.application.services.interview_service import InterviewService
from src.modules.iam.api.dependencies import get_current_user, get_tenant_context

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/start", response_model=StartInterviewResponse)
def start_interview(
    request: StartInterviewRequest,
    current_user=Depends(get_current_user),
    tenant_id: UUID | None = Depends(get_tenant_context),
    db: Session = Depends(get_db),
):
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")
    svc = InterviewService(db)
    try:
        result = svc.start_interview(
            tenant_id=tenant_id,
            user_id=current_user.id,
            domain=request.domain,
            resume_session_id=request.resume_session_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return result


@router.get("/active", response_model=ActiveInterviewResponse)
def get_active_interview(
    response: Response,
    tenant_id: UUID | None = Depends(get_tenant_context),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")
    svc = InterviewService(db)
    result = svc.get_active(tenant_id)
    if not result:
        response.status_code = 204
        return Response(status_code=204)
    return result


@router.get("/{session_id}/state", response_model=InterviewStateResponse)
def get_interview_state(
    session_id: UUID,
    tenant_id: UUID | None = Depends(get_tenant_context),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")
    svc = InterviewService(db)
    result = svc.get_state(session_id, tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@router.post("/{session_id}/pause")
def pause_interview(
    session_id: UUID,
    tenant_id: UUID | None = Depends(get_tenant_context),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")
    svc = InterviewService(db)
    success = svc.pause(session_id, tenant_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot pause session")
    return {"status": "paused"}


@router.post("/{session_id}/abandon")
def abandon_interview(
    session_id: UUID,
    tenant_id: UUID | None = Depends(get_tenant_context),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")
    svc = InterviewService(db)
    success = svc.abandon(session_id, tenant_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot abandon session")
    return {"status": "abandoned"}
```

- [ ] **Step 6: Register router in copilot API __init__**

In `backend/src/modules/copilot/api/__init__.py`, add:

```python
from src.modules.copilot.api.interview import router as interview_router

# In the main router inclusion:
router.include_router(interview_router)
```

- [ ] **Step 7: Run tests — verify GREEN**

```bash
cd backend && .venv/bin/pytest tests/modules/copilot/test_interview_api.py -v
```

- [ ] **Step 8: Run full backend suite**

```bash
cd backend && .venv/bin/pytest -x -q --tb=short
```

- [ ] **Step 9: Commit**

```bash
git add backend/src/modules/copilot/application/services/interview_service.py backend/src/modules/copilot/api/interview.py backend/src/modules/copilot/api/dto/interview_dto.py backend/src/modules/copilot/api/__init__.py backend/tests/modules/copilot/test_interview_api.py
git commit -m "feat(copilot): add Interview Service, API endpoints, and DTOs"
```

---

## Task 8: Frontend — Copilot Store Extensions + API Client

**Files:**
- Modify: `frontend/src/features/copilot/store/copilot-store.ts`
- Create: `frontend/src/features/copilot/api/interview-api.ts`
- Test: `frontend/src/features/copilot/hooks/__tests__/useInterviewChat.test.ts`

- [ ] **Step 1: Write store test**

```typescript
// frontend/src/features/copilot/hooks/__tests__/useInterviewChat.test.ts
import { describe, it, expect, beforeEach } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { useCopilotStore } from "../../store/copilot-store";

describe("Copilot Store — Interview Extensions", () => {
  beforeEach(() => {
    act(() => {
      useCopilotStore.getState().clearInterview();
    });
  });

  it("setInterviewMode activates interview", () => {
    act(() => {
      useCopilotStore.getState().setInterviewMode(true, "session-123");
    });
    const state = useCopilotStore.getState();
    expect(state.interviewMode).toBe(true);
    expect(state.interviewSessionId).toBe("session-123");
  });

  it("updateInterviewPreview merges delta", () => {
    act(() => {
      useCopilotStore.getState().setInterviewMode(true, "s1");
      useCopilotStore.getState().updateInterviewPreview({ "story.origin": "v1" });
      useCopilotStore.getState().updateInterviewPreview({ "story.mission": "v2" });
    });
    const data = useCopilotStore.getState().interviewPreviewData;
    expect(data).toEqual({ "story.origin": "v1", "story.mission": "v2" });
  });

  it("clearInterview resets all fields", () => {
    act(() => {
      useCopilotStore.getState().setInterviewMode(true, "s1");
      useCopilotStore.getState().updateInterviewPreview({ key: "val" });
      useCopilotStore.getState().clearInterview();
    });
    const state = useCopilotStore.getState();
    expect(state.interviewMode).toBe(false);
    expect(state.interviewSessionId).toBeNull();
    expect(state.interviewPreviewData).toBeNull();
  });

  it("interviewMode false by default", () => {
    expect(useCopilotStore.getState().interviewMode).toBe(false);
  });
});
```

- [ ] **Step 2: Run test — verify RED**

```bash
cd frontend && npx vitest run src/features/copilot/hooks/__tests__/useInterviewChat.test.ts
```

- [ ] **Step 3: Add interview fields to copilot store**

Add to `frontend/src/features/copilot/store/copilot-store.ts` state interface and create slice:

```typescript
// Add to state type:
interviewMode: boolean;
interviewSessionId: string | null;
interviewPreviewData: Record<string, unknown> | null;

// Add actions:
setInterviewMode: (active: boolean, sessionId?: string) => void;
updateInterviewPreview: (delta: Record<string, unknown>) => void;
clearInterview: () => void;

// Add to create():
interviewMode: false,
interviewSessionId: null,
interviewPreviewData: null,

setInterviewMode: (active, sessionId) =>
  set({ interviewMode: active, interviewSessionId: sessionId ?? null }),

updateInterviewPreview: (delta) =>
  set((state) => ({
    interviewPreviewData: { ...(state.interviewPreviewData ?? {}), ...delta },
  })),

clearInterview: () =>
  set({ interviewMode: false, interviewSessionId: null, interviewPreviewData: null }),
```

- [ ] **Step 4: Create API client**

```typescript
// frontend/src/features/copilot/api/interview-api.ts
import { fetchClient } from "@/lib/api-client";

export interface StartInterviewResponse {
  session_id: string;
  conversation_id: string;
  config: Record<string, unknown>;
  initial_message: string;
}

export interface ActiveInterviewResponse {
  session_id: string;
  domain: string;
  domain_label: string;
  bloque_actual: string;
  bloques_completados: string[];
  total_bloques: number;
}

export interface InterviewStateResponse {
  session_id: string;
  mapa_global: Record<string, unknown>;
  bloque_actual: string;
  bloques_completados: string[];
  config: Record<string, unknown>;
  messages_count: number;
}

export async function startInterview(domain: string = "brand"): Promise<StartInterviewResponse> {
  const res = await fetchClient("/api/v1/copilot/interview/start", {
    method: "POST",
    body: JSON.stringify({ domain }),
  });
  return res.json();
}

export async function getActiveInterview(): Promise<ActiveInterviewResponse | null> {
  const res = await fetchClient("/api/v1/copilot/interview/active");
  if (res.status === 204) return null;
  return res.json();
}

export async function getInterviewState(sessionId: string): Promise<InterviewStateResponse> {
  const res = await fetchClient(`/api/v1/copilot/interview/${sessionId}/state`);
  return res.json();
}

export async function pauseInterview(sessionId: string): Promise<void> {
  await fetchClient(`/api/v1/copilot/interview/${sessionId}/pause`, { method: "POST" });
}

export async function abandonInterview(sessionId: string): Promise<void> {
  await fetchClient(`/api/v1/copilot/interview/${sessionId}/abandon`, { method: "POST" });
}
```

- [ ] **Step 5: Run test — verify GREEN**

```bash
cd frontend && npx vitest run src/features/copilot/hooks/__tests__/useInterviewChat.test.ts
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/copilot/store/copilot-store.ts frontend/src/features/copilot/api/interview-api.ts frontend/src/features/copilot/hooks/__tests__/useInterviewChat.test.ts
git commit -m "feat(copilot): add interview mode to store and API client"
```

---

## Task 9: Frontend — Generative UI Cards (AlternativesCard + ClarifyCard + CheckpointCard)

**Files:**
- Create: `frontend/src/features/copilot/components/cards/alternatives-card.tsx`
- Create: `frontend/src/features/copilot/components/cards/clarify-card.tsx`
- Create: `frontend/src/features/copilot/components/cards/checkpoint-card.tsx`
- Create: `frontend/src/features/copilot/components/cards/interview-complete-card.tsx`
- Test: `frontend/src/features/copilot/components/cards/__tests__/alternatives-card.test.tsx`
- Test: `frontend/src/features/copilot/components/cards/__tests__/checkpoint-card.test.tsx`

- [ ] **Step 1: Write card tests**

```typescript
// frontend/src/features/copilot/components/cards/__tests__/alternatives-card.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { AlternativesCard } from "../alternatives-card";

const mockAlternatives = [
  { id: "a", title: "The Magician", description: "Transforms complex", recommended: true, recommendationReason: "Matches your brand" },
  { id: "b", title: "The Hero", description: "Empowers users", recommended: false },
  { id: "c", title: "The Caregiver", description: "Protects and guides", recommended: false },
];

describe("AlternativesCard", () => {
  it("renders all alternatives", () => {
    render(
      <AlternativesCard
        fieldPath="identity.archetype"
        question="Which archetype fits?"
        alternatives={mockAlternatives}
        allowCustom={true}
        onSelect={vi.fn()}
        onCustom={vi.fn()}
        status="pending"
      />
    );
    expect(screen.getByText("The Magician")).toBeInTheDocument();
    expect(screen.getByText("The Hero")).toBeInTheDocument();
    expect(screen.getByText("The Caregiver")).toBeInTheDocument();
  });

  it("shows recommendation badge on recommended option", () => {
    render(
      <AlternativesCard
        fieldPath="identity.archetype"
        question="Which archetype fits?"
        alternatives={mockAlternatives}
        allowCustom={true}
        onSelect={vi.fn()}
        onCustom={vi.fn()}
        status="pending"
      />
    );
    expect(screen.getByText(/Matches your brand/)).toBeInTheDocument();
  });

  it("calls onSelect when option clicked and confirmed", () => {
    const onSelect = vi.fn();
    render(
      <AlternativesCard
        fieldPath="identity.archetype"
        question="Which archetype fits?"
        alternatives={mockAlternatives}
        allowCustom={true}
        onSelect={onSelect}
        onCustom={vi.fn()}
        status="pending"
      />
    );
    fireEvent.click(screen.getByText("The Hero"));
    fireEvent.click(screen.getByRole("button", { name: /seleccionar/i }));
    expect(onSelect).toHaveBeenCalledWith("b");
  });

  it("disables interaction when resolved", () => {
    render(
      <AlternativesCard
        fieldPath="identity.archetype"
        question="Which archetype fits?"
        alternatives={mockAlternatives}
        allowCustom={true}
        onSelect={vi.fn()}
        onCustom={vi.fn()}
        status="resolved"
      />
    );
    const buttons = screen.queryAllByRole("button");
    buttons.forEach((btn) => expect(btn).toBeDisabled());
  });
});
```

```typescript
// frontend/src/features/copilot/components/cards/__tests__/checkpoint-card.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { CheckpointCard } from "../checkpoint-card";

describe("CheckpointCard", () => {
  const defaultProps = {
    blockId: "identidad",
    blockLabel: "Tu Identidad",
    summary: { "story.origin_story": "Founded in 2019...", "story.mission": "Democratize sales" },
    healthScore: 85,
    blocksProgress: { completed: 1, total: 5 },
    onConfirm: vi.fn(),
    onRevise: vi.fn(),
    status: "pending" as const,
  };

  it("renders block label and summary fields", () => {
    render(<CheckpointCard {...defaultProps} />);
    expect(screen.getByText(/Tu Identidad/)).toBeInTheDocument();
    expect(screen.getByText(/Founded in 2019/)).toBeInTheDocument();
    expect(screen.getByText(/Democratize sales/)).toBeInTheDocument();
  });

  it("shows health score", () => {
    render(<CheckpointCard {...defaultProps} />);
    expect(screen.getByText("85%")).toBeInTheDocument();
  });

  it("calls onConfirm when confirm button clicked", () => {
    const onConfirm = vi.fn();
    render(<CheckpointCard {...defaultProps} onConfirm={onConfirm} />);
    fireEvent.click(screen.getByRole("button", { name: /perfecto/i }));
    expect(onConfirm).toHaveBeenCalled();
  });

  it("calls onRevise when revise button clicked", () => {
    const onRevise = vi.fn();
    render(<CheckpointCard {...defaultProps} onRevise={onRevise} />);
    fireEvent.click(screen.getByRole("button", { name: /ajustar/i }));
    expect(onRevise).toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Run tests — verify RED**

```bash
cd frontend && npx vitest run src/features/copilot/components/cards/__tests__/
```

- [ ] **Step 3: Implement AlternativesCard**

Create `frontend/src/features/copilot/components/cards/alternatives-card.tsx` with:
- Purple dark background (`bg-[#1e1b4b]`, `border-purple-500`)
- `💡` icon + question text
- Clickable option cards with hover ring
- Recommended option badge ("✨ {reason}")
- "Seleccionar marcados" + "Otro" buttons
- Disabled state when `status === "resolved"`

- [ ] **Step 4: Implement ClarifyCard**

Create `frontend/src/features/copilot/components/cards/clarify-card.tsx` with:
- Amber dark background (`bg-[#422006]`, `border-amber-500`)
- `⚠️` icon + "Algo no cuadra"
- Issue text + quick resolution buttons (ghost style)
- Max 2 items rendered
- Resolved state: collapsed with "✓ Aclarado"

- [ ] **Step 5: Implement CheckpointCard**

Create `frontend/src/features/copilot/components/cards/checkpoint-card.tsx` with:
- Purple dark background, progress dots header
- Compact summary (1 line per field, field label colored purple)
- Health score progress bar (green)
- "👍 Perfecto, sigamos" (primary) + "Ajustar algo" (ghost)
- Confirmed state: green border + "✓ Guardado" badge

- [ ] **Step 6: Implement InterviewCompleteCard**

Create `frontend/src/features/copilot/components/cards/interview-complete-card.tsx` with:
- Green theme, health score large, redirect button

- [ ] **Step 7: Run tests — verify GREEN**

```bash
cd frontend && npx vitest run src/features/copilot/components/cards/__tests__/
```

- [ ] **Step 8: Commit**

```bash
git add frontend/src/features/copilot/components/cards/alternatives-card.tsx frontend/src/features/copilot/components/cards/clarify-card.tsx frontend/src/features/copilot/components/cards/checkpoint-card.tsx frontend/src/features/copilot/components/cards/interview-complete-card.tsx frontend/src/features/copilot/components/cards/__tests__/
git commit -m "feat(copilot): add AlternativesCard, ClarifyCard, CheckpointCard generative UI"
```

---

## Task 10: Frontend — Interview Chat Panel + Message Renderer

**Files:**
- Create: `frontend/src/features/copilot/components/interview/interview-chat-panel.tsx`
- Create: `frontend/src/features/copilot/components/interview/interview-message.tsx`
- Create: `frontend/src/features/copilot/components/interview/interview-input.tsx`
- Create: `frontend/src/features/copilot/hooks/useInterviewChat.ts`

- [ ] **Step 1: Implement useInterviewChat hook**

Hook that:
- Calls `POST /api/v1/copilot/interview/{sessionId}/message` via SSE (reuse `streamCopilotChat` pattern)
- Handles `preview_update` → `updateInterviewPreview(delta)` in store + React Query cache invalidation
- Handles `alternatives_card`, `clarify_card`, `checkpoint_card` → adds to message ui_actions
- Handles `interview_complete` → `clearInterview()` + router.push(redirect)
- Auto-sends card interactions as messages (e.g., "Elegí: {title}")

- [ ] **Step 2: Implement InterviewMessage component**

Switch on `action.type`:
```typescript
case "alternatives_card": return <AlternativesCard {...props} onSelect={sendSelection} />;
case "clarify_card": return <ClarifyCard {...props} onResolve={sendResolution} />;
case "checkpoint_card": return <CheckpointCard {...props} onConfirm={sendConfirm} onRevise={sendRevise} />;
case "interview_complete": return <InterviewCompleteCard {...props} />;
case "preview_update": return null; // Silent
```

- [ ] **Step 3: Implement InterviewInput**

- Text input with placeholder "Escribe aquí..."
- Mic button (disabled, tooltip "Disponible en Fase 3")
- Send button (arrow icon)
- Disabled state during `status === "thinking"`

- [ ] **Step 4: Implement InterviewChatPanel**

Composes: Header + Messages scroll area + Input. Props: `sessionId: string`.

- [ ] **Step 5: Run type check**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/copilot/components/interview/ frontend/src/features/copilot/hooks/useInterviewChat.ts
git commit -m "feat(copilot): add InterviewChatPanel with message rendering and hook"
```

---

## Task 11: Frontend — Split View Page + Header

**Files:**
- Create: `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/interview/page.tsx`
- Create: `frontend/src/features/brand/components/interview/interview-split-view.tsx`
- Create: `frontend/src/features/brand/components/interview/interview-header.tsx`
- Create: `frontend/src/features/brand/components/interview/session-restore-modal.tsx`

- [ ] **Step 1: Create page route (Server Component)**

```typescript
// frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/interview/page.tsx
import { InterviewSplitView } from "@/features/brand/components/interview/interview-split-view";

interface PageProps {
  searchParams: Promise<{ session?: string }>;
}

export default async function InterviewPage({ searchParams }: PageProps) {
  const params = await searchParams;
  return <InterviewSplitView sessionId={params.session} />;
}
```

- [ ] **Step 2: Implement InterviewSplitView**

Client component that:
- If no `sessionId` prop → check for active session → show SessionRestoreModal or create new
- Fetches interview state via React Query (`["interview", sessionId, "state"]`)
- Layout: `flex h-[calc(100vh-64px)]` → left (flex-1, tabs + previews read-only) + right (w-[420px], chat)
- Left panel uses `BrandStudioTabs` + view components WITHOUT `onEdit` callbacks
- Preview data = merge of BrandSettings (persisted) + mapa_global (draft)
- Auto-scroll on block change

- [ ] **Step 3: Implement InterviewHeader**

- Title: "🎙️ Cocreando tu Marca"
- Subtitle: "Bloque: {bloque_label}"
- Progress dots: done (green), current (purple pulse), pending (gray)

- [ ] **Step 4: Implement SessionRestoreModal**

- Dialog with "Tienes una entrevista pausada (X/Y bloques)"
- "Continuar donde quedé" → navigate with `?session={id}`
- "Empezar de nuevo" → abandon old + start new

- [ ] **Step 5: Run type check**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/app/\(main\)/\[tenantId\]/\(dashboard\)/brand-studio/interview/ frontend/src/features/brand/components/interview/
git commit -m "feat(brand): add Interview split view page with session restore"
```

---

## Task 12: Frontend — Interview Banner + Wizard Integration

**Files:**
- Create: `frontend/src/components/shared/interview-banner.tsx`
- Modify: `frontend/src/app/(main)/[tenantId]/(dashboard)/layout.tsx`
- Modify: `frontend/src/features/brand/components/onboarding/step-source-picker.tsx`
- Modify: `frontend/src/features/brand/hooks/useOnboardingWizard.ts`

- [ ] **Step 1: Implement InterviewBanner**

```typescript
// frontend/src/components/shared/interview-banner.tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { usePathname, useParams } from "next/navigation";
import Link from "next/link";
import { getActiveInterview } from "@/features/copilot/api/interview-api";

export function InterviewBanner() {
  const pathname = usePathname();
  const params = useParams();
  const tenantId = params.tenantId as string;

  const { data: active } = useQuery({
    queryKey: ["interview", "active"],
    queryFn: getActiveInterview,
    staleTime: 60_000,
  });

  // Don't show on the interview page itself
  if (!active || pathname.includes("/brand-studio/interview")) return null;

  return (
    <div className="bg-[#1e1b4b] border border-purple-500 rounded-lg px-4 py-2.5 mx-4 mt-2 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-2 h-2 rounded-full bg-purple-500 animate-pulse" />
        <span className="text-sm text-white">
          Entrevista {active.domain_label} en curso
        </span>
        <span className="text-xs text-gray-400">
          ({active.bloques_completados.length}/{active.total_bloques} bloques)
        </span>
      </div>
      <Link
        href={`/${tenantId}/brand-studio/interview?session=${active.session_id}`}
        className="bg-purple-600 hover:bg-purple-700 text-white text-xs px-3 py-1.5 rounded-md font-medium"
      >
        Continuar →
      </Link>
    </div>
  );
}
```

- [ ] **Step 2: Mount banner in dashboard layout**

In `frontend/src/app/(main)/[tenantId]/(dashboard)/layout.tsx`, add:

```typescript
import { InterviewBanner } from "@/components/shared/interview-banner";

// Inside the layout, before {children}:
<InterviewBanner />
```

- [ ] **Step 3: Enable interview option in step-source-picker**

In `frontend/src/features/brand/components/onboarding/step-source-picker.tsx`:
- Remove `isDisabled` logic for the `"interview"` option
- Change label from "Próximamente" to nothing (or remove the disabled badge)

- [ ] **Step 4: Update useOnboardingWizard for interview routing**

In `frontend/src/features/brand/hooks/useOnboardingWizard.ts`:
- When `selectedSources === ["interview"]` → instead of showing placeholder step, call `router.push(\`/${tenantId}/brand-studio/interview\`)`
- When sources include interview after extraction → gap-review shows CTA that links to interview page

- [ ] **Step 5: Run frontend tests + type check**

```bash
cd frontend && npx tsc --noEmit && npx vitest run
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/shared/interview-banner.tsx frontend/src/app/\(main\)/\[tenantId\]/\(dashboard\)/layout.tsx frontend/src/features/brand/components/onboarding/step-source-picker.tsx frontend/src/features/brand/hooks/useOnboardingWizard.ts
git commit -m "feat(brand): add InterviewBanner, enable interview option in wizard"
```

---

## Task 13: Integration Test + Final Verification

**Files:**
- Test: `backend/tests/modules/copilot/test_interview_integration.py`

- [ ] **Step 1: Write integration test**

```python
"""Integration test for Interview Engine flow."""
import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from src.modules.copilot.application.services.interview_service import InterviewService
from src.modules.copilot.domain.interview_session import InterviewStatus


class TestInterviewFlow:
    """End-to-end flow: start → extract → checkpoint → advance → complete."""

    def test_full_interview_lifecycle(self, db):
        tenant_id = uuid4()
        user_id = uuid4()
        svc = InterviewService(db)

        # Start
        result = svc.start_interview(tenant_id=tenant_id, user_id=user_id, domain="brand")
        session_id = result["session_id"]
        assert result["initial_message"] != ""

        # Get state
        state = svc.get_state(session_id, tenant_id)
        assert state["bloque_actual"] == "identidad"
        assert state["messages_count"] == 0

        # Get active
        active = svc.get_active(tenant_id)
        assert active["session_id"] == session_id

        # Pause
        assert svc.pause(session_id, tenant_id)
        state = svc.get_state(session_id, tenant_id)
        # Session still exists but is paused
        active = svc.get_active(tenant_id)
        assert active is None  # Not active anymore

        # Resume via start with resume_session_id
        result = svc.start_interview(tenant_id=tenant_id, user_id=user_id, domain="brand", resume_session_id=session_id)
        assert result["session_id"] == session_id

        # Cannot start another while active
        with pytest.raises(ValueError, match="Active session exists"):
            svc.start_interview(tenant_id=tenant_id, user_id=user_id, domain="brand")

        # Abandon
        assert svc.abandon(session_id, tenant_id)
        active = svc.get_active(tenant_id)
        assert active is None
```

- [ ] **Step 2: Run integration test**

```bash
cd backend && .venv/bin/pytest tests/modules/copilot/test_interview_integration.py -v
```

- [ ] **Step 3: Run full test suites**

```bash
cd backend && .venv/bin/pytest -x -q --tb=short
cd frontend && npx tsc --noEmit && npx vitest run
```

- [ ] **Step 4: Run lint**

```bash
cd backend && .venv/bin/ruff check src/ tests/ --no-cache
cd frontend && npx eslint src/
```

- [ ] **Step 5: Commit integration test**

```bash
git add backend/tests/modules/copilot/test_interview_integration.py
git commit -m "test(copilot): add Interview Engine integration test"
```

- [ ] **Step 6: Final commit — update registry model import**

Ensure `InterviewSessionModel` is imported in the shared model registry so Alembic picks it up:

```bash
# Check if there's a model registry file and add the import
cd backend && .venv/bin/pytest -x -q --tb=short
```

---

## Dependency Graph

```
Task 1 (Migration)
  └── Task 2 (Domain entities)
       └── Task 3 (Model + Repository)
            ├── Task 4 (Tools: extract + alternatives)
            ├── Task 5 (Tools: clarify + checkpoint + advance + complete)
            │    └── Task 6 (Registry + Persister + Prompts)
            │         └── Task 7 (Service + API)
            └── Task 8 (Frontend Store + API client)
                 ├── Task 9 (Cards UI)
                 │    └── Task 10 (Chat Panel)
                 │         └── Task 11 (Split View Page)
                 └── Task 12 (Banner + Wizard)

Task 13 (Integration) — runs after all above
```

**Parallelizable groups:**
- Tasks 4+5 (backend tools) can run in parallel
- Tasks 8+9 (frontend store + cards) can start once Task 7 API is defined
- Tasks 10+11+12 are sequential (each builds on previous)
