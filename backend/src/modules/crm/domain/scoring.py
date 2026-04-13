"""CRM Scoring Configuration.

Frozen dataclasses defining scoring weights, thresholds, decay, and inactivity.
Change requires deploy -- versioned in git by design.

Thresholds: SUBSCRIBER -> LEAD (>=10), LEAD -> MQL (>=40), MQL -> SQL (>=70).
Decay: 5% of current score per day of inactivity, floor at 0.
Inactivity: 14 days without any journey_event.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScoringWeights:
    """Event weights by category.

    Three dimensions:
    - Engagement: low-intent signals (opens, clicks, views)
    - Intent: high-intent signals (forms, checkout, meetings)
    - Fit: profile-based one-time adjustments (financial capacity, sophistication, business stage)
    """

    engagement: dict[str, float] = field(
        default_factory=lambda: {
            "page_view": 1.0,
            "email_opened": 2.0,
            "email_clicked": 3.0,
            "social_interaction": 1.5,
            "content_downloaded": 3.0,
        },
    )

    intent: dict[str, float] = field(
        default_factory=lambda: {
            "form_submitted": 5.0,
            "checkout_started": 8.0,
            "meeting_requested": 10.0,
            "pricing_viewed": 4.0,
            "demo_requested": 10.0,
            "message_sent": 4.0,
            "contact_extracted": 5.0,
        },
    )

    fit: dict[str, float] = field(
        default_factory=lambda: {
            "financial_capacity_high": 8.0,
            "financial_capacity_medium": 5.0,
            "sophistication_product_aware": 6.0,
            "sophistication_most_aware": 8.0,
            "business_stage_active": 10.0,
            "business_stage_idea": 5.0,
        },
    )


@dataclass(frozen=True)
class ScoringThresholds:
    """Stage transition thresholds. Score >= threshold triggers transition."""

    lead: float = 10.0  # SUBSCRIBER -> LEAD
    mql: float = 40.0  # LEAD -> MQL
    sql: float = 70.0  # MQL -> SQL


@dataclass(frozen=True)
class DecayConfig:
    """Score decay settings."""

    daily_decay_rate: float = 0.05  # 5% per day of inactivity
    min_score: float = 0.0  # Floor -- score never goes negative


@dataclass(frozen=True)
class InactivityConfig:
    """Inactivity detection settings."""

    inactive_days: int = 14  # Days without any journey_event


# Module-level singletons -- import these in application code
SCORING_WEIGHTS = ScoringWeights()
SCORING_THRESHOLDS = ScoringThresholds()
DECAY_CONFIG = DecayConfig()
INACTIVITY_CONFIG = InactivityConfig()
