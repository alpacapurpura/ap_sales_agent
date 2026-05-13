"""Tests for ``pin_to_memory`` tool — F4 url contextual."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest

from luana_core_platform.core.context import (
    set_conversation_id,
    set_tenant_id,
    set_user_id,
)
from luana_core_copilot.application.tools.pin_to_memory import (
    _pin_to_memory_impl,
)
from luana_core_copilot.infrastructure.repositories.inspiration_repository import (
    CopilotInspirationRepository,
)
from luana_core_copilot.infrastructure.repositories.pinned_memory_repository import (
    CopilotPinnedMemoryRepository,
)


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def conversation_id():
    return uuid4()


@pytest.fixture(autouse=True)
def _ctx():
    set_tenant_id(None)
    set_user_id(None)
    set_conversation_id(None)
    yield
    set_tenant_id(None)
    set_user_id(None)
    set_conversation_id(None)


def _seed_inspiration(db, *, tenant_id, conversation_id, slug="x"):
    repo = CopilotInspirationRepository(db)
    row = repo.upsert(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        slug=slug,
        url=f"https://{slug}.example.com",
        why="r",
        domain=f"{slug}.example.com",
        title="T",
        summary=f"summary {slug}",
        sub_elements={},
        brand_relevance_score=0.8,
        content_md=f"---\nslug: {slug}\n---\n# {slug}\nbody",
        og_image=None,
    )
    db.commit()
    return row


class TestPinToMemoryImpl:
    @pytest.mark.asyncio
    async def test_no_tenant_errors(self) -> None:
        out = await _pin_to_memory_impl(slug="x")
        assert json.loads(out)["status"] == "error"

    @pytest.mark.asyncio
    async def test_unknown_slug_errors(
        self,
        db,
        tenant_id,
        user_id,
        conversation_id,
    ) -> None:
        set_tenant_id(tenant_id)
        set_user_id(user_id)
        set_conversation_id(str(conversation_id))
        out = await _pin_to_memory_impl(slug="nope", db=db)
        payload = json.loads(out)
        assert payload["status"] == "error"
        assert "nope" in payload["message"]

    @pytest.mark.asyncio
    async def test_pin_promotes_inspiration(
        self,
        db,
        tenant_id,
        user_id,
        conversation_id,
    ) -> None:
        set_tenant_id(tenant_id)
        set_user_id(user_id)
        set_conversation_id(str(conversation_id))
        _seed_inspiration(
            db,
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            slug="mujer-coraje",
        )

        out = await _pin_to_memory_impl(slug="mujer-coraje", db=db)
        payload = json.loads(out)
        assert payload["status"] == "pinned"
        assert payload["path"] == "/memories/inspirations/mujer-coraje.md"
        assert payload["ui_action"]["type"] == "memory_pinned"

        pinned_repo = CopilotPinnedMemoryRepository(db)
        row = pinned_repo.get(
            tenant_id=tenant_id,
            user_id=user_id,
            path="/memories/inspirations/mujer-coraje.md",
        )
        assert row is not None
        assert "mujer-coraje" in row.content
        assert row.pinned_from_conversation_id == conversation_id

    @pytest.mark.asyncio
    async def test_idempotent_re_pin_updates(
        self,
        db,
        tenant_id,
        user_id,
        conversation_id,
    ) -> None:
        set_tenant_id(tenant_id)
        set_user_id(user_id)
        set_conversation_id(str(conversation_id))
        insp = _seed_inspiration(
            db,
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            slug="x",
        )
        await _pin_to_memory_impl(slug="x", db=db)
        # Update inspiration content, then re-pin: pinned content should
        # follow.
        repo = CopilotInspirationRepository(db)
        repo.upsert(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            slug="x",
            url=insp.url,
            why="updated",
            domain=insp.domain,
            title=insp.title,
            summary="new summary",
            sub_elements={},
            brand_relevance_score=0.9,
            content_md="updated body",
            og_image=None,
        )
        db.commit()
        await _pin_to_memory_impl(slug="x", db=db)

        pinned = CopilotPinnedMemoryRepository(db).get(
            tenant_id=tenant_id,
            user_id=user_id,
            path="/memories/inspirations/x.md",
        )
        assert pinned is not None
        assert pinned.content == "updated body"
