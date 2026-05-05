"""Tests for ``scripts/extract_baseline_metrics_from_transcripts.py``.

The script lives at repo root (process tooling, not a backend script), so we
exercise it via subprocess against synthetic Claude Code JSONL transcripts.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "extract_baseline_metrics_from_transcripts.py"


def _make_assistant_event(
    *,
    timestamp: str = "2026-05-04T17:06:00.000Z",
    model: str = "claude-opus-4-7",
    input_tokens: int = 6,
    output_tokens: int = 240,
    cache_read: int = 18000,
    cache_create_5m: int = 0,
    cache_create_1h: int = 50000,
    tool_use_id: str | None = None,
    tool_name: str | None = None,
) -> dict:
    content: list[dict] = [{"type": "text", "text": "ok"}]
    if tool_use_id and tool_name:
        content.append(
            {"type": "tool_use", "id": tool_use_id, "name": tool_name, "input": {}}
        )
    return {
        "type": "assistant",
        "isSidechain": False,
        "timestamp": timestamp,
        "uuid": "u-assistant",
        "sessionId": "fixture-session",
        "message": {
            "model": model,
            "role": "assistant",
            "content": content,
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_read_input_tokens": cache_read,
                "cache_creation_input_tokens": cache_create_5m + cache_create_1h,
                "cache_creation": {
                    "ephemeral_5m_input_tokens": cache_create_5m,
                    "ephemeral_1h_input_tokens": cache_create_1h,
                },
            },
        },
    }


def _make_agent_result_event(
    *,
    timestamp: str = "2026-05-04T17:10:00.000Z",
    tool_use_id: str = "tu-agent-1",
    agent_type: str = "builder-backend",
    total_tokens: int = 305000,
    duration_ms: int = 1561697,
    tool_use_count: int = 133,
    cache_read: int = 302339,
    cache_create_1h: int = 997,
    read_count: int = 28,
    bash_count: int = 77,
    edit_count: int = 28,
    lines_added: int = 1443,
    lines_removed: int = 305,
) -> dict:
    return {
        "type": "user",
        "isSidechain": False,
        "timestamp": timestamp,
        "uuid": "u-user",
        "sessionId": "fixture-session",
        "message": {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": [{"type": "text", "text": "done"}],
                }
            ],
        },
        "toolUseResult": {
            "status": "completed",
            "agentType": agent_type,
            "agentId": "a-fixture",
            "totalTokens": total_tokens,
            "totalDurationMs": duration_ms,
            "totalToolUseCount": tool_use_count,
            "usage": {
                "input_tokens": 1,
                "output_tokens": 1407,
                "cache_read_input_tokens": cache_read,
                "cache_creation_input_tokens": cache_create_1h,
                "cache_creation": {
                    "ephemeral_5m_input_tokens": 0,
                    "ephemeral_1h_input_tokens": cache_create_1h,
                },
            },
            "toolStats": {
                "readCount": read_count,
                "bashCount": bash_count,
                "editFileCount": edit_count,
                "searchCount": 0,
                "linesAdded": lines_added,
                "linesRemoved": lines_removed,
                "otherToolCount": 0,
            },
        },
    }


def _write_transcript(tmp_dir: Path, name: str, events: list[dict]) -> Path:
    path = tmp_dir / f"{name}.jsonl"
    with open(path, "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
    return path


def _run_extractor(transcripts_dir: Path, output_path: Path, **flags: str) -> None:
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--transcripts-dir",
        str(transcripts_dir),
        "--output",
        str(output_path),
    ]
    for k, v in flags.items():
        cmd.extend([f"--{k.replace('_', '-')}", v])
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert result.returncode == 0, f"script failed: {result.stderr}"


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_extracts_main_session_metrics(tmp_path: Path) -> None:
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    output = tmp_path / "out.jsonl"
    _write_transcript(
        transcripts_dir,
        "session-A",
        [_make_assistant_event(input_tokens=6, output_tokens=240, cache_read=18000)],
    )
    _run_extractor(transcripts_dir, output)

    rows = _read_jsonl(output)
    assert len(rows) == 1
    row = rows[0]
    assert row["run_type"] == "main"
    assert row["agent_type"] == "main"
    assert row["session_id"] == "session-A"
    assert row["model"] == "claude-opus-4-7"
    assert row["input_tokens"] == 6
    assert row["output_tokens"] == 240
    assert row["cache_read_tokens"] == 18000
    assert row["cache_creation_1h_tokens"] == 50000
    assert row["stop_reason"] == "end_turn"


def test_extracts_subagent_metrics_with_tool_stats(tmp_path: Path) -> None:
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    output = tmp_path / "out.jsonl"
    _write_transcript(
        transcripts_dir,
        "session-B",
        [
            _make_assistant_event(tool_use_id="tu-1", tool_name="Agent"),
            _make_agent_result_event(tool_use_id="tu-1", agent_type="builder-backend"),
        ],
    )
    _run_extractor(transcripts_dir, output)

    rows = _read_jsonl(output)
    assert len(rows) == 2  # main turn + subagent run
    sub = next(r for r in rows if r["run_type"] == "subagent")
    assert sub["agent_type"] == "builder-backend"
    assert sub["total_tokens"] == 305000
    assert sub["duration_ms"] == 1561697
    assert sub["tool_use_count"] == 133
    assert sub["read_count"] == 28
    assert sub["bash_count"] == 77
    assert sub["edit_count"] == 28
    assert sub["lines_added"] == 1443
    assert sub["lines_removed"] == 305
    assert sub["tool_use_id"] == "tu-1"


def test_filters_by_date_range(tmp_path: Path) -> None:
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    output = tmp_path / "out.jsonl"
    _write_transcript(
        transcripts_dir,
        "session-mixed",
        [
            _make_assistant_event(timestamp="2026-04-01T12:00:00Z", input_tokens=1),
            _make_assistant_event(timestamp="2026-05-04T12:00:00Z", input_tokens=2),
            _make_assistant_event(timestamp="2026-06-01T12:00:00Z", input_tokens=3),
        ],
    )
    _run_extractor(
        transcripts_dir,
        output,
        since="2026-05-01",
        until="2026-05-31",
    )

    rows = _read_jsonl(output)
    assert len(rows) == 1
    assert rows[0]["input_tokens"] == 2


def test_handles_malformed_lines(tmp_path: Path) -> None:
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    output = tmp_path / "out.jsonl"
    path = transcripts_dir / "session-broken.jsonl"
    with open(path, "w") as f:
        f.write("not json at all\n")
        f.write(json.dumps(_make_assistant_event(input_tokens=42)) + "\n")
        f.write("{partial\n")
    _run_extractor(transcripts_dir, output)

    rows = _read_jsonl(output)
    assert len(rows) == 1
    assert rows[0]["input_tokens"] == 42


def test_skips_user_results_without_agent_metadata(tmp_path: Path) -> None:
    """Bash tool_results have ``toolUseResult`` shape but no ``agentType`` —
    extractor must NOT emit a row for them.
    """
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    output = tmp_path / "out.jsonl"
    bash_result = {
        "type": "user",
        "timestamp": "2026-05-04T18:00:00Z",
        "sessionId": "session-bash",
        "message": {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": "tu-bash", "content": "stdout"}
            ],
        },
        "toolUseResult": {
            "stdout": "ok",
            "stderr": "",
            "interrupted": False,
            "isImage": False,
            "noOutputExpected": False,
        },
    }
    _write_transcript(transcripts_dir, "session-bash", [bash_result])
    _run_extractor(transcripts_dir, output)

    rows = _read_jsonl(output)
    assert rows == []


def test_summary_only_skips_output_write(tmp_path: Path) -> None:
    transcripts_dir = tmp_path / "transcripts"
    transcripts_dir.mkdir()
    output = tmp_path / "out.jsonl"
    _write_transcript(transcripts_dir, "session-S", [_make_assistant_event()])

    cmd = [
        sys.executable,
        str(SCRIPT),
        "--transcripts-dir",
        str(transcripts_dir),
        "--output",
        str(output),
        "--summary-only",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert not output.exists()
    assert "Summary by agent_type" in result.stderr
