"""Tests for Campaign FSM transitions matrix.

Property-based tests with Hypothesis to verify FSM invariants.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings, strategies as st

from src.modules.campaigns.domain.campaign import Campaign, _FSM_TRANSITIONS
from src.modules.campaigns.domain.enums import CampaignStatus


TERMINAL_STATES = frozenset({CampaignStatus.COMPLETED, CampaignStatus.CANCELED})
ALL_STATUSES = list(CampaignStatus)


class TestFsmMatrixCompleteness:
    """Test FSM matrix covers all states correctly."""

    def test_all_statuses_in_matrix(self):
        """Every CampaignStatus must appear as a key in _FSM_TRANSITIONS."""
        for status in CampaignStatus:
            assert status in _FSM_TRANSITIONS

    def test_draft_transitions(self):
        """DRAFT can only go to SCHEDULED or CANCELED."""
        allowed = _FSM_TRANSITIONS[CampaignStatus.DRAFT]
        assert allowed == frozenset({CampaignStatus.SCHEDULED, CampaignStatus.CANCELED})

    def test_scheduled_transitions(self):
        """SCHEDULED can go to RUNNING, PAUSED, or CANCELED."""
        allowed = _FSM_TRANSITIONS[CampaignStatus.SCHEDULED]
        assert allowed == frozenset({CampaignStatus.RUNNING, CampaignStatus.PAUSED, CampaignStatus.CANCELED})

    def test_running_transitions(self):
        """RUNNING can go to PAUSED, COMPLETED, or CANCELED."""
        allowed = _FSM_TRANSITIONS[CampaignStatus.RUNNING]
        assert allowed == frozenset({CampaignStatus.PAUSED, CampaignStatus.COMPLETED, CampaignStatus.CANCELED})

    def test_paused_transitions(self):
        """PAUSED can go to RUNNING (resume) or CANCELED."""
        allowed = _FSM_TRANSITIONS[CampaignStatus.PAUSED]
        assert allowed == frozenset({CampaignStatus.RUNNING, CampaignStatus.CANCELED})

    def test_completed_terminal(self):
        """COMPLETED is terminal — no allowed transitions."""
        assert _FSM_TRANSITIONS[CampaignStatus.COMPLETED] == frozenset()

    def test_canceled_terminal(self):
        """CANCELED is terminal — no allowed transitions."""
        assert _FSM_TRANSITIONS[CampaignStatus.CANCELED] == frozenset()

    def test_running_paused_toggle(self):
        """RUNNING <-> PAUSED toggle works both ways."""
        assert Campaign.transition_allowed(CampaignStatus.RUNNING, CampaignStatus.PAUSED)
        assert Campaign.transition_allowed(CampaignStatus.PAUSED, CampaignStatus.RUNNING)

    def test_terminal_states_reject_all(self):
        """No transition is allowed from COMPLETED or CANCELED."""
        for terminal in TERMINAL_STATES:
            for target in CampaignStatus:
                assert not Campaign.transition_allowed(terminal, target), (
                    f"Terminal state {terminal} should not allow transition to {target}"
                )


class TestFsmInvalidTransitions:
    """Test specific invalid transitions are rejected."""

    def test_canceled_to_running(self):
        assert not Campaign.transition_allowed(CampaignStatus.CANCELED, CampaignStatus.RUNNING)

    def test_completed_to_running(self):
        assert not Campaign.transition_allowed(CampaignStatus.COMPLETED, CampaignStatus.RUNNING)

    def test_draft_to_running_direct(self):
        """DRAFT cannot jump directly to RUNNING (must go through SCHEDULED)."""
        assert not Campaign.transition_allowed(CampaignStatus.DRAFT, CampaignStatus.RUNNING)

    def test_draft_to_completed_direct(self):
        """DRAFT cannot jump directly to COMPLETED."""
        assert not Campaign.transition_allowed(CampaignStatus.DRAFT, CampaignStatus.COMPLETED)

    def test_draft_to_paused_direct(self):
        """DRAFT cannot jump directly to PAUSED."""
        assert not Campaign.transition_allowed(CampaignStatus.DRAFT, CampaignStatus.PAUSED)


class TestFsmPropertyBased:
    """Property-based tests using Hypothesis."""

    @settings(max_examples=100)
    @given(
        from_status=st.sampled_from(list(CampaignStatus)),
        to_status=st.sampled_from(list(CampaignStatus)),
    )
    def test_only_allowed_transitions_return_true(self, from_status, to_status):
        """Only transitions listed in _FSM_TRANSITIONS should return True."""
        result = Campaign.transition_allowed(from_status, to_status)
        expected = to_status in _FSM_TRANSITIONS[from_status]
        assert result == expected, f"transition_allowed({from_status}, {to_status}) = {result}, expected {expected}"

    @settings(max_examples=50)
    @given(terminal_status=st.sampled_from(list(TERMINAL_STATES)))
    def test_no_transition_from_terminal(self, terminal_status):
        """No status should be reachable from a terminal state."""
        for target in CampaignStatus:
            assert not Campaign.transition_allowed(terminal_status, target)
