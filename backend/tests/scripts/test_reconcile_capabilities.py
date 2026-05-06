"""Tests for ``scripts/reconcile_capabilities.py`` (R32).

Each test builds a throwaway ``docs/product/{capabilities,stories}/`` tree
under ``tmp_path`` and invokes the script via subprocess with
``--repo tmp_path``. Asserts on exit code + stdout + post-fix file content.

The script is path-rooted at ``--repo`` arg, so isolation is trivial — no
fixture surgery needed.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "reconcile_capabilities.py"


def _write_cap(
    repo: Path,
    module: str,
    cap_id: str,
    *,
    story_ids: list[str],
    status: str,
    live: int,
    planned: int,
    total: int,
) -> Path:
    path = repo / "docs" / "product" / "capabilities" / module / f"{cap_id}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = dedent(
        f"""\
        ---
        id: {cap_id}
        name: "test cap"
        module: {module}
        status: {status}
        stories_live: {live}
        stories_planned: {planned}
        stories_total: {total}
        story_ids:
        """
    )
    for sid in story_ids:
        body += f"  - {sid}\n"
    body += "---\n\nbody prose\n"
    path.write_text(body, encoding="utf-8")
    return path


def _write_story(repo: Path, module: str, story_id: str, status: str, *, with_comments: bool = False) -> Path:
    path = repo / "docs" / "product" / "stories" / module / f"{story_id}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    prefix = "# Header comment\n# Another comment\n\n" if with_comments else ""
    path.write_text(
        f"{prefix}---\nid: {story_id}\nstatus: {status}\nmodule: {module}\n",
        encoding="utf-8",
    )
    return path


def _run(repo: Path, *, check: bool = False) -> subprocess.CompletedProcess:
    args = [sys.executable, str(SCRIPT), "--repo", str(repo)]
    if check:
        args.append("--check")
    return subprocess.run(args, capture_output=True, text=True, check=False)  # noqa: S603


def test_no_drift_returns_ok(tmp_path: Path) -> None:
    _write_story(tmp_path, "foo", "s1", "live")
    _write_story(tmp_path, "foo", "s2", "live")
    _write_cap(tmp_path, "foo", "c1", story_ids=["s1", "s2"], status="live", live=2, planned=0, total=2)

    result = _run(tmp_path, check=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout


def test_drift_check_exits_1_no_write(tmp_path: Path) -> None:
    _write_story(tmp_path, "foo", "s1", "live")
    _write_story(tmp_path, "foo", "s2", "planned")
    cap = _write_cap(tmp_path, "foo", "c1", story_ids=["s1", "s2"], status="live", live=2, planned=0, total=2)
    before = cap.read_text()

    result = _run(tmp_path, check=True)
    assert result.returncode == 1, result.stdout
    assert "DRIFT" in result.stdout
    assert "in-progress" in result.stdout
    assert cap.read_text() == before, "check mode must not modify files"


def test_fix_mode_rewrites_status_and_counts(tmp_path: Path) -> None:
    _write_story(tmp_path, "foo", "s1", "live")
    _write_story(tmp_path, "foo", "s2", "planned")
    cap = _write_cap(tmp_path, "foo", "c1", story_ids=["s1", "s2"], status="live", live=2, planned=0, total=2)

    result = _run(tmp_path, check=False)
    assert result.returncode == 0, result.stdout

    text = cap.read_text()
    assert "status: in-progress" in text
    assert "stories_live: 1" in text
    assert "stories_planned: 1" in text
    assert "stories_total: 2" in text


def test_all_planned_derives_planned(tmp_path: Path) -> None:
    _write_story(tmp_path, "bar", "s1", "planned")
    _write_story(tmp_path, "bar", "s2", "planned")
    cap = _write_cap(tmp_path, "bar", "c1", story_ids=["s1", "s2"], status="live", live=2, planned=0, total=2)

    _run(tmp_path)
    text = cap.read_text()
    assert "status: planned" in text
    assert "stories_live: 0" in text
    assert "stories_planned: 2" in text


def test_ratified_treated_as_pre_build(tmp_path: Path) -> None:
    _write_story(tmp_path, "x", "s1", "ratified")
    _write_story(tmp_path, "x", "s2", "ratified")
    cap = _write_cap(tmp_path, "x", "c1", story_ids=["s1", "s2"], status="live", live=0, planned=0, total=0)

    _run(tmp_path)
    text = cap.read_text()
    assert "status: planned" in text
    assert "stories_planned: 2" in text


def test_mixed_live_and_ratified_is_in_progress(tmp_path: Path) -> None:
    _write_story(tmp_path, "x", "s1", "live")
    _write_story(tmp_path, "x", "s2", "ratified")
    cap = _write_cap(tmp_path, "x", "c1", story_ids=["s1", "s2"], status="live", live=2, planned=0, total=2)

    _run(tmp_path)
    text = cap.read_text()
    assert "status: in-progress" in text
    assert "stories_live: 1" in text
    assert "stories_planned: 1" in text


def test_all_deprecated_derives_deprecated(tmp_path: Path) -> None:
    _write_story(tmp_path, "x", "s1", "deprecated")
    cap = _write_cap(tmp_path, "x", "c1", story_ids=["s1"], status="live", live=1, planned=0, total=1)

    _run(tmp_path)
    text = cap.read_text()
    assert "status: deprecated" in text


def test_missing_story_file_reported_in_check(tmp_path: Path) -> None:
    _write_story(tmp_path, "z", "s1", "live")
    _write_cap(tmp_path, "z", "c1", story_ids=["s1", "s_ghost"], status="live", live=1, planned=0, total=2)

    result = _run(tmp_path, check=True)
    assert result.returncode == 1
    assert "s_ghost" in result.stdout


def test_story_with_leading_comment_block_parses(tmp_path: Path) -> None:
    _write_story(tmp_path, "y", "s1", "live", with_comments=True)
    cap = _write_cap(tmp_path, "y", "c1", story_ids=["s1"], status="planned", live=0, planned=1, total=1)

    _run(tmp_path)
    text = cap.read_text()
    assert "status: live" in text


def test_empty_story_ids_skips_capability(tmp_path: Path) -> None:
    cap_path = tmp_path / "docs" / "product" / "capabilities" / "q" / "c_empty.yaml"
    cap_path.parent.mkdir(parents=True)
    cap_path.write_text(
        dedent(
            """\
            ---
            id: c_empty
            module: q
            status: planned
            story_ids: []
            ---
            """
        )
    )
    result = _run(tmp_path, check=True)
    assert result.returncode == 0


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        (["live", "live", "live"], "live"),
        (["planned", "planned"], "planned"),
        (["ratified", "ratified"], "planned"),
        (["live", "planned"], "in-progress"),
        (["live", "in-progress"], "in-progress"),
        (["deprecated", "deprecated"], "deprecated"),
        (["live", "deprecated"], "live"),
        ([], "planned"),
    ],
)
def test_derive_status_table(statuses: list[str], expected: str) -> None:
    """Direct unit test of pure function — bypass subprocess for exhaustive table."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    try:
        from reconcile_capabilities import derive_status
    finally:
        sys.path.pop(0)
    assert derive_status(statuses) == expected
