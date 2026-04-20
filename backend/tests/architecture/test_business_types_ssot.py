"""Architecture fitness: business_types has a single source of truth.

After the 2026-04-20 mudanza, the ONLY module allowed to declare a persistent
``business_types`` field (dataclass, Pydantic model, or SQLAlchemy column) is
``tenant_profile``. Everything else MUST access the field via the port at
``src.shared.links.ports.tenant_profile``.

What this test does NOT flag (intentionally):
- API query parameters annotated as ``business_types: list[ExpertBusinessType]``
  — those are function parameters, not storage.
- Function parameters on catalog helpers like ``get_presets_for_business_types``
  — same rationale.
- Local variables or DTO fields that only exist within ``tenant_profile`` itself.

Ratchet pattern: the allowlist is empty and MUST stay empty. Adding entries
requires design-doc justification.
"""

from __future__ import annotations

import ast
from pathlib import Path

# Path to the src/modules tree.
_MODULES_ROOT = Path(__file__).resolve().parents[2] / "src" / "modules"

# Relative POSIX paths (under src/modules/) permitted to declare a persistent
# ``business_types`` field. Empty by design — keep it empty.
_ALLOWED_FILES: frozenset[str] = frozenset(
    {
        "tenant_profile/domain/tenant_profile.py",
        "tenant_profile/domain/events.py",
        "tenant_profile/infrastructure/models/tenant_profile_model.py",
        "tenant_profile/api/dtos.py",
    }
)


def _is_persistent_field_assignment(node: ast.AST) -> bool:
    """Return True if ``node`` is a class-level field assignment.

    Matches both ``business_types: X`` (AnnAssign) and ``business_types = X``
    (Assign) inside a ClassDef, which is where Pydantic/dataclass/SQLAlchemy
    declare persistent fields.
    """
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id == "business_types"
    if isinstance(node, ast.Assign):
        return any(isinstance(t, ast.Name) and t.id == "business_types" for t in node.targets)
    return False


def _find_business_types_declarations(path: Path) -> list[int]:
    """Return line numbers where ``business_types`` is declared as a class field."""
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    return [
        child.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
        for child in node.body
        if _is_persistent_field_assignment(child)
    ]


def test_business_types_declared_only_in_tenant_profile() -> None:
    """No dataclass / Pydantic model / SQLAlchemy column outside tenant_profile
    may declare a field named ``business_types``.
    """
    violations: list[str] = []

    for py_file in _MODULES_ROOT.rglob("*.py"):
        relative = py_file.relative_to(_MODULES_ROOT).as_posix()
        if relative in _ALLOWED_FILES:
            continue
        if "__pycache__" in relative:
            continue

        hits = _find_business_types_declarations(py_file)
        violations.extend(f"{relative}:{line}" for line in hits)

    assert not violations, (
        "Forbidden 'business_types' field declarations outside tenant_profile:\n"
        + "\n".join(f"  - {v}" for v in violations)
        + "\n\nAccess the field via the port "
        "(src.shared.links.ports.tenant_profile) instead."
    )


def test_brand_identity_does_not_declare_business_types() -> None:
    """Belt-and-suspenders check: the Pydantic model imports cleanly and the
    field has been removed from ``BrandIdentity``.

    The AST test above covers this, but a direct import verifies at runtime
    that the Pydantic model was rebuilt without the field.
    """
    from src.modules.brand.domain.identity import BrandIdentity

    assert "business_types" not in BrandIdentity.model_fields, (
        "BrandIdentity.model_fields still contains 'business_types'. "
        "Remove it — access the field via the tenant_profile port."
    )
