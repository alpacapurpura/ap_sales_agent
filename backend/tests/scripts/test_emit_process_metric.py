"""Tests for ``scripts/emit_process_metric.py`` (R12 layer 1 emitter)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "emit_process_metric.py"


def _run(output: Path, **flags: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(SCRIPT), "--output", str(output)]
    for k, v in flags.items():
        cmd.extend([f"--{k.replace('_', '-')}", str(v)])
    return subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603 — fixed-cmd subprocess for fixture-driven test


def test_appends_record_with_required_fields(tmp_path: Path) -> None:
    out = tmp_path / "runs.jsonl"
    result = _run(out, ticket="T-1", phase="build")
    assert result.returncode == 0, result.stderr
    lines = out.read_text().splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["ticket"] == "T-1"
    assert rec["phase"] == "build"
    assert rec["iter"] == 1
    assert rec["pi"] is None  # optional, not provided
    assert rec["ts"].endswith("Z")


def test_appends_multiple_records_in_order(tmp_path: Path) -> None:
    out = tmp_path / "runs.jsonl"
    _run(out, ticket="T-1", phase="build", verdict="tests-passing")
    _run(out, ticket="T-1", phase="audit", verdict="APPROVED")
    lines = out.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["phase"] == "build"
    assert json.loads(lines[1])["phase"] == "audit"


def test_full_payload_with_all_fields(tmp_path: Path) -> None:
    out = tmp_path / "runs.jsonl"
    result = _run(
        out,
        pi="PI-12",
        sprint="S1-eval-runner",
        story="sales-agent-litellm-canonicalization",
        ticket="T-1",
        phase="build",
        agent_type="builder-backend",
        verdict="pushed",
        commit_sha="5856be4d",
        duration_ms="1561697",
        total_tokens="304744",
        tool_use_count="133",
        iter="1",
    )
    assert result.returncode == 0, result.stderr
    rec = json.loads(out.read_text().strip())
    assert rec["pi"] == "PI-12"
    assert rec["sprint"] == "S1-eval-runner"
    assert rec["story"] == "sales-agent-litellm-canonicalization"
    assert rec["ticket"] == "T-1"
    assert rec["agent_type"] == "builder-backend"
    assert rec["commit_sha"] == "5856be4d"
    assert rec["duration_ms"] == 1561697
    assert rec["total_tokens"] == 304744
    assert rec["tool_use_count"] == 133


def test_rejects_invalid_phase(tmp_path: Path) -> None:
    out = tmp_path / "runs.jsonl"
    result = _run(out, ticket="T-1", phase="not-a-real-phase")
    assert result.returncode != 0
    assert "invalid choice" in result.stderr or "argument" in result.stderr


def test_creates_parent_directory(tmp_path: Path) -> None:
    out = tmp_path / "deep" / "nested" / "runs.jsonl"
    result = _run(out, ticket="T-1", phase="build")
    assert result.returncode == 0
    assert out.exists()
    assert json.loads(out.read_text().strip())["ticket"] == "T-1"


def test_truncates_long_note(tmp_path: Path) -> None:
    out = tmp_path / "runs.jsonl"
    long_note = "x" * 500
    result = _run(out, ticket="T-1", phase="build", note=long_note)
    assert result.returncode == 0
    rec = json.loads(out.read_text().strip())
    assert rec["note"] is not None
    assert len(rec["note"]) == 200
