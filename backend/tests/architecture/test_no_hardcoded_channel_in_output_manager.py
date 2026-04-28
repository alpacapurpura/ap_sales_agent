"""S5 — Architecture ratchet: no hardcoded channel literals in OutputManager.

Mirror del pattern S4 ``test_no_hardcoded_models_sales_agent.py``. Sin allowlist:
cualquier comparación contra string-literal de canal en
``infrastructure/external/output_manager.py`` falla CI.

# [SALES-AGENT-CHANNEL-REGISTRY-S5]
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_MANAGER_PATH = (
    PROJECT_ROOT / "src" / "modules" / "sales_agent" / "infrastructure" / "external" / "output_manager.py"
)

FORBIDDEN_CHANNEL_LITERALS: frozenset[str] = frozenset(
    {
        "whatsapp",
        "telegram",
        "instagram_dm",
        "instagram",
        "sms",
        "voice",
        "email",
        "chat",
        "web_chat",
        "web",
    },
)


def _walk_compare_offenders(tree: ast.AST) -> list[tuple[int, str]]:
    """Return ``(lineno, literal)`` pairs for every Compare node where one side
    is a string-literal channel name."""
    offenders: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        sides = [node.left, *node.comparators]
        for side in sides:
            if (
                isinstance(side, ast.Constant)
                and isinstance(side.value, str)
                and side.value.lower() in FORBIDDEN_CHANNEL_LITERALS
            ):
                offenders.append((node.lineno, side.value))
    return offenders


def _walk_dict_key_offenders(tree: ast.AST) -> list[tuple[int, str]]:
    """Forbid lookup dicts keyed by channel-name literal — that's hardcoded
    routing in disguise. ``ChannelType`` mappings live in
    ``application/services/channel_resolver.py`` (out of scope)."""
    offenders: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key in node.keys:
            if (
                isinstance(key, ast.Constant)
                and isinstance(key.value, str)
                and key.value.lower() in FORBIDDEN_CHANNEL_LITERALS
            ):
                offenders.append((node.lineno, key.value))
    return offenders


class TestNoHardcodedChannelLiterals:
    def test_output_manager_module_exists(self) -> None:
        assert OUTPUT_MANAGER_PATH.is_file(), f"missing {OUTPUT_MANAGER_PATH}"

    def test_no_string_literal_channel_comparisons(self) -> None:
        tree = ast.parse(OUTPUT_MANAGER_PATH.read_text(encoding="utf-8"))
        offenders = _walk_compare_offenders(tree)
        assert not offenders, (
            "OutputManager must route channel logic through the shared registry "
            "(`shared.agent_observability.channels.format.get_channel_format`). "
            "Found hardcoded channel comparisons (line, literal):\n  - "
            + "\n  - ".join(f"{ln}: {lit!r}" for ln, lit in offenders)
        )

    def test_no_dict_keyed_by_channel_literal(self) -> None:
        tree = ast.parse(OUTPUT_MANAGER_PATH.read_text(encoding="utf-8"))
        offenders = _walk_dict_key_offenders(tree)
        assert not offenders, (
            "OutputManager must not own per-channel lookup dicts (registry duty). "
            "Found dicts keyed by channel literal (line, key):\n  - "
            + "\n  - ".join(f"{ln}: {lit!r}" for ln, lit in offenders)
        )


class TestRegistryImported:
    def test_imports_get_channel_format(self) -> None:
        src = OUTPUT_MANAGER_PATH.read_text(encoding="utf-8")
        # Accept import from the package or from the format submodule.
        assert (
            "from src.shared.agent_observability.channels.format import" in src
            or "from src.shared.agent_observability.channels import" in src
        ), "OutputManager must import the shared channels registry."
        assert "get_channel_format" in src
