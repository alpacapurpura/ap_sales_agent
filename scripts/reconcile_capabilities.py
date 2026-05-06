#!/usr/bin/env python3
"""Reconcile capability YAML status fields from story YAML status (R32).

Capability files at ``docs/product/capabilities/{module}/{cap}.yaml`` declare
``status``, ``stories_live``, ``stories_planned``, ``stories_total`` in their
frontmatter. These MUST be a deterministic function of the referenced
``story_ids`` (each pointing at ``docs/product/stories/{module}/{story_id}.yaml``).

Without enforcement, ``/pm`` updates the capability manually at merge time and
drift is invisible — readers (auditors, eval runners, dashboards) get stale
overview data.

This script reads every capability YAML, looks up each referenced story,
recomputes the four derived fields, and either:

  * ``--check``  → exits 1 if any drift; prints details. Used by pre-commit hook.
  * (default)    → rewrites drifted capability files in place using regex on
                   the frontmatter (preserves comments / key order / blank lines).

Run via ``python scripts/reconcile_capabilities.py [--check] [--repo PATH]``.

Origen
======
Process improvement R32 (2026-05-05). Replaces manual ``/pm`` recalc step in
SDD merge phase with deterministic gate.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

VALID_STORY_STATUS = {"planned", "ratified", "in-progress", "live", "deprecated"}
# `ratified` = spec approved by Chris, not yet built — bucketed with `planned`
# for capability rollup (capability isn't shipping until at least 1 story `live`).
PRE_BUILD_STATUSES = {"planned", "ratified"}


@dataclass
class CapDrift:
    """Drift record for a single capability YAML."""

    path: Path
    diffs: dict[str, tuple[object, object]]  # field → (actual, expected)
    missing_stories: list[str]


class FrontmatterError(ValueError):
    """Raised when a YAML file has malformed or missing frontmatter."""


def load_frontmatter(path: Path) -> dict:
    r"""Parse YAML frontmatter.

    Three layouts supported:
      * Markdown-style: ``---\n<yaml>\n---\n<body>`` (capabilities, modules)
      * Pure YAML with leading marker: ``---\n<yaml>`` (stories — no body, no closer)
      * Comment block + frontmatter: ``# ...\n---\n<yaml>`` (some service stories
        prefix the YAML with header comments documenting eval policy / owners).
    """
    text = path.read_text(encoding="utf-8")

    # Skip leading comment-only lines and blank lines until reaching '---'
    lines = text.splitlines(keepends=True)
    cursor = 0
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped in {"", "\n"}:
            cursor += len(line)
            continue
        break

    body = text[cursor:]
    if not body.startswith("---"):
        raise FrontmatterError(str(path))

    after = body[3:].lstrip("\n")
    yaml_text = after.split("\n---", 1)[0]

    data = yaml.safe_load(yaml_text)
    if not isinstance(data, dict):
        raise FrontmatterError(str(path))
    return data


def derive_status(stories_status: list[str]) -> str:
    """Pure function: capability status from list of story statuses.

    Bucketing:
      * empty / no live → ``planned``
      * all deprecated → ``deprecated``
      * all live (non-deprecated) → ``live``
      * all pre-build (planned/ratified) → ``planned``
      * mixed → ``in-progress``
    """
    if not stories_status:
        return "planned"
    non_deprecated = [s for s in stories_status if s != "deprecated"]
    if not non_deprecated:
        return "deprecated"
    if all(s == "live" for s in non_deprecated):
        return "live"
    if all(s in PRE_BUILD_STATUSES for s in non_deprecated):
        return "planned"
    return "in-progress"


def replace_frontmatter_field(text: str, key: str, value: object) -> str:
    """Replace ``key: <whatever>`` in frontmatter, preserving rest of file.

    Only substitutes the first occurrence (frontmatter) to avoid touching
    body content that might mention the same key in prose.
    """
    pattern = rf"^({re.escape(key)}:)[^\n]*$"
    replacement = f"{key}: {value}"
    return re.sub(pattern, replacement, text, count=1, flags=re.MULTILINE)


def reconcile(repo: Path, *, check_only: bool) -> tuple[int, list[CapDrift]]:
    """Walk capabilities, detect drift, optionally rewrite. Returns (exit_code, drifts)."""
    caps_dir = repo / "docs" / "product" / "capabilities"
    stories_dir = repo / "docs" / "product" / "stories"

    if not caps_dir.exists():
        sys.stderr.write(f"ERROR: {caps_dir} does not exist\n")
        return 2, []

    drifts: list[CapDrift] = []

    for cap_file in sorted(caps_dir.rglob("*.yaml")):
        try:
            cap = load_frontmatter(cap_file)
        except (FrontmatterError, yaml.YAMLError) as exc:
            sys.stderr.write(f"SKIP {cap_file}: {exc}\n")
            continue

        module = cap.get("module")
        story_ids = cap.get("story_ids") or []
        if not module or not story_ids:
            continue

        stories_status: list[str] = []
        missing: list[str] = []
        for sid in story_ids:
            sfile = stories_dir / module / f"{sid}.yaml"
            if not sfile.exists():
                missing.append(sid)
                continue
            try:
                story = load_frontmatter(sfile)
            except (FrontmatterError, yaml.YAMLError):
                missing.append(sid)
                continue
            status = story.get("status", "planned")
            if status not in VALID_STORY_STATUS:
                status = "planned"
            stories_status.append(status)

        expected = {
            "status": derive_status(stories_status),
            "stories_live": sum(1 for s in stories_status if s == "live"),
            "stories_planned": sum(1 for s in stories_status if s in PRE_BUILD_STATUSES),
            "stories_total": len(stories_status),
        }
        actual = {k: cap.get(k) for k in expected}

        diffs = {k: (actual[k], expected[k]) for k in expected if actual[k] != expected[k]}
        if not diffs and not missing:
            continue

        drifts.append(CapDrift(path=cap_file, diffs=diffs, missing_stories=missing))

        if not check_only and diffs:
            text = cap_file.read_text(encoding="utf-8")
            for key, val in expected.items():
                text = replace_frontmatter_field(text, key, val)
            cap_file.write_text(text, encoding="utf-8")

    return 0, drifts


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 on drift without modifying files (CI / pre-commit gate).",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repo root containing docs/product/. Defaults to script's parent.",
    )
    args = parser.parse_args()

    err, drifts = reconcile(args.repo, check_only=args.check)
    if err:
        return err

    if not drifts:
        print("OK — all capabilities consistent with stories.")  # noqa: T201
        return 0

    print(f"DRIFT detected in {len(drifts)} capability file(s):")  # noqa: T201
    for d in drifts:
        rel = d.path.relative_to(args.repo)
        print(f"\n  {rel}")  # noqa: T201
        for key, (actual, expected) in d.diffs.items():
            print(f"    {key}: actual={actual!r} → expected={expected!r}")  # noqa: T201
        if d.missing_stories:
            print(f"    missing story files: {d.missing_stories}")  # noqa: T201

    if args.check:
        print("\nRun without --check to fix in place.")  # noqa: T201
        return 1

    print(f"\nFixed {len(drifts)} file(s).")  # noqa: T201
    return 0


if __name__ == "__main__":
    sys.exit(main())
