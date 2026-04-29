"""Arch ratchet — DeepSeek aliases retired Jul 24 2026 (S12).

Cierra S4 watchpoint ``[MEDIUM] DeepSeek alias retire deadline 2026-07-24``.

DeepSeek anunció (research S4) que los aliases ``deepseek-chat`` y
``deepseek-reasoner`` se retiran completamente Jul 24 2026 15:59 UTC.
Después de la deadline, cualquier call a esos modelos rompe con HTTP 404.
Migración explícita: ``deepseek-v4-flash`` (284B params, cheap) o
``deepseek-v4-pro`` (1.6T params, complejo).

Este arch test bloquea regresión: si alguien introduce un literal
``deepseek-chat`` o ``deepseek-reasoner`` en código fuente
(``backend/src/``) — incluyendo defaults env, Pydantic Field default,
test fixture, llm router — la suite falla.

Allowlist: comments / docstrings que documentan la deadline o el alias
retire son OK porque mantienen la historia accesible. El AST scan solo
flagea **string literales**.

# [SALES-AGENT-DEEPSEEK-ALIAS-S12] -> docs/domains/sales-agent/redesign-2026-04/phases/S12-final-hardening-zero-debt.md
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"

RETIRED_ALIASES: frozenset[str] = frozenset({"deepseek-chat", "deepseek-reasoner"})

# Files allowed to mention the retired aliases (documentation, alias
# resolver tables that explicitly translate legacy → modern). Tests live
# under ``tests/`` (not scanned). If a new entry needs to be added,
# justify with comment + commit message — this is a ratchet, allowlist
# shrinks over time.
ALLOWLIST_RELATIVE_PATHS: frozenset[Path] = frozenset(
    {
        # ``aliases.py`` lives in ``src/shared/agent_observability/pricing/``
        # and is allowed to translate legacy DeepSeek aliases to canonical
        # LiteLLM keys for back-compat with rows persisted before
        # 2026-07-24. The translation runs on read-side only — we never
        # write retired aliases to new rows.
        Path("shared/agent_observability/pricing/aliases.py"),
    },
)


def _iter_python_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.py") if "__pycache__" not in p.parts]


def _collect_string_literals(tree: ast.AST) -> list[str]:
    """Return every ``ast.Constant`` string in ``tree``."""
    return [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)]


@pytest.fixture(scope="module")
def offending_paths() -> dict[Path, list[str]]:
    """Map relative path → list of retired alias literals found inside."""
    found: dict[Path, list[str]] = {}
    for path in _iter_python_files(SRC_ROOT):
        rel = path.relative_to(SRC_ROOT)
        if rel in ALLOWLIST_RELATIVE_PATHS:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue  # broken syntax surfaces in ruff, not here
        literals = _collect_string_literals(tree)
        hits = [lit for lit in literals if lit in RETIRED_ALIASES]
        if hits:
            found[rel] = hits
    return found


class TestDeepSeekAliasNotRetired:
    def test_no_retired_aliases_in_src(self, offending_paths: dict[Path, list[str]]) -> None:
        if offending_paths:
            details = "\n".join(f"  {path}: {sorted(set(hits))}" for path, hits in offending_paths.items())
            pytest.fail(
                "DeepSeek aliases ``deepseek-chat`` y ``deepseek-reasoner`` se "
                "retiran 2026-07-24 (research S4). Reemplaza por "
                "``deepseek-v4-flash`` o ``deepseek-v4-pro`` en:\n" + details,
            )

    def test_allowlist_paths_exist(self) -> None:
        """Each allowlisted path must point to a real file."""
        for rel in ALLOWLIST_RELATIVE_PATHS:
            assert (SRC_ROOT / rel).is_file(), f"Allowlist path {rel} does not exist"
