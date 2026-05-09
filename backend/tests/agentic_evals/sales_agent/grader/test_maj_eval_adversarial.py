"""Validator-path alias for Scenario 4 adversarial prompt injection tests (Story E T-9).

The 04-validators.yaml ``scenario_4_prompt_injection_via_transcript`` and
``sandbox_markers_resist_injection`` validators reference this exact path —
re-exports the free-function tests from
``scenarios/test_scenario_4_adversarial_prompt_injection.py`` so pytest
collects them under both paths.

# voseo-allowed: docstring quotes validator path naming
"""

# NO ``from __future__ import annotations`` — story-wide cement parity.

import pytest

# Re-export Scenario 4 free-function tests under the validator-canonical path.
from tests.agentic_evals.sales_agent.grader.scenarios.test_scenario_4_adversarial_prompt_injection import (
    test_injection_attempt_detected_flag_propagated,
    test_prompt_injection_in_transcript_no_score_1,
    test_sandbox_markers_protect_judge_prompt,
    test_suspicious_flag_when_all_judges_score_1_with_injection,
)

pytestmark = pytest.mark.no_eval

__all__ = [
    "test_injection_attempt_detected_flag_propagated",
    "test_prompt_injection_in_transcript_no_score_1",
    "test_sandbox_markers_protect_judge_prompt",
    "test_suspicious_flag_when_all_judges_score_1_with_injection",
]
