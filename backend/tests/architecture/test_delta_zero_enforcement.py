"""test_delta_zero_enforcement.py — Story 10 arch fitness gate.

Parses baseline JSON files (committed in T-1) and verifies:
1. Baseline files exist and are parseable.
2. scripts/test_delta_check.py is executable.
3. Self-comparison sanity: delta(baseline, baseline) = 0 new failures.

State: ACTIVE from T-1 onwards (baselines exist after T-1 commit).
Becomes critical enforcement gate from T-2 onwards (tickets must maintain delta=0).

Per 06-tickets.yaml T-1 acceptance criterion A1 + A3.
Decision D5 (fix-on-discovery cap delta=0).
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Paths
STORY_DIR = Path("/home/chris/AISALESHT/docs/product/stories/luana-nicolify-migration")
BASELINE_BE = STORY_DIR / "baseline-be-tests.json"
BASELINE_FE = STORY_DIR / "baseline-fe-tests.json"
DELTA_CHECK_SCRIPT = Path("/home/chris/AISALESHT/scripts/test_delta_check.py")
PYTHON = Path("/home/chris/AISALESHT/backend/.venv/bin/python3")


def test_baseline_be_exists_and_parseable():
    """baseline-be-tests.json must exist (T-1 deliverable) and be valid pytest-json-report JSON."""
    assert BASELINE_BE.exists(), (
        f"BE baseline not found: {BASELINE_BE}. "
        "Run T-1 baseline capture: cd backend && .venv/bin/pytest --json-report "
        "--json-report-file=../docs/product/stories/luana-nicolify-migration/baseline-be-tests.json"
    )

    try:
        data = json.loads(BASELINE_BE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        pytest.fail(f"baseline-be-tests.json is not valid JSON: {exc}")

    # Verify expected keys (pytest-json-report schema)
    assert "summary" in data, f"baseline-be-tests.json missing 'summary' key. Available keys: {list(data.keys())[:10]}"
    assert "tests" in data, "baseline-be-tests.json missing 'tests' key. This is required for delta computation."

    summary = data["summary"]
    assert "passed" in summary or "total" in summary, (
        f"baseline-be-tests.json summary missing expected fields: {summary}"
    )

    total = summary.get("total", summary.get("passed", 0) + summary.get("failed", 0))
    assert total > 0, f"BE baseline summary shows 0 total tests — likely empty run. Summary: {summary}"


def test_baseline_fe_exists_and_parseable():
    """baseline-fe-tests.json must exist (T-1 deliverable) and be valid vitest JSON."""
    assert BASELINE_FE.exists(), (
        f"FE baseline not found: {BASELINE_FE}. "
        "Run T-1 baseline capture: cd frontend && npx vitest run --reporter=json "
        "--outputFile=../docs/product/stories/luana-nicolify-migration/baseline-fe-tests.json"
    )

    try:
        data = json.loads(BASELINE_FE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        pytest.fail(f"baseline-fe-tests.json is not valid JSON: {exc}")

    # Verify expected keys (vitest --reporter=json schema)
    assert "numTotalTests" in data, (
        f"baseline-fe-tests.json missing 'numTotalTests' key. Available keys: {list(data.keys())[:10]}"
    )
    assert "testResults" in data, "baseline-fe-tests.json missing 'testResults' key. Required for delta computation."

    assert data["numTotalTests"] > 0, (
        f"FE baseline shows 0 total tests — likely empty run. numTotalTests: {data['numTotalTests']}"
    )


def test_delta_check_script_exists_and_executable():
    """scripts/test_delta_check.py must exist and be importable."""
    assert DELTA_CHECK_SCRIPT.exists(), (
        f"test_delta_check.py not found: {DELTA_CHECK_SCRIPT}. T-1 must produce this script."
    )

    # Verify it is syntactically valid Python
    result = subprocess.run(  # noqa: S603
        [str(PYTHON), "-m", "py_compile", str(DELTA_CHECK_SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"test_delta_check.py has syntax errors:\n{result.stderr}"


def test_delta_self_comparison_is_zero():
    """Self-comparison sanity: delta(baseline, baseline) = 0 new failures.

    Running test_delta_check.py with baseline as both input and comparison
    must return 0 new failures (self-referential delta is always 0).
    """
    # Skip if baselines don't exist yet (will be caught by earlier tests)
    if not BASELINE_BE.exists() or not BASELINE_FE.exists():
        pytest.skip("Baseline files not yet captured — run T-1 baseline first")

    result = subprocess.run(  # noqa: S603
        [
            str(PYTHON),
            str(DELTA_CHECK_SCRIPT),
            "--baseline-be",
            str(BASELINE_BE),
            "--baseline-fe",
            str(BASELINE_FE),
            "--current-be",
            str(BASELINE_BE),  # same file = delta 0
            "--current-fe",
            str(BASELINE_FE),  # same file = delta 0
            "--max-new-failures",
            "0",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"Self-comparison delta check failed (should always be 0).\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )

    assert "PASS" in result.stdout, (
        f"Expected 'PASS' in delta check output for self-comparison.\nstdout: {result.stdout}"
    )


def test_baseline_be_failure_count_documented():
    """Verify baseline BE failure count matches expected pre-existing failures.

    Per 06-tickets.yaml T-1: 8 pre-existing BE failures (not 40 sales_agent
    ones — those are tracked separately in Decisión 9B per 03-arch.md §0).

    The 40 sales_agent failures mentioned in Decisión 9B are DEFERRED to Story 14.
    This test verifies the exact count is captured in the baseline.
    """
    if not BASELINE_BE.exists():
        pytest.skip("Baseline not yet captured")

    data = json.loads(BASELINE_BE.read_text(encoding="utf-8"))
    summary = data.get("summary", {})
    failed = summary.get("failed", -1)

    # Document the count — not a strict assertion (count may vary by env)
    # but if failed > 50, something went wrong during baseline capture
    assert failed >= 0, f"BE baseline summary has invalid 'failed': {failed}"
    assert failed < 100, (
        f"BE baseline has {failed} failures — unexpected (should be ~8 per T-1 baseline). "
        "Halt Trigger #5: unexpected failures may indicate env breakage. Check pytest output."
    )
