"""F6 — Offer pilot Workflow declarations.

Ships ``design_offer_from_url`` as the offer-side example of the unified
``Workflow`` model. Same coexistencia rule as brand: legacy
``extraction_card_flow`` keeps running live; this declaration is the future
home of the URL-driven offer-design flow once F-pos wires the orchestrator
through ``WorkflowEngine``.

[COPILOT-WORKFLOW-F6]
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from luana_core_copilot.domain.workflow import (
    Workflow,
    WorkflowNode,
    WorkflowTrigger,
)
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from collections.abc import Sequence


class OfferDesignFromUrlState(BaseModel):
    """Persisted state for ``design_offer_from_url`` runs."""

    model_config = ConfigDict(extra="forbid")

    source_url: str = ""
    extracted_summary: str = ""
    pending_questions: list[str] = Field(default_factory=list)
    answers: dict[str, str] = Field(default_factory=dict)
    proposed_offer: dict[str, object] = Field(default_factory=dict)


DESIGN_OFFER_FROM_URL = Workflow(
    id="design_offer_from_url",
    domain="offer",
    description_es=(
        "Diseñar oferta a partir de una URL: analiza la fuente, pregunta lo que falta y propone la oferta final."
    ),
    trigger=WorkflowTrigger.URL_PASTED,
    nodes=(
        WorkflowNode(
            id="extract_url",
            handler_ref="luana_core_offer_studio.copilot_provider.workflow_handlers:extract_url",
            next="ask_clarifications",
        ),
        WorkflowNode(
            id="ask_clarifications",
            handler_ref="luana_core_offer_studio.copilot_provider.workflow_handlers:ask_clarifications",
            next="propose_offer",
        ),
        WorkflowNode(
            id="propose_offer",
            handler_ref="luana_core_offer_studio.copilot_provider.workflow_handlers:propose_offer",
        ),
    ),
    state_schema=OfferDesignFromUrlState,
    ui_progress_kind="plan_card",
    max_clarify_questions=5,
)


class OfferWorkflowProvider:
    """``WorkflowProvider`` adapter for the offer module."""

    def workflows(self) -> Sequence[Workflow]:
        return (DESIGN_OFFER_FROM_URL,)
