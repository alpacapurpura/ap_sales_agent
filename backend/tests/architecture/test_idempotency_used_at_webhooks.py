"""Architectural fitness: @idempotent decorator on inbound webhook endpoints.

Policy (Sub-F PR-1):
  Every ``@router.post("...webhook...")`` endpoint that receives **external**
  (untrusted, potentially-retried) HTTP traffic MUST be decorated with
  ``@idempotent`` from ``src.shared.idempotency.application.decorator``.

Rationale:
  External providers (Meta, Clerk, WhatsApp, ManyChat, Shopify, payment/
  scheduler platforms) retry on 5xx or timeout. Without idempotency protection
  the same event can be processed twice, causing duplicate enrollments,
  duplicate charges, duplicate messages, etc.

Detection strategy:
  AST-walk source files whose path or whose ``@router.post`` route path
  contains ``"webhook"`` (case-insensitive). For each handler function found,
  check whether ``idempotent`` appears in the decorator list.

Fail-closed ratchet:
  ``WEBHOOK_ALLOWLIST`` contains the set of ``"module/file.py::function_name"``
  that are **not yet** decorated. The list must only shrink — when a webhook
  is protected with ``@idempotent`` its entry is removed. Adding a new entry
  requires a justified commit message (legacy webhook, internal, or exempt).

Current allowlist (all pre-PR-1 webhooks — none yet use @idempotent):
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ connections/api/whatsapp.py::whatsapp_webhook                           │
  │ connections/api/whatsapp.py::handle_whatsapp_webhook                    │
  │ connections/api/telegram.py::telegram_webhook_legacy                    │
  │ connections/api/telegram.py::telegram_webhook_tenant                    │
  │ connections/api/webhook.py::webhook_chat                                │
  │ connections/api/meta.py::webhook_event                                  │
  │ connections/api/marketing_webhooks.py::shopify_webhook                  │
  │ connections/api/marketing_webhooks.py::handle_mailerlite_webhook        │
  │ connections/api/marketing_webhooks.py::mailerlite_webhook_legacy        │
  │ connections/api/marketing_webhooks.py::handle_manychat_webhook          │
  │ sales_agent/api/scheduler_webhooks.py::scheduler_webhook                │
  │ sales_agent/api/payment_webhooks.py::payment_webhook                    │
  │ iam/api/webhooks.py::clerk_webhook_handler                              │
  └─────────────────────────────────────────────────────────────────────────┘

Explicitly EXCLUDED (not inbound webhooks, not fail-closed):
  - iam/api/settings.py::regenerate_webhook_secret  — internal management
    endpoint that regenerates a secret, not an inbound event receiver.
  - connections/api/meta.py::verify_webhook  — GET-verified handshake endpoint,
    not a POST event receiver.
"""

from __future__ import annotations

import ast
from pathlib import Path

WEBHOOK_ALLOWLIST: frozenset[str] = frozenset(
    {
        # WhatsApp inbound — 2 routes (with and without tenant_id in path)
        "connections/api/whatsapp.py::whatsapp_webhook",
        "connections/api/whatsapp.py::handle_whatsapp_webhook",
        # Telegram inbound — 2 routes (legacy path, tenant_id path)
        "connections/api/telegram.py::telegram_webhook_legacy",
        "connections/api/telegram.py::telegram_webhook_tenant",
        # Generic chat webhook (external partners send here via X-Webhook-Secret)
        "connections/api/webhook.py::webhook_chat",
        # Meta (Facebook / Instagram) graph webhook
        "connections/api/meta.py::webhook_event",
        # Marketing platform webhooks
        "connections/api/marketing_webhooks.py::shopify_webhook",
        "connections/api/marketing_webhooks.py::handle_mailerlite_webhook",
        "connections/api/marketing_webhooks.py::mailerlite_webhook_legacy",
        "connections/api/marketing_webhooks.py::handle_manychat_webhook",
        # Sales-agent scheduler and payment webhooks
        "sales_agent/api/scheduler_webhooks.py::scheduler_webhook",
        "sales_agent/api/payment_webhooks.py::payment_webhook",
        # IAM — Clerk user-lifecycle events
        "iam/api/webhooks.py::clerk_webhook_handler",
    }
)

_EXCLUDED_FUNCTIONS: frozenset[str] = frozenset(
    {
        # Regenerates the tenant's webhook secret (management operation)
        "regenerate_webhook_secret",
        # Meta GET — webhook verification handshake, not an event receiver
        "verify_webhook",
    }
)

_SRC_MODULES = Path(__file__).resolve().parents[2] / "src" / "modules"
_IDEMPOTENT_NAMES = frozenset({"idempotent"})


def _file_is_webhook_candidate(py_file: Path) -> bool:
    """Return True if the file is likely to contain inbound webhook endpoints."""
    if "webhook" in py_file.name.lower():
        return True
    rel = py_file.relative_to(_SRC_MODULES).as_posix()
    return "webhook" in rel.lower()


def _route_path_has_webhook(decorator: ast.expr) -> bool:
    """Return True if a decorator call's first argument contains 'webhook'."""
    if not isinstance(decorator, ast.Call):
        return False
    if not decorator.args:
        return False
    first_arg = decorator.args[0]
    if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
        return "webhook" in first_arg.value.lower()
    return False


def _is_router_post(decorator: ast.expr) -> bool:
    """Return True if the decorator is ``@router.post(...)``."""
    if not isinstance(decorator, ast.Call):
        return False
    func = decorator.func
    return isinstance(func, ast.Attribute) and func.attr == "post"


def _decorator_uses_idempotent(decorator: ast.expr) -> bool:
    """Return True if the decorator references 'idempotent'."""
    if isinstance(decorator, ast.Name):
        return decorator.id in _IDEMPOTENT_NAMES
    if isinstance(decorator, ast.Call):
        func = decorator.func
        if isinstance(func, ast.Name):
            return func.id in _IDEMPOTENT_NAMES
        if isinstance(func, ast.Attribute):
            return func.attr in _IDEMPOTENT_NAMES
    return False


def _collect_webhook_handlers(py_file: Path) -> list[tuple[str, bool]]:
    """Parse file and return (func_name, has_idempotent) for webhook POST handlers."""
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
    except SyntaxError:
        return []

    results: list[tuple[str, bool]] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name in _EXCLUDED_FUNCTIONS:
            continue

        decorators = node.decorator_list
        # Check if this function has a @router.post("...webhook...") decorator
        has_router_post_webhook = any(_is_router_post(d) and _route_path_has_webhook(d) for d in decorators)
        if not has_router_post_webhook:
            continue

        # Check if @idempotent is also in the decorator list
        has_idempotent = any(_decorator_uses_idempotent(d) for d in decorators)
        results.append((node.name, has_idempotent))

    return results


def _rel_key(py_file: Path, func_name: str) -> str:
    """Build 'module/subpath.py::func_name' key relative to src/modules."""
    rel = py_file.relative_to(_SRC_MODULES).as_posix()
    return f"{rel}::{func_name}"


def test_webhook_endpoints_use_idempotent_decorator() -> None:
    """All inbound webhook POST endpoints must have @idempotent or be in the allowlist.

    When a webhook is protected with ``@idempotent``, remove it from
    ``WEBHOOK_ALLOWLIST``. The allowlist MUST NOT grow without a justified
    commit message (new legacy route or documented exemption).
    """
    violations: list[str] = []

    for py_file in sorted(_SRC_MODULES.rglob("*.py")):
        if not _file_is_webhook_candidate(py_file):
            continue

        handlers = _collect_webhook_handlers(py_file)
        for func_name, has_idempotent in handlers:
            key = _rel_key(py_file, func_name)

            if has_idempotent:
                # Good — correctly decorated. If still in allowlist → stale entry.
                if key in WEBHOOK_ALLOWLIST:
                    violations.append(
                        f"STALE ALLOWLIST: {key} now has @idempotent — "
                        "remove it from WEBHOOK_ALLOWLIST (allowlist shrinks only)."
                    )
            # No @idempotent — must be in allowlist.
            elif key not in WEBHOOK_ALLOWLIST:
                violations.append(
                    f"MISSING @idempotent: {key} — either add "
                    "@idempotent decorator or add to WEBHOOK_ALLOWLIST with justification."
                )

    assert not violations, (
        "Webhook idempotency invariants violated.\n\n"
        "Policy: every inbound @router.post(webhook) must be decorated with @idempotent.\n"
        "Legacy webhooks without @idempotent must appear in WEBHOOK_ALLOWLIST.\n"
        "Allowlist shrinks only — never add new entries without justification.\n\n"
        "Violations:\n" + "\n".join(f"  - {v}" for v in violations)
    )


def test_allowlist_not_grown() -> None:
    """Ratchet: WEBHOOK_ALLOWLIST must not exceed 13 entries (current legacy count).

    Current cap: 13 (all pre-PR-1 legacy webhooks, zero @idempotent yet).
    When webhooks are migrated, this count decreases.
    """
    current_count = len(WEBHOOK_ALLOWLIST)
    cap = 13
    assert current_count <= cap, (
        f"WEBHOOK_ALLOWLIST grew to {current_count} entries (cap={cap}). "
        "New webhooks must use @idempotent from day one (no allowlist entry). "
        "Existing entries must be removed as webhooks are migrated. "
        "Raising the cap requires architectural justification in the commit message."
    )
