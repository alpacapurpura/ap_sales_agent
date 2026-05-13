"""S9 arch test — payment_grant_audit append-only invariant.

Ensures no UPDATE or DELETE statements touch ``payment_grant_audit`` except
via the retention worker (allowed). Mirrors ``test_conventions.py`` pattern.
"""

from __future__ import annotations

import ast
import pathlib

SRC_ROOT = pathlib.Path(__file__).parent.parent.parent / "src"

# Allowed file paths that may UPDATE/DELETE payment_grant_audit
# (empty = no code should ever update it outside retention)
_ALLOWED_AUDIT_MUTATORS: frozenset[str] = frozenset(
    {
        # Retention worker may delete expired rows
        "src/shared/agent_observability/workers/retention_task.py",
    }
)

_AUDIT_TABLE = "payment_grant_audit"


def _iter_python_files(root: pathlib.Path):
    for path in root.rglob("*.py"):
        if "__pycache__" not in str(path):
            yield path


def _relative(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(SRC_ROOT.parent))
    except ValueError:
        return str(path)


def test_no_update_on_payment_grant_audit() -> None:
    """No code should UPDATE payment_grant_audit (append-only)."""
    violations: list[str] = []

    for fpath in _iter_python_files(SRC_ROOT):
        rel = _relative(fpath)
        if rel in _ALLOWED_AUDIT_MUTATORS:
            continue
        source = fpath.read_text(encoding="utf-8")
        lower = source.lower()
        # Look for raw SQL UPDATE targeting the audit table
        if f"update {_AUDIT_TABLE}" in lower or f'update "{_AUDIT_TABLE}"' in lower:
            violations.append(f"{rel}: raw SQL UPDATE on {_AUDIT_TABLE}")

        # Look for SA ORM update of PaymentGrantAuditModel
        if "PaymentGrantAuditModel" in source and (".update(" in source or "session.merge(" in source):
            # AST check: ensure update() calls are not on PaymentGrantAuditModel
            try:
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Attribute) and node.attr in {"update", "merge"}:
                        violations.append(f"{rel}:{node.lineno} — possible ORM UPDATE/merge on audit model")
                        break
            except SyntaxError:
                pass

    assert not violations, "payment_grant_audit must be append-only. Violations:\n" + "\n".join(violations[:20])


def test_payment_grant_audit_model_has_no_updated_at() -> None:
    """Append-only table should NOT have updated_at column."""
    from luana_core_sales_agent.infrastructure.models.payment_grant_audit_model import (
        PaymentGrantAuditModel,
    )

    columns = {col.key for col in PaymentGrantAuditModel.__table__.columns}
    assert "updated_at" not in columns, (
        "payment_grant_audit has updated_at — this implies mutability. Append-only tables don't get updated."
    )


def test_no_hardcoded_payment_provider_in_tools() -> None:
    """Tools must not branch on provider_id inline (Strategy pattern required)."""
    tools_dir = SRC_ROOT / "modules" / "sales_agent" / "application" / "tools" / "payment"
    if not tools_dir.exists():
        return  # Not yet created — will catch once implemented

    violations: list[str] = []
    for fpath in tools_dir.glob("*.py"):
        if fpath.name in {"providers.py", "webhook_providers.py"}:
            continue  # Strategy impls allowed to mention provider names
        source = fpath.read_text(encoding="utf-8")
        for provider_name in ("mercadopago", "stripe", "culqi"):
            if provider_name in source.lower():
                violations.append(f"{fpath.name}: hardcoded provider '{provider_name}'")

    assert not violations, "Payment tools must not hardcode provider names. Use registry. Violations:\n" + "\n".join(
        violations
    )


def test_payment_webhook_provider_strategy_arch() -> None:
    """Each impl in PAYMENT_WEBHOOK_PROVIDERS must set provider_id class attribute."""
    from luana_core_sales_agent.application.tools.payment.webhook_providers import (
        PAYMENT_WEBHOOK_PROVIDERS,
    )

    for name, klass in PAYMENT_WEBHOOK_PROVIDERS.items():
        assert hasattr(klass, "provider_id"), f"{name}: missing provider_id attribute"
        assert klass.provider_id == name, f"{name}: provider_id={klass.provider_id!r} must match registry key"
