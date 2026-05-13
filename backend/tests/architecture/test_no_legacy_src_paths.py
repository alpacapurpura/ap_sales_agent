"""test_no_legacy_src_paths.py — Story 10 arch fitness gate.

Asserts that `from src.` imports are absent in luana-platform/nicolify/backend/
after Story 10 rewrite completes.

State during T-1 (pre-rewrite): SKIP — luana-platform/nicolify/ does not exist yet.
State post Story 10 merge: ACTIVE — fails build if any legacy import re-introduced.

Per 03-arch.md §0.4 and 06-tickets.yaml T-1 acceptance criterion A3.
"""

import subprocess
from pathlib import Path

import pytest

# Path to the post-migration backend source (will exist post Story 10)
NICOLIFY_BACKEND = Path.home() / "luana-platform" / "nicolify" / "backend" / "src"

# Skip guard: Story 10 not yet run → nicolify/backend/src/ absent
_NICOLIFY_BACKEND_PRESENT = NICOLIFY_BACKEND.exists()


@pytest.mark.skipif(
    not _NICOLIFY_BACKEND_PRESENT,
    reason="Story 10 not run yet — luana-platform/nicolify/backend/src/ absent. "
    "This test becomes an active gate post Story 10 merge.",
)
def test_no_legacy_src_imports_in_nicolify_backend():
    """After Story 10 rewrite, zero `from src.` imports should remain in nicolify/backend/src/.

    Catches any accidental re-introduction of legacy import paths post-migration.
    Ratchet: this count must stay at 0 — shrink-only.
    """
    result = subprocess.run(  # noqa: S603
        [  # noqa: S607
            "grep",
            "-rn",
            "--include=*.py",
            r"from src\.",
            str(NICOLIFY_BACKEND),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    matches = [line for line in result.stdout.strip().split("\n") if line]

    assert len(matches) == 0, (
        f"Found {len(matches)} legacy `from src.` import(s) in {NICOLIFY_BACKEND}. "
        "These must be rewritten to luana-core or nicolify_backend equivalents.\n"
        "Matches:\n" + "\n".join(f"  {m}" for m in matches[:20]) + ("\n  ..." if len(matches) > 20 else "")
    )


@pytest.mark.skipif(
    not _NICOLIFY_BACKEND_PRESENT,
    reason="Story 10 not run yet — luana-platform/nicolify/ absent.",
)
def test_no_bare_src_imports_in_nicolify_backend():
    """Zero `^import src.` (bare module import) patterns in nicolify/backend/src/."""
    result = subprocess.run(  # noqa: S603
        [  # noqa: S607
            "grep",
            "-rn",
            "--include=*.py",
            r"^import src\.",
            str(NICOLIFY_BACKEND),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    matches = [line for line in result.stdout.strip().split("\n") if line]

    assert len(matches) == 0, (
        f"Found {len(matches)} bare `import src.` pattern(s) in {NICOLIFY_BACKEND}. "
        "These must be rewritten.\n" + "\n".join(f"  {m}" for m in matches[:20])
    )
