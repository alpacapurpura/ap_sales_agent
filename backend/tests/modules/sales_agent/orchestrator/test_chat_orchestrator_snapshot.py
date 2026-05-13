"""Snapshot test — pre/post-decomposition safety net for S11B.

Replays a full ``ChatOrchestrator.process_chat_flow`` against a canonical
scenario (telegram, brand-new lead) with every external collaborator
mocked, then asserts the captured side-effects (audit log, journey
events, domain events, WS emissions, OutputManager calls, checkpoint
saves, agent invocations) match a JSON baseline byte-equal.

If S11B's Strangler Fig (extract AuditEmitter / IdentityResolver /
ConversationPipeline) preserves behavior, the diff is zero. Any
divergence (extra row, reordered call, changed kwarg shape) fails the
test and surfaces the offending payload — that's the contract.

Snapshots track *observable behavior* (what the lead sees + what the
ops team sees in Closer Studio + what we persist), NOT internal
collaborator wiring. Refactors that move the same call from
ChatOrchestrator to a new class produce diff = 0.

# [SALES-AGENT-ORCHESTRATOR-SNAPSHOT-S11B] -> docs/domains/sales-agent/redesign-2026-04/phases/S11-shared-lift-orchestrator-decomp.md
"""

from __future__ import annotations

import pytest

from luana_core_platform.domain.messages import IncomingMessage
from tests.modules.sales_agent.orchestrator._chat_flow_snapshot_helpers import (
    TENANT_ID,
    FlowCapture,
    assert_matches_snapshot,
    build_capturing_channel_adapter,
    install_chat_module_patches,
    render_snapshot,
)


@pytest.mark.asyncio
async def test_chat_flow_telegram_new_lead_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    """Canonical scenario: telegram webhook, brand-new lead, single-turn rapport."""
    capture = FlowCapture()
    install_chat_module_patches(monkeypatch, capture)

    from luana_core_sales_agent.application.orchestrator.chat import ChatOrchestrator

    adapter = build_capturing_channel_adapter(capture)
    incoming = IncomingMessage(
        user_id="tg_user_123",
        text="Hola, quiero info",
        channel_type="telegram",
        metadata={"first_name": "Lead", "last_name": "Test", "message_id": "tg_msg_1"},
    )

    orchestrator = ChatOrchestrator()
    await orchestrator.process_chat_flow(adapter, incoming, str(TENANT_ID))

    snapshot = render_snapshot(capture)
    assert_matches_snapshot(snapshot, "telegram_new_lead_baseline.json")
