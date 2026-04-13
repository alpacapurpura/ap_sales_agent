"""Procedure Engine — schema-driven multi-step workflows for the copilot.

Procedures are declared with steps that reference MODULE_REGISTRY modules.
Completion is checked dynamically via schema_introspection — no hardcoded fields.
"""

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.orm import Session

from src.core.database import SessionLocal
from src.modules.copilot.domain.module_registry import ModuleDescriptor, get_module_registry
from src.modules.copilot.domain.schema_introspection import (
    check_section_completion,
    get_model_sections,
)


@dataclass
class ProcedureStep:
    """Handle procedure step logic."""

    step_id: str
    module_id: str  # "brand", "offer" → lookup in MODULE_REGISTRY
    section_id: str | None  # Section in the Pydantic model (auto-discovered)
    instruction: str  # What to tell the user
    validation: str  # "has_any_data" | "has_required_fields" | "custom"
    tips: list[str] = field(default_factory=list)
    route_hint: str | None = None  # Suggested navigation route


@dataclass
class Procedure:
    """Handle procedure logic."""

    procedure_id: str
    name: str
    description: str
    steps: list[ProcedureStep]

    def get_current_step_index(self, tenant_id: UUID) -> int:
        """Find the first incomplete step. Uses MODULE_REGISTRY + schema_introspection."""
        db = SessionLocal()
        try:
            registry = get_module_registry()
            for i, step in enumerate(self.steps):
                if not self._is_step_complete(step, tenant_id, db, registry):
                    return i
            return len(self.steps)  # All complete
        finally:
            db.close()

    def get_completion_summary(self, tenant_id: UUID) -> dict[str, bool]:
        """Return {step_id: bool} indicating completion of each step."""
        db = SessionLocal()
        try:
            registry = get_module_registry()
            return {step.step_id: self._is_step_complete(step, tenant_id, db, registry) for step in self.steps}
        finally:
            db.close()

    @staticmethod
    def _is_step_complete(
        step: ProcedureStep,
        tenant_id: UUID,
        db: Session,
        registry: dict[str, ModuleDescriptor],
    ) -> bool:
        descriptor = registry.get(step.module_id)
        if not descriptor or not descriptor.repo_factory:
            return False

        try:
            repo = descriptor.repo_factory(db)
            data = descriptor.read_fn(repo, tenant_id)
        except Exception:  # noqa: BLE001 — copilot resilience
            return False

        if not data:
            return False

        # "has_any_data" — data exists and passed `not data` check, so it's complete
        if step.validation == "has_any_data":
            return True

        # For modules with model_class, verify specific section
        if step.section_id and descriptor.model_class:
            raw = data.model_dump(mode="json") if hasattr(data, "model_dump") else {}
            sections = get_model_sections(descriptor.model_class)
            completion = check_section_completion(raw, sections)
            section_status = completion.get(step.section_id)
            return section_status.is_configured if section_status else False

        return True
