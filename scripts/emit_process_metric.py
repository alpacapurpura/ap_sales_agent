#!/usr/bin/env python3
"""Emit a single metric event to ``docs/process/metrics/runs.jsonl``.

R12 layer 1 — orchestrators (`/dev-team`, `/auditor`) call this after each
agent run to append a summary row. Token-level detail (input/output/cache
breakdown per subagent) is harvested post-hoc by
``scripts/extract_baseline_metrics_from_transcripts.py`` from the session
JSONL transcript; this script captures the orchestrator-level metadata
(ticket, verdict, commit_sha, phase) that is NOT in the transcript.

Usage:
    ./scripts/emit_process_metric.py \\
        --pi PI-12 --sprint S1-eval-runner --story T-1-bis \\
        --ticket T-1-bis --phase build \\
        --agent-type builder-backend \\
        --verdict tests-passing \\
        --commit-sha 5856be4d \\
        --duration-ms 1561697 \\
        --total-tokens 304744 \\
        --tool-use-count 133

All --* fields are optional except --ticket and --phase. Missing fields
serialize to null. Output schema is forward-compatible with
``baseline-pre-R1-R9.jsonl`` so consumers can union both sets.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "process" / "metrics" / "runs.jsonl"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--pi", default=None, help="PI id, e.g. PI-12")
    ap.add_argument("--sprint", default=None, help="Sprint id, e.g. S1-eval-runner")
    ap.add_argument("--story", default=None, help="Story id (folder name)")
    ap.add_argument("--ticket", required=True, help="Ticket id, e.g. T-1 or T-1.bis")
    ap.add_argument(
        "--phase",
        required=True,
        choices=["po", "architect", "build", "audit", "context-build", "gate-run"],
        help="Pipeline phase",
    )
    ap.add_argument("--agent-type", default=None, help="Subagent type")
    ap.add_argument(
        "--verdict",
        default=None,
        help="ready|building|tests-failing|tests-passing|pushed|APPROVED|CHANGES_REQUESTED|ESCALATED|FAIL|PASS|WARN",
    )
    ap.add_argument("--commit-sha", default=None, help="git commit SHA (short or full)")
    ap.add_argument(
        "--duration-ms", type=int, default=None, help="Wall-clock duration ms"
    )
    ap.add_argument(
        "--total-tokens", type=int, default=None, help="Sum tokens this agent run"
    )
    ap.add_argument(
        "--tool-use-count", type=int, default=None, help="Tool calls during agent run"
    )
    ap.add_argument("--iter", type=int, default=1, help="Iteration index (1-based)")
    ap.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"Output JSONL path (default: {DEFAULT_OUTPUT})",
    )
    ap.add_argument(
        "--note", default=None, help="Free-text note (truncated to 200 chars in output)"
    )
    args = ap.parse_args()

    record = {
        "ts": dt.datetime.now(tz=dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "pi": args.pi,
        "sprint": args.sprint,
        "story": args.story,
        "ticket": args.ticket,
        "phase": args.phase,
        "iter": args.iter,
        "agent_type": args.agent_type,
        "verdict": args.verdict,
        "commit_sha": args.commit_sha,
        "duration_ms": args.duration_ms,
        "total_tokens": args.total_tokens,
        "tool_use_count": args.tool_use_count,
        "note": (args.note or "")[:200] or None,
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a") as f:
        f.write(json.dumps(record, separators=(",", ":")) + "\n")
    print(
        f"[emit_process_metric] appended {args.phase}/{args.ticket} → {out}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
