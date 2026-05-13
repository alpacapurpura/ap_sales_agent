"""F6 — workflow_state JSONB persistence + dual-read fallback.

Verifies the new ``workflow_state`` column on ``copilot_conversations`` carries
the ``WorkflowExecutionState`` payload, and the repo accessors read/write it
without disturbing the legacy ``procedure_state`` column (coexistence during
the cutover).
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from luana_core_copilot.domain.workflow import WorkflowExecutionState
from luana_core_copilot.infrastructure.repositories.conversation_repository import (
    ConversationRepository,
)


@pytest.fixture
def repo(db) -> ConversationRepository:
    return ConversationRepository(db)


@pytest.fixture
def tenant_user() -> tuple:
    return uuid4(), uuid4()


def _create_conv(repo: ConversationRepository, tenant_id, user_id, *, title: str = "wf-test"):
    return repo.create(
        conversation_id=uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        title=title,
    )


class TestWorkflowStatePersistence:
    def test_update_workflow_state_persists_payload(
        self,
        repo: ConversationRepository,
        tenant_user: tuple,
        db,
    ) -> None:
        tenant_id, user_id = tenant_user
        conv = _create_conv(repo, tenant_id, user_id)
        state = WorkflowExecutionState(
            workflow_id="setup_brand_minimal",
            current_node="analyze",
            data={"score": 5},
        )
        repo.update_workflow_state(
            conversation_id=conv.id,
            tenant_id=tenant_id,
            workflow_state=state.to_jsonb_dict(),
        )
        db.commit()
        loaded = repo.get_workflow_state(conversation_id=conv.id, tenant_id=tenant_id)
        assert loaded is not None
        assert loaded["workflow_id"] == "setup_brand_minimal"
        assert loaded["data"] == {"score": 5}

    def test_workflow_state_does_not_overwrite_procedure_state(
        self,
        repo: ConversationRepository,
        tenant_user: tuple,
        db,
    ) -> None:
        tenant_id, user_id = tenant_user
        conv = _create_conv(repo, tenant_id, user_id)
        repo.update_procedure_state(
            conversation_id=conv.id,
            tenant_id=tenant_id,
            procedure_state={"legacy": True},
        )
        repo.update_workflow_state(
            conversation_id=conv.id,
            tenant_id=tenant_id,
            workflow_state={"workflow_id": "wf", "current_node": "a"},
        )
        db.commit()
        # Legacy column intact (coexistencia hasta cutover F-pos).
        model = repo.get_by_id(conv.id, tenant_id)
        assert model is not None
        assert model.procedure_state == {"legacy": True}
        assert model.workflow_state == {"workflow_id": "wf", "current_node": "a"}

    def test_read_workflow_state_falls_back_to_procedure_state(
        self,
        repo: ConversationRepository,
        tenant_user: tuple,
        db,
    ) -> None:
        """Conversations created before F6 only have procedure_state set; reader
        must surface that payload under workflow_state semantics during cutover.
        """
        tenant_id, user_id = tenant_user
        conv = _create_conv(repo, tenant_id, user_id)
        repo.update_procedure_state(
            conversation_id=conv.id,
            tenant_id=tenant_id,
            procedure_state={"legacy": True, "guided": {"current_block_id": "x"}},
        )
        db.commit()
        loaded = repo.get_workflow_state(
            conversation_id=conv.id,
            tenant_id=tenant_id,
            fallback_to_procedure=True,
        )
        assert loaded == {"legacy": True, "guided": {"current_block_id": "x"}}

    def test_read_workflow_state_missing_returns_none(
        self,
        repo: ConversationRepository,
        tenant_user: tuple,
        db,
    ) -> None:
        tenant_id, user_id = tenant_user
        conv = _create_conv(repo, tenant_id, user_id)
        db.commit()
        assert repo.get_workflow_state(conversation_id=conv.id, tenant_id=tenant_id) is None

    def test_clear_workflow_state(
        self,
        repo: ConversationRepository,
        tenant_user: tuple,
        db,
    ) -> None:
        tenant_id, user_id = tenant_user
        conv = _create_conv(repo, tenant_id, user_id)
        repo.update_workflow_state(
            conversation_id=conv.id,
            tenant_id=tenant_id,
            workflow_state={"workflow_id": "wf", "current_node": "a"},
        )
        db.commit()
        repo.update_workflow_state(
            conversation_id=conv.id,
            tenant_id=tenant_id,
            workflow_state=None,
        )
        db.commit()
        assert repo.get_workflow_state(conversation_id=conv.id, tenant_id=tenant_id) is None
