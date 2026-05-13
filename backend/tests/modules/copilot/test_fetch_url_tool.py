"""Tests for ``fetch_url`` tool — F4 url contextual."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest

from luana_core_platform.core.context import (
    set_conversation_id,
    set_tenant_id,
    set_user_id,
)
from luana_core_copilot.application.tools.fetch_url import (
    ACTIVE_INSPIRATIONS_CAP,
    MAX_INSPIRATIONS_PER_CONVERSATION,
    _fetch_url_impl,
)
from luana_core_copilot.application.tools.url_inspiration_analyzer import (
    InspirationAnalysis,
)
from luana_core_copilot.infrastructure.repositories.inspiration_repository import (
    CopilotInspirationRepository,
)
from luana_core_copilot.infrastructure.web.trafilatura_client import (
    WebExtractResult,
)


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def conversation_id():
    return uuid4()


@pytest.fixture(autouse=True)
def _clear_context():
    set_tenant_id(None)
    set_user_id(None)
    set_conversation_id(None)
    yield
    set_tenant_id(None)
    set_user_id(None)
    set_conversation_id(None)


def _stub_extract(
    url: str = "https://mujercoraje.example.com/programa",
    domain: str = "mujercoraje.example.com",
    title: str = "Mujer Coraje · Despertar",
    md: str = "# Despertar\nPrograma 12 semanas.",
):
    async def _f(_url: str) -> WebExtractResult:
        return WebExtractResult(
            url=url,
            domain=domain,
            title=title,
            content_md=md,
            og_image="https://cdn.example.com/og.jpg",
        )

    return _f


async def _stub_lighthouse(_tenant_id):
    return None


def _stub_analyze(slug: str = "mujer-coraje", score: float = 0.8):
    def _a(**_: object) -> InspirationAnalysis:
        return InspirationAnalysis(
            slug=slug,
            summary="Programa de transformación 12 semanas para mujeres adultas.",
            sub_elements={
                "testimonials": ["t1"],
                "ctas": ["Inscribirme"],
                "value_props": ["12 semanas"],
                "visual_cues": [],
            },
            brand_relevance_score=score,
        )

    return _a


class TestFetchUrlImpl:
    @pytest.mark.asyncio
    async def test_no_tenant_returns_error(self) -> None:
        out = await _fetch_url_impl(url="https://x.com", why="")
        payload = json.loads(out)
        assert payload["status"] == "error"
        assert "tenant" in payload["message"].lower()

    @pytest.mark.asyncio
    async def test_no_conversation_returns_error(self, tenant_id) -> None:
        set_tenant_id(tenant_id)
        out = await _fetch_url_impl(url="https://x.com", why="")
        payload = json.loads(out)
        assert payload["status"] == "error"
        assert "conversación" in payload["message"].lower() or "conversation" in payload["message"].lower()

    @pytest.mark.asyncio
    async def test_invalid_url_returns_error(
        self,
        db,
        tenant_id,
        conversation_id,
    ) -> None:
        set_tenant_id(tenant_id)
        set_conversation_id(str(conversation_id))
        await _fetch_url_impl(
            url="ftp://example.com",
            why="",
            db=db,
            extract_fn=_stub_extract(),
            analyze_fn=_stub_analyze(),
            lighthouse_fn=_stub_lighthouse,
        )
        # Validation happens INSIDE fetch_extract; with stub we'd skip,
        # so override extract_fn to actually call validation.
        # This path uses real fetch_extract by NOT passing extract_fn —
        # but test infra wants a stub. Instead: test with a stub that
        # mimics validation rejection.
        # Simpler: remove this test — covered by test_trafilatura_client.
        # Keep as smoke that the flow handles invalid URLs gracefully
        # via the FetchUrlError path:
        from luana_core_copilot.infrastructure.web.trafilatura_client import (
            FetchUrlError,
        )

        async def _raises(url: str) -> WebExtractResult:
            msg = "URL inválida."
            raise FetchUrlError(msg)

        out2 = await _fetch_url_impl(
            url="anything",
            why="",
            db=db,
            extract_fn=_raises,
            analyze_fn=_stub_analyze(),
            lighthouse_fn=_stub_lighthouse,
        )
        payload = json.loads(out2)
        assert payload["status"] == "error"
        assert "URL inválida" in payload["message"]

    @pytest.mark.asyncio
    async def test_happy_path_persists_row(
        self,
        db,
        tenant_id,
        conversation_id,
    ) -> None:
        set_tenant_id(tenant_id)
        set_conversation_id(str(conversation_id))
        out = await _fetch_url_impl(
            url="https://mujercoraje.example.com/programa",
            why="competencia voz",
            db=db,
            extract_fn=_stub_extract(),
            analyze_fn=_stub_analyze(),
            lighthouse_fn=_stub_lighthouse,
        )
        payload = json.loads(out)
        assert payload["status"] == "saved"
        assert payload["slug"] == "mujer-coraje"
        assert payload["scratchpad_path"] == "/inspirations/mujer-coraje.md"
        assert payload["brand_relevance_score"] == 0.8
        assert payload["ui_action"]["type"] == "inspiration_saved"

        # Llm content is short — does not include the markdown body.
        assert len(payload["llm_content"]) < 500
        assert "# Despertar" not in payload["llm_content"]

        # Row persisted.
        repo = CopilotInspirationRepository(db)
        rows = repo.list_active_for_conversation(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
        )
        assert len(rows) == 1
        row = rows[0]
        assert row.slug == "mujer-coraje"
        assert row.why == "competencia voz"
        assert row.og_image == "https://cdn.example.com/og.jpg"
        assert "Despertar" in row.content_md  # frontmatter present

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_after_max(
        self,
        db,
        tenant_id,
        conversation_id,
    ) -> None:
        set_tenant_id(tenant_id)
        set_conversation_id(str(conversation_id))
        repo = CopilotInspirationRepository(db)
        # Pre-populate up to the cap.
        for i in range(MAX_INSPIRATIONS_PER_CONVERSATION):
            repo.upsert(
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                slug=f"x-{i}",
                url=f"https://x{i}.com",
                why="",
                domain=f"x{i}.com",
                title=None,
                summary="s",
                sub_elements={},
                brand_relevance_score=0.5,
                content_md="b",
                og_image=None,
            )
            db.commit()

        out = await _fetch_url_impl(
            url="https://new.example.com",
            why="",
            db=db,
            extract_fn=_stub_extract(),
            analyze_fn=_stub_analyze(slug="other"),
            lighthouse_fn=_stub_lighthouse,
        )
        payload = json.loads(out)
        assert payload["status"] == "error"
        assert payload["limit"] == MAX_INSPIRATIONS_PER_CONVERSATION

    @pytest.mark.asyncio
    async def test_fifo_trims_beyond_active_cap(
        self,
        db,
        tenant_id,
        conversation_id,
    ) -> None:
        set_tenant_id(tenant_id)
        set_conversation_id(str(conversation_id))
        for i in range(ACTIVE_INSPIRATIONS_CAP + 2):
            await _fetch_url_impl(
                url=f"https://site{i}.example.com",
                why="",
                db=db,
                extract_fn=_stub_extract(
                    url=f"https://site{i}.example.com",
                    domain=f"site{i}.example.com",
                ),
                analyze_fn=_stub_analyze(slug=f"site{i}"),
                lighthouse_fn=_stub_lighthouse,
            )

        repo = CopilotInspirationRepository(db)
        rows = repo.list_active_for_conversation(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            limit=20,
        )
        assert len(rows) <= ACTIVE_INSPIRATIONS_CAP

    @pytest.mark.asyncio
    async def test_returns_short_llm_content(
        self,
        db,
        tenant_id,
        conversation_id,
    ) -> None:
        set_tenant_id(tenant_id)
        set_conversation_id(str(conversation_id))
        out = await _fetch_url_impl(
            url="https://x.com",
            why="r",
            db=db,
            extract_fn=_stub_extract(md="x" * 20_000),  # huge body
            analyze_fn=_stub_analyze(),
            lighthouse_fn=_stub_lighthouse,
        )
        payload = json.loads(out)
        # Even with a huge page, llm_content stays well under 1KB.
        assert len(payload["llm_content"]) < 1000
