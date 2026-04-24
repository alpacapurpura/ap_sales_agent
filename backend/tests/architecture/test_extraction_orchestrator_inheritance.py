"""Fitness gate: extraction orchestrators inherit from the shared base.

Any module that owns a wave-based LLM extraction pipeline MUST reuse the
shared scheduling + progress emission helpers from
``src.shared.application.extraction.base_orchestrator.BaseExtractionOrchestrator``.

Catches the previous pattern (brand/offer before Apr 2026) where
``_run_wave``, ``_pause_between_waves``, and ``_announce_sections`` were
copy-pasted per module and drifted over time.

Detection: any class whose name contains both ``Extraction`` and
``Orchestrator`` under ``src/modules/*/application/`` must declare the
shared base in its MRO (via ``ast`` parse of the bases list).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

MODULES_DIR = Path(__file__).resolve().parents[2] / "src" / "modules"

# Ratchet allowlist — classes permitted to skip the base class. Must
# shrink only. Justify any addition with a commit message reference.
KNOWN_ORCHESTRATORS_WITHOUT_BASE: set[str] = set()

_ORCHESTRATOR_NAME_RE = re.compile(r"Extraction.*Orchestrator|Orchestrator.*Extraction")
_ALLOWED_BASES = {
    "BaseExtractionOrchestrator",
    # Fully-qualified references are unlikely but supported.
    "base_orchestrator.BaseExtractionOrchestrator",
    "extraction.BaseExtractionOrchestrator",
}


def _collect_orchestrator_classes() -> list[tuple[str, ast.ClassDef]]:
    """Return (rel_path, class_node) for every extraction orchestrator class."""
    results: list[tuple[str, ast.ClassDef]] = []
    for py_file in sorted(MODULES_DIR.rglob("application/*.py")):
        rel = py_file.relative_to(MODULES_DIR.parent.parent)
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and _ORCHESTRATOR_NAME_RE.search(node.name):
                results.append((str(rel), node))
    return results


def test_every_extraction_orchestrator_inherits_base() -> None:
    """Any ``*Extraction*Orchestrator*`` class must declare the shared base."""
    violations: list[str] = []
    found_any = False

    for rel, cls in _collect_orchestrator_classes():
        found_any = True
        base_names = {ast.unparse(b) for b in cls.bases}
        if base_names & _ALLOWED_BASES:
            continue
        key = f"{rel}:{cls.name}"
        if key in KNOWN_ORCHESTRATORS_WITHOUT_BASE:
            continue
        violations.append(
            f"{rel}:{cls.name} — does not inherit from BaseExtractionOrchestrator. "
            "Subclass it from "
            "`src.shared.application.extraction.base_orchestrator` so wave "
            "scheduling + progress emission stays DRY across modules.",
        )

    assert found_any, (
        "No extraction orchestrator classes found — did the search glob change? "
        "Expected at least brand's ExtractionOrchestrator and "
        "offer's OfferExtractionOrchestrator."
    )
    assert not violations, "\n".join(violations)
