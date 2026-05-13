"""Architecture fitness gate (PR-6 Sub-E): no legacy in-memory bus emits.

Verifies that modules ``{sales_agent, copilot, brand}`` do NOT directly call
``EventBus.publish_in_memory(...)`` after PR-6 cutover.

Post-cutover (Sub-B/C/D), all event emissions go through the
``EventBusAdapter`` which routes to the outbox table when the per-module
flag is ON, and falls back to the legacy bus when OFF.

The ``KNOWN_DIRECT_LEGACY_EMITTERS`` allowlist below tracks callsites that
still bypass the adapter — shrink-only ratchet.
"""

from __future__ import annotations

import ast
from pathlib import Path

# ---------------------------------------------------------------------------
# Allowlist: direct legacy bus emitters NOT yet routed through adapter.
# Each entry must include WHY (subscriber registration, test fixture, etc.).
# Shrink-only ratchet.
# ---------------------------------------------------------------------------

KNOWN_DIRECT_LEGACY_EMITTERS: frozenset[tuple[str, str]] = frozenset(
    {
        # No remaining direct emitters in cutover modules post Sub-B/C/D.
        # Empty allowlist = ratchet seeded clean.
    }
)

CUTOVER_MODULES = ("sales_agent", "copilot", "brand")
FORBIDDEN_CALLS = ("publish_in_memory",)


def _backend_root() -> Path:
    """Return backend src root."""
    return Path(__file__).resolve().parents[2] / "src"


def _module_paths() -> list[Path]:
    """Yield Python files under each cutover module (excluding __pycache__)."""
    root = _backend_root() / "modules"
    paths: list[Path] = []
    for module in CUTOVER_MODULES:
        module_root = root / module
        if not module_root.exists():
            continue
        paths.extend(p for p in module_root.rglob("*.py") if "__pycache__" not in p.parts)
    return paths


def _scan_file_for_forbidden_calls(path: Path) -> list[tuple[str, int]]:
    """Return list of (call_name, line) for forbidden direct legacy emits."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []

    findings: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            if attr in FORBIDDEN_CALLS:
                findings.append((attr, node.lineno))
    return findings


def test_no_direct_legacy_publish_in_cutover_modules() -> None:
    """Modules cutover MUST NOT call ``publish_in_memory`` directly.

    All emits go through ``EventBusAdapter.publish(event, session=...)``
    which routes to outbox or legacy based on the per-module flag.
    """
    root = _backend_root()
    new_violations: list[str] = []

    for path in _module_paths():
        rel = "src/" + str(path.relative_to(root))
        findings = _scan_file_for_forbidden_calls(path)
        for call_name, lineno in findings:
            entry = (rel, f"{call_name}:line {lineno}")
            if (rel, entry[1]) not in KNOWN_DIRECT_LEGACY_EMITTERS:
                new_violations.append(f"{rel}:{lineno} → {call_name}")

    assert not new_violations, (
        "New direct legacy bus emits detected in cutover modules — route "
        "through EventBusAdapter instead. Violations:\n  - " + "\n  - ".join(new_violations)
    )


def test_known_direct_emitters_allowlist_size() -> None:
    """Allowlist size guard — shrink-only ratchet."""
    expected_max = 0  # post-cutover seeded clean
    assert len(KNOWN_DIRECT_LEGACY_EMITTERS) <= expected_max, (
        f"KNOWN_DIRECT_LEGACY_EMITTERS grew beyond {expected_max} — verify "
        "each entry has a justified TODO + follow-up issue."
    )


def test_event_bus_adapter_is_real() -> None:
    """Sanity: EventBusAdapter importable + routes via _is_outbox_enabled."""
    from luana_core_events.outbox.application.event_bus_adapter import (
        EventBusAdapter,
    )

    adapter = EventBusAdapter()
    assert hasattr(adapter, "publish")
    assert hasattr(adapter, "_is_outbox_enabled")
