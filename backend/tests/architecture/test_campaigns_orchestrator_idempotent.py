"""Architectural fitness — CampaignOrchestrator.launch decorated with @idempotent.

AST scan:
  Walks src/modules/campaigns/application/services/orchestrator.py.
  Finds AsyncFunctionDef name='launch' inside ClassDef name='CampaignOrchestrator'.
  Asserts the function has at least one decorator whose name resolves to
  'idempotent' (Call.func.id == 'idempotent').

Ratchet: shrink-only EXEMPT_METHODS (initially empty). New public orchestrator
method that mutates state requires @idempotent OR allowlist entry with
justification comment.

# [CAMPAIGNS-ORCHESTRATOR-IDEMPOTENT-PR5-S2]
"""

from __future__ import annotations

import ast
import pathlib

_ORCHESTRATOR_PATH = pathlib.Path("src/modules/campaigns/application/services/orchestrator.py")

# Shrink-only allowlist.
# Add entry ONLY with justification comment explaining why @idempotent is not needed.
EXEMPT_METHODS: frozenset[str] = frozenset({})


def _get_decorator_names(func_node: ast.AsyncFunctionDef | ast.FunctionDef) -> list[str]:
    """Extract decorator names from a function definition node."""
    names: list[str] = []
    for deco in func_node.decorator_list:
        if isinstance(deco, ast.Name):
            names.append(deco.id)
        elif isinstance(deco, ast.Call):
            if isinstance(deco.func, ast.Name):
                names.append(deco.func.id)
            elif isinstance(deco.func, ast.Attribute):
                names.append(deco.func.attr)
        elif isinstance(deco, ast.Attribute):
            names.append(deco.attr)
    return names


class TestCampaignOrchestratorIdempotent:
    """CampaignOrchestrator.launch() must be decorated with @idempotent."""

    def test_orchestrator_file_exists(self) -> None:
        """orchestrator.py exists at expected path."""
        assert _ORCHESTRATOR_PATH.exists(), (
            f"CampaignOrchestrator not found at {_ORCHESTRATOR_PATH}. PR-5 must ship orchestrator.py."
        )

    def test_launch_has_idempotent_decorator(self) -> None:
        """CampaignOrchestrator.launch is decorated with @idempotent.

        The decorator ensures that re-launch within LAUNCH_IDEMPOTENCY_TTL_SECONDS
        (600s) returns a cached result without running the full orchestration again.
        This is critical for preventing double-launches from UI double-clicks or
        ARQ retry storms.
        """
        source = _ORCHESTRATOR_PATH.read_text()
        tree = ast.parse(source)

        orchestrator_class: ast.ClassDef | None = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "CampaignOrchestrator":
                orchestrator_class = node
                break

        assert orchestrator_class is not None, (
            "ClassDef 'CampaignOrchestrator' not found in orchestrator.py. The orchestrator class must exist."
        )

        launch_fn: ast.AsyncFunctionDef | None = None
        for node in ast.walk(orchestrator_class):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "launch":
                launch_fn = node
                break

        assert launch_fn is not None, (
            "async def launch() not found in CampaignOrchestrator. The launch method must be async."
        )

        decorator_names = _get_decorator_names(launch_fn)
        assert "idempotent" in decorator_names, (
            f"CampaignOrchestrator.launch() must be decorated with @idempotent. "
            f"Found decorators: {decorator_names}. "
            "The @idempotent decorator (from src.shared.idempotency) prevents "
            "double-launch within LAUNCH_IDEMPOTENCY_TTL_SECONDS=600 window."
        )

    def test_exempt_methods_ratchet(self) -> None:
        """EXEMPT_METHODS allowlist is empty (ratchet: shrink-only)."""
        assert frozenset() == EXEMPT_METHODS, (
            f"EXEMPT_METHODS is not empty: {EXEMPT_METHODS}. "
            "New entries require justification comment explaining why @idempotent "
            "is not needed for that method."
        )

    def test_idempotent_import_in_orchestrator(self) -> None:
        """orchestrator.py imports @idempotent from shared/idempotency."""
        source = _ORCHESTRATOR_PATH.read_text()
        assert "idempotent" in source, (
            "orchestrator.py must import the @idempotent decorator. "
            "Expected import from src.shared.idempotency.application.decorator."
        )

    def test_launch_idempotency_ttl_defined(self) -> None:
        """CampaignOrchestrator defines LAUNCH_IDEMPOTENCY_TTL_SECONDS constant."""
        source = _ORCHESTRATOR_PATH.read_text()
        assert "LAUNCH_IDEMPOTENCY_TTL_SECONDS" in source, (
            "CampaignOrchestrator must define LAUNCH_IDEMPOTENCY_TTL_SECONDS constant "
            "(expected value: 600). This documents the idempotency window and is "
            "referenced by the @idempotent decorator configuration."
        )
