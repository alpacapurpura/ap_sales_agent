"""S8 — SchedulerProvider strategy fitness.

Enforces:

* Every concrete impl in ``SCHEDULER_PROVIDERS`` is structurally
  ``runtime_checkable`` against the ``SchedulerProvider`` Protocol.
* Each impl declares a non-empty ``provider_id`` class attribute.
* The endpoint + tools never branch on ``provider_id`` (no
  ``if provider_id == "..."`` outside the registry resolver).
* Every concrete impl in ``SCHEDULER_WEBHOOK_PROVIDERS`` is structurally
  ``runtime_checkable`` against the ``WebhookProvider`` Protocol.
* The webhook endpoint dispatches via ``webhook_provider_for(...)``,
  never via inline if/elif.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from src.modules.sales_agent.application.tools.scheduling.providers import (
    SCHEDULER_PROVIDERS,
    SchedulerProvider,
)
from src.modules.sales_agent.application.tools.scheduling.webhook_providers import (
    SCHEDULER_WEBHOOK_PROVIDERS,
    WebhookProvider,
)

SRC_ROOT = Path(__file__).parents[2] / "src"


def test_every_scheduler_provider_implements_protocol() -> None:
    for provider_id, klass in SCHEDULER_PROVIDERS.items():
        # Construct without calling __init__ to skip the DB session arg.
        instance = klass.__new__(klass)
        # Protocol requires the methods + provider_id attribute. Verify both.
        assert hasattr(instance, "create_booking_link"), provider_id
        assert hasattr(instance, "verify_booking_status"), provider_id
        assert hasattr(instance, "get_available_slots"), provider_id
        assert getattr(klass, "provider_id", None), f"{klass.__name__} missing provider_id class attribute"


def test_every_webhook_provider_implements_protocol() -> None:
    for provider_id, klass in SCHEDULER_WEBHOOK_PROVIDERS.items():
        instance = klass.__new__(klass)
        assert hasattr(instance, "verify_signature"), provider_id
        assert hasattr(instance, "parse_payload"), provider_id
        assert getattr(klass, "provider_id", None), f"{klass.__name__} missing provider_id class attribute"


def _scan_for_hardcoded_provider_branches(file_path: Path) -> list[str]:
    """Walk ast looking for ``if x == 'internal'/'calcom'/'calendly'``.

    Tools + endpoint should resolve provider via registry. Inline branch
    on a provider literal is the anti-pattern this gate blocks.
    """
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    bad: list[str] = []
    forbidden_literals = {"internal", "calcom", "calendly", "gcal_push"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare) and isinstance(node.left, ast.Name):
            for comparator in node.comparators:
                if (
                    isinstance(comparator, ast.Constant)
                    and isinstance(comparator.value, str)
                    and comparator.value in forbidden_literals
                    and node.left.id in {"provider", "provider_id"}
                ):
                    bad.append(f"{file_path}:{node.lineno}")
    return bad


def test_no_hardcoded_provider_branches_in_tools_or_endpoint() -> None:
    """Tools + webhook endpoint must dispatch via registry, not inline."""
    targets = [
        SRC_ROOT / "modules/sales_agent/application/tools/scheduling/tools.py",
        SRC_ROOT / "modules/sales_agent/api/scheduler_webhooks.py",
    ]
    offenders = []
    for t in targets:
        if t.exists():
            offenders.extend(_scan_for_hardcoded_provider_branches(t))
    assert not offenders, "Hardcoded provider literal comparison detected (use registry instead):\n" + "\n".join(
        offenders
    )


def test_webhook_endpoint_uses_registry_resolver() -> None:
    """Endpoint must call ``webhook_provider_for(provider)`` to resolve."""
    endpoint = (SRC_ROOT / "modules/sales_agent/api/scheduler_webhooks.py").read_text(encoding="utf-8")
    assert re.search(r"webhook_provider_for\s*\(\s*provider\s*\)", endpoint), (
        "Endpoint must dispatch via webhook_provider_for(provider) registry call."
    )


def test_internal_provider_registered() -> None:
    """``InternalSchedulerProvider`` must be the registered ``internal`` impl."""
    from src.modules.sales_agent.application.tools.scheduling.providers import (
        InternalSchedulerProvider,
    )

    assert SCHEDULER_PROVIDERS.get("internal") is InternalSchedulerProvider
