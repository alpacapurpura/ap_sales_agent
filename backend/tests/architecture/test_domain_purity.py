"""Enforce domain layer purity — no framework coupling.

Fitness gates:
1. Domain entities must NOT inherit from SQLAlchemy Base/DeclarativeBase
2. Domain files must not reference Session or engine directly
"""

import ast
import re
from pathlib import Path

MODULES_DIR = Path(__file__).resolve().parents[2] / "src" / "modules"

# Known violations (ratchet pattern — list must shrink, never grow)
KNOWN_SQLALCHEMY_BASE_IN_DOMAIN: set[str] = set()
KNOWN_SESSION_IN_DOMAIN: set[str] = set()

SQLALCHEMY_BASE_PATTERNS = {
    "DeclarativeBase",
    "declarative_base",
    "registry.generate_base",
}

SESSION_PATTERNS = re.compile(r"\b(Session|AsyncSession|engine\.connect|create_engine|sessionmaker)\s*\(")


def test_domain_entities_no_sqlalchemy_base():
    """Domain classes must NOT inherit from SQLAlchemy ORM base classes.

    Domain layer = pure Python + Pydantic. ORM models belong in infrastructure/models/.
    """
    violations = []
    for py_file in sorted(MODULES_DIR.rglob("*.py")):
        rel = py_file.relative_to(MODULES_DIR)
        parts = rel.parts
        if len(parts) < 2 or parts[1] != "domain":
            continue

        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    base_str = ast.unparse(base)
                    if any(pattern in base_str for pattern in SQLALCHEMY_BASE_PATTERNS):
                        key = f"{rel}:{node.name}"
                        if key not in KNOWN_SQLALCHEMY_BASE_IN_DOMAIN:
                            violations.append(f"{rel}:{node.lineno} class {node.name} inherits {base_str}")

    assert not violations, "Domain classes with SQLAlchemy inheritance (move to infrastructure/models/):\n" + "\n".join(
        f"  {v}" for v in violations
    )


def test_domain_no_session_usage():
    """Domain layer must not directly reference Session, engine, or sessionmaker.

    Database access belongs in infrastructure/repositories/.
    """
    violations = []
    for py_file in sorted(MODULES_DIR.rglob("*.py")):
        rel = py_file.relative_to(MODULES_DIR)
        parts = rel.parts
        if len(parts) < 2 or parts[1] != "domain":
            continue

        content = py_file.read_text(encoding="utf-8")
        for i, line in enumerate(content.splitlines(), 1):
            if SESSION_PATTERNS.search(line):
                key = f"{rel}:{i}"
                if key not in KNOWN_SESSION_IN_DOMAIN:
                    violations.append(f"{rel}:{i}: {line.strip()}")

    assert not violations, "Domain files referencing Session/engine (use repository pattern):\n" + "\n".join(
        f"  {v}" for v in violations
    )
