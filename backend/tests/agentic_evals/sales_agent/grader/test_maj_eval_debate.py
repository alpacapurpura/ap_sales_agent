"""Validator-path alias for Scenario 2 edge Round 2 debate tests (Story E T-9).

The 04-validators.yaml ``scenario_2_judge_disagreement_triggers_debate``,
``round_2_convergence_or_unconverged_flag``, and
``r2_partial_fallback_judge_fail`` validators reference this exact path —
re-exports the free-function tests from
``scenarios/test_scenario_2_edge_round_2_debate.py`` so pytest collects them
under both paths.

# voseo-allowed: docstring quotes validator path naming
"""

# NO ``from __future__ import annotations`` — story-wide cement parity.

import pytest

# Re-export Scenario 2 free-function tests under the validator-canonical path.
from tests.agentic_evals.sales_agent.grader.scenarios.test_scenario_2_edge_round_2_debate import (
    test_r2_partial_fallback_judge_fail,
    test_round_2_convergence_or_unconverged_flag,
    test_round_2_peer_reasoning_excludes_self,
    test_variance_triggers_round_2,
)

pytestmark = pytest.mark.no_eval

__all__ = [
    "test_r2_partial_fallback_judge_fail",
    "test_round_2_convergence_or_unconverged_flag",
    "test_round_2_peer_reasoning_excludes_self",
    "test_variance_triggers_round_2",
]
