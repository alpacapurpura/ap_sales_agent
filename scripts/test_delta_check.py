"""test_delta_check.py — Story 10 test parity enforcement.

Parses baseline JSON (pytest-json-report + vitest --reporter=json) and
current run JSONs, asserts new_failures ≤ --max-new-failures (default 0).

Usage:
    python scripts/test_delta_check.py \\
        --baseline-be docs/product/stories/luana-nicolify-migration/baseline-be-tests.json \\
        --baseline-fe docs/product/stories/luana-nicolify-migration/baseline-fe-tests.json \\
        --current-be /tmp/current-be-tests.json \\
        --current-fe /tmp/current-fe-tests.json \\
        --max-new-failures 0

Exit codes:
    0 — new_failures ≤ max_new_failures (PASS)
    1 — new_failures > max_new_failures (FAIL)
    2 — argument error or missing file

Decision D5 (fix-on-discovery cap delta=0): any new test failure introduced
by a codemod rewrite must be fixed in the same ticket (within cap_delta=0).

Baseline files committed in T-1 audit-trail commit per 06-tickets.yaml §T-1.
"""

import argparse
import json
import sys
from pathlib import Path


def parse_pytest_json(path: Path) -> set[str]:
    """Parse pytest-json-report output. Returns set of failed test nodeids."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: cannot parse BE baseline {path}: {exc}", file=sys.stderr)
        sys.exit(2)

    failed: set[str] = set()
    for test in data.get("tests", []):
        if test.get("outcome") == "failed":
            failed.add(test["nodeid"])
    return failed


def parse_vitest_json(path: Path) -> set[str]:
    """Parse vitest --reporter=json output. Returns set of failed test names.

    Vitest JSON schema (v1):
        {
            "numTotalTests": N,
            "numFailedTests": M,
            "testResults": [
                {
                    "name": "<suite path>",
                    "assertionResults": [
                        {"status": "passed"|"failed", "title": "<test name>"},
                        ...
                    ]
                },
                ...
            ]
        }
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: cannot parse FE baseline {path}: {exc}", file=sys.stderr)
        sys.exit(2)

    failed: set[str] = set()
    for suite in data.get("testResults", []):
        suite_name = suite.get("name", "<unknown>")
        for test in suite.get("assertionResults", []):
            if test.get("status") == "failed":
                title = test.get("title", "<unknown>")
                failed.add(f"{suite_name}::{title}")
    return failed


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Story 10 test parity enforcement (D5 cap delta=0). "
            "Compares baseline vs current test results, asserts no new failures."
        )
    )
    parser.add_argument(
        "--baseline-be",
        type=Path,
        required=True,
        help="Path to baseline pytest-json-report JSON (captured pre-migration in T-1)",
    )
    parser.add_argument(
        "--baseline-fe",
        type=Path,
        required=True,
        help="Path to baseline vitest --reporter=json JSON (captured pre-migration in T-1)",
    )
    parser.add_argument(
        "--current-be",
        type=Path,
        required=True,
        help="Path to current pytest-json-report JSON (post-rewrite run)",
    )
    parser.add_argument(
        "--current-fe",
        type=Path,
        required=True,
        help="Path to current vitest --reporter=json JSON (post-rewrite run)",
    )
    parser.add_argument(
        "--max-new-failures",
        type=int,
        default=0,
        help="Maximum allowed new failures (D5 cap default=0)",
    )
    args = parser.parse_args()

    # Validate paths exist
    for path_attr in ["baseline_be", "baseline_fe", "current_be", "current_fe"]:
        p: Path = getattr(args, path_attr)
        if not p.exists():
            print(
                f"ERROR: file not found: {p} (--{path_attr.replace('_', '-')})",
                file=sys.stderr,
            )
            sys.exit(2)

    # Parse all four JSONs
    base_be = parse_pytest_json(args.baseline_be)
    cur_be = parse_pytest_json(args.current_be)
    base_fe = parse_vitest_json(args.baseline_fe)
    cur_fe = parse_vitest_json(args.current_fe)

    # Delta computation: new failures = current failures NOT in baseline
    new_be = cur_be - base_be
    new_fe = cur_fe - base_fe
    total_new = len(new_be) + len(new_fe)

    # Also detect fixed failures (informational only — good signal)
    fixed_be = base_be - cur_be
    fixed_fe = base_fe - cur_fe

    # Report
    print(
        f"BE: baseline_failed={len(base_be)} current_failed={len(cur_be)} "
        f"new={len(new_be)} fixed={len(fixed_be)}"
    )
    print(
        f"FE: baseline_failed={len(base_fe)} current_failed={len(cur_fe)} "
        f"new={len(new_fe)} fixed={len(fixed_fe)}"
    )

    if fixed_be or fixed_fe:
        print(f"\nINFO — {len(fixed_be) + len(fixed_fe)} pre-existing failures fixed:")
        for t in sorted(fixed_be):
            print(f"  FIXED BE: {t}")
        for t in sorted(fixed_fe):
            print(f"  FIXED FE: {t}")

    if total_new > args.max_new_failures:
        print(
            f"\nFAIL — {total_new} new failures introduced "
            f"(max allowed per D5 cap: {args.max_new_failures})",
            file=sys.stderr,
        )
        for t in sorted(new_be):
            print(f"  NEW FAIL BE: {t}", file=sys.stderr)
        for t in sorted(new_fe):
            print(f"  NEW FAIL FE: {t}", file=sys.stderr)
        sys.exit(1)

    print(
        f"\nPASS — 0 new failures "
        f"(BE={len(cur_be)} cur vs {len(base_be)} base | "
        f"FE={len(cur_fe)} cur vs {len(base_fe)} base)"
    )


if __name__ == "__main__":
    main()
