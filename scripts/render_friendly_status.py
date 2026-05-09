#!/usr/bin/env python3
"""Render friendly /pm status output from BACKLOG.yaml.

Origen: 2026-05-09 G8 cost-routing. /pm "estado/panorama/qué tenemos"
preguntas frecuentes — Opus formatear es waste. Este script hace
template-fill desde BACKLOG.yaml deterministico, sin LLM.

Output spec: matches `pm` SKILL.md "Friendly backlog status" canonical
template. /pm SKILL.md "estado" → invoca este script en lugar de Opus.

Run:
  backend/.venv/bin/python scripts/render_friendly_status.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

CAPS = {
    "refining": 3,
    "refined": 5,
    "ready": 5,
    "developing": 3,
    "developed": 10,
    "reviewing": 2,
}

EMOJI = {
    "idea": "💡",
    "refining": "🔬",
    "refined": "✅",
    "ready": "📦",
    "developing": "🔨",
    "developed": "🧪",
    "reviewing": "🔍",
    "done": "🚢",
    "parked": "🅿",
    "dropped": "🛑",
}

LABEL = {
    "idea": "Ideas",
    "refining": "Refinando",
    "refined": "Refinadas — listas para arquitectos",
    "ready": "Ready for development",
    "developing": "Developing",
    "developed": "Developed — esperando QA",
    "reviewing": "Reviewing",
    "done": "Recently shipped",
    "parked": "Parked",
    "dropped": "Dropped",
}


def _eligible(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Cap-eligible: kind=story, no legacy:* tag (forward-only enforcement)."""
    return [
        it
        for it in items
        if it.get("kind") == "story"
        and not any(t.startswith("legacy:") for t in it.get("tags", []))
    ]


def _format_item(it: dict[str, Any]) -> str:
    iid = it.get("id", "?")
    state = it.get("state", "?")
    extra = ""
    if it.get("kind") == "outcome":
        extra = " (outcome)"
    elif any(t.startswith("legacy:") for t in it.get("tags", [])):
        extra = " (legacy)"
    return f"- {iid}{extra}"


def render(backlog: dict[str, Any]) -> str:
    """Render friendly grouped output."""
    buckets = backlog.get("buckets", {})
    out: list[str] = []

    states_active = ["idea", "refining", "refined", "ready", "developing", "developed", "reviewing"]
    bottleneck = None

    for state in states_active:
        items = buckets.get(state, [])
        eligible = _eligible(items) if state in CAPS else items
        cap = CAPS.get(state)
        cap_str = f" / cap {cap}" if cap else ""
        warn = ""
        if cap is not None:
            n_eligible = len(eligible)
            if n_eligible > cap:
                warn = f" ⚠️ ({n_eligible - cap} sobre cap, excl. legacy)"
            elif n_eligible == cap:
                bottleneck = state

        emoji = EMOJI[state]
        label = LABEL[state]
        out.append(f"\n## {emoji} {label} ({len(items)}{cap_str}{warn})")
        if not items:
            out.append("- _(none)_")
        else:
            for it in items[:10]:  # cap display 10 per state
                out.append(_format_item(it))
            if len(items) > 10:
                out.append(f"- _(+{len(items) - 10} more — read BACKLOG.md for full list)_")

    # Recently shipped (last 90d)
    done = buckets.get("done", [])
    if done:
        out.append(f"\n## 🚢 Recently shipped (last 90d, {len(done)})")
        for it in done[:5]:
            out.append(_format_item(it))
        if len(done) > 5:
            out.append(f"- _(+{len(done) - 5} more)_")

    # Parked + Dropped (compact)
    parked = buckets.get("parked", [])
    dropped = buckets.get("dropped", [])
    if parked or dropped:
        out.append(f"\n## 🅿 Parked ({len(parked)}) · 🛑 Dropped ({len(dropped)})")
        for it in parked[:3]:
            out.append(f"- 🅿 {it.get('id')}")
        for it in dropped[:3]:
            out.append(f"- 🛑 ~~{it.get('id')}~~")

    # Bottleneck warning
    if bottleneck:
        out.append(f"\n**Próximo cuello de botella:** `{bottleneck}` está al cap.")

    # Warnings from backlog
    warns = backlog.get("warnings", [])
    if warns:
        out.append(f"\n⚠ Warnings ({len(warns)}):")
        for w in warns[:3]:
            out.append(f"- {w}")

    return "\n".join(out).lstrip("\n") + "\n"


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repo root (default: script's parent).",
    )
    args = parser.parse_args()

    backlog_path = args.repo / "docs" / "product" / "BACKLOG.yaml"
    if not backlog_path.exists():
        print("ERROR — docs/product/BACKLOG.yaml missing. Run scripts/generate_backlog.py first.", file=sys.stderr)  # noqa: T201
        return 1

    backlog = yaml.safe_load(backlog_path.read_text(encoding="utf-8"))
    if not backlog:
        print("ERROR — BACKLOG.yaml empty or invalid.", file=sys.stderr)  # noqa: T201
        return 1

    print(render(backlog))  # noqa: T201
    return 0


if __name__ == "__main__":
    sys.exit(main())
