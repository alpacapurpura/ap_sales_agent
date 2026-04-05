"""
Procedure Tools — start, check status, and advance guided procedures.

Returns markdown for the LLM + ui_action for the frontend stepper.
"""

import json

import structlog
from langchain_core.tools import tool

from src.core.context import get_tenant_id
from src.modules.copilot.application.procedures.base import Procedure
from src.modules.copilot.application.procedures.brand_setup import BRAND_SETUP
from src.modules.copilot.application.procedures.first_setup import FIRST_SETUP
from src.modules.copilot.application.procedures.offer_creation import OFFER_CREATION

logger = structlog.get_logger()

PROCEDURE_REGISTRY: dict[str, Procedure] = {
    "brand_setup": BRAND_SETUP,
    "offer_creation": OFFER_CREATION,
    "first_setup": FIRST_SETUP,
}


def _build_ui_action(
    procedure: Procedure, summary: dict[str, bool], current_idx: int
) -> dict:
    """Build a procedure_progress ui_action payload."""
    steps = []
    for i, step in enumerate(procedure.steps):
        completed = summary.get(step.step_id, False)
        if completed:
            status = "completed"
        elif i == current_idx:
            status = "current"
        else:
            status = "pending"
        steps.append(
            {
                "id": step.step_id,
                "label": step.instruction.split(":")[0].split("—")[0].strip()[:30],
                "status": status,
                "routeHint": step.route_hint,
            }
        )

    return {
        "type": "procedure_progress",
        "procedure_id": procedure.procedure_id,
        "procedure_name": procedure.name,
        "steps": steps,
        "current_step_index": current_idx,
    }


@tool
def start_procedure(procedure_id: str) -> str:
    """Inicia un procedimiento guiado. Opciones: "brand_setup", "offer_creation", "first_setup"."""
    procedure = PROCEDURE_REGISTRY.get(procedure_id)
    if not procedure:
        available = ", ".join(PROCEDURE_REGISTRY.keys())
        return f"Procedimiento '{procedure_id}' no encontrado. Opciones: {available}"

    tenant_id = get_tenant_id()
    if not tenant_id:
        return "Error: No se pudo obtener el tenant_id."

    current_idx = procedure.get_current_step_index(tenant_id)
    summary = procedure.get_completion_summary(tenant_id)
    total = len(procedure.steps)

    # All complete
    if current_idx >= total:
        ui_action = _build_ui_action(procedure, summary, total)
        result = {
            "text": f"## {procedure.name}\n\n¡Todos los pasos están completados! 🎉",
            "ui_action": ui_action,
        }
        return json.dumps(result)

    step = procedure.steps[current_idx]
    completed_count = sum(1 for v in summary.values() if v)

    tips_text = ""
    if step.tips:
        tips_text = "\n**Tips:**\n" + "\n".join(f"- {t}" for t in step.tips)

    ui_action = _build_ui_action(procedure, summary, current_idx)

    text = (
        f"## {procedure.name} ({completed_count}/{total} completados)\n\n"
        f"**Paso {current_idx + 1}/{total}:** {step.instruction}"
        f"{tips_text}\n\n"
        f"Cuando termines este paso, dime y avanzaré al siguiente."
    )

    result = {"text": text, "ui_action": ui_action}
    return json.dumps(result)


@tool
def get_procedure_status(procedure_id: str) -> str:
    """Consulta el progreso de un procedimiento."""
    procedure = PROCEDURE_REGISTRY.get(procedure_id)
    if not procedure:
        available = ", ".join(PROCEDURE_REGISTRY.keys())
        return f"Procedimiento '{procedure_id}' no encontrado. Opciones: {available}"

    tenant_id = get_tenant_id()
    if not tenant_id:
        return "Error: No se pudo obtener el tenant_id."

    summary = procedure.get_completion_summary(tenant_id)
    current_idx = procedure.get_current_step_index(tenant_id)
    total = len(procedure.steps)
    completed_count = sum(1 for v in summary.values() if v)

    lines = [f"## {procedure.name} — Progreso: {completed_count}/{total}"]
    for i, step in enumerate(procedure.steps):
        done = summary.get(step.step_id, False)
        if done:
            icon = "✅"
        elif i == current_idx:
            icon = "👉"
        else:
            icon = "⬜"
        lines.append(f"{icon} **{step.step_id}**: {step.instruction}")

    ui_action = _build_ui_action(procedure, summary, current_idx)
    result = {"text": "\n".join(lines), "ui_action": ui_action}
    return json.dumps(result)


@tool
def advance_procedure(procedure_id: str) -> str:
    """Revisa si el paso actual está completo y avanza al siguiente."""
    procedure = PROCEDURE_REGISTRY.get(procedure_id)
    if not procedure:
        available = ", ".join(PROCEDURE_REGISTRY.keys())
        return f"Procedimiento '{procedure_id}' no encontrado. Opciones: {available}"

    tenant_id = get_tenant_id()
    if not tenant_id:
        return "Error: No se pudo obtener el tenant_id."

    current_idx = procedure.get_current_step_index(tenant_id)
    summary = procedure.get_completion_summary(tenant_id)
    total = len(procedure.steps)

    # All complete
    if current_idx >= total:
        ui_action = _build_ui_action(procedure, summary, total)
        result = {
            "text": f"## {procedure.name}\n\n¡Procedimiento completado! 🎉 Todos los pasos están listos.",
            "ui_action": ui_action,
        }
        return json.dumps(result)

    step = procedure.steps[current_idx]
    completed_count = sum(1 for v in summary.values() if v)

    tips_text = ""
    if step.tips:
        tips_text = "\n**Tips:**\n" + "\n".join(f"- {t}" for t in step.tips)

    ui_action = _build_ui_action(procedure, summary, current_idx)

    text = (
        f"## {procedure.name} ({completed_count}/{total} completados)\n\n"
        f"**Paso actual ({current_idx + 1}/{total}):** {step.instruction}"
        f"{tips_text}\n\n"
        f"Completa este paso y dime cuando estés listo para continuar."
    )

    result = {"text": text, "ui_action": ui_action}
    return json.dumps(result)


PROCEDURE_TOOLS = [start_procedure, get_procedure_status, advance_procedure]
