"""Architectural fitness test — sales_agent specialists MUST NOT hardcode model names.

Specialists in ``application/agents/sales/`` route via :class:`ModelRole`
through the :data:`SPECIALIST_TO_ROLE` SSoT mapping declared in
``domain/model_tier.py``. Hardcoded model strings (``"gpt-*"``,
``"deepseek-*"``, ``"kimi-*"``, ``"claude-*"``, ``"o3"``, ``"o4-mini"``)
break per-role multi-provider routing because the env var
``AI_PROVIDER_<ROLE>`` is bypassed when a wire-name is pinned in code.

Ratchet pattern: zero allowlist. Any new specialist that pins a model
literal fails CI. Configurable models live in ``settings.AI_MODEL_<ROLE>``
+ ``AI_PROVIDER_<ROLE>`` env vars; SSoT mapping lives in
``domain/model_tier.py::SPECIALIST_TO_ROLE``.

Excluded paths (legitimate model-name string occurrences):
- ``domain/model_tier.py`` itself (declares the SSoT, references
  ``ModelRole`` enum members which are *role* names not model names).
- Test fixtures in ``tests/`` (mocks may stub specific providers).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SPECIALISTS_ROOT = REPO / "src" / "modules" / "sales_agent" / "application" / "agents" / "sales"

# Wire model names that, if pinned in specialist code, break per-role
# multi-provider routing. Patterns intentionally permissive — anything
# that *looks* like a chat-model wire name should fail.
FORBIDDEN_MODEL_PATTERNS = (
    re.compile(r"^gpt-[\d.]"),
    re.compile(r"^o[34](?:-[a-z]+)?$"),  # o3 / o4-mini / o3-pro
    re.compile(r"^claude-"),
    re.compile(r"^deepseek-"),
    re.compile(r"^kimi-"),
    re.compile(r"^moonshot-"),
    re.compile(r"^qwen[\d-]"),
    re.compile(r"^gemini-"),
)


def _iter_specialist_py_files() -> list[Path]:
    return [p for p in SPECIALISTS_ROOT.rglob("*.py") if p.name != "__init__.py"]


def _string_constants(tree: ast.Module) -> list[tuple[str, int]]:
    """Walk AST + collect every string literal with line number."""
    out: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append((node.value, node.lineno))
    return out


class TestNoHardcodedModelsInSpecialists:
    """Specialists MUST resolve models via ``ModelRole`` enum + env vars."""

    def test_no_forbidden_model_string_literals(self) -> None:
        violations: list[str] = []
        for path in _iter_specialist_py_files():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for value, lineno in _string_constants(tree):
                stripped = value.strip().lower()
                if any(p.search(stripped) for p in FORBIDDEN_MODEL_PATTERNS):
                    rel = path.relative_to(REPO)
                    violations.append(f"{rel}:{lineno}  {value!r}")

        assert not violations, (
            "Hardcoded model wire names found in sales_agent specialists. "
            "Use ModelRole + SPECIALIST_TO_ROLE (domain/model_tier.py) so "
            "AI_PROVIDER_<ROLE> env vars route correctly:\n  " + "\n  ".join(violations)
        )


class TestSpecialistRoleMappingExists:
    """``SPECIALIST_TO_ROLE`` is the SSoT — must be declared + cover specialists."""

    def test_model_tier_module_exists(self) -> None:
        target = REPO / "src" / "modules" / "sales_agent" / "domain" / "model_tier.py"
        assert target.is_file(), f"missing SSoT: {target.relative_to(REPO)}"

    def test_specialist_to_role_exposes_required_keys(self) -> None:
        from src.modules.sales_agent.domain.model_tier import SPECIALIST_TO_ROLE

        required = {"supervisor", "qualifier", "product_expert", "closer"}
        missing = required - set(SPECIALIST_TO_ROLE.keys())
        assert not missing, f"SPECIALIST_TO_ROLE missing: {sorted(missing)}"

    def test_nodes_imports_specialist_to_role(self) -> None:
        nodes = SPECIALISTS_ROOT / "nodes.py"
        tree = ast.parse(nodes.read_text(encoding="utf-8"))
        imported = False
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and "model_tier" in (node.module or "")
                and any(alias.name == "SPECIALIST_TO_ROLE" for alias in node.names)
            ):
                imported = True
                break
        assert imported, "nodes.py must import SPECIALIST_TO_ROLE from domain/model_tier.py"
