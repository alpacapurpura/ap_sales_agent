"""test_no_legacy_src_mock_paths.py — Story 10 arch fitness gate.

Asserts that `patch('src.X.Y')` or `patch("src.X.Y")` string-path mock patterns
are absent in luana-platform/nicolify/backend/tests/ after Story 10 rewrite.

State during T-1 (pre-rewrite): SKIP (and verify current count is 0 per
03-arch-be.md §1.3 baseline — verified 2026-05-12 via grep = 0).
State post Story 10 merge: ACTIVE — fails build if stale test mocks re-introduced.

Per 03-arch.md §0.4, 03-arch-be.md §1.3, and 06-tickets.yaml T-1 acceptance A3.

Halt Trigger #11: if a `patch("src.X.Y")` has no clear equivalent in luana-core
→ halt + ask Chris. Do NOT silently skip.
"""

import subprocess
from pathlib import Path

import pytest

# Paths: check both current AISALESHT (for pre-rewrite baseline verification)
# and post-migration luana-platform/nicolify (for post-rewrite gate)
AISALESHT_TESTS = Path("/home/chris/AISALESHT/backend/tests")
NICOLIFY_TESTS = Path.home() / "luana-platform" / "nicolify" / "backend" / "tests"

_NICOLIFY_TESTS_PRESENT = NICOLIFY_TESTS.exists()


def _count_stale_mocks(tests_dir: Path) -> list[str]:
    """Return list of grep matches for patch('src.X') patterns."""
    result = subprocess.run(  # noqa: S603
        [  # noqa: S607
            "grep",
            "-rn",
            "--include=*.py",
            r"""patch.*['"](src\.)""",
            str(tests_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return [line for line in result.stdout.strip().split("\n") if line]


def test_no_stale_src_mock_paths_in_aisalesht():
    """Pre-rewrite baseline: AISALESHT tests must have 0 `patch('src.')` patterns.

    Per 03-arch-be.md §1.3: verified 2026-05-12 = 0. This test ensures drift
    is caught immediately if a dev accidentally introduces stale mock paths
    during parallel development.

    Note: mocker.patch.object() patterns are NOT affected (operate on imported
    objects, not string paths). Only string-path patches need rewrite.
    """
    matches = _count_stale_mocks(AISALESHT_TESTS)

    assert len(matches) == 0, (
        f"Found {len(matches)} stale `patch('src.X')` mock pattern(s) in {AISALESHT_TESTS}. "
        "T-1 baseline verified this was 0. A dev introduced a stale mock path.\n"
        "Fix: rewrite to use the luana_core_* path directly, or use mocker.patch.object().\n"
        "If the luana_core equivalent doesn't exist → Halt Trigger #11 (escalate Chris).\n"
        "Matches:\n" + "\n".join(f"  {m}" for m in matches[:20]) + ("\n  ..." if len(matches) > 20 else "")
    )


@pytest.mark.skipif(
    not _NICOLIFY_TESTS_PRESENT,
    reason="Story 10 not run yet — luana-platform/nicolify/backend/tests/ absent. "
    "This test becomes an active gate post Story 10 merge.",
)
def test_no_stale_src_mock_paths_in_nicolify():
    """Post-rewrite gate: nicolify tests must have 0 `patch('src.')` patterns.

    Catches accidental re-introduction of stale mock paths after migration.
    Ratchet: count must stay at 0 — shrink-only.
    """
    matches = _count_stale_mocks(NICOLIFY_TESTS)

    assert len(matches) == 0, (
        f"Found {len(matches)} stale `patch('src.X')` mock pattern(s) in {NICOLIFY_TESTS}. "
        "All test mocks must use luana_core_* or nicolify_backend paths.\n"
        "Matches:\n" + "\n".join(f"  {m}" for m in matches[:20]) + ("\n  ..." if len(matches) > 20 else "")
    )
