"""Concurrent session safety tests for the Interview Engine.

These tests verify that the InterviewService correctly handles race conditions
when multiple requests arrive simultaneously for the same tenant+domain:

1. Duplicate-start prevention: two simultaneous start_interview calls for the
   same tenant+domain must not create two active sessions.
2. Concurrent state reads: two simultaneous get_state calls must both succeed
   and return consistent data.
3. Cross-tenant isolation: concurrent sessions for different tenants must not
   interfere with each other.
4. IntegrityError race condition: the service catches SQLAlchemy IntegrityError
   (duplicate active session) and gracefully returns the existing session.

Why no real threads?
- The DB fixture uses SQLite in-memory with a StaticPool — sharing it across
  threads is unsafe in tests.
- The concurrency contract lives in the application layer (service logic +
  IntegrityError handler), not in SQLite's locking model.
- We test the concurrency _behaviour_ (post-IntegrityError recovery) by
  directly triggering the IntegrityError path, which is more reliable and
  faster than thread-based tests.
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from langchain_core.messages import AIMessage
from sqlalchemy.exc import IntegrityError

from src.modules.copilot.application.orchestrator.chat import CopilotOrchestrator
from src.modules.copilot.application.services.interview_service import InterviewService
from src.modules.copilot.infrastructure.repositories.interview_session_repository import (
    InterviewSessionRepository,
)

# ── Helpers ───────────────────────────────────────────────────────────


def _make_service(db) -> InterviewService:
    """Build an InterviewService with a real in-memory DB session but mocked ConversationRepo."""
    with patch.object(InterviewService, "__init__", lambda self, db: None):
        svc = InterviewService.__new__(InterviewService)
        svc.db = db
        svc.session_repo = InterviewSessionRepository(db)
        svc.conversation_repo = MagicMock()
    return svc


def _make_orch() -> CopilotOrchestrator:
    """Build a CopilotOrchestrator with fully mocked dependencies."""
    mock_db = MagicMock()
    mock_conv = MagicMock()
    mock_conv.title = None
    mock_conv.messages = []

    with patch(
        "src.modules.copilot.application.orchestrator.chat.ConversationRepository",
    ) as mock_cls:
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_conv
        mock_repo.create.return_value = mock_conv
        mock_cls.return_value = mock_repo
        orch = CopilotOrchestrator(mock_db)

    orch.conv_repo = mock_repo
    return orch


def _extract_event_types(frames: list[str]) -> list[str | None]:
    """Extract the SSE event type from each raw frame string."""
    result = []
    for raw in frames:
        event_type = next(
            (line[len("event: ") :] for line in raw.split("\n") if line.startswith("event: ")),
            None,
        )
        result.append(event_type)
    return result


def _get_done_conv_id(frames: list[str]) -> str | None:
    """Extract conversation_id from the 'done' SSE frame."""
    for frame in frames:
        lines = frame.strip().split("\n")
        ev_type = next((line[len("event: ") :] for line in lines if line.startswith("event: ")), None)
        if ev_type == "done":
            data_str = next((line[len("data: ") :] for line in lines if line.startswith("data: ")), "{}")
            return json.loads(data_str).get("conversation_id")
    return None


# ── Sequential duplicate prevention (application-layer guard) ─────────


class TestDuplicateSessionPrevention:
    """Verify that the service rejects a second active session for the same domain."""

    def test_second_start_raises_value_error(self, db) -> None:
        """start_interview raises ValueError if an active session already exists."""
        svc = _make_service(db)
        tenant_id = uuid4()
        user_id = uuid4()

        svc.start_interview(tenant_id=tenant_id, user_id=user_id, domain="brand")

        with pytest.raises(ValueError, match="Active session exists"):
            svc.start_interview(tenant_id=tenant_id, user_id=user_id, domain="brand")

    def test_second_start_different_tenant_same_domain_succeeds(self, db) -> None:
        """Starting brand interviews for two different tenants simultaneously is allowed."""
        svc = _make_service(db)
        tenant_a = uuid4()
        tenant_b = uuid4()
        user_id = uuid4()

        r1 = svc.start_interview(tenant_id=tenant_a, user_id=user_id, domain="brand")
        r2 = svc.start_interview(tenant_id=tenant_b, user_id=user_id, domain="brand")

        # Each tenant gets its own distinct session
        assert r1["session_id"] != r2["session_id"]

    def test_second_start_different_tenant_succeeds(self, db) -> None:
        """Two tenants can both have active brand sessions simultaneously."""
        svc = _make_service(db)
        tenant_a = uuid4()
        tenant_b = uuid4()
        user_id = uuid4()

        r_a = svc.start_interview(tenant_id=tenant_a, user_id=user_id, domain="brand")
        r_b = svc.start_interview(tenant_id=tenant_b, user_id=user_id, domain="brand")

        # Both sessions must be distinct and active
        assert r_a["session_id"] != r_b["session_id"]
        assert svc.get_active(tenant_a) is not None
        assert svc.get_active(tenant_b) is not None

    def test_abandon_then_start_succeeds(self, db) -> None:
        """After abandoning a session, a new one can be started for the same domain."""
        svc = _make_service(db)
        tenant_id = uuid4()
        user_id = uuid4()

        r1 = svc.start_interview(tenant_id=tenant_id, user_id=user_id, domain="brand")
        svc.abandon(r1["session_id"], tenant_id)

        r2 = svc.start_interview(tenant_id=tenant_id, user_id=user_id, domain="brand")
        assert r2["session_id"] != r1["session_id"]

    def test_pause_allows_new_start(self, db) -> None:
        """A PAUSED session does NOT block a new active session.

        get_active_by_domain only queries for ACTIVE status — so pausing
        frees the slot for a brand-new session to be started.
        """
        svc = _make_service(db)
        tenant_id = uuid4()
        user_id = uuid4()

        r1 = svc.start_interview(tenant_id=tenant_id, user_id=user_id, domain="brand")
        svc.pause(r1["session_id"], tenant_id)

        # With paused session, a new start should succeed (no active session exists)
        r2 = svc.start_interview(tenant_id=tenant_id, user_id=user_id, domain="brand")
        assert r2["session_id"] != r1["session_id"]
        # The new session is now active
        active = svc.get_active(tenant_id)
        assert active is not None
        assert active["domain"] == "brand"


# ── IntegrityError race-condition handler ─────────────────────────────


class TestIntegrityErrorRecovery:
    """Verify that start_interview recovers from a DB IntegrityError (race condition)."""

    def test_integrity_error_returns_existing_session(self, db) -> None:
        """When IntegrityError is raised (race condition), the service returns the winner's session.

        The race condition scenario: two requests both pass get_active_by_domain (both see
        no active session), both create a session, but only one wins the DB unique constraint.
        The loser gets IntegrityError and must recover by fetching the winner's session.

        We simulate this by:
        1. Bypassing the normal get_active_by_domain check (mock returns None even though
           the session exists).
        2. Having save() raise IntegrityError on the first call.
        3. Verifying the service falls back to get_active_by_domain and returns the winner.
        """
        from src.modules.copilot.domain.interview_config import get_interview_config
        from src.modules.copilot.domain.interview_session import InterviewSession

        svc = _make_service(db)
        tenant_id = uuid4()
        user_id = uuid4()

        # Pre-create the "winner" session directly via repo (bypassing service guard)
        config = get_interview_config("brand")
        winner_session = InterviewSession.create(
            tenant_id=tenant_id,
            domain="brand",
            config=config,
            conversation_id=uuid4(),
        )
        svc.session_repo.save(winner_session)
        db.commit()
        winner_id = winner_session.id

        # Patch get_active_by_domain to return None on the first call
        # (simulating the race: check passed BEFORE the winner committed),
        # then return the winner on the second call (after rollback + recovery).
        real_get_active = svc.session_repo.get_active_by_domain
        call_count = {"n": 0}

        def patched_get_active(tid: UUID, domain: str) -> InterviewSession | None:
            call_count["n"] += 1
            if call_count["n"] == 1:
                # First call: slot looks empty (race condition window)
                return None
            # Subsequent calls: winner is already there
            return real_get_active(tid, domain)

        svc.session_repo.get_active_by_domain = patched_get_active

        # Patch save to raise IntegrityError (the "loser" hits the constraint)
        integrity_err = "unique_active_session_per_domain"

        def save_raises_once(session: InterviewSession) -> None:
            db.rollback()
            raise IntegrityError(integrity_err, {}, None)

        svc.session_repo.save = save_raises_once

        # The service must recover: catch IntegrityError, re-query, return winner
        result = svc.start_interview(tenant_id=tenant_id, user_id=user_id, domain="brand")

        assert result["session_id"] == winner_id
        assert "initial_message" in result

    def test_integrity_error_non_duplicate_is_reraised(self, db) -> None:
        """An IntegrityError that is NOT a duplicate active session is re-raised."""
        svc = _make_service(db)
        tenant_id = uuid4()
        user_id = uuid4()

        # Patch save to raise IntegrityError when no existing session is in DB
        other_constraint = "other_constraint"

        def always_raise(session: InterviewService) -> None:
            db.rollback()
            raise IntegrityError(other_constraint, {}, None)

        svc.session_repo.save = always_raise

        with pytest.raises(IntegrityError):
            svc.start_interview(tenant_id=tenant_id, user_id=user_id, domain="brand")


# ── Concurrent get_state reads ────────────────────────────────────────


class TestConcurrentStateReads:
    """Verify that concurrent state reads return consistent data."""

    def test_multiple_get_state_calls_consistent(self, db) -> None:
        """Multiple sequential get_state calls return the same snapshot."""
        svc = _make_service(db)
        tenant_id = uuid4()
        user_id = uuid4()

        result = svc.start_interview(tenant_id=tenant_id, user_id=user_id, domain="brand")
        session_id = result["session_id"]

        states = [svc.get_state(session_id, tenant_id) for _ in range(5)]

        # All reads return the same data
        assert all(s is not None for s in states)
        assert all(s["session_id"] == session_id for s in states)
        assert all(s["bloque_actual"] == states[0]["bloque_actual"] for s in states)

    def test_get_active_consistent_across_reads(self, db) -> None:
        """Multiple get_active calls return the same active session."""
        svc = _make_service(db)
        tenant_id = uuid4()
        user_id = uuid4()

        svc.start_interview(tenant_id=tenant_id, user_id=user_id, domain="brand")

        actives = [svc.get_active(tenant_id) for _ in range(5)]

        assert all(a is not None for a in actives)
        assert all(a["domain"] == "brand" for a in actives)

    async def test_async_concurrent_get_active_reads(self, db) -> None:
        """Async gather of multiple get_active calls all return identical results."""
        svc = _make_service(db)
        tenant_id = uuid4()
        user_id = uuid4()

        svc.start_interview(tenant_id=tenant_id, user_id=user_id, domain="brand")

        # Run 10 concurrent async coroutines wrapping the sync call
        async def read() -> dict | None:
            return svc.get_active(tenant_id)

        results = await asyncio.gather(*[read() for _ in range(10)])

        assert all(r is not None for r in results)
        # All results must be for the same domain
        assert all(r["domain"] == "brand" for r in results)


# ── Concurrent chat message simulation ────────────────────────────────


class TestConcurrentChatMessages:
    """Verify orchestrator behaviour when two messages arrive simultaneously."""

    async def test_two_messages_both_get_responses(self) -> None:
        """Two concurrent stream_chat calls each yield at least a done event."""

        async def fake_fast_stream(state: dict, *, version: str = "v2"):  # type: ignore[return]
            yield {
                "event": "on_chat_model_end",
                "data": {"output": AIMessage(content="Respuesta rápida")},
            }

        async def run_chat(orch: CopilotOrchestrator, msg_id: int) -> list[str]:
            with (
                patch(
                    "src.modules.copilot.application.orchestrator.chat.copilot_graph",
                ) as mock_graph,
                patch(
                    "src.modules.copilot.application.orchestrator.chat.redis_client",
                    None,
                ),
            ):
                mock_graph.astream_events = fake_fast_stream
                return [
                    frame
                    async for frame in orch.stream_chat(
                        user_id=uuid4(),
                        tenant_id=uuid4(),
                        message=f"Mensaje {msg_id}",
                    )
                ]

        orch1 = _make_orch()
        orch2 = _make_orch()

        # Run both concurrently
        results1, results2 = await asyncio.gather(
            run_chat(orch1, 1),
            run_chat(orch2, 2),
        )

        event_types_1 = _extract_event_types(results1)
        event_types_2 = _extract_event_types(results2)

        assert "done" in event_types_1, f"Chat 1 missing done: {event_types_1}"
        assert "done" in event_types_2, f"Chat 2 missing done: {event_types_2}"

    async def test_two_messages_same_tenant_independent_conversations(self) -> None:
        """Two chat messages in different conversations are fully independent."""

        async def fake_stream(state: dict, *, version: str = "v2"):  # type: ignore[return]
            yield {
                "event": "on_chat_model_end",
                "data": {"output": AIMessage(content="OK")},
            }

        tenant_id = uuid4()

        async def run_and_capture(orch: CopilotOrchestrator, conv_id: UUID) -> list[str]:
            with (
                patch(
                    "src.modules.copilot.application.orchestrator.chat.copilot_graph",
                ) as mock_graph,
                patch(
                    "src.modules.copilot.application.orchestrator.chat.redis_client",
                    None,
                ),
            ):
                mock_graph.astream_events = fake_stream
                return [
                    frame
                    async for frame in orch.stream_chat(
                        user_id=uuid4(),
                        tenant_id=tenant_id,
                        message="Hola",
                        conversation_id=str(conv_id),
                    )
                ]

        conv1 = uuid4()
        conv2 = uuid4()
        orch1 = _make_orch()
        orch2 = _make_orch()

        frames1, frames2 = await asyncio.gather(
            run_and_capture(orch1, conv1),
            run_and_capture(orch2, conv2),
        )

        done_conv1 = _get_done_conv_id(frames1)
        done_conv2 = _get_done_conv_id(frames2)

        assert done_conv1 == str(conv1), f"Expected {conv1}, got {done_conv1}"
        assert done_conv2 == str(conv2), f"Expected {conv2}, got {done_conv2}"
        assert done_conv1 != done_conv2


# ── Cross-tenant isolation ────────────────────────────────────────────


class TestCrossTenantIsolation:
    """Verify that concurrent operations across different tenants remain isolated."""

    def test_pause_one_tenant_does_not_affect_other(self, db) -> None:
        """Pausing tenant A's session has no effect on tenant B's session."""
        svc = _make_service(db)
        user_id = uuid4()
        tenant_a = uuid4()
        tenant_b = uuid4()

        r_a = svc.start_interview(tenant_id=tenant_a, user_id=user_id, domain="brand")
        svc.start_interview(tenant_id=tenant_b, user_id=user_id, domain="brand")

        # Pause tenant A
        svc.pause(r_a["session_id"], tenant_a)

        # Tenant B should still be active
        active_b = svc.get_active(tenant_b)
        assert active_b is not None
        assert active_b["domain"] == "brand"

        # Tenant A should not be active
        active_a = svc.get_active(tenant_a)
        assert active_a is None

    def test_tenant_b_cannot_read_tenant_a_state(self, db) -> None:
        """get_state for tenant B must not return tenant A's session data."""
        svc = _make_service(db)
        user_id = uuid4()
        tenant_a = uuid4()
        tenant_b = uuid4()

        r_a = svc.start_interview(tenant_id=tenant_a, user_id=user_id, domain="brand")

        # Tenant B tries to read tenant A's session
        state = svc.get_state(r_a["session_id"], tenant_b)
        assert state is None  # Must not be accessible across tenants

    def test_abandon_is_tenant_scoped(self, db) -> None:
        """Tenant B cannot abandon tenant A's session."""
        svc = _make_service(db)
        user_id = uuid4()
        tenant_a = uuid4()
        tenant_b = uuid4()

        r_a = svc.start_interview(tenant_id=tenant_a, user_id=user_id, domain="brand")

        # Tenant B tries to abandon tenant A's session
        success = svc.abandon(r_a["session_id"], tenant_b)
        assert success is False

        # Tenant A's session must still be active
        assert svc.get_active(tenant_a) is not None

    def test_session_status_isolation(self, db) -> None:
        """Checking session status for wrong tenant returns None, not wrong status."""
        svc = _make_service(db)
        user_id = uuid4()
        tenant_a = uuid4()
        tenant_b = uuid4()

        r_a = svc.start_interview(tenant_id=tenant_a, user_id=user_id, domain="brand")

        # Direct repo query with wrong tenant
        session = svc.session_repo.get_by_id(r_a["session_id"], tenant_b)
        assert session is None
