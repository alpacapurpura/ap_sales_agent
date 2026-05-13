"""Regression tests for conversation context bugs.

Bug #1: LLM receives no conversation history — state["messages"] only contains
        the current user message, so the LLM treats every turn as first contact.
Bug #2: session_gap_hours always ≈ 0 — _determine_session_state is called AFTER
        logging the current message, so get_last_message returns the just-logged msg.
Bug #3: agent_identity.j2 greeting example biases LLM to greet every turn.
"""

import importlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from luana_core_sales_agent.application.orchestrator.chat import (
    merge_history_with_current,
)
from luana_core_sales_agent.application.orchestrator.conversation_pipeline import (
    ConversationPipeline,
)

# ---------------------------------------------------------------------------
# Bug #1: merge_history_with_current
# ---------------------------------------------------------------------------


class TestMergeHistoryWithCurrent:
    """Pure function that builds full message list from history + current message."""

    def test_empty_history_returns_only_current(self):
        result = merge_history_with_current([], "Hola", "Hola")
        assert result == [{"role": "user", "content": "Hola"}]

    def test_history_prepended_to_current(self):
        history = [
            {"role": "user", "content": "Me interesa"},
            {"role": "assistant", "content": "¡Genial! ¿A qué te dedicas?"},
        ]
        result = merge_history_with_current(history, "Soy coach", "Soy coach")
        assert len(result) == 3
        assert result[0]["content"] == "Me interesa"
        assert result[1]["content"] == "¡Genial! ¿A qué te dedicas?"
        assert result[2]["content"] == "Soy coach"

    def test_deduplicates_current_message_from_history(self):
        """When history includes the current user msg (logged before history load),
        it should be deduplicated so the message doesn't appear twice."""
        history = [
            {"role": "user", "content": "Anterior"},
            {"role": "assistant", "content": "Respuesta"},
            {"role": "user", "content": "Tengo 3 clientes"},  # duplicate of current
        ]
        result = merge_history_with_current(history, "Tengo 3 clientes", "Tengo 3 clientes")
        assert len(result) == 3  # 2 history + 1 current (deduped)
        assert result[-1]["content"] == "Tengo 3 clientes"
        assert result[-2]["content"] == "Respuesta"

    def test_no_false_dedup_when_last_history_is_assistant(self):
        """Only dedup if last history entry is role=user matching current text."""
        history = [
            {"role": "user", "content": "Hola"},
            {"role": "assistant", "content": "Tengo 3 clientes"},  # assistant, not user
        ]
        result = merge_history_with_current(history, "Tengo 3 clientes", "Tengo 3 clientes")
        assert len(result) == 3  # no dedup — last history is assistant

    def test_sanitized_text_used_in_output(self):
        """Output uses sanitized_text, not raw_text."""
        history = [
            {"role": "user", "content": "raw text with <script>"},  # duplicate of raw
        ]
        result = merge_history_with_current(
            history,
            sanitized_text="raw text with script",  # sanitized
            raw_text="raw text with <script>",  # raw matches history
        )
        assert len(result) == 1  # deduped
        assert result[0]["content"] == "raw text with script"  # sanitized version

    def test_does_not_mutate_input_history(self):
        """The input list must not be modified."""
        history = [
            {"role": "user", "content": "Hola"},
            {"role": "user", "content": "duplicate"},
        ]
        original_len = len(history)
        merge_history_with_current(history, "duplicate", "duplicate")
        assert len(history) == original_len


# ---------------------------------------------------------------------------
# Bug #2: session_gap_hours calculation
# ---------------------------------------------------------------------------


class TestSessionGapCalculation:
    """_determine_session_state must reflect time since PREVIOUS message,
    not the just-logged current message."""

    def test_returns_correct_gap_for_returning_user(self):
        """When last message is 2 hours old, session_gap_hours ≈ 2.0."""
        mock_audit = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "test-lead-id"

        two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
        mock_msg = MagicMock()
        mock_msg.created_at = two_hours_ago
        mock_msg.metadata_log = None
        mock_audit.get_last_message.return_value = mock_msg

        result = ConversationPipeline.determine_session_state(mock_audit, mock_user)

        assert result["is_returning_user"] is True
        assert result["session_active"] is True  # < 6 hours
        assert 1.9 < result["session_gap_hours"] < 2.1

    def test_session_expired_after_timeout(self):
        """When last message is 8 hours old, session_active should be False."""
        mock_audit = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "test-lead-id"

        eight_hours_ago = datetime.now(timezone.utc) - timedelta(hours=8)
        mock_msg = MagicMock()
        mock_msg.created_at = eight_hours_ago
        mock_msg.metadata_log = None
        mock_audit.get_last_message.return_value = mock_msg

        result = ConversationPipeline.determine_session_state(mock_audit, mock_user)

        assert result["is_returning_user"] is True
        assert result["session_active"] is False
        assert 7.9 < result["session_gap_hours"] < 8.1

    def test_new_user_has_no_gap(self):
        """Brand new user (no previous messages) → gap is None, not returning."""
        mock_audit = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "test-lead-id"
        mock_audit.get_last_message.return_value = None

        result = ConversationPipeline.determine_session_state(mock_audit, mock_user)

        assert result["is_returning_user"] is False
        assert result["session_gap_hours"] is None
        assert result["session_active"] is True


# ---------------------------------------------------------------------------
# Bug #3: agent_identity.j2 must not have greeting example
# ---------------------------------------------------------------------------


class TestAgentIdentityTemplate:
    """agent_identity.j2 must not contain hardcoded greeting patterns
    that bias the LLM to greet on every turn."""

    def test_no_hola_greeting_example(self):
        """The template must not have a 'Saludo natural: Hola' example."""
        template_path = Path(__file__).resolve().parents[3] / (
            "src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2"
        )
        content = template_path.read_text()
        assert "Saludo natural" not in content, (
            "agent_identity.j2 contains a greeting example that biases the LLM to greet on every turn"
        )
