"""Architectural fitness — FSM invariants del Campaign aggregate.

Introspecciona ``Campaign._FSM_TRANSITIONS`` y verifica:
- Estados terminales (COMPLETED, CANCELED) tienen frozenset vacío.
- DRAFT solo va a SCHEDULED o CANCELED.
- SCHEDULED solo va a RUNNING, PAUSED, CANCELED.
- RUNNING ⇄ PAUSED toggle; también puede ir a COMPLETED o CANCELED.
- PAUSED puede ir a RUNNING o CANCELED.
- Property-based (Hypothesis): ningún ``to_status`` no listado produce
  ``transition_allowed=True``.

# [CAMPAIGNS-FSM-INVARIANTS-PR3-S1]
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from luana_core_campaigns.domain.campaign import Campaign, _FSM_TRANSITIONS
from luana_core_campaigns.domain.enums import CampaignStatus


class TestCampaignFSMStructure:
    """Verifica la estructura de la matriz FSM."""

    def test_all_statuses_have_transitions_entry(self) -> None:
        """Toda estado del enum debe tener entrada en _FSM_TRANSITIONS."""
        for status in CampaignStatus:
            assert status in _FSM_TRANSITIONS, f"CampaignStatus.{status.value} no tiene entrada en _FSM_TRANSITIONS"

    def test_terminal_states_have_empty_transitions(self) -> None:
        """COMPLETED y CANCELED son terminales — frozenset vacío."""
        assert _FSM_TRANSITIONS[CampaignStatus.COMPLETED] == frozenset(), "COMPLETED debe ser terminal (no transitions)"
        assert _FSM_TRANSITIONS[CampaignStatus.CANCELED] == frozenset(), "CANCELED debe ser terminal (no transitions)"

    def test_draft_transitions(self) -> None:
        """DRAFT solo puede ir a SCHEDULED o CANCELED."""
        allowed = _FSM_TRANSITIONS[CampaignStatus.DRAFT]
        expected = frozenset({CampaignStatus.SCHEDULED, CampaignStatus.CANCELED})
        assert allowed == expected, f"DRAFT transitions: esperado {expected}, got {allowed}"

    def test_scheduled_transitions(self) -> None:
        """SCHEDULED puede ir a RUNNING, PAUSED o CANCELED."""
        allowed = _FSM_TRANSITIONS[CampaignStatus.SCHEDULED]
        expected = frozenset({CampaignStatus.RUNNING, CampaignStatus.PAUSED, CampaignStatus.CANCELED})
        assert allowed == expected, f"SCHEDULED transitions: esperado {expected}, got {allowed}"

    def test_running_transitions(self) -> None:
        """RUNNING puede ir a PAUSED, COMPLETED o CANCELED."""
        allowed = _FSM_TRANSITIONS[CampaignStatus.RUNNING]
        assert CampaignStatus.PAUSED in allowed, "RUNNING debe poder ir a PAUSED"
        assert CampaignStatus.COMPLETED in allowed, "RUNNING debe poder ir a COMPLETED"
        assert CampaignStatus.CANCELED in allowed, "RUNNING debe poder ir a CANCELED"
        # RUNNING no puede volver a DRAFT ni a SCHEDULED
        assert CampaignStatus.DRAFT not in allowed, "RUNNING no puede ir a DRAFT"
        assert CampaignStatus.SCHEDULED not in allowed, "RUNNING no puede ir a SCHEDULED"

    def test_paused_running_toggle(self) -> None:
        """PAUSED ⇄ RUNNING son toggle mutuos."""
        assert CampaignStatus.RUNNING in _FSM_TRANSITIONS[CampaignStatus.PAUSED], "PAUSED debe poder volver a RUNNING"
        assert CampaignStatus.PAUSED in _FSM_TRANSITIONS[CampaignStatus.RUNNING], "RUNNING debe poder ir a PAUSED"

    def test_no_transition_from_terminal_to_any(self) -> None:
        """Ningún estado puede alcanzarse desde un estado terminal."""
        terminals = {CampaignStatus.COMPLETED, CampaignStatus.CANCELED}
        for terminal in terminals:
            assert not _FSM_TRANSITIONS[terminal], f"Estado terminal {terminal.value} no debe tener transiciones"

    def test_completed_not_reachable_from_draft_or_scheduled(self) -> None:
        """COMPLETED solo es alcanzable desde RUNNING."""
        not_allowed_sources = {CampaignStatus.DRAFT, CampaignStatus.SCHEDULED, CampaignStatus.PAUSED}
        for source in not_allowed_sources:
            assert CampaignStatus.COMPLETED not in _FSM_TRANSITIONS[source], (
                f"{source.value} no debe poder ir directamente a COMPLETED"
            )


class TestCampaignFSMPropertyBased:
    """Property-based tests via Hypothesis."""

    @given(
        from_status=st.sampled_from(list(CampaignStatus)),
        to_status=st.sampled_from(list(CampaignStatus)),
    )
    @settings(max_examples=200)
    def test_transition_allowed_matches_matrix(self, from_status: CampaignStatus, to_status: CampaignStatus) -> None:
        """``Campaign.transition_allowed()`` debe ser coherente con _FSM_TRANSITIONS."""
        expected = to_status in _FSM_TRANSITIONS[from_status]
        actual = Campaign.transition_allowed(from_status, to_status)
        assert actual == expected, (
            f"transition_allowed({from_status.value!r}, {to_status.value!r}) = {actual}, "
            f"pero _FSM_TRANSITIONS dice {expected}"
        )

    @given(from_status=st.sampled_from([CampaignStatus.COMPLETED, CampaignStatus.CANCELED]))
    @settings(max_examples=50)
    def test_no_escape_from_terminal(self, from_status: CampaignStatus) -> None:
        """Desde estados terminales ninguna transición es válida."""
        for to_status in CampaignStatus:
            assert not Campaign.transition_allowed(from_status, to_status), (
                f"Estado terminal {from_status.value} no debe poder transicionar a {to_status.value}"
            )

    @given(to_status=st.sampled_from([CampaignStatus.COMPLETED, CampaignStatus.CANCELED]))
    @settings(max_examples=50)
    def test_only_running_reaches_completed(self, to_status: CampaignStatus) -> None:
        """COMPLETED solo se alcanza desde RUNNING. CANCELED se alcanza desde múltiples."""
        if to_status == CampaignStatus.COMPLETED:
            for from_status in CampaignStatus:
                if from_status == CampaignStatus.RUNNING:
                    assert Campaign.transition_allowed(from_status, to_status)
                else:
                    assert not Campaign.transition_allowed(from_status, to_status), (
                        f"{from_status.value} no debe poder ir a COMPLETED (solo RUNNING puede)"
                    )
