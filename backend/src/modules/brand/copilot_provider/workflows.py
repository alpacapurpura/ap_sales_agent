"""F6 — Brand pilot Workflow declarations.

Ships ``setup_brand_minimal`` as the canonical example of the unified
``Workflow`` model that subsumes ``guided`` + ``procedure`` +
``extraction_card_flow``. The pilot keeps full coexistencia with the legacy
guided engine: this workflow declares the *shape* (nodes + state schema +
handlers) but does NOT replace the live guided runner — F-pos cutover wires
the orchestrator to consume ``WorkflowEngine`` once all flows are migrated.

Handlers live in ``handlers.py`` next to the declaration so the brand module
owns its full surface (declaration + execution code) per the F1 deep-migration
pattern.

[COPILOT-WORKFLOW-F6]
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from src.modules.copilot.domain.workflow import (
    Workflow,
    WorkflowNode,
    WorkflowTrigger,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class BrandSetupState(BaseModel):
    """Persisted state for ``setup_brand_minimal`` runs.

    Mirrors the fields the legacy guided engine writes into
    ``procedure_state["guided"]`` but is now a typed Pydantic schema validated
    on every step.
    """

    model_config = ConfigDict(extra="forbid")

    tenant_id: str = ""
    pending_sections: list[str] = Field(default_factory=list)
    completed_sections: list[str] = Field(default_factory=list)
    next_question: str | None = None
    summary_after: str = ""


SETUP_BRAND_MINIMAL = Workflow(
    id="setup_brand_minimal",
    domain="brand",
    description_es=(
        "Configurar la marca paso a paso: revisa qué secciones faltan, "
        "pregunta una a una y deja el resumen actualizado."
    ),
    trigger=WorkflowTrigger.WIZARD_BUTTON,
    nodes=(
        WorkflowNode(
            id="probe_brand",
            handler_ref="src.modules.brand.copilot_provider.workflow_handlers:probe_brand",
            next="ask_next_section",
        ),
        WorkflowNode(
            id="ask_next_section",
            handler_ref="src.modules.brand.copilot_provider.workflow_handlers:ask_next_section",
            next="finalize_summary",
        ),
        WorkflowNode(
            id="finalize_summary",
            handler_ref="src.modules.brand.copilot_provider.workflow_handlers:finalize_summary",
        ),
    ),
    state_schema=BrandSetupState,
    ui_progress_kind="plan_card",
    max_clarify_questions=5,
)


class BrandWorkflowProvider:
    """``WorkflowProvider`` adapter for the brand module."""

    def workflows(self) -> Sequence[Workflow]:
        return (SETUP_BRAND_MINIMAL,)
