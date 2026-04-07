"""
Centralized tunable parameters for the sales agent.

Adjust these values to tune agent behavior without modifying business logic.
"""

# ─── Scoring ──────────────────────────────────────────────────────────────────
BUYING_SIGNAL_WEIGHT = 15  # Points per buying signal
QUALIFICATION_FIELD_WEIGHT = 10  # Points per qualification field
LEAD_SCORE_MAX = 100  # Maximum lead score
LEAD_SCORE_CLOSE_THRESHOLD = 30  # Min score to allow routing to closer
BUYING_SIGNALS_CLOSE_THRESHOLD = 2  # Min signals to allow routing to closer
QUALIFICATION_FIELDS_TARGET = 5  # Fields needed for "fully qualified"

# ─── Stage Transitions ────────────────────────────────────────────────────────
STAGE_CLOSING_SCORE = 70  # Min score for auto-transition to closing
STAGE_CLOSING_SIGNALS = 3  # Min signals for auto-transition to closing
STAGE_PRESENTATION_QA = 3  # Min qualification answers for presentation
STAGE_DISCOVERY_QA = 1  # Min qualification answers for discovery

# ─── Graph Control ────────────────────────────────────────────────────────────
MAX_INTERNAL_TURNS = 3  # Max loops within single user message
MAX_TOTAL_TURNS = 20  # Before forced escalation
SUPERVISOR_MESSAGE_WINDOW = 6  # Messages passed to supervisor for routing

# ─── Semantic Router ──────────────────────────────────────────────────────────
SEMANTIC_CONFIDENCE_THRESHOLD = 0.65  # Default threshold for intent detection
SOFT_SIGNAL_THRESHOLD = 0.50  # Threshold for accumulating soft signals

# ─── Output ───────────────────────────────────────────────────────────────────
CPM_SPEED = 320  # Characters per minute typing speed
TYPING_JITTER = (0.8, 1.2)  # Variability factor range
MIN_TYPING_TIME = 1.5  # Seconds minimum typing indicator
MAX_TYPING_TIME = 6.0  # Seconds maximum typing indicator
MICRO_DELAY_RANGE = (0.4, 0.8)  # Seconds between chunks

# ─── Session ──────────────────────────────────────────────────────────────────
SESSION_TIMEOUT_HOURS = 6  # Hours before session is considered expired
MESSAGE_HISTORY_LIMIT = 10  # Max messages loaded from audit history

# ─── Question Fatigue (Fase 3) ───────────────────────────────────────────────
CONSECUTIVE_QUESTION_FATIGUE_LIMIT = (
    3  # Max consecutive qualifier turns before forcing value
)

# ─── Follow-up Cadences (Fase 4) ─────────────────────────────────────────────
FOLLOW_UP_CADENCES = {
    "low": {"delays_hours": [2, 24, 48]},
    "mid": {"delays_hours": [6, 24, 72]},
    "high": {"delays_hours": [4, 24]},
}
FOLLOW_UP_MAX_TOTAL = 3  # Hard cap: never more than 3 follow-ups per lead
