#!/usr/bin/env python3
# ruff: noqa: S607
# Reason: invokes well-known commands (`git`, venv-relative `python`) where partial
# path is intentional + acceptable. Repo PATH controls resolution.
"""Stop hook validator — Wave 4 (R34).

Runs at Claude Code session close to enforce invariants that ensure no
context loss / no orphan state across sessions.

Checks (each block-or-warn classified):

  1. WIP cap enforcement (BLOCK if exceeded):
     - building stories ≤ 3
     - ready stories ≤ 5
     - validated entries ≤ 10
     - review stories ≤ 2

  2. BACKLOG freshness (WARN if stale):
     - generate_backlog.py --check passes
     - reconcile_capabilities.py --check passes

  3. WIP not committed (WARN, suggest commit/stash):
     - git status reports modified/untracked files

  4. Story checkpoint freshness (WARN):
     - Stories with state in {ready,building,review} but checkpoint.md
       last_modified > 7d → flag stale

Exit codes:
  0 — all clean (session may close)
  1 — BLOCK (cap violation; user must fix)
  2 — WARN (proceed but show issues)

Run:
  python scripts/validate_session_close.py [--repo PATH] [--quiet]

Settings.json hook integration:
  {
    "hooks": {
      "Stop": [{
        "matcher": "",
        "hooks": [{
          "type": "command",
          "command": "${CLAUDE_PROJECT_DIR}/backend/.venv/bin/python "
                     "${CLAUDE_PROJECT_DIR}/scripts/validate_session_close.py"
        }]
      }]
    }
  }
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

# ─── Constants (must match scripts/generate_backlog.py CAPS) ───────────

CAPS = {
    "validated_max": 10,
    "ready_max": 5,
    "building_max": 3,
    "review_max": 2,
}
CHECKPOINT_STALE_DAYS = 7


def _read_backlog_yaml(repo: Path) -> dict | None:
    """Read BACKLOG.yaml if exists; return parsed dict or None."""
    path = repo / "docs" / "product" / "BACKLOG.yaml"
    if not path.exists():
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return None


def check_wip_caps(backlog: dict) -> list[str]:
    """Return list of cap violations (BLOCK)."""
    violations: list[str] = []
    buckets = backlog.get("buckets", {})
    for state, cap_key in [
        ("validated", "validated_max"),
        ("ready", "ready_max"),
        ("building", "building_max"),
        ("review", "review_max"),
    ]:
        n = len(buckets.get(state, []))
        cap = CAPS[cap_key]
        if n > cap:
            violations.append(f"{state}: {n} items > cap {cap} ({n - cap} over). Park or finish before adding more.")
    return violations


def check_backlog_freshness(repo: Path) -> list[str]:
    """Run generate_backlog.py --check + reconcile_capabilities.py --check. Return warnings."""
    warns: list[str] = []
    venv_py = repo / "backend" / ".venv" / "bin" / "python"
    if not venv_py.exists():
        return ["backend/.venv/bin/python missing — skipping freshness checks"]

    for script_name, label in [
        ("generate_backlog.py", "BACKLOG drift"),
        ("reconcile_capabilities.py", "Capability status drift"),
    ]:
        script = repo / "scripts" / script_name
        if not script.exists():
            continue
        result = subprocess.run(  # noqa: S603
            [str(venv_py), str(script), "--check"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        if result.returncode != 0:
            warns.append(f"{label}: {result.stdout.strip().splitlines()[0] if result.stdout else 'failed'}")
    return warns


def check_uncommitted_wip(repo: Path) -> list[str]:
    """Detect modified/untracked files. Return warnings."""
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
    if not lines:
        return []
    return [f"{len(lines)} uncommitted file(s) — commit or stash before close."]


def check_checkpoint_staleness(repo: Path) -> list[str]:
    """Stories in {ready,building,review} with checkpoint.md older than 7d."""
    warns: list[str] = []
    stories_dir = repo / "docs" / "product" / "stories"
    if not stories_dir.exists():
        return warns
    cutoff = datetime.now(timezone.utc).timestamp() - CHECKPOINT_STALE_DAYS * 86400
    for d in sorted(stories_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        cp = d / "checkpoint.md"
        if not cp.exists():
            continue
        try:
            text = cp.read_text(encoding="utf-8")
        except OSError:
            continue
        # Quick state extraction
        state = None
        for line in text.split("\n", 50):
            if line.startswith("state:"):
                state = line.split(":", 1)[1].strip()
                break
        if state not in {"ready", "building", "review"}:
            continue
        mtime = cp.stat().st_mtime
        if mtime < cutoff:
            age_days = int((datetime.now(timezone.utc).timestamp() - mtime) / 86400)
            warns.append(f"{d.name}: state={state}, checkpoint.md {age_days}d stale (>7d)")
    return warns


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repo root. Default: script's parent.",
    )
    parser.add_argument("--quiet", action="store_true", help="Only print on warn/block.")
    args = parser.parse_args()

    backlog = _read_backlog_yaml(args.repo)
    block_violations: list[str] = []
    warns: list[str] = []

    if backlog is None:
        warns.append("BACKLOG.yaml missing — run scripts/generate_backlog.py first.")
    else:
        block_violations.extend(check_wip_caps(backlog))

    warns.extend(check_backlog_freshness(args.repo))
    warns.extend(check_uncommitted_wip(args.repo))
    warns.extend(check_checkpoint_staleness(args.repo))

    if block_violations:
        print("\n\033[31m" + "─" * 65)  # noqa: T201
        print("STOP HOOK BLOCKED — WIP caps exceeded:")  # noqa: T201
        print("─" * 65)  # noqa: T201
        for v in block_violations:
            print(f"  ❌ {v}")  # noqa: T201
        print("─" * 65)  # noqa: T201
        print("Resolution: park/drop/finish stories before closing session.")  # noqa: T201
        print("Edit checkpoint.md state field OR ideas-pool.yaml entry to park/drop.\033[0m")  # noqa: T201
        return 1

    if warns:
        if not args.quiet:
            print("\n\033[33m" + "─" * 65)  # noqa: T201
            print("STOP HOOK WARN — review before close:")  # noqa: T201
            print("─" * 65)  # noqa: T201
            for w in warns:
                print(f"  ⚠ {w}")  # noqa: T201
            print("─" * 65 + "\033[0m")  # noqa: T201
        return 2

    if not args.quiet:
        print("\033[32m✅ Stop hook OK — session clean.\033[0m")  # noqa: T201
    return 0


if __name__ == "__main__":
    sys.exit(main())
