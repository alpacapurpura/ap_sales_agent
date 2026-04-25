"""F4 — golden tests for inspirations table in the system prompt.

Verifies:

- ``build_inspirations_layer`` returns the table when there's at least
  one inspiration row for the conversation; empty otherwise.
- The fragment is byte-stable for the same row set (cache-friendly).
- ``build_system_prompt`` inserts the inspirations fragment BETWEEN the
  brand lighthouse (F3) and the volatile completion snapshot.
- The deep-agent suffix (F2) still sits at the tail.
- Missing tenant/conversation/db gracefully returns an empty fragment
  (no exception bubbles to the chat path).
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.modules.copilot.application.orchestrator.inspirations_layer import (
    build_inspirations_layer,
)
from src.modules.copilot.infrastructure.repositories.inspiration_repository import (
    CopilotInspirationRepository,
)


@pytest.fixture(autouse=True)
def _reset_provider_discovery():
    from src.modules.copilot.application.discovery import reset_discovery

    reset_discovery()
    yield
    reset_discovery()


@pytest.fixture(autouse=True)
def _stub_db_helpers(monkeypatch):
    """Bypass DB-touching helpers in ``build_system_prompt``.

    Mirrors F3 golden tests so we exercise the REAL builder path —
    only the prompt-builder DB hits are stubbed; the inspirations
    layer's own DB hit is exercised for real (in-memory SQLite).
    """
    monkeypatch.setattr(
        "src.modules.copilot.application.orchestrator.graph._get_completion_snapshot",
        lambda _tenant_id: "",
    )
    monkeypatch.setattr(
        "src.modules.copilot.application.orchestrator.graph._get_behavior_summary",
        lambda _tenant_id, _user_id: "",
    )
    monkeypatch.setattr(
        "src.modules.copilot.domain.schema_introspection.format_all_editable_catalogs_markdown",
        lambda: "",
    )


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def conversation_id():
    return uuid4()


def _seed(repo, *, tenant_id, conversation_id, slug, why="razón", score=0.7):
    return repo.upsert(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        slug=slug,
        url=f"https://{slug}.example.com",
        why=why,
        domain=f"{slug}.example.com",
        title=None,
        summary="x",
        sub_elements={},
        brand_relevance_score=score,
        content_md="md",
        og_image=None,
    )


# ── Layer renderer ───────────────────────────────────────────────────────


class TestBuildInspirationsLayer:
    def test_empty_when_no_rows(self, db, tenant_id, conversation_id) -> None:
        state = {
            "tenant_id": tenant_id,
            "conversation_id": str(conversation_id),
        }
        # No inspirations seeded — layer is empty.
        out = build_inspirations_layer(state)
        assert out == ""

    def test_renders_table_when_rows_exist(
        self,
        db,
        monkeypatch,
        tenant_id,
        conversation_id,
    ) -> None:
        repo = CopilotInspirationRepository(db)
        _seed(repo, tenant_id=tenant_id, conversation_id=conversation_id, slug="a")
        _seed(repo, tenant_id=tenant_id, conversation_id=conversation_id, slug="b")
        db.commit()

        # Patch SessionLocal to return our test session — layer opens
        # its own session via SessionLocal in production, which is fine
        # in this unit test as the in-memory SQLite is the test engine.
        monkeypatch.setattr(
            "src.core.database.SessionLocal",
            lambda: db,
        )
        # The layer calls .close() — keep the session usable for assertions.
        monkeypatch.setattr(db, "close", lambda: None)

        state = {
            "tenant_id": tenant_id,
            "conversation_id": str(conversation_id),
        }
        out = build_inspirations_layer(state)
        assert "## Inspiraciones cargadas" in out
        assert "`a`" in out
        assert "`b`" in out
        assert "relevance 0.70" in out

    def test_no_relative_timestamps(
        self,
        db,
        monkeypatch,
        tenant_id,
        conversation_id,
    ) -> None:
        """Cache-friendliness: no 'hace 5 min' style strings."""
        repo = CopilotInspirationRepository(db)
        _seed(repo, tenant_id=tenant_id, conversation_id=conversation_id, slug="a")
        db.commit()
        monkeypatch.setattr(
            "src.core.database.SessionLocal",
            lambda: db,
        )
        monkeypatch.setattr(db, "close", lambda: None)

        state = {
            "tenant_id": tenant_id,
            "conversation_id": str(conversation_id),
        }
        out = build_inspirations_layer(state)
        forbidden = ("hace ", "ago", "min", "horas", "días")
        for marker in forbidden:
            assert marker not in out.lower(), f"unstable token in fragment: {marker!r}"

    def test_handles_missing_state_gracefully(self) -> None:
        assert build_inspirations_layer({}) == ""
        assert build_inspirations_layer({"tenant_id": uuid4()}) == ""
        assert (
            build_inspirations_layer(
                {"tenant_id": "not-uuid", "conversation_id": "x"},
            )
            == ""
        )


# ── Order in build_system_prompt ─────────────────────────────────────────


_LIGHTHOUSE_TEXT = "Marca formación para empresarias LatAm. Promesa: escalar negocios sin perder humanidad."


@pytest.fixture
def stub_summary(monkeypatch):
    from src.modules.brand.copilot_provider import summary as summary_mod

    async def _stub(self, *, tenant_id):
        return _LIGHTHOUSE_TEXT

    monkeypatch.setattr(summary_mod.BrandSummaryProvider, "summary", _stub)


class TestSystemPromptOrder:
    def test_inspirations_between_lighthouse_and_base(
        self,
        db,
        monkeypatch,
        stub_summary,
        tenant_id,
        conversation_id,
    ) -> None:
        # Seed an inspiration so the layer renders.
        repo = CopilotInspirationRepository(db)
        _seed(
            repo,
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            slug="mujer-coraje",
            why="competencia voz",
            score=0.85,
        )
        db.commit()

        monkeypatch.setattr("src.core.database.SessionLocal", lambda: db)
        monkeypatch.setattr(db, "close", lambda: None)

        state = {
            "tenant_id": tenant_id,
            "user_id": uuid4(),
            "conversation_id": str(conversation_id),
            "messages": [],
            "client_context": {
                "current_route": "/abc/offer-studio",
                "selected_fields": [],
                "form_data": {},
                "locale": "es",
            },
            "active_tool_names": [],
        }

        from src.modules.copilot.application.orchestrator.graph import (
            build_system_prompt,
        )

        prompt = build_system_prompt(state)

        # All three sections present.
        assert "## Brand Lighthouse" in prompt
        assert "## Inspiraciones cargadas" in prompt
        # F8 §5.2 reorder: identity (base prompt body) is the FIRST fragment
        # in the cacheable prefix, lighthouse comes 3rd, inspirations sit in
        # the volatile tail AFTER the cache boundary marker. Final order is
        #   identity ("Eres ...") < lighthouse < cache boundary < inspirations
        from src.modules.copilot.application.orchestrator.system_prompt_layout import (
            CACHE_BOUNDARY_MARKER,
        )

        base_pos = prompt.index("Eres el Copilot de Nicolify")
        lh_pos = prompt.index("## Brand Lighthouse")
        insp_pos = prompt.index("## Inspiraciones cargadas")
        boundary_pos = prompt.index(CACHE_BOUNDARY_MARKER)
        assert base_pos < lh_pos < boundary_pos < insp_pos

    def test_deep_agent_suffix_still_tail(
        self,
        db,
        monkeypatch,
        stub_summary,
        tenant_id,
        conversation_id,
    ) -> None:
        repo = CopilotInspirationRepository(db)
        _seed(repo, tenant_id=tenant_id, conversation_id=conversation_id, slug="x")
        db.commit()
        monkeypatch.setattr("src.core.database.SessionLocal", lambda: db)
        monkeypatch.setattr(db, "close", lambda: None)

        state = {
            "tenant_id": tenant_id,
            "user_id": uuid4(),
            "conversation_id": str(conversation_id),
            "messages": [],
            "client_context": {
                "current_route": "/abc/offer-studio",
                "selected_fields": [],
                "form_data": {},
                "locale": "es",
            },
            "active_tool_names": [],
        }

        from src.modules.copilot.application.orchestrator.deep_agent import (
            _DEEP_AGENT_SUFFIX_ES,
            _build_combined_system_prompt,
        )

        combined = _build_combined_system_prompt(state)
        assert combined.endswith(_DEEP_AGENT_SUFFIX_ES)
        insp_pos = combined.index("## Inspiraciones cargadas")
        suffix_pos = combined.index(_DEEP_AGENT_SUFFIX_ES.split("\n", 1)[0])
        assert insp_pos < suffix_pos

    def test_inspirations_absent_when_no_rows(
        self,
        db,
        monkeypatch,
        stub_summary,
        tenant_id,
        conversation_id,
    ) -> None:
        # No seed.
        monkeypatch.setattr("src.core.database.SessionLocal", lambda: db)
        monkeypatch.setattr(db, "close", lambda: None)
        state = {
            "tenant_id": tenant_id,
            "user_id": uuid4(),
            "conversation_id": str(conversation_id),
            "messages": [],
            "client_context": {
                "current_route": "/abc/offer-studio",
                "selected_fields": [],
                "form_data": {},
                "locale": "es",
            },
            "active_tool_names": [],
        }
        from src.modules.copilot.application.orchestrator.graph import (
            build_system_prompt,
        )

        prompt = build_system_prompt(state)
        assert "## Inspiraciones cargadas" not in prompt
        # Lighthouse still present (precedes inspirations layer).
        assert "## Brand Lighthouse" in prompt
