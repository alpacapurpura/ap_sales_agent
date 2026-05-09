"""MAJ-EVAL grader Pydantic types (Story E v1 cement).

Schema versioning: ``MajEvalScore.schema_version: Literal[1] = 1``. Future bumps via
``SCHEMA_MIGRATIONS`` registry (Story B H1 reuse) — register identity migrator
(MajEvalScore, 1, 2) when bumping to v2. Frozen=True per ConfigDict (immutable post-grade).

Decisions applicable: D-BE-3 (schema-mirror R5), D-BE-4 (MajEvalScore v1 cement),
D-BE-5 (Pydantic frozen extra forbid).
"""

# voseo-allowed: docstring cita rubric IDs canónicos en spec v2

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class JudgeOpinion(BaseModel):
    """Single judge vote per (turn x rubric x round).

    Immutable post-creation (frozen=True). score=None when judge execution fails
    — excluded from variance computation and weighted average.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    judge_id: Literal["sonnet", "gpt4o", "kimi"]
    model_used: str  # e.g. "claude-sonnet-4-6", "gpt-4o-2024-11-20", "kimi-k2.6"
    weight: float = Field(ge=0.0, le=1.0)  # 0.4 / 0.4 / 0.2
    score: float | None = Field(default=None, ge=0.0, le=1.0)  # None when judge fail
    reasoning: str  # English (DQ4) — verbatim audit trail
    confidence: float = Field(ge=0.0, le=1.0)
    latency_ms: int = Field(ge=0)
    tokens_input: int = Field(ge=0)
    tokens_output: int = Field(ge=0)
    cost_usd: Decimal
    round_n: Literal[1, 2]
    cache_hit: bool  # prompt cache hit (Anthropic / OpenAI / Kimi caching)
    injection_attempt_detected: bool = False


class MajEvalScore(BaseModel):
    """MAJ-EVAL aggregated score per (simulation x turn x rubric).

    schema_version=1 is cement (Literal[1]). Future bumps via SCHEMA_MIGRATIONS registry.
    Frozen=True: instances are immutable post-grade persist (D-BE-5).
    judges list contains 3 entries (Round 1 only) or 6 entries (Round 1 + Round 2 debate).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1  # cement v1 — future bumps register migrator
    simulation_id: str  # FK Story B SimulationResult.simulation_id
    turn_n: int = Field(ge=1)
    rubric_id: Literal[
        "voice-fidelity",
        "qualification-accuracy",
        "no-overpromise",
        "no-hallucination",
    ]
    rubric_version: int = Field(ge=1)
    tenant_slug: str  # FK Story A 5 valid slugs
    persona_kind: Literal["happy", "nurture", "unqualified", "adversarial"]
    actor_profile_id: str  # FK Story C YAML id
    judges: list[JudgeOpinion]  # 3 (R1 only) or 6 (R1+R2)
    round_1_score: float = Field(ge=0.0, le=1.0)  # weighted avg R1 (excluding None scores)
    round_2_score: float | None = Field(default=None, ge=0.0, le=1.0)
    final_score: float = Field(ge=0.0, le=1.0)  # round_2_score if debate converged else round_1_score
    round_1_variance: float = Field(ge=0.0, le=1.0)
    round_2_variance: float | None = Field(default=None, ge=0.0, le=1.0)
    debate_triggered: bool = False
    unconverged: bool = False  # Round 2 variance >= 0.10 -> True
    r2_partial: bool = False  # Round 2 had >=1 judge fail; mixed R1/R2 scores per DQ6
    suspicious: bool = False  # all 3 judges score 1.0 + injection_attempt — DQ8 audit
    injection_attempt_detected: bool = False  # ANY judge flagged — propagated
    cost_usd_total: Decimal = Decimal(0)
    latency_ms_total: int = Field(ge=0)
    cache_hit_count: int = Field(ge=0, le=6)  # 0-6 (3 judges x 2 rounds max)
    created_at: datetime


class RubricGradeRequest(BaseModel):
    """Input to ``grade_transcript_maj_eval`` (Story E public API — H9 expand 7->8).

    Frozen=True: request is immutable once built (prevents accidental mutation mid-eval).
    transcript and tenant_voice_profile are typed as Any for forward-compatibility with
    Story D GoldenTurnModel and Story A PersonalityProfile (avoids circular imports in
    test-infrastructure layer).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    transcript: list[Any]  # Story D GoldenTurnModel list
    tenant_voice_profile: Any  # Story A PersonalityProfile
    rubrics: list[
        Literal[
            "voice-fidelity",
            "qualification-accuracy",
            "no-overpromise",
            "no-hallucination",
        ]
    ]
    judge_set: Literal["full_3"] = "full_3"  # forward-compat for future ensembles
    cache_policy: Literal["use", "bypass"] = "use"
    simulation_id: str
    tenant_slug: str
    persona_kind: Literal["happy", "nurture", "unqualified", "adversarial"]
    actor_profile_id: str
