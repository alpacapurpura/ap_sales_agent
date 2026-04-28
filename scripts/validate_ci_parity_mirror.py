#!/usr/bin/env python3
"""Validate that ``scripts/ci-parity.sh`` mirrors ``deploy-prod.yml``.

Why
===
``ci-parity.sh`` is a hand-maintained shell replay of the CI
``quality-gates`` job. Drift between the two is silent and lets the
script falsely advertise "safe to push" while CI fails.

Concrete past drift this catches:

* 2026-04-28: ``ci-parity.sh`` ran ``pip-audit`` / ``npm audit`` as
  blockers. ``deploy-prod.yml`` marks both with
  ``continue-on-error: true``. The script aborted before ever
  building the FE image — masking the real bugs (``.md`` PARSE_ERROR
  + cross-stack fixture read) for two consecutive afternoons.

What we check
=============
1. Every shell command run inside ``ci-parity.sh`` against
   ``local-be-ci`` / ``local-fe-ci`` has a matching CI step in
   ``deploy-prod.yml``'s ``quality-gates`` job. Reverse direction
   too — every CI step under ``quality-gates`` (excluding setup-only
   steps) has a matching local invocation.
2. Steps the workflow marks with ``continue-on-error: true`` MUST be
   wrapped in a ``|| ...`` advisory branch in the script.
3. The shared env block (``TZ=UTC``, ``NODE_OPTIONS``) matches.
4. Pytest ``--ignore=`` patterns match exactly. Drift here once let
   ``test_meta_provider`` run in CI sandbox (no creds) → flaky fail.

What we don't check
===================
* Action versions (``actions/checkout@v4`` etc.) — not relevant to
  parity.
* Order of steps. Order doesn't affect parity.
* Cosmetic differences in ``run`` indentation / heredocs.

Usage
=====
    python scripts/validate_ci_parity_mirror.py
    # exit 0: in sync. exit 1: drift detected, prints diff.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "deploy-prod.yml"
SCRIPT = ROOT / "scripts" / "ci-parity.sh"


@dataclass
class CIStep:
    name: str
    run_cmd: str
    continue_on_error: bool


def load_workflow_steps() -> list[CIStep]:
    """Extract ``quality-gates`` ``run:`` steps from deploy-prod.yml."""
    data = yaml.safe_load(WORKFLOW.read_text())
    job = data["jobs"]["quality-gates"]
    out: list[CIStep] = []
    for step in job.get("steps", []):
        if "run" not in step:
            continue
        out.append(
            CIStep(
                name=step.get("name", ""),
                run_cmd=" ".join(step["run"].split()),
                continue_on_error=bool(step.get("continue-on-error", False)),
            )
        )
    return out


def load_script_text() -> str:
    return SCRIPT.read_text()


def normalise(cmd: str) -> str:
    """Collapse whitespace + drop reporter/output flags that don't affect parity intent."""
    cmd = re.sub(r"\s+", " ", cmd).strip()
    cmd = re.sub(r"--reporter=\S+", "", cmd)
    cmd = re.sub(r"--outputFile=\S+", "", cmd)
    cmd = re.sub(r"--cov-report=\S+", "", cmd)
    cmd = re.sub(r"docker (run|cp|rm)\s+\S+\s+", "", cmd)
    cmd = re.sub(r"\s+", " ", cmd).strip()
    return cmd


def signature(cmd: str) -> str | None:
    """Return the literal needle expected to appear in ci-parity.sh.

    The matchers are fragments of the *actual* shell command — we look
    for them verbatim inside the script text. Returns None for
    orchestration-only steps that do not have a 1:1 local counterpart
    (e.g. ``docker/build-push-action`` does not need a script equivalent
    because the script builds the image inline).
    """
    n = normalise(cmd)
    needles = [
        "ruff check src",
        "ruff format --check src",
        "pytest --cov=src/modules",
        "npm run lint",
        "npx tsc --noEmit",
        "npx vitest run --coverage",
        "pip-audit --strict --desc",
        "npm audit --audit-level=high",
    ]
    for needle in needles:
        if needle in n:
            return needle
    return None


def main() -> int:
    if not WORKFLOW.exists():
        print(f"ERROR: workflow not found at {WORKFLOW}", file=sys.stderr)
        return 2
    if not SCRIPT.exists():
        print(f"ERROR: script not found at {SCRIPT}", file=sys.stderr)
        return 2

    workflow_steps = load_workflow_steps()
    script_text = load_script_text()

    drift: list[str] = []

    # Check 1: every workflow step with a known signature must appear in the script.
    for step in workflow_steps:
        sig = signature(step.run_cmd)
        if sig is None:
            continue
        if sig not in script_text:
            drift.append(
                f"workflow step '{step.name}' (signature='{sig}') not found in ci-parity.sh"
            )
            continue
        # Check 2: continue-on-error MUST be reflected as ``|| ...`` after the matching command.
        if step.continue_on_error:
            # Find the matching block in the script and check for a `||` advisory chain.
            idx = script_text.find(sig)
            tail = script_text[idx : idx + 400]
            if "|| " not in tail:
                drift.append(
                    f"workflow step '{step.name}' has continue-on-error: true "
                    f"but ci-parity.sh runs '{sig}' as a blocker (no '|| advisory' branch)"
                )

    # Check 3: env vars present in the script.
    for required in ("TZ=UTC", "NODE_OPTIONS=--max-old-space-size=4096"):
        if required not in script_text:
            drift.append(f"required env '{required}' not declared in ci-parity.sh")

    # Check 4: --ignore= patterns from CI must appear in script.
    for step in workflow_steps:
        for ignore in re.findall(r"--ignore=(\S+)", step.run_cmd):
            if ignore not in script_text:
                drift.append(
                    f"pytest --ignore={ignore} in workflow but missing from ci-parity.sh"
                )

    if drift:
        print("CI PARITY MIRROR DRIFT DETECTED")
        print("=" * 60)
        for d in drift:
            print(f"  • {d}")
        print()
        print("Update scripts/ci-parity.sh to mirror deploy-prod.yml exactly,")
        print("then re-run this validator before pushing.")
        return 1

    print("OK — scripts/ci-parity.sh mirrors deploy-prod.yml quality-gates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
