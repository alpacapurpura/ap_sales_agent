"""Architecture fitness gate (PR-3 PI-11): no legacy EventBus.publish mocks when outbox flag default = True.

Origen: PR-3 PI-11 — anti-default-flip enforcement.
Root cause: commit 64738354 flipped USE_OUTBOX_PATTERN_* True without auditing tests
mocking legacy EventBus.publish path → 25 failures in /pase-produccion 2026-05-04.

Workflow obligatorio: `.claude/rules/anti-default-flip-audit.md`.

Detection: AST walk per test_*.py file. Detects @patch / mocker.patch /
monkeypatch.setattr calls whose first string arg matches LEGACY_MOCK_TARGETS,
and patch.object(EventBus, "publish") patterns (synthesized as "EventBus.publish").

Bypass:
- File path in BYPASS_FILES (capability tests + meta-tests of adapter routing)
- File path in KNOWN_LEGACY_MOCK_FILES (deferred migration — shrink-only ratchet)
- Magic comment '# arch-bypass: testing legacy capability' anywhere in file
"""

from __future__ import annotations

import ast
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Targets prohibited when outbox flag default = True.
# Tests mocking these paths are testing a dead code path (when flag=True).
# ---------------------------------------------------------------------------

LEGACY_MOCK_TARGETS: frozenset[str] = frozenset(
    {
        "src.shared.domain.events.EventBus.publish",
        "shared.domain.events.EventBus.publish",
        "EventBus.publish",
        "LegacyEventBus.publish",
        "src.shared.domain_events.legacy_event_bus.LegacyEventBus.publish",
    }
)

# ---------------------------------------------------------------------------
# BYPASS_FILES — permanent bypass for capability/meta tests.
# These files legitimately test the legacy bus path (adapter routing when
# flag=False, or the LegacyEventBus module itself).
# Each entry MUST have a justification comment below. Shrink-only ratchet.
# ---------------------------------------------------------------------------

BYPASS_FILES: frozenset[str] = frozenset(
    {
        # LegacyEventBus capability test (tests the bus module itself)
        "tests/shared/test_event_bus.py",
        # EventBusAdapter meta-tests (probe legacy fall-through path when flag=False)
        "tests/shared/domain_events/test_event_bus_adapter.py",
        "tests/shared/domain_events/test_event_bus_adapter_infers_module.py",
        # Cutover integration tests: probe BOTH paths (flag=True + flag=False)
        "tests/integration/test_outbox_cutover_e2e.py",
        "tests/modules/copilot/integration/test_outbox_cutover.py",
        "tests/modules/brand/integration/test_outbox_cutover.py",
        "tests/modules/sales_agent/integration/test_outbox_cutover.py",
        # Outbox adapter integration capability tests: probe routing when flag=False
        "tests/modules/copilot/test_outbox_adapter_integration.py",
        "tests/modules/brand/test_outbox_adapter_integration.py",
        "tests/modules/sales_agent/test_outbox_adapter_integration.py",
    }
)

# ---------------------------------------------------------------------------
# KNOWN_LEGACY_MOCK_FILES — DEFERRED migration (shrink-only ratchet).
# Files in this list have not yet been migrated to mock the new canonical
# path (adapter_bus.publish / outbox table probe). Each entry MUST include
# a comment explaining WHY and referencing the PR that will migrate it.
# Remove entries as migration PRs complete.
# ---------------------------------------------------------------------------

KNOWN_LEGACY_MOCK_FILES: frozenset[str] = frozenset(
    {
        # test_grant_access_idempotent.py: patches EventBus.publish directly.
        # Not a capability test — needs migration to adapter_bus mock.
        # Deferred: future PR post PR-3 per PI-11 D9.
        "tests/modules/sales_agent/tools/payment/test_grant_access_idempotent.py",
        # test_sale_lifecycle.py: patch.object(EventBus, "publish") for CRM sale event.
        # crm module not yet migrated to EventBusAdapter.
        # Deferred: future PR post PR-3 per PI-11 D9.
        "tests/modules/crm/test_sale_lifecycle.py",
        # test_audit_emitter.py: patches EventBus.publish + sets _is_outbox_enabled=False.
        # Tests legacy-fallback behavior of AuditEmitter with outbox OFF.
        # Deferred: future PR post PR-3 per PI-11 D9.
        "tests/modules/sales_agent/orchestrator/test_audit_emitter.py",
    }
)

BYPASS_MAGIC_COMMENT: str = "# arch-bypass: testing legacy capability"


# ---------------------------------------------------------------------------
# AST walk helpers
# ---------------------------------------------------------------------------


def _backend_root() -> Path:
    """Return backend root (parent of src/ and tests/)."""
    return Path(__file__).resolve().parents[2]


def _test_files() -> list[Path]:
    """Yield all test_*.py files under backend/tests/ (excluding __pycache__)."""
    root = _backend_root() / "tests"
    return [p for p in root.rglob("test_*.py") if "__pycache__" not in p.parts]


def _extract_first_string_arg(node: ast.Call) -> str | None:
    """Return first string-literal arg of an ast.Call, or None if not a string constant."""
    if not node.args:
        return None
    first = node.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return first.value
    return None


def _walk_mock_targets(tree: ast.AST) -> set[str]:
    """Extract mock target strings from patch/setattr calls in AST.

    Patterns recognized:

        @patch("X")                           → detects "X"
        mocker.patch("X")                     → detects "X"
        monkeypatch.setattr("X", val)         → detects "X"
        @patch.object(SomeClass, "method")    → synthesizes "SomeClass.method"

    NOTE: AST walk is best-effort. Dynamic patch targets (computed strings,
    variables) will not be detected. The magic comment bypass covers edge cases.
    """
    targets: set[str] = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        func = node.func

        # Pattern 1: bare patch("X"), mocker.patch("X"), monkeypatch.setattr("X", ...)
        is_patch_or_setattr_call = (isinstance(func, ast.Name) and func.id == "patch") or (
            isinstance(func, ast.Attribute) and func.attr in ("patch", "setattr")
        )
        if is_patch_or_setattr_call:
            target = _extract_first_string_arg(node)
            if target:
                targets.add(target)

        # Pattern 2: patch.object(ClassName, "method") → synthesize "ClassName.method"
        is_patch_object = (
            isinstance(func, ast.Attribute)
            and func.attr == "object"
            and isinstance(func.value, ast.Name)
            and func.value.id == "patch"
        )
        if is_patch_object and len(node.args) >= 2:
            cls_node = node.args[0]
            method_node = node.args[1]
            if (
                isinstance(cls_node, ast.Name)
                and isinstance(method_node, ast.Constant)
                and isinstance(method_node.value, str)
            ):
                targets.add(f"{cls_node.id}.{method_node.value}")

    return targets


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_no_legacy_eventbus_mock_when_outbox_flag_default_on() -> None:
    """Tests MUST NOT mock LegacyEventBus.publish when outbox flag default = True.

    When USE_OUTBOX_PATTERN_{SALES_AGENT,COPILOT,BRAND} = True (default post-2026-04-29),
    mocking EventBus.publish is testing a dead code path — the mock never fires in
    production, so the test asserts nothing real.

    Migration target:
        Mock `event_bus_adapter.adapter_bus.publish` (adapter canonical path)
        OR probe `domain_event_outbox` table (persistence sink).

    Bypass:
        - Add file to BYPASS_FILES (permanent capability/meta tests)
        - Add file to KNOWN_LEGACY_MOCK_FILES (deferred migration — shrink only)
        - Add '# arch-bypass: testing legacy capability' comment in file

    Ver `.claude/rules/anti-default-flip-audit.md`.
    """
    root = _backend_root()
    violations: list[str] = []

    for test_file in _test_files():
        rel_path = str(test_file.relative_to(root))

        # Bypass: permanent capability/meta tests
        if rel_path in BYPASS_FILES:
            continue

        # Bypass: deferred migration (shrink-only ratchet)
        if rel_path in KNOWN_LEGACY_MOCK_FILES:
            continue

        try:
            source = test_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        # Bypass: magic comment in file
        if BYPASS_MAGIC_COMMENT in source:
            continue

        # AST parse
        try:
            tree = ast.parse(source, filename=str(test_file))
        except SyntaxError:
            continue

        # Detect violations
        mock_targets = _walk_mock_targets(tree)
        legacy_hits = mock_targets & LEGACY_MOCK_TARGETS
        if legacy_hits:
            violations.append(f"{rel_path}: legacy mock targets {sorted(legacy_hits)}")

    assert not violations, (
        "Tests mockean LegacyEventBus.publish path cuando outbox flag default = True.\n"
        "Migrar a `event_bus_adapter.adapter_bus.publish` mock o "
        "`domain_event_outbox` table probe.\n"
        "Bypass permanente: agregar archivo a BYPASS_FILES (capability/meta tests).\n"
        "Bypass temporal: agregar archivo a KNOWN_LEGACY_MOCK_FILES (deferred migration — shrink only).\n"
        "Bypass in-file: comentario '# arch-bypass: testing legacy capability' en el archivo.\n"
        "Ver `.claude/rules/anti-default-flip-audit.md`.\n"
        "Violations:\n  - " + "\n  - ".join(violations)
    )


def test_bypass_files_size_ratchet() -> None:
    """BYPASS_FILES allowlist size guard — shrink-only ratchet.

    Post-PR-3 baseline: 10 files (LegacyEventBus capability + adapter meta-tests +
    cutover integration + outbox adapter routing capability tests).
    Additions require justification comment + auditor approval.
    """
    expected_max = 10  # post-PR-3 baseline
    assert len(BYPASS_FILES) <= expected_max, (
        f"BYPASS_FILES grew beyond {expected_max} — verify each new entry "
        "has justification comment in this file + auditor approval "
        "per `.claude/rules/anti-default-flip-audit.md`."
    )


def test_known_legacy_mock_files_size_ratchet() -> None:
    """KNOWN_LEGACY_MOCK_FILES size guard — shrink-only ratchet.

    Post-PR-3 baseline: 3 files (deferred migration per PI-11 D9).
    Each migration PR reduces this list. Target: 0 (all migrated post PI-11 S2).
    Additions require justification + PM approval.
    """
    expected_max = 3  # post-PR-3 baseline
    assert len(KNOWN_LEGACY_MOCK_FILES) <= expected_max, (
        f"KNOWN_LEGACY_MOCK_FILES grew beyond {expected_max} — this list MUST shrink "
        "as migration PRs complete. Each new entry requires PM approval + "
        "migration PR scheduled. Per `.claude/rules/anti-default-flip-audit.md`."
    )


def test_arch_fitness_performance_budget() -> None:
    """AST walk completes within 4-second budget.

    Walks all test_*.py files; suite at 800+ files post PI-11 coverage push.
    Budget bumped from 2s → 4s on 2026-05-04 to absorb suite growth.
    """
    start = time.monotonic()

    files = _test_files()
    parsed_count = 0

    for test_file in files:
        try:
            source = test_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(test_file))
            _walk_mock_targets(tree)
            parsed_count += 1
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue

    elapsed = time.monotonic() - start

    assert elapsed < 4.0, (
        f"AST walk took {elapsed:.3f}s for {parsed_count} files — "
        "exceeds 4s budget. Consider pytest-xdist parallelization or "
        "incremental cache if test suite grows beyond 1500 files."
    )
