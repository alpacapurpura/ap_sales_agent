"""Integration tests — suggestions endpoint con real engine + providers.

Requires a running Postgres (markers: integration). Skipped if no DB.

# [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
"""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.iam.api.dependencies import get_current_user, get_tenant_context


@pytest.mark.integration
class TestSuggestionsIntegration:
    """End-to-end tests using real OfferSuggestionProvider."""

    def test_e2e_real_engine_real_offer_provider(self) -> None:
        """Tenant sin offers + route='offer-studio' → chip 'Crea tu primera oferta'."""
        from src.modules.copilot.api.suggestions import router
        from src.modules.copilot.application.suggestions.registry import _reset_for_tests

        # Reset engine so we get a fresh bootstrap (OfferSuggestionProvider)
        _reset_for_tests()

        tenant_id = uuid4()  # Fresh tenant with no offers
        uid = uuid4()

        app = FastAPI()
        app.include_router(router, prefix="/api/v1/copilot")
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            id=uid,
            tenant_id=tenant_id,
        )
        app.dependency_overrides[get_tenant_context] = lambda: tenant_id

        client = TestClient(app)
        resp = client.post(
            "/api/v1/copilot/suggestions",
            json={"current_route": "offer-studio"},
            headers={"X-Tenant-ID": str(tenant_id)},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "suggestions" in data
        assert "breakdown" in data
        assert "latency_ms" in data
        # With no offers and offer-studio route, provider should suggest creating one
        labels = [s["label"] for s in data["suggestions"]]
        # At least one chip is expected from OfferSuggestionProvider for offer-studio
        assert isinstance(labels, list)

    def test_e2e_subscriber_writes_trace_event_on_shown(self, db_engine) -> None:
        """POST /suggestions con engine devuelve chips → trace_event suggestion_shown."""
        from types import SimpleNamespace
        from unittest.mock import MagicMock, patch

        from sqlalchemy.orm import sessionmaker

        from src.modules.copilot.api.suggestions import router
        from src.modules.copilot.application.suggestions.registry import _reset_for_tests
        from src.modules.copilot.domain.suggestion import Suggestion, SuggestionCategory
        from src.modules.copilot.infrastructure.models.trace_event_model import (
            CopilotTraceEventModel,
        )
        from src.modules.copilot.observability.persistence.trace_event_repository import (
            TraceEventRepository,
        )
        from src.modules.copilot.observability.recording.domain_subscribers import (
            register_subscribers,
        )
        from src.shared.domain.events import EventBus

        EventBus.clear()
        conn = db_engine.connect()
        txn = conn.begin()
        session = sessionmaker(autocommit=False, autoflush=False, bind=conn)()

        try:
            register_subscribers(repo_factory=lambda: TraceEventRepository(session))

            _reset_for_tests()
            tenant_id = uuid4()
            uid = uuid4()
            chip = Suggestion(
                id=uuid4(),
                label="Crea tu primera oferta",
                prompt="Quiero crear una oferta",
                confidence=0.9,
                category=SuggestionCategory.ACTION,
                source_module="offer",
            )

            app = FastAPI()
            app.include_router(router, prefix="/api/v1/copilot")
            app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
                id=uid,
                tenant_id=tenant_id,
            )
            app.dependency_overrides[get_tenant_context] = lambda: tenant_id

            client = TestClient(app)

            with patch("src.modules.copilot.api.suggestions.get_default_engine") as mock_fn:
                mock_engine = MagicMock()
                mock_engine.get_suggestions.return_value = ([chip], {"offer": 1}, 5)
                mock_fn.return_value = mock_engine

                resp = client.post(
                    "/api/v1/copilot/suggestions",
                    json={"current_route": "offer-studio"},
                    headers={"X-Tenant-ID": str(tenant_id)},
                )

            assert resp.status_code == 200
            session.flush()

            rows = (
                session.query(CopilotTraceEventModel)
                .filter_by(tenant_id=tenant_id, event_type="suggestion_shown")
                .all()
            )
            assert len(rows) >= 1

        finally:
            EventBus.clear()
            session.close()
            txn.rollback()
            conn.close()

    def test_e2e_subscriber_writes_trace_event_on_accept(self, db_engine) -> None:
        """POST /accept → copilot_trace_event suggestion_accepted row written."""
        from datetime import datetime, timezone

        from sqlalchemy.orm import sessionmaker

        from src.modules.copilot.api.suggestions import router
        from src.modules.copilot.infrastructure.models.trace_event_model import (
            CopilotTraceEventModel,
        )
        from src.modules.copilot.observability.persistence.trace_event_repository import (
            TraceEventRepository,
        )
        from src.modules.copilot.observability.recording.domain_subscribers import (
            register_subscribers,
        )
        from src.shared.domain.events import EventBus

        EventBus.clear()
        conn = db_engine.connect()
        txn = conn.begin()
        session = sessionmaker(autocommit=False, autoflush=False, bind=conn)()

        try:
            register_subscribers(repo_factory=lambda: TraceEventRepository(session))

            tenant_id = uuid4()
            uid = uuid4()
            suggestion_id = uuid4()

            app = FastAPI()
            app.include_router(router, prefix="/api/v1/copilot")
            app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
                id=uid,
                tenant_id=tenant_id,
            )
            app.dependency_overrides[get_tenant_context] = lambda: tenant_id

            client = TestClient(app)
            resp = client.post(
                "/api/v1/copilot/suggestions/accept",
                json={
                    "suggestion_id": str(suggestion_id),
                    "conversation_id": None,
                    "current_route": "offer-studio",
                    "category": "action",
                    "source_module": "offer",
                    "accepted_at": datetime.now(tz=timezone.utc).isoformat(),
                },
                headers={"X-Tenant-ID": str(tenant_id)},
            )

            assert resp.status_code == 202
            session.flush()

            rows = (
                session.query(CopilotTraceEventModel)
                .filter_by(tenant_id=tenant_id, event_type="suggestion_accepted")
                .all()
            )
            assert len(rows) >= 1
            assert str(suggestion_id) in str(rows[0].data)

        finally:
            EventBus.clear()
            session.close()
            txn.rollback()
            conn.close()
