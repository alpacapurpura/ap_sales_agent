"""Typed payload schemas per ``CardBlock.card_kind``.

Why this exists: ``CardBlock.payload`` is ``dict`` by design — it carries
whatever shape the emitter (LLM + tool) produced. That openness is good for
forward compatibility but bad for discovering bugs at the boundary. This
registry pairs every ``card_kind`` literal with a Pydantic model describing
its expected shape, and offers a **warn-only** validator the orchestrator
calls before dispatch.

Validator semantics: it NEVER rejects a card. If the payload doesn't match,
the validator logs a structured warning (caller surfaces it) and the card
is still emitted so the frontend can decide how to degrade. This is
intentional — the LLM produces these payloads and we prefer a noisy log
over a user-facing dead turn.

Arch test ``test_card_payload_schemas.py`` enforces that every ``card_kind``
declared on ``CardBlock`` has a model entry here. That's the compile-time
safety net.

Adding a new card_kind requires:
1. Append literal to ``CardBlock.card_kind`` in ``message_blocks.py``.
2. Add model class + mapping entry here.
3. Mirror TypeScript types in frontend ``types/message-blocks.ts``.
4. Architecture test will fail on step (1) without (2) — ratchet.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

# ── Shared helpers ───────────────────────────────────────────────────────────


class _PayloadBase(BaseModel):
    """Common envelope for card payloads.

    Extra fields are allowed so minor LLM drift doesn't block the card. Arch
    tests + per-kind required fields catch the real regressions.
    """

    model_config = ConfigDict(extra="allow")


# ── clarify ──────────────────────────────────────────────────────────────────


class ClarifyItem(_PayloadBase):
    """One contradiction/ambiguity the user must resolve."""

    field_path: str
    issue: str
    options: list[str]


class ClarifyCardPayload(_PayloadBase):
    """Payload for card_kind="clarify" — quick-reply disambiguation card.

    Frontend renderer: ``features/copilot/components/cards/ClarifyCard.tsx``.
    The FE reads ``clarify_items`` (NOT ``items``); renaming breaks rendering.
    Max items enforced at tool level (``MAX_CLARIFY_ITEMS = 4``).
    """

    type: str = "clarify_card"
    clarify_items: list[ClarifyItem]


# ── alternatives ────────────────────────────────────────────────────────────


class AlternativeOption(_PayloadBase):
    """One option inside an AlternativesCard."""

    id: str
    title: str
    description: str | None = None
    recommended: bool = False
    recommendation_reason: str | None = None


class AlternativesCardPayload(_PayloadBase):
    """Payload for card_kind="alternatives".

    N-way choice card with an optional recommendation flag. Emitted by the
    ``offer_alternatives`` tool.
    """

    type: str = "alternatives_card"
    field_path: str
    question: str
    alternatives: list[AlternativeOption]
    allow_custom: bool = False


# ── proposal (propose_field_updates) ────────────────────────────────────────


class ProposalUpdate(_PayloadBase):
    """One field-level change proposed inside a ProposalCard."""

    field_id: str
    new_value: Any
    reason: str | None = None
    domain: str | None = None


class ProposalCardPayload(_PayloadBase):
    """Payload for card_kind="proposal" — batch field updates awaiting approval."""

    type: str = "proposal"
    updates: list[ProposalUpdate]


# ── checkpoint ──────────────────────────────────────────────────────────────


class CheckpointCardPayload(_PayloadBase):
    """Payload for card_kind="checkpoint" — interview block review point."""

    type: str = "checkpoint_card"
    block_id: str
    block_label: str
    summary: dict[str, Any]


# ── interview_complete ──────────────────────────────────────────────────────


class InterviewCompleteCardPayload(_PayloadBase):
    """Payload for card_kind="interview_complete" — post-interview summary."""

    type: str = "interview_complete_card"
    # Remaining fields are template-specific. `extra="allow"` lets them through.


# ── metric_summary ──────────────────────────────────────────────────────────


class MetricSummaryCardPayload(_PayloadBase):
    """Payload for card_kind="metric_summary" — compact KPI card.

    Shape is driven by analytics DTOs which evolve faster than this schema;
    validation is loose (extra allowed) until those stabilize.
    """

    type: str = "metric_summary_card"


# ── comparison ──────────────────────────────────────────────────────────────


class ComparisonCardPayload(_PayloadBase):
    """Payload for card_kind="comparison" — side-by-side comparison card."""

    type: str = "comparison_card"


# ── checklist ───────────────────────────────────────────────────────────────


class ChecklistCardPayload(_PayloadBase):
    """Payload for card_kind="checklist" — progress checklist."""

    type: str = "checklist_card"


# ── multi_option ────────────────────────────────────────────────────────────


class MultiOptionCardPayload(_PayloadBase):
    """Payload for card_kind="multi_option" — generic option picker."""

    type: str = "multi_option_card"


# ── navigation ──────────────────────────────────────────────────────────────


class NavigationCardPayload(_PayloadBase):
    """Payload for card_kind="navigation" — link/button navigation card."""

    type: str = "navigation_card"


# ── extraction_summary ──────────────────────────────────────────────────────


class ExtractionSummarySectionCoverage(_PayloadBase):
    """Coverage breakdown for one section inside an extraction summary card."""

    slug: str
    label: str
    filled: int
    total: int


class ExtractionSummaryCardPayload(_PayloadBase):
    """Payload for card_kind="extraction_summary" — end-of-extraction closure card.

    Emitted by ``run_brand_extraction`` / ``run_offer_extraction`` workers at
    job completion. Closes the loop on the "te aviso cuando termine" promise.

    Frontend renderer: ``features/copilot/components/cards/ExtractionSummaryCard.tsx``.
    Shape matches FLOW-SPEC §3.4 / UI-SPEC Proposal 3.
    """

    type: str = "extraction_summary"
    source_ref: str  # URL or asset_id that was analyzed
    duration_seconds: int | None = None  # wall-clock seconds for the job
    total_fields: int = 0  # total fields populated
    total_sections: int = 0  # number of sections touched
    coverage_by_section: list[ExtractionSummarySectionCoverage] = []
    strong_assumptions_count: int = 0  # fields filled with low confidence
    open_questions_count: int = 0  # fields still empty / requiring user input
    primary_cta_route: str | None = None  # deeplink e.g. "/brand-studio/identity"


class InspirationSavedCardPayload(_PayloadBase):
    """Payload for card_kind="inspiration_saved" — F4 URL inspiration capture.

    Emitted by ``fetch_url`` after persisting a row in
    ``copilot_inspiration``. Frontend renderer is the swipe-card preview
    (TBD per F4 §7) showing the OG image + summary + relevance badge.
    """

    type: str = "inspiration_saved"
    slug: str
    url: str
    domain: str
    summary: str
    brand_relevance_score: float
    og_image: str | None = None
    scratchpad_path: str | None = None


class MemoryPinnedCardPayload(_PayloadBase):
    """Payload for card_kind="memory_pinned" — F4 ``pin_to_memory`` confirmation."""

    type: str = "memory_pinned"
    slug: str
    path: str


class PlanCardTodo(BaseModel):
    """Single todo entry inside a ``plan_card`` payload (B18-TP9)."""

    model_config = ConfigDict(extra="allow")
    content: str
    status: str  # "pending" | "in_progress" | "completed"
    active_form: str = ""


class PlanCardPayload(_PayloadBase):
    """Payload for card_kind="plan_card" — F2 deep-agent ``write_todos`` synthesis (B18-TP9).

    The deep-agent harness emits a ``write_todos`` tool call to expose its
    multi-step plan. ``_write_todos_to_plan_card`` transforms the tool args
    into this shape so the FE renders a checklist with status transitions
    (pending → in_progress → completed). No user approval — the card is
    informational and progresses as the agent advances.
    """

    type: str = "plan_card"
    todos: list[PlanCardTodo]


# ── Registry ────────────────────────────────────────────────────────────────


CARD_PAYLOAD_MODELS: dict[str, type[_PayloadBase]] = {
    "clarify": ClarifyCardPayload,
    "alternatives": AlternativesCardPayload,
    "proposal": ProposalCardPayload,
    "checkpoint": CheckpointCardPayload,
    "interview_complete": InterviewCompleteCardPayload,
    "metric_summary": MetricSummaryCardPayload,
    "comparison": ComparisonCardPayload,
    "checklist": ChecklistCardPayload,
    "multi_option": MultiOptionCardPayload,
    "navigation": NavigationCardPayload,
    "extraction_summary": ExtractionSummaryCardPayload,
    "inspiration_saved": InspirationSavedCardPayload,
    "memory_pinned": MemoryPinnedCardPayload,
    "plan_card": PlanCardPayload,
}
"""Map ``CardBlock.card_kind`` → payload Pydantic model.

Arch test ``test_card_payload_schemas.py::test_every_card_kind_is_registered``
guarantees this dict is kept in sync with the ``CardBlock`` discriminator.
"""


def validate_card_payload(
    card_kind: str,
    payload: dict[str, Any],
) -> tuple[bool, str | None]:
    """Best-effort validate a card payload against its registered model.

    Returns ``(True, None)`` on success, ``(False, error_message)`` on
    failure. The caller is expected to **log** the error and still emit the
    card — we never reject at this layer because LLM output quality
    fluctuates and a noisy warning beats a silent dead card.

    An unknown ``card_kind`` also returns ``False`` so the caller knows to
    check the registry.
    """
    model = CARD_PAYLOAD_MODELS.get(card_kind)
    if model is None:
        return False, f"unknown card_kind: {card_kind!r}"
    try:
        model.model_validate(payload)
    except ValidationError as e:
        return False, str(e)
    return True, None


__all__ = [
    "CARD_PAYLOAD_MODELS",
    "AlternativeOption",
    "AlternativesCardPayload",
    "ChecklistCardPayload",
    "CheckpointCardPayload",
    "ClarifyCardPayload",
    "ClarifyItem",
    "ComparisonCardPayload",
    "ExtractionSummaryCardPayload",
    "ExtractionSummarySectionCoverage",
    "InterviewCompleteCardPayload",
    "MetricSummaryCardPayload",
    "MultiOptionCardPayload",
    "NavigationCardPayload",
    "PlanCardPayload",
    "PlanCardTodo",
    "ProposalCardPayload",
    "ProposalUpdate",
    "validate_card_payload",
]
