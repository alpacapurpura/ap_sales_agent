"""Architectural fitness: API contract enforcement.

Every FastAPI endpoint MUST declare response_model= (PII allowlist pattern).
Exceptions: webhooks, redirects, 204 No Content, SSE/streaming.
"""

import ast
import re
from pathlib import Path

from tests.architecture.conftest import MODULES_DIR

# ──────────────────────────────────────────────────────────────
# KNOWN VIOLATIONS — ratchet: only remove lines, never add.
# Expected format — "module/api/filename.py::function_name"
# ──────────────────────────────────────────────────────────────
KNOWN_MISSING_RESPONSE_MODEL: set[str] = set()

# Endpoints that legitimately don't need response_model:
# webhooks, OAuth callbacks, auth URLs, disconnect handlers
EXEMPT_PATTERNS: set[str] = {
    # --- OAuth auth URLs (return simple {"url": ...}) ---
    "connections/api/calendar.py::get_auth_url",
    "connections/api/calendar.py::oauth_callback",
    "connections/api/gmail.py::get_auth_url",
    "connections/api/gmail.py::oauth_callback",
    "connections/api/google_analytics.py::get_auth_url",
    "connections/api/google_workspace.py::get_auth_url",
    "connections/api/google_workspace.py::oauth_callback",
    "connections/api/meta.py::get_auth_url",
    "connections/api/meta.py::oauth_callback",
    "connections/api/shopify.py::auth_callback",
    "connections/api/youtube.py::get_auth_url",
    "connections/api/youtube.py::oauth_callback",
    # --- Webhook handlers (external callers, return 200 OK) ---
    "connections/api/meta.py::verify_webhook",
    "connections/api/meta.py::webhook_event",
    "connections/api/marketing_webhooks.py::handle_mailerlite_webhook",
    "connections/api/marketing_webhooks.py::handle_manychat_webhook",
    "connections/api/marketing_webhooks.py::mailerlite_webhook_legacy",
    "connections/api/marketing_webhooks.py::shopify_webhook",
    "connections/api/shopify_compliance.py::customers_data_request",
    "connections/api/shopify_compliance.py::customers_redact",
    "connections/api/shopify_compliance.py::shop_redact",
    "connections/api/telegram.py::telegram_webhook_legacy",
    "connections/api/telegram.py::telegram_webhook_tenant",
    "connections/api/webhook.py::webhook_chat",
    "connections/api/whatsapp.py::handle_whatsapp_webhook",
    "connections/api/whatsapp.py::verify_whatsapp_webhook",
    "connections/api/whatsapp.py::whatsapp_webhook",
    "iam/api/webhooks.py::clerk_webhook_handler",
    # --- Disconnect handlers (return 200 OK confirmation) ---
    "connections/api/calendar.py::disconnect",
    "connections/api/gmail.py::disconnect",
    "connections/api/google_analytics.py::disconnect",
    "connections/api/google_workspace.py::disconnect_all",
    "connections/api/meta.py::disconnect",
    "connections/api/telegram.py::disconnect_telegram",
    "connections/api/youtube.py::disconnect",
    "connections/api/whatsapp.py::delete_whatsapp_session",
    # --- Delete handlers without explicit 204 ---
    "assets/api/offer_gallery.py::delete_offer_image",
    "assets/api/router.py::delete_asset",
    "connections/api/calendar.py::delete_schedule",
    "copilot/api/chat.py::copilot_chat",  # SSE StreamingResponse
    "copilot/api/knowledge.py::delete_document",
    "sales_agent/api/audit.py::clear_lead_history",
    "scheduling/api/event_types.py::delete_event_type",
}


def _find_route_decorators(filepath: Path) -> list[dict]:
    """Parse a Python file and find all FastAPI route decorators with metadata."""
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except SyntaxError:
        return []

    routes: list[dict] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            # Match @router.get(...), @router.post(...), etc.
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr not in ("get", "post", "put", "patch", "delete"):
                continue

            has_response_model = False
            status_code = None
            for kw in decorator.keywords:
                if kw.arg == "response_model":
                    has_response_model = True
                if kw.arg == "status_code":
                    if isinstance(kw.value, ast.Constant):
                        status_code = kw.value.value
                    elif isinstance(kw.value, ast.Attribute):
                        # status.HTTP_204_NO_CONTENT → extract from name
                        attr_name = kw.value.attr
                        match = re.search(r"(\d+)", attr_name)
                        if match:
                            status_code = int(match.group(1))

            routes.append(
                {
                    "function": node.name,
                    "method": func.attr.upper(),
                    "has_response_model": has_response_model,
                    "status_code": status_code,
                    "line": node.lineno,
                },
            )
    return routes


def test_all_endpoints_have_response_model():
    """Every endpoint must declare response_model= unless exempt.

    Exempt: status_code 204 (no content), 202 (accepted), 301/302 (redirect).
    Known violations are allowlisted with the ratchet pattern.
    """
    exempt_status_codes = {204, 202, 301, 302}
    violations: list[str] = []

    for api_dir in sorted(MODULES_DIR.rglob("api")):
        if not api_dir.is_dir():
            continue
        for py_file in sorted(api_dir.glob("*.py")):
            if py_file.name.startswith("__"):
                continue
            rel_path = str(py_file.relative_to(MODULES_DIR))

            for route in _find_route_decorators(py_file):
                if route["has_response_model"]:
                    continue
                if route["status_code"] in exempt_status_codes:
                    continue

                violation_key = f"{rel_path}::{route['function']}"
                if violation_key in KNOWN_MISSING_RESPONSE_MODEL:
                    continue
                if violation_key in EXEMPT_PATTERNS:
                    continue

                violations.append(
                    f"{violation_key} (line {route['line']}, "
                    f"{route['method']}, no response_model)",
                )

    assert violations == [], (
        "NEW endpoints without response_model= detected.\n"
        "Every endpoint MUST declare response_model= to prevent PII leaks.\n\n"
        "Options:\n"
        "  1. Add response_model=YourResponseSchema to the decorator\n"
        "  2. If this is a webhook/redirect/SSE, add to EXEMPT_PATTERNS\n"
        "  3. If legacy, add to KNOWN_MISSING_RESPONSE_MODEL (requires justification)\n\n"
        "Violations:\n" + "\n".join(f"  - {v}" for v in violations)
    )
