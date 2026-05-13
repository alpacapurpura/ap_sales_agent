"""Voice fidelity grader scaffold (S7 Fase C).

Lightweight harness for measuring whether a sales_agent run still sounds like
the configured PersonalityProfile after model swaps (DeepSeek V3→V4, Kimi
K2.5→K2.6) or compiler refactors. Read ``.claude/rules/sales-agent-brand-voice.md``
section "Voice fidelity grader (Fase C — biggest ROI)" before extending.

The harness is callable but the golden pack is intentionally small (5 prompts
per preset = 30 total) so iteration is cheap. Expand to 30 per preset before
flipping the CI gate on.
"""

from luana_core_brand_studio.application.voice_fidelity.golden import GOLDEN_PROMPTS
from luana_core_brand_studio.application.voice_fidelity.grader import (
    GraderResult,
    GraderRubric,
    grade_response,
)

__all__ = (
    "GOLDEN_PROMPTS",
    "GraderResult",
    "GraderRubric",
    "grade_response",
)
