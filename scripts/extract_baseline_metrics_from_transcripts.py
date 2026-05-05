#!/usr/bin/env python3
"""Extract baseline process-pipeline metrics from Claude Code transcripts.

Origen: process-improvement A2 (2026-05-05). Captura datos pre-R1-R9 ROI medible.

Reads JSONL transcripts in ~/.claude/projects/-home-chris-AISALESHT/ and emits
one JSONL row per agent run (main session turn OR subagent invocation) with
tokens, cache breakdown, tool counts, duration, and LOC delta.

Output schema:
    {
        "ts": "2026-05-04T17:06:00Z",
        "session_id": "8fca7a7e-...",
        "run_type": "main" | "subagent",
        "agent_type": "main" | "builder-backend" | "auditor-backend" | ...,
        "model": "claude-opus-4-7",
        "input_tokens": int,
        "output_tokens": int,
        "cache_read_tokens": int,
        "cache_creation_5m_tokens": int,
        "cache_creation_1h_tokens": int,
        "total_tokens": int,           # subagent only (sum from message)
        "duration_ms": int,            # subagent only
        "tool_use_count": int,         # subagent only
        "read_count": int,             # subagent only
        "bash_count": int,             # subagent only
        "edit_count": int,             # subagent only
        "lines_added": int,            # subagent only
        "lines_removed": int           # subagent only
    }

Usage:
    ./scripts/extract_baseline_metrics_from_transcripts.py \\
        --since 2026-04-29 --until 2026-05-05 \\
        --output docs/process/metrics/baseline-pre-R1-R9.jsonl

If --since/--until omitted, processes ALL transcripts.
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import sys
from pathlib import Path

DEFAULT_TRANSCRIPTS_DIR = os.path.expanduser("~/.claude/projects/-home-chris-AISALESHT")


def parse_iso(s: str) -> dt.datetime | None:
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return dt.datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def in_range(
    ts: dt.datetime | None, since: dt.datetime | None, until: dt.datetime | None
) -> bool:
    if ts is None:
        return True  # keep if unknown — let downstream filter
    if since and ts < since:
        return False
    if until and ts > until:
        return False
    return True


def extract_main_assistant_metrics(o: dict, session_id: str) -> dict | None:
    """Pull metrics from a main-session `assistant` message."""
    msg = o.get("message", {})
    if not isinstance(msg, dict):
        return None
    usage = msg.get("usage", {})
    if not isinstance(usage, dict):
        return None
    cache_creation = usage.get("cache_creation", {}) or {}
    return {
        "ts": o.get("timestamp"),
        "session_id": session_id,
        "run_type": "main",
        "agent_type": "main",
        "model": msg.get("model"),
        "input_tokens": int(usage.get("input_tokens") or 0),
        "output_tokens": int(usage.get("output_tokens") or 0),
        "cache_read_tokens": int(usage.get("cache_read_input_tokens") or 0),
        "cache_creation_5m_tokens": int(
            cache_creation.get("ephemeral_5m_input_tokens") or 0
        ),
        "cache_creation_1h_tokens": int(
            cache_creation.get("ephemeral_1h_input_tokens") or 0
        ),
        "stop_reason": msg.get("stop_reason"),
    }


def extract_subagent_metrics(
    tur: dict, ts: str, session_id: str, agent_use_id: str | None
) -> dict | None:
    """Pull metrics from an Agent tool_result `toolUseResult`."""
    if not isinstance(tur, dict):
        return None
    if "agentType" not in tur or "totalTokens" not in tur:
        return None
    usage = tur.get("usage", {}) or {}
    cache_creation = usage.get("cache_creation", {}) or {}
    tool_stats = tur.get("toolStats", {}) or {}
    return {
        "ts": ts,
        "session_id": session_id,
        "run_type": "subagent",
        "agent_type": tur.get("agentType"),
        "agent_id": tur.get("agentId"),
        "tool_use_id": agent_use_id,
        "model": None,  # subagent results don't expose model directly
        "status": tur.get("status"),
        "input_tokens": int(usage.get("input_tokens") or 0),
        "output_tokens": int(usage.get("output_tokens") or 0),
        "cache_read_tokens": int(usage.get("cache_read_input_tokens") or 0),
        "cache_creation_5m_tokens": int(
            cache_creation.get("ephemeral_5m_input_tokens") or 0
        ),
        "cache_creation_1h_tokens": int(
            cache_creation.get("ephemeral_1h_input_tokens") or 0
        ),
        "total_tokens": int(tur.get("totalTokens") or 0),
        "duration_ms": int(tur.get("totalDurationMs") or 0),
        "tool_use_count": int(tur.get("totalToolUseCount") or 0),
        "read_count": int(tool_stats.get("readCount") or 0),
        "bash_count": int(tool_stats.get("bashCount") or 0),
        "edit_count": int(tool_stats.get("editFileCount") or 0),
        "search_count": int(tool_stats.get("searchCount") or 0),
        "lines_added": int(tool_stats.get("linesAdded") or 0),
        "lines_removed": int(tool_stats.get("linesRemoved") or 0),
    }


def process_transcript(
    path: str, since: dt.datetime | None, until: dt.datetime | None
) -> list[dict]:
    """Walk one JSONL transcript, return list of metric rows."""
    session_id = Path(path).stem
    rows: list[dict] = []
    # Build map: tool_use_id -> ts when Agent tool_use was emitted
    agent_use_ts: dict[str, str] = {}
    try:
        with open(path) as fh:
            for line in fh:
                try:
                    o = json.loads(line)
                except json.JSONDecodeError:
                    continue
                t = o.get("type")
                if t == "assistant":
                    if o.get("isSidechain"):
                        # Sidechain entries (rare in current Claude Code) — already
                        # accounted for via toolUseResult of parent; skip dup.
                        continue
                    ts = o.get("timestamp")
                    # Capture Agent tool_use timestamps for matching with results.
                    msg = o.get("message", {}) or {}
                    content = msg.get("content")
                    if isinstance(content, list):
                        for c in content:
                            if not isinstance(c, dict):
                                continue
                            if c.get("type") == "tool_use" and c.get("name") == "Agent":
                                use_id = c.get("id")
                                if use_id:
                                    agent_use_ts[use_id] = ts
                    # Main-session assistant metrics (one per turn).
                    row = extract_main_assistant_metrics(o, session_id)
                    if row and in_range(parse_iso(row.get("ts") or ""), since, until):
                        rows.append(row)
                elif t == "user":
                    msg = o.get("message", {}) or {}
                    content = msg.get("content")
                    if not isinstance(content, list):
                        continue
                    for c in content:
                        if not isinstance(c, dict):
                            continue
                        if c.get("type") != "tool_result":
                            continue
                        tur = o.get("toolUseResult")
                        if not isinstance(tur, dict):
                            continue
                        if "agentType" not in tur:
                            continue
                        use_id = c.get("tool_use_id")
                        ts = agent_use_ts.get(use_id) or o.get("timestamp")
                        row = extract_subagent_metrics(tur, ts, session_id, use_id)
                        if row and in_range(
                            parse_iso(row.get("ts") or ""), since, until
                        ):
                            rows.append(row)
    except OSError as e:
        print(f"[warn] could not read {path}: {e}", file=sys.stderr)
    return rows


def aggregate_summary(rows: list[dict]) -> dict:
    """Compute summary stats for stdout reporting."""
    by_type: dict[str, dict] = {}
    for r in rows:
        agent = r.get("agent_type") or "unknown"
        b = by_type.setdefault(
            agent,
            {
                "count": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_read_tokens": 0,
                "cache_creation_5m_tokens": 0,
                "cache_creation_1h_tokens": 0,
                "total_tokens": 0,
                "duration_ms": 0,
                "tool_use_count": 0,
            },
        )
        b["count"] += 1
        for k in (
            "input_tokens",
            "output_tokens",
            "cache_read_tokens",
            "cache_creation_5m_tokens",
            "cache_creation_1h_tokens",
            "total_tokens",
            "duration_ms",
            "tool_use_count",
        ):
            b[k] += int(r.get(k) or 0)
    return by_type


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument(
        "--transcripts-dir",
        default=DEFAULT_TRANSCRIPTS_DIR,
        help=f"Directory of *.jsonl transcripts (default: {DEFAULT_TRANSCRIPTS_DIR})",
    )
    ap.add_argument("--since", help="ISO date (YYYY-MM-DD) lower bound", default=None)
    ap.add_argument("--until", help="ISO date (YYYY-MM-DD) upper bound", default=None)
    ap.add_argument(
        "--output",
        default="docs/process/metrics/baseline-pre-R1-R9.jsonl",
        help="Output JSONL path",
    )
    ap.add_argument(
        "--summary-only", action="store_true", help="Print summary only, no JSONL"
    )
    args = ap.parse_args()

    since = parse_iso(args.since + "T00:00:00Z") if args.since else None
    until = parse_iso(args.until + "T23:59:59Z") if args.until else None

    transcripts = sorted(glob.glob(os.path.join(args.transcripts_dir, "*.jsonl")))
    print(
        f"[info] scanning {len(transcripts)} transcripts in {args.transcripts_dir}",
        file=sys.stderr,
    )
    if since:
        print(f"[info] since: {since.isoformat()}", file=sys.stderr)
    if until:
        print(f"[info] until: {until.isoformat()}", file=sys.stderr)

    all_rows: list[dict] = []
    for t in transcripts:
        # Cheap mtime filter to skip clearly out-of-range files.
        try:
            mtime = dt.datetime.fromtimestamp(os.path.getmtime(t), tz=dt.timezone.utc)
        except OSError:
            continue
        if until and mtime < (since or dt.datetime.min.replace(tzinfo=dt.timezone.utc)):
            continue
        rows = process_transcript(t, since, until)
        all_rows.extend(rows)

    print(f"[info] extracted {len(all_rows)} metric rows", file=sys.stderr)

    if not args.summary_only:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w") as fh:
            for r in all_rows:
                fh.write(json.dumps(r, separators=(",", ":")) + "\n")
        print(f"[info] wrote {out}", file=sys.stderr)

    summary = aggregate_summary(all_rows)
    print("\n# Summary by agent_type", file=sys.stderr)
    print(
        f"{'agent_type':<25} {'count':>6} {'tokens_total':>14} "
        f"{'cache_read':>12} {'duration_s':>11} {'tools':>7}",
        file=sys.stderr,
    )
    for agent, b in sorted(summary.items(), key=lambda x: -x[1]["count"]):
        tok = b["total_tokens"] or (
            b["input_tokens"]
            + b["output_tokens"]
            + b["cache_read_tokens"]
            + b["cache_creation_5m_tokens"]
            + b["cache_creation_1h_tokens"]
        )
        print(
            f"{agent:<25} {b['count']:>6} {tok:>14,} "
            f"{b['cache_read_tokens']:>12,} "
            f"{b['duration_ms'] / 1000:>11.0f} {b['tool_use_count']:>7}",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
