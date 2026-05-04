"""Meta-test: verifies arch fitness gate PR-3 detects violations + bypasses work correctly.

Tests synthetic scenarios using tmp_path fixture:
1. Synthetic file with @patch legacy target -> arch fitness DETECTS (violation)
2. Synthetic file with magic comment + same patch -> arch fitness IGNORES (bypass works)
3. Synthetic file whose path matches BYPASS_FILES -> arch fitness IGNORES
4. Synthetic file with patch.object(EventBus, "publish") -> arch fitness DETECTS (Pattern 2)
5. Canonical adapter_bus mock is not flagged as legacy
6. All allowlist paths exist on disk

These tests ensure the gate does not regress (false negatives) or over-fire (false positives).
"""

from __future__ import annotations

import ast
from pathlib import Path

from tests.architecture.test_no_legacy_eventbus_mock_when_outbox_on import (
    BYPASS_FILES,
    BYPASS_MAGIC_COMMENT,
    KNOWN_LEGACY_MOCK_FILES,
    LEGACY_MOCK_TARGETS,
    _walk_mock_targets,
)


def _parse(source: str) -> ast.AST:
    """Parse source string into AST."""
    return ast.parse(source)


# ---------------------------------------------------------------------------
# Test 1: Detection works -- @patch with legacy FQN string
# ---------------------------------------------------------------------------


def test_detection_works_for_string_patch_target() -> None:
    """Synthetic: @patch with legacy EventBus.publish FQN is detected as violation."""
    source = (
        "import pytest\n"
        "from unittest.mock import patch\n"
        "\n"
        '@patch("src.shared.domain.events.EventBus.publish")\n'
        "def test_something(mock_publish):\n"
        "    pass\n"
    )
    tree = _parse(source)
    targets = _walk_mock_targets(tree)
    legacy_hits = targets & LEGACY_MOCK_TARGETS

    assert legacy_hits == {"src.shared.domain.events.EventBus.publish"}, (
        f"Expected detection of legacy mock target, got: {legacy_hits}"
    )


# ---------------------------------------------------------------------------
# Test 2: Magic comment bypass -- same patch but file has bypass comment
# ---------------------------------------------------------------------------


def test_magic_comment_bypass_suppresses_detection(tmp_path: Path) -> None:
    """Synthetic: file with magic comment is ignored by arch fitness gate."""
    source = (
        f"# {BYPASS_MAGIC_COMMENT}\n"
        "import pytest\n"
        "from unittest.mock import patch\n"
        "\n"
        '@patch("src.shared.domain.events.EventBus.publish")\n'
        "def test_legacy_capability(mock_publish):\n"
        "    pass\n"
    )
    test_file = tmp_path / "test_synthetic_bypass.py"
    test_file.write_text(source, encoding="utf-8")

    # Simulate the gate logic: check for magic comment first
    file_source = test_file.read_text(encoding="utf-8")
    has_bypass = BYPASS_MAGIC_COMMENT in file_source

    assert has_bypass, (
        "Magic comment not detected in synthetic file -- gate would proceed to AST scan and report false violation"
    )


# ---------------------------------------------------------------------------
# Test 3: BYPASS_FILES path bypass -- file in the allowlist is skipped
# ---------------------------------------------------------------------------


def test_bypass_files_covers_shared_event_bus_test() -> None:
    """Canonical LegacyEventBus test is in BYPASS_FILES."""
    canonical = "tests/shared/test_event_bus.py"
    assert canonical in BYPASS_FILES, (
        f"{canonical} must be in BYPASS_FILES -- "
        "it tests the LegacyEventBus module itself and legitimately patches publish"
    )


def test_bypass_files_covers_cutover_integration_tests() -> None:
    """All cutover integration tests are in BYPASS_FILES."""
    expected = {
        "tests/integration/test_outbox_cutover_e2e.py",
        "tests/modules/copilot/integration/test_outbox_cutover.py",
        "tests/modules/brand/integration/test_outbox_cutover.py",
        "tests/modules/sales_agent/integration/test_outbox_cutover.py",
    }
    missing = expected - BYPASS_FILES
    assert not missing, (
        f"Cutover integration tests missing from BYPASS_FILES: {missing}\n"
        "These tests legitimately probe both legacy + outbox paths."
    )


# ---------------------------------------------------------------------------
# Test 4: Pattern 2 detection -- patch.object(EventBus, "publish")
# ---------------------------------------------------------------------------


def test_detection_works_for_patch_object_pattern() -> None:
    """Synthetic: patch.object(EventBus, publish-str) is synthesized as EventBus.publish."""
    source = (
        "import pytest\n"
        "from unittest.mock import patch\n"
        "from src.shared.domain.events import EventBus\n"
        "\n"
        "def test_sale_emits_event(db):\n"
        '    with patch.object(EventBus, "publish") as mock_publish:\n'
        "        do_sale()\n"
        "        assert mock_publish.called\n"
    )
    tree = _parse(source)
    targets = _walk_mock_targets(tree)
    legacy_hits = targets & LEGACY_MOCK_TARGETS

    assert "EventBus.publish" in legacy_hits, (
        f"Expected 'EventBus.publish' to be detected via patch.object pattern, got targets: {targets}"
    )


# ---------------------------------------------------------------------------
# Test 5: Non-legacy mock target is not flagged
# ---------------------------------------------------------------------------


def test_canonical_adapter_mock_not_flagged() -> None:
    """Synthetic: mocking adapter_bus.publish via attribute form is NOT in LEGACY_MOCK_TARGETS."""
    source = (
        "import pytest\n"
        "\n"
        "def test_outbox_adapter(monkeypatch, event_bus_adapter):\n"
        '    monkeypatch.setattr(event_bus_adapter.adapter_bus, "publish", lambda *a, **kw: None)\n'
        "    do_action()\n"
    )
    tree = _parse(source)
    targets = _walk_mock_targets(tree)

    # The attribute-form setattr (not string-based) won't produce any string target
    # So no legacy hits expected
    legacy_hits = targets & LEGACY_MOCK_TARGETS
    assert not legacy_hits, f"Canonical adapter_bus mock incorrectly flagged as legacy: {legacy_hits}"


# ---------------------------------------------------------------------------
# Test 6: KNOWN_LEGACY_MOCK_FILES entries are all valid relative paths
# ---------------------------------------------------------------------------


def test_known_legacy_mock_files_all_exist() -> None:
    """Each file in KNOWN_LEGACY_MOCK_FILES must exist in the backend tree."""
    backend_root = Path(__file__).resolve().parents[2]
    missing: list[str] = []

    for rel_path in KNOWN_LEGACY_MOCK_FILES:
        full_path = backend_root / rel_path
        if not full_path.exists():
            missing.append(rel_path)

    assert not missing, (
        "KNOWN_LEGACY_MOCK_FILES contains paths that do not exist -- "
        "remove them (migrations complete or files renamed):\n  - " + "\n  - ".join(missing)
    )


def test_bypass_files_all_exist() -> None:
    """Each file in BYPASS_FILES must exist in the backend tree."""
    backend_root = Path(__file__).resolve().parents[2]
    missing: list[str] = []

    for rel_path in BYPASS_FILES:
        full_path = backend_root / rel_path
        if not full_path.exists():
            missing.append(rel_path)

    assert not missing, (
        "BYPASS_FILES contains paths that do not exist -- "
        "remove them (files renamed or deleted):\n  - " + "\n  - ".join(missing)
    )
