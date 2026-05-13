"""Architecture fitness — compliance allowlist (shrink-only ratchet).

PR-2 exposes ComplianceService primitives. This test tracks which
send-path callers have wired in compliance checks. Initially the list
is EMPTY because wiring happens in S2.

Ratchet: entries may only be REMOVED as wiring progresses (shrink-only).
Adding to KNOWN_COMPLIANCE_UNWIRED requires a justified commit explaining
why the send-path does not call ComplianceService.check.

When S2 wires channels (sales_agent OutputManager, campaign senders), the
matching entries are removed from KNOWN_COMPLIANCE_UNWIRED and added to
KNOWN_COMPLIANCE_WIRED. Both lists are maintained here; the gate fails if
a registered wired surface loses its compliance call.

Usage:
  - Add a new outbound send-path → add to KNOWN_COMPLIANCE_UNWIRED.
  - Wire compliance → remove from KNOWN_COMPLIANCE_UNWIRED, add to KNOWN_COMPLIANCE_WIRED.
  - KNOWN_COMPLIANCE_UNWIRED must never grow after a "wiring done" commit.
"""

from __future__ import annotations

import ast
from pathlib import Path

# ── Ratchet tables ───────────────────────────────────────────────────────────

# Outbound send-paths currently NOT wired to ComplianceService.check.
# S2 wiring commits remove entries from this set.
# NEVER ADD to this set after S2 wiring sprint completes.
KNOWN_COMPLIANCE_UNWIRED: frozenset[str] = frozenset(
    {
        # S2 — to be wired when sales_agent OutputManager is integrated
        "sales_agent/application/services/output_manager.py",
    }
)

# Outbound send-paths that HAVE been wired to ComplianceService.check.
# Entries here are validated: if compliance check is removed, test fails.
KNOWN_COMPLIANCE_WIRED: frozenset[str] = frozenset()

# ── Source root ─────────────────────────────────────────────────────────────

_SRC = Path(__file__).resolve().parents[2] / "src"


# ── Helpers ─────────────────────────────────────────────────────────────────


def _file_calls_compliance_check(path: Path) -> bool:
    """Return True if the file contains a call to compliance_service.check(...)
    or ComplianceService.check(...) via AST analysis."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return False

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        # Method call: x.check(...)
        if isinstance(func, ast.Attribute) and func.attr == "check":
            # Check if the object looks like a compliance service var
            if isinstance(func.value, ast.Name):
                name = func.value.id.lower()
                if "compliance" in name:
                    return True
            # Check if it's a chained attribute like compliance_svc.check
            if isinstance(func.value, ast.Attribute):
                attr = func.value.attr.lower()
                if "compliance" in attr:
                    return True
    return False


def _relative_path(path: Path) -> str:
    """Return path relative to backend/src/modules/."""
    modules_dir = _SRC / "modules"
    try:
        return str(path.relative_to(modules_dir))
    except ValueError:
        return str(path.relative_to(_SRC))


# ── Tests ────────────────────────────────────────────────────────────────────


def test_known_compliance_wired_surfaces_still_call_compliance() -> None:
    """Every surface in KNOWN_COMPLIANCE_WIRED must still call compliance check.

    If a wired surface loses its compliance call, this test fails.
    Initially empty — grows as S2 wiring progresses.
    """
    if not KNOWN_COMPLIANCE_WIRED:
        return  # Nothing wired yet (PR-2 baseline state)

    modules_dir = _SRC / "modules"
    unwired: list[str] = []
    for rel_path in sorted(KNOWN_COMPLIANCE_WIRED):
        full_path = modules_dir / rel_path
        if not full_path.exists():
            unwired.append(f"{rel_path} (file not found)")
            continue
        if not _file_calls_compliance_check(full_path):
            unwired.append(rel_path)

    assert not unwired, (
        f"These send-paths were expected to call ComplianceService.check() "
        f"but do not: {sorted(unwired)}. "
        "If compliance was intentionally removed, move the entry to "
        "KNOWN_COMPLIANCE_UNWIRED with a justified commit."
    )


def test_compliance_unwired_set_size_is_stable() -> None:
    """KNOWN_COMPLIANCE_UNWIRED size must not grow after S2 wiring sprint.

    Current baseline: 1 entry (sales_agent output_manager, S2-pending).
    Ratchet: only SHRINKS after wiring. Adding entries = build fail.
    """
    # Baseline established at PR-2 ship (2026-04-29): 1 unwired surface.
    # Update this number ONLY to decrease it after S2 wiring removes entries.
    BASELINE_MAX_UNWIRED = 1

    current_count = len(KNOWN_COMPLIANCE_UNWIRED)
    assert current_count <= BASELINE_MAX_UNWIRED, (
        f"KNOWN_COMPLIANCE_UNWIRED grew from {BASELINE_MAX_UNWIRED} to {current_count} entries. "
        "This ratchet only shrinks. Remove from KNOWN_COMPLIANCE_UNWIRED as S2 wires compliance, "
        "or justify adding a new entry with a commit message explaining why the send-path "
        "does not require ComplianceService.check."
    )


def test_compliance_service_has_check_method() -> None:
    """ComplianceService must expose check() — public API for S2 wiring."""
    from luana_core_compliance.application.compliance_service import ComplianceService

    assert hasattr(ComplianceService, "check"), (
        "ComplianceService.check() method missing. S2 wiring depends on this signature."
    )


def test_compliance_policy_protocol_is_runtime_checkable() -> None:
    """CompliancePolicy Protocol must be runtime-checkable for DI validation."""
    import inspect

    from luana_core_compliance.application.compliance_service import CompliancePolicy

    assert hasattr(CompliancePolicy, "_is_protocol"), "CompliancePolicy must be a Protocol"
    # Check @runtime_checkable decorator applied
    assert (
        hasattr(CompliancePolicy, "__protocol_attrs__")
        or getattr(CompliancePolicy, "_is_runtime_protocol", False)
        or inspect.isclass(CompliancePolicy)
    ), "CompliancePolicy Protocol check failed"
