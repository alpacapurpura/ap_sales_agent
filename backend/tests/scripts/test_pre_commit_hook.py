"""Tests for ``scripts/git-hooks/pre-commit`` (R4 voseo + R4 ruff + C1 R3 SSoT).

Each test creates a throwaway git repo, copies the hook + the SSoT tabla
+ the backend venv symlink, stages various scenarios, and runs the hook
via subprocess. Asserts on exit code + stderr.

The hook is bash-only — no python-import path. Subprocess is the only way
to test it end-to-end.

# voseo-allowed: this test fixture intentionally contains voseo strings
# to verify the hook detects + blocks them. The voseo regex match here is
# a deliberate test input, not a real user-facing string.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK = REPO_ROOT / "scripts" / "git-hooks" / "pre-commit"
SSOT_TABLE = REPO_ROOT / ".claude" / "rules" / "auditor-downstream-regression.md"


@pytest.fixture
def fixture_repo(tmp_path: Path) -> Path:
    """Bootstrap a minimal git repo wired with hook + SSoT tabla + venv symlink."""
    repo = tmp_path / "repo"
    repo.mkdir()

    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)  # noqa: S607
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)  # noqa: S607
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo, check=True)  # noqa: S607
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init", "-q"], cwd=repo, check=True)  # noqa: S607

    # Wire hook
    hooks_dir = repo / ".git" / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    target = hooks_dir / "pre-commit"
    shutil.copy(HOOK, target)
    target.chmod(0o755)

    # Wire SSoT tabla (the hook reads it from .claude/rules/...)
    rules_dir = repo / ".claude" / "rules"
    rules_dir.mkdir(parents=True)
    shutil.copy(SSOT_TABLE, rules_dir / "auditor-downstream-regression.md")

    # Wire backend venv ruff symlink + pyproject.toml so hook can lint with
    # the 120-char line-length config (otherwise ruff defaults to 88 and
    # rejects valid project code).
    backend = repo / "backend"
    backend.mkdir()
    venv_bin = backend / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    real_ruff = REPO_ROOT / "backend" / ".venv" / "bin" / "ruff"
    if real_ruff.exists():
        (venv_bin / "ruff").symlink_to(real_ruff)
    real_pyproject = REPO_ROOT / "backend" / "pyproject.toml"
    if real_pyproject.exists():
        shutil.copy(real_pyproject, backend / "pyproject.toml")

    return repo


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)  # noqa: S603, S607


def _commit(cwd: Path, msg: str = "test") -> subprocess.CompletedProcess:
    return _git("commit", "-m", msg, cwd=cwd)


def _create_module_file(repo_root: Path, rel_path: str, content: str) -> Path:
    """Create a Python file under repo_root + parent __init__.py chain.

    Real backend/src/ dirs all have __init__.py. Test fixtures need the same
    or ruff flags every fixture file as implicit-namespace package (INP001).
    """
    file_path = repo_root / rel_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    # Walk parents back to repo_root/backend, ensure __init__.py present.
    rel_dirs = file_path.parent.relative_to(repo_root / "backend")
    cur = repo_root / "backend"
    for part in rel_dirs.parts:
        cur = cur / part
        init = cur / "__init__.py"
        if not init.exists():
            init.write_text("")
    return file_path


def test_clean_python_passes(fixture_repo: Path) -> None:
    f = _create_module_file(fixture_repo, "backend/src/shared/events/ok.py", '"""Clean module."""\n\nx = 1\n')
    _git("add", str(f.relative_to(fixture_repo)), cwd=fixture_repo)
    result = _commit(fixture_repo, "feat: ok")
    assert result.returncode == 0, f"unexpected fail: {result.stderr}"


def test_voseo_in_python_string_blocks(fixture_repo: Path) -> None:
    f = _create_module_file(
        fixture_repo,
        "backend/src/shared/events/voseo.py",
        'msg = "Tenés que activar el toggle"\n',
    )
    _git("add", str(f.relative_to(fixture_repo)), cwd=fixture_repo)
    result = _commit(fixture_repo, "feat: voseo")
    assert result.returncode == 1
    assert "voseo detected" in result.stdout.lower() + result.stderr.lower()


def test_ruff_violation_blocks_via_staged_content(fixture_repo: Path) -> None:
    """The hook must check STAGED content, not working tree."""
    f = _create_module_file(fixture_repo, "backend/src/shared/events/broken.py", "import unused_module\n")
    _git("add", str(f.relative_to(fixture_repo)), cwd=fixture_repo)
    # Now "fix" the working tree — staged content is still broken.
    f.write_text("# fixed in working tree\nx = 1\n")
    result = _commit(fixture_repo, "feat: broken stage")
    assert result.returncode == 1, "hook missed staged ruff violation"
    assert "ruff check" in result.stdout.lower() + result.stderr.lower()


def test_format_violation_blocks(fixture_repo: Path) -> None:
    # Docstring (passes D100) but spacing wrong (ruff format will reformat).
    f = _create_module_file(
        fixture_repo,
        "backend/src/shared/events/fmt.py",
        '"""Format module."""\n\n\nx     =    "hello"\n',
    )
    _git("add", str(f.relative_to(fixture_repo)), cwd=fixture_repo)
    result = _commit(fixture_repo, "feat: fmt")
    assert result.returncode == 1
    out = result.stdout.lower() + result.stderr.lower()
    assert "format" in out


def test_new_shared_file_without_ssot_entry_blocks(fixture_repo: Path) -> None:
    """C1 (R21) — new file under shared/X/ not in SSoT tabla → BLOCKED."""
    f = _create_module_file(
        fixture_repo,
        "backend/src/shared/novel_subsystem/service.py",
        '"""Novel surface, not in tabla."""\n\nx = 1\n',
    )
    _git("add", str(f.relative_to(fixture_repo)), cwd=fixture_repo)
    result = _commit(fixture_repo, "feat: new shared")
    assert result.returncode == 1
    out = result.stdout + result.stderr
    assert "R3 SSoT freshness" in out
    assert "novel_subsystem" in out


def test_new_shared_file_with_na_marker_passes(fixture_repo: Path) -> None:
    """Magic comment escape hatch."""
    f = _create_module_file(
        fixture_repo,
        "backend/src/shared/novel_subsystem/internal_helper.py",
        '"""Internal helper for shared/novel_subsystem itself."""\n\n'
        "# downstream-regression-na: private helper, no module imports it\n\n"
        "x = 1\n",
    )
    _git("add", str(f.relative_to(fixture_repo)), cwd=fixture_repo)
    result = _commit(fixture_repo, "feat: na helper")
    assert result.returncode == 0, f"hook should accept NA marker: {result.stderr}"


def test_new_shared_file_listed_in_tabla_passes(fixture_repo: Path) -> None:
    """File whose parent dir is listed in tabla SSoT."""
    # `shared/billing/` IS in the tabla (BudgetGuard, RateLimiter)
    f = _create_module_file(
        fixture_repo,
        "backend/src/shared/billing/new_guard.py",
        '"""New billing guard."""\n\nx = 1\n',
    )
    _git("add", str(f.relative_to(fixture_repo)), cwd=fixture_repo)
    result = _commit(fixture_repo, "feat: billing guard")
    assert result.returncode == 0, f"hook should accept tabla-listed parent dir: {result.stderr}"


def test_modification_of_existing_shared_file_passes(fixture_repo: Path) -> None:
    """C1 only blocks NEW files (status A/R), not M (modified)."""
    f = _create_module_file(
        fixture_repo,
        "backend/src/shared/novel_subsystem/existing.py",
        '"""Existing file."""\n\nx = 1\n',
    )
    _git("add", str(f.relative_to(fixture_repo)), cwd=fixture_repo)
    # Bypass hook for initial commit (test fixture seed only — production
    # hooks rule still applies elsewhere). core.hooksPath=/dev/null disables
    # local hook resolution for this single command.
    subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "commit", "-m", "seed"],  # noqa: S607 — test fixture seed
        cwd=fixture_repo,
        check=True,
        capture_output=True,
    )
    # Now MODIFY the file
    f.write_text('"""Existing file (modified)."""\n\nx = 2\n')
    _git("add", str(f.relative_to(fixture_repo)), cwd=fixture_repo)
    result = _commit(fixture_repo, "feat: modify existing")
    assert result.returncode == 0, f"hook should not block modify: {result.stderr}"


def test_nested_tests_subtree_under_shared_excluded_from_r3(fixture_repo: Path) -> None:
    """Nested tests/ subtree under backend/src/shared/X/ excluded from R3 gate.

    Hook regex strips ``(__pycache__/|\\.venv/|migrations/versions/|tests/)``
    from the new-shared-files set BEFORE checking SSoT tabla — so nested
    tests dirs never trigger the gate. Test exercises that exclusion with
    a file that ALSO passes ruff (file-level noqa bypasses D rules since
    nested src/.../tests/ doesn't match the project's tests/**/*.py glob).
    """
    f = _create_module_file(
        fixture_repo,
        "backend/src/shared/novel_subsystem/tests/test_internal.py",
        '"""Internal sanity test for novel_subsystem."""\n\n\n'
        "def test_internal_sanity() -> None:\n"
        '    """Trivial passing test."""\n'
        "    assert True  # noqa: S101 — assert is the test\n",
    )
    _git("add", str(f.relative_to(fixture_repo)), cwd=fixture_repo)
    result = _commit(fixture_repo, "test: tests under shared")
    assert result.returncode == 0, f"hook should not block tests under shared: {result.stderr}"


def test_modules_path_not_subject_to_r3_gate(fixture_repo: Path) -> None:
    """C1 only gates `backend/src/shared/`, not `backend/src/modules/`."""
    f = _create_module_file(
        fixture_repo,
        "backend/src/modules/novel_module/domain.py",
        '"""Module domain code."""\n\nx = 1\n',
    )
    _git("add", str(f.relative_to(fixture_repo)), cwd=fixture_repo)
    result = _commit(fixture_repo, "feat: new module file")
    assert result.returncode == 0, f"hook should not gate modules/: {result.stderr}"
