"""Validator-path alias for Scenario 1 happy multi-judge tests (Story E T-9).

The 04-validators.yaml ``scenario_1_maj_eval_multi_judge_happy`` validator
references this exact path — re-exports the free-function tests from
``scenarios/test_scenario_1_happy_multi_judge.py`` so pytest collects them
under both paths.

# voseo-allowed: docstring quotes validator path naming
"""

# NO ``from __future__ import annotations`` — story-wide cement parity.

import pytest

# Re-export Scenario 1 free-function tests under the validator-canonical path.
from tests.agentic_evals.sales_agent.grader.scenarios.test_scenario_1_happy_multi_judge import (
    test_3_rubrics_per_turn,
    test_extended_eval_metadata_persona_kind_and_grader,
)

pytestmark = pytest.mark.no_eval

__all__ = [
    "test_3_rubrics_per_turn",
    "test_extended_eval_metadata_persona_kind_and_grader",
]
