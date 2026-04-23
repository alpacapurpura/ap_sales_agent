"""Fixtures for admin-panel smoke tests.

Admin pages rely on Postgres, Qdrant and several repositories. Smoke tests run
headless with no infrastructure, so we replace the heavy dependencies with
stubs that return empty results. Every admin page wraps its body in a
try/except UI error boundary, so these stubs exercise the real render code
path while keeping tests hermetic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

# ── Stub repo & service payloads ────────────────────────────────────────────
_EMPTY_ENGAGEMENT = {
    "total_messages": 0,
    "total_conversations": 0,
    "avg_messages_per_conv": 0.0,
}
_EMPTY_SUMMARY = {
    "proposal_accepted": 0,
    "proposal_rejected": 0,
    "total_events": 0,
    "total_messages": 0,
    "nudges_shown": 0,
    "nudges_accepted": 0,
    "procedure_started": 0,
    "procedure_completed": 0,
    "procedure_abandoned": 0,
}


def _stub_event_repo() -> MagicMock:
    repo = MagicMock(name="CopilotEventRepository")
    repo.get_global_engagement.return_value = _EMPTY_ENGAGEMENT
    repo.get_global_summary.return_value = _EMPTY_SUMMARY
    repo.get_global_procedure_rates.return_value = {}
    repo.get_global_friction_map.return_value = {}
    repo.get_recent_events_all.return_value = []
    repo.get_global_nudge_stats.return_value = {"shown": 0, "accepted": 0, "dismissed": 0}
    repo.get_top_friction_routes.return_value = []
    repo.get_event_type_breakdown.return_value = {}
    return repo


def _stub_conversation_repo() -> MagicMock:
    repo = MagicMock(name="ConversationRepository")
    repo.count_all.return_value = 0
    repo.list_all_paginated.return_value = []
    repo.get_global_stats.return_value = {"total": 0, "avg_messages": 0.0, "with_tools": 0}
    return repo


def _stub_session() -> MagicMock:
    sess = MagicMock(name="AdminSessionStub")
    sess.close.return_value = None
    # SQLAlchemy .execute().fetchone() / iteration → empty-ish responses
    cursor = MagicMock()
    cursor.fetchone.return_value = None
    cursor.fetchall.return_value = []
    cursor.__iter__ = lambda self: iter([])
    cursor.scalars.return_value.all.return_value = []
    cursor.scalar.return_value = 0
    # SQLAlchemy 2.0 mapping API used by the traces page:
    cursor.mappings.return_value.all.return_value = []
    sess.execute.return_value = cursor
    return sess


def _stub_knowledge_store() -> MagicMock:
    store = MagicMock(name="CopilotKnowledgeStore")
    store.get_collection_stats.return_value = {"points_count": 0}
    store.list_documents.return_value = []
    return store


def _stub_tenant_service() -> Callable[..., MagicMock]:
    def factory(*_args: Any, **_kwargs: Any) -> MagicMock:
        svc = MagicMock(name="TenantService")
        svc.get_all_tenants.return_value = []
        return svc

    return factory


@pytest.fixture(autouse=True)
def _mock_admin_dependencies(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Replace DB, Qdrant and repositories used by admin modules with stubs."""
    # 1) Session factory — any `SessionLocal()` call returns our stub session.
    monkeypatch.setattr("src.core.database.SessionLocal", _stub_session)

    # 2) Tenant service (used by `_shared.get_tenant_options`).
    monkeypatch.setattr(
        "src.modules.iam.application.services.tenant_service.TenantService",
        _stub_tenant_service(),
    )

    # 3) Copilot repos (instantiated inside render_*).
    monkeypatch.setattr(
        "src.modules.copilot.infrastructure.repositories.event_repository.CopilotEventRepository",
        lambda *_a, **_kw: _stub_event_repo(),
    )
    monkeypatch.setattr(
        "src.modules.copilot.infrastructure.repositories.conversation_repository.ConversationRepository",
        lambda *_a, **_kw: _stub_conversation_repo(),
    )

    # 4) Qdrant vector store — avoid network calls.
    monkeypatch.setattr(
        "src.modules.copilot.infrastructure.knowledge.vector_store.CopilotKnowledgeStore",
        lambda *_a, **_kw: _stub_knowledge_store(),
    )

    # 5) Pre-cached tenant list + adoption funnel used by `_shared`.
    monkeypatch.setattr(
        "src.admin.modules._shared.get_tenant_options",
        list,
    )
    monkeypatch.setattr(
        "src.admin.modules._shared.get_all_tenants_summary",
        list,
    )
    monkeypatch.setattr(
        "src.admin.modules._shared.get_adoption_funnel",
        lambda: {
            "total_tenants": 0,
            "has_brand": 0,
            "has_offer": 0,
            "has_connection": 0,
            "has_copilot": 0,
            "has_procedure_completed": 0,
        },
    )
    monkeypatch.setattr(
        "src.admin.modules._shared.get_tenant_name",
        lambda _tenant_id: "—",
    )

    # 6) Tenant selector — stub to `None` so pages render their empty-state.
    # Smoke tests exercise the render path, not the picker UX.
    import uuid as _uuid

    _fake_tenant = _uuid.UUID("00000000-0000-0000-0000-000000000001")

    def _fake_selector(key: str, allow_all: bool = True) -> _uuid.UUID | None:
        return None if allow_all else _fake_tenant

    monkeypatch.setattr("src.admin.modules._shared.render_tenant_selector", _fake_selector)

    # 7) Module-local tenant fetchers — users.py and tenants.py each have their
    # own `get_tenants()` helper that hits the ORM directly (SA 1.x). Force
    # empty so their render functions hit the "no tenants" empty-state path.
    monkeypatch.setattr("src.admin.modules.users.get_tenants", list)
    monkeypatch.setattr("src.admin.modules.tenants.get_tenants", list)

    yield
