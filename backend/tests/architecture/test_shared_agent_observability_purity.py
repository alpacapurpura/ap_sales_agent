"""Enforce ``shared/agent_observability/`` purity.

Cross-cutting shared module: must NOT import from ``src.modules.*``
(otherwise it'd couple every agent BC together via the shared layer).

Allowed imports:

* ``src.shared.*``       — fellow shared primitives (base entity, events).
* ``src.core.*``         — config / database / sentry.
* stdlib + 3rd-party     — sqlalchemy, langchain_core, structlog, httpx, etc.

Ratchet pattern: ``KNOWN_VIOLATIONS`` must stay empty. Any new offending
import fails CI immediately so the ``shared/agent_observability/``
boundary stays clean as S0..S10 evolve.
"""

from __future__ import annotations

import ast
from pathlib import Path

SHARED_OBS_DIR = Path(__file__).resolve().parents[2] / "src" / "shared" / "agent_observability"

# Empty ratchet — any cross-module coupling is a regression.
KNOWN_VIOLATIONS: set[str] = set()


def test_shared_agent_observability_does_not_import_modules() -> None:
    """No file under ``shared/agent_observability/`` may import ``src.modules.*``."""
    violations: list[str] = []

    for py_file in sorted(SHARED_OBS_DIR.rglob("*.py")):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        rel = py_file.relative_to(SHARED_OBS_DIR.parents[2])  # src-relative
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.startswith(("src.modules.", "modules.")):
                    key = f"{rel}: {module}"
                    if key not in KNOWN_VIOLATIONS:
                        violations.append(key)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    if name.startswith(("src.modules.", "modules.")):
                        key = f"{rel}: {name}"
                        if key not in KNOWN_VIOLATIONS:
                            violations.append(key)

    assert not violations, "shared/agent_observability/ imported from src.modules.*:\n" + "\n".join(violations)


def test_shared_agent_observability_directory_layout() -> None:
    """Sub-packages exist and carry an ``__init__.py``.

    Anchors the layout decided in the S0 phase doc; if a subpackage is
    renamed/removed the change is loud.
    """
    expected = {
        "recording",
        "pricing",
        "cost",
        "persistence",
        "persistence/models",
        "reporting",
        "workers",
    }
    missing: list[str] = []
    for sub in expected:
        init = SHARED_OBS_DIR / sub / "__init__.py"
        if not init.is_file():
            missing.append(sub)
    assert not missing, f"Missing subpackages under shared/agent_observability/: {missing}"
