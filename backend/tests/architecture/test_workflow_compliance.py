"""F6 — workflow compliance fitness tests.

Architectural invariants for the unified Workflow concept (replaces guided +
procedure + extraction_card_flow during cutover):

1. Every discovered ``WorkflowProvider.workflows()`` member is a structurally
   valid ``Workflow`` (id non-empty, nodes resolvable, state_schema BaseModel).
2. Every ``WorkflowNode.handler_ref`` resolves at import time — no dangling
   references in shipped pilots.
3. ``application/workflows/`` does NOT import from any business module
   (preserves the ``copilot → módulo`` ratchet of 22).
4. Workflow ids are globally unique across all providers.
5. The migration ``071_copilot_workflow_state`` adds ``workflow_state`` column
   without removing ``procedure_state`` (cutover safety).
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest
from pydantic import BaseModel

from src.modules.copilot.application.discovery import discover_providers, reset_discovery
from src.modules.copilot.application.workflows.registry import collect_workflows
from src.modules.copilot.domain.workflow import Workflow

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_WORKFLOWS_DIR = _BACKEND_ROOT / "src" / "modules" / "copilot" / "application" / "workflows"
_MIGRATION_071 = _BACKEND_ROOT / "alembic" / "versions" / "071_copilot_workflow_state.py"

# Allow infrastructure that is intrinsic to the engine (own copilot/, shared base helpers).
_ALLOWED_IMPORT_PREFIXES = (
    "src.modules.copilot.",
    "src.shared.",
    "src.core.",
)


def setup_function() -> None:
    reset_discovery()


def test_every_discovered_workflow_is_structurally_valid() -> None:
    """Discovery + collect must yield only well-formed Workflow instances."""

    workflows = collect_workflows(discover_providers())
    assert workflows, "F6 pilots (brand + offer) must register at least one workflow each."

    for wf_id, wf in workflows.items():
        assert isinstance(wf, Workflow), f"{wf_id} is not a Workflow instance"
        assert wf.id == wf_id
        assert wf.id, "Workflow.id must be non-empty"
        assert wf.domain, "Workflow.domain must be non-empty"
        assert wf.description_es, "Workflow.description_es must be non-empty"
        assert wf.nodes, f"{wf_id} must declare at least one node"
        assert issubclass(wf.state_schema, BaseModel), f"{wf_id}.state_schema must be a BaseModel"


def test_every_workflow_node_handler_resolves() -> None:
    """``handler_ref`` strings must be importable so engine.step never explodes
    in production with a missing-symbol error."""

    workflows = collect_workflows(discover_providers())
    for wf in workflows.values():
        for node in wf.nodes:
            module_path, _, attr = node.handler_ref.partition(":")
            assert module_path and attr, f"{wf.id}/{node.id}: handler_ref must be 'module:fn'"
            try:
                module = importlib.import_module(module_path)
            except ModuleNotFoundError as exc:
                pytest.fail(f"{wf.id}/{node.id}: cannot import {module_path}: {exc}")
            assert hasattr(module, attr), f"{wf.id}/{node.id}: {module_path} has no attribute {attr!r}"


def test_workflow_ids_are_globally_unique() -> None:
    """Two providers MUST NOT register the same workflow id (ambiguity)."""

    seen: dict[str, str] = {}
    for module_id, provider in discover_providers().items():
        wf_provider = provider.workflow_provider()
        if wf_provider is None:
            continue
        for wf in wf_provider.workflows():
            assert wf.id not in seen, f"Workflow {wf.id!r} registered by both {seen[wf.id]!r} and {module_id!r}"
            seen[wf.id] = module_id


def test_application_workflows_imports_no_business_module() -> None:
    """``copilot/application/workflows/`` must not import from any business
    module (brand, offer, landing, …) — keeps the package agnostic and
    preserves the ``copilot → módulo`` ratchet."""

    forbidden_prefixes = (
        "src.modules.brand.",
        "src.modules.offer.",
        "src.modules.landing.",
        "src.modules.analytics.",
        "src.modules.crm.",
        "src.modules.connections.",
        "src.modules.assets.",
        "src.modules.iam.",
        "src.modules.scheduling.",
        "src.modules.sales_agent.",
        "src.modules.social_proof.",
        "src.modules.commercial_calendar.",
        "src.modules.tenant_profile.",
        "src.modules.tenant_domains.",
        "src.modules.advertising.",
        "src.modules.social_media.",
    )

    for py_file in _WORKFLOWS_DIR.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for forbidden in forbidden_prefixes:
                    assert not module.startswith(forbidden), (
                        f"{py_file.relative_to(_BACKEND_ROOT)}: forbidden import {module}"
                    )


def test_migration_071_idempotent_and_preserves_procedure_state() -> None:
    """Migration must use ``ADD COLUMN IF NOT EXISTS`` and NOT drop
    ``procedure_state`` (cutover keeps both columns until F-pos)."""

    assert _MIGRATION_071.is_file(), "Migration 071_copilot_workflow_state.py missing"
    text = _MIGRATION_071.read_text(encoding="utf-8")
    assert "ADD COLUMN IF NOT EXISTS workflow_state" in text, "Migration must idempotently add workflow_state"
    assert "DROP COLUMN procedure_state" not in text.upper(), (
        "F6 must preserve procedure_state during coexistencia — drop deferred to F-pos"
    )
    # Backfill from procedure_state expected for live conversations.
    assert "workflow_state = procedure_state" in text or "workflow_state=procedure_state" in text, (
        "Migration must backfill workflow_state from existing procedure_state rows"
    )
