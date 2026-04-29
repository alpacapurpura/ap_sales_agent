"""Snapshot helpers for ChatOrchestrator decomposition — S11B.

Used by ``test_chat_orchestrator_snapshot.py`` to replay a deterministic
``process_chat_flow`` end-to-end and capture the observable side-effects
of the orchestrator: the messages it sends to the lead, the events it
publishes, the rows it persists, the WS notifications it emits.

Determinism: every UUID, datetime, and DB call is patched. Refactor
preserves behavior ⇔ snapshot diff = 0 byte-equal.

# [SALES-AGENT-ORCHESTRATOR-SNAPSHOT-S11B] -> docs/domains/sales-agent/redesign-2026-04/phases/S11-shared-lift-orchestrator-decomp.md
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

# ── Deterministic fixtures ──────────────────────────────────────────────

TENANT_ID = UUID("44444444-4444-4444-4444-444444444444")
CUSTOMER_ID = UUID("aaaaaaaa-1111-1111-1111-aaaaaaaaaaaa")
LEAD_ID = UUID("55555555-5555-5555-5555-555555555555")
SESSION_UUID_SEED = UUID("99999999-0000-0000-0000-000000000001")

FROZEN_NOW = datetime(2026, 4, 28, 12, 0, 0, tzinfo=UTC)

SNAPSHOT_DIR = Path(__file__).resolve().parents[3] / "snapshots" / "orchestrator"


# ── Captured shape ──────────────────────────────────────────────────────


@dataclass(slots=True)
class FlowCapture:
    """Container for every observable side-effect of one ``process_chat_flow``."""

    audit_log_messages: list[dict[str, Any]] = field(default_factory=list)
    journey_events: list[dict[str, Any]] = field(default_factory=list)
    domain_events: list[dict[str, Any]] = field(default_factory=list)
    ws_emissions: list[dict[str, Any]] = field(default_factory=list)
    output_manager_calls: list[dict[str, Any]] = field(default_factory=list)
    state_checkpoint_saves: list[dict[str, Any]] = field(default_factory=list)
    agent_invocations: list[dict[str, Any]] = field(default_factory=list)
    customer_traits_updates: list[dict[str, Any]] = field(default_factory=list)
    channel_adapter_calls: list[dict[str, Any]] = field(default_factory=list)


# ── Stubs / fakes ───────────────────────────────────────────────────────


def _customer_stub() -> SimpleNamespace:
    """Fixed CustomerProfileModel stub returned by IdentityService."""
    return SimpleNamespace(
        id=CUSTOMER_ID,
        full_name="Lead Test",
        traits={"first_name": "Lead", "last_name": "Test"},
    )


def _lead_stub() -> SimpleNamespace:
    """Fixed LeadModel stub returned by LeadRepository."""
    return SimpleNamespace(
        id=LEAD_ID,
        customer_id=CUSTOMER_ID,
        profile_data={
            "first_name": "Lead",
            "last_name": "Test",
        },
        custom_system_instruction=None,
        style_profile=None,
    )


def _tenant_stub() -> SimpleNamespace:
    """Fixed TenantModel stub returned by ``_fetch_tenant_config``."""
    return SimpleNamespace(
        id=TENANT_ID,
        config_json={"locale": "es-LA"},
    )


def _agent_result_stub() -> dict[str, Any]:
    """Deterministic graph response — single assistant message."""
    return {
        "messages": [
            {"role": "user", "content": "Hola, quiero info"},
            {"role": "assistant", "content": "¡Hola! Cuéntame más."},
        ],
        "current_state": "rapport",
        "lead_score": 5,
        "lead_data": {"name": "Lead"},
        "buying_signals": [],
        "objection_history": [],
        "qualification_answers": {},
        "turn_count": 1,
        "next_node": "qualifier",
        "close_strategy": None,
        "consecutive_questions": 0,
        "follow_up_cadence": None,
    }


# ── Determinism: freeze clocks + uuid ──────────────────────────────────


_DETERMINISTIC_UUID_BASE = "99999999-0000-0000-0000-{:012d}"


class _DeterministicUuid:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> UUID:
        self.calls += 1
        return UUID(_DETERMINISTIC_UUID_BASE.format(self.calls))


class _FrozenDatetime:
    @staticmethod
    def now(tz: object | None = None) -> datetime:
        return FROZEN_NOW


# ── Setup helpers ──────────────────────────────────────────────────────


def install_chat_module_patches(  # noqa: PLR0915 — orchestrator has many touchpoints
    monkeypatch: Any,
    capture: FlowCapture,
) -> None:
    """Patch every external touchpoint of ``chat.process_chat_flow``.

    The patch surface mirrors the orchestrator collaborators 1:1 so the
    snapshot is an end-to-end observation, not an isolated unit. When
    Sub-sprint B extracts AuditEmitter / IdentityResolver /
    ConversationPipeline, the patches stay where the call happens — only
    the call site moves between classes. Diff = 0 = behavior preserved.
    """
    chat_mod = "src.modules.sales_agent.application.orchestrator.chat"

    # 1. Frozen datetime (only used inside chat for human_mode timestamps)
    monkeypatch.setattr(f"{chat_mod}.datetime", _FrozenDatetime)

    # 2. Deterministic uuid4 (session_id + observability turn_id)
    monkeypatch.setattr(f"{chat_mod}.uuid.uuid4", _DeterministicUuid())

    # 3. Patch SessionLocal — return a MagicMock that stubs execute/flush/commit/rollback.
    fake_db = MagicMock(name="db_session")
    fake_db.commit = MagicMock()
    fake_db.flush = MagicMock()
    fake_db.rollback = MagicMock()
    fake_db.close = MagicMock()
    fake_db.add = MagicMock()
    # ``_fetch_tenant_config`` calls ``db.execute(select(TenantModel)...).scalars().first()``
    # so we shape execute().scalars().first() to return our tenant stub.
    fake_db.execute.return_value.scalars.return_value.first.return_value = _tenant_stub()
    monkeypatch.setattr(f"{chat_mod}.SessionLocal", lambda: fake_db)

    # 4. Patch ``set_tenant_id`` — record but no-op.
    monkeypatch.setattr(f"{chat_mod}.set_tenant_id", lambda _tid: None)

    # 5. Repos returned by ``_init_repos``.
    lead_repo = MagicMock(name="lead_repo")
    lead_repo.get_active_lead.return_value = None  # forces create_lead path
    lead_repo.create_lead.return_value = _lead_stub()
    lead_repo.close = MagicMock()

    identity_service = MagicMock(name="identity_service")
    identity_service.get_or_create_customer.return_value = (_customer_stub(), True)

    audit_repo = MagicMock(name="audit_repo")
    audit_repo.get_chat_history.return_value = []
    audit_repo.get_last_message.return_value = None  # new user

    def _capture_log_message(**kwargs: Any) -> None:
        capture.audit_log_messages.append(_serialize(kwargs))

    audit_repo.log_message.side_effect = _capture_log_message
    audit_repo.close = MagicMock()

    biz_repo = MagicMock(name="biz_repo")
    biz_repo.get_current_launch_product.return_value = (None, None)
    biz_repo.get_enrollment.return_value = None
    biz_repo.close = MagicMock()

    monkeypatch.setattr(
        f"{chat_mod}.ChatOrchestrator._init_repos",
        staticmethod(lambda _db: (lead_repo, identity_service, audit_repo, biz_repo)),
    )

    # 6. Journey event tracking — capture via crm_repos port.
    journey_repo = MagicMock(name="journey_repo")

    def _capture_track_event(**kwargs: Any) -> None:
        capture.journey_events.append(_serialize(kwargs))

    journey_repo.track_event.side_effect = _capture_track_event
    monkeypatch.setattr(
        "src.shared.links.ports.crm_repos.get_journey_event_repository",
        lambda _db: journey_repo,
    )

    # 7. Domain event publishing.
    def _capture_publish(event: Any, session: Any = None) -> None:
        del session
        capture.domain_events.append(
            {
                "event_name": event.event_name,
                "tenant_id": str(event.tenant_id),
                "payload": _serialize(event.payload),
            },
        )

    # Patch at definition site so the capture works wherever the call
    # originates (chat.py pre-S11B, audit_emitter.py post-extraction).
    monkeypatch.setattr("src.shared.domain.events.EventBus.publish", staticmethod(_capture_publish))

    # 8. Customer traits update — patch at IdentityResolver (post-S11B) so the
    #    capture works regardless of who's calling (chat.py legacy delegate or
    #    IdentityResolver.process_customer_lifecycle directly).
    def _capture_traits(_db: Any, customer: Any, incoming: Any) -> None:
        capture.customer_traits_updates.append(
            {
                "customer_id": str(customer.id),
                "metadata_keys": sorted(incoming.metadata.keys()) if incoming.metadata else [],
            },
        )

    monkeypatch.setattr(
        "src.modules.sales_agent.application.orchestrator.identity_resolver.IdentityResolver.update_customer_traits",
        staticmethod(_capture_traits),
    )

    # 9. StateRepository — instantiated inside ``process_chat_flow``.
    state_repo = MagicMock(name="state_repo")
    state_repo.get_active_checkpoint.return_value = None
    state_repo.deactivate = MagicMock()

    def _capture_save_checkpoint(**kwargs: Any) -> None:
        capture.state_checkpoint_saves.append(_serialize(kwargs))

    state_repo.save_checkpoint.side_effect = _capture_save_checkpoint
    monkeypatch.setattr(f"{chat_mod}.StateRepository", lambda _db: state_repo)

    # 10. TenantKnowledgeBuilder — fixed identity + voice strings.
    knowledge_builder = MagicMock(name="knowledge_builder")
    knowledge_builder.build_identity.return_value = "ID:test-brand"
    knowledge_builder.build_brand_voice.return_value = "VOICE:test-voice"
    monkeypatch.setattr(
        f"{chat_mod}.TenantKnowledgeBuilder",
        lambda _db: knowledge_builder,
    )

    # 11. Safety layer — pass-through (no modification).
    async def _safety_passthrough(text: str) -> tuple[str, bool]:
        return text, False

    safety_stub = SimpleNamespace(sanitize_content=_safety_passthrough)
    monkeypatch.setattr(
        "src.modules.sales_agent.infrastructure.external.safety_service.SafetyLayerService",
        lambda: safety_stub,
    )

    # 12. SemanticRouter — deterministic intent.
    monkeypatch.setattr(
        f"{chat_mod}.SemanticRouter.detect_and_accumulate",
        staticmethod(lambda _text, existing_signals, tenant_id: (None, 0.0, list(existing_signals))),
    )

    # 13. Observability handler factory — return a sentinel so we can verify
    #     the orchestrator forwards it as a callback.
    handler_sentinel = SimpleNamespace(name="OBS_HANDLER")
    monkeypatch.setattr(
        "src.modules.sales_agent.observability.recording.factory.build_sales_agent_callback_handler",
        lambda **_kw: handler_sentinel,
    )

    # 14. Tool dedup tracker — replace with a deterministic stand-in so the
    #     snapshot of ``initial_state`` is comparable across runs.
    class _DeterministicDedup:
        def __repr__(self) -> str:
            return "ToolCallDedupTracker(stub)"

    monkeypatch.setattr(
        "src.modules.sales_agent.application.orchestrator.tool_call_dedup.ToolCallDedupTracker",
        _DeterministicDedup,
    )

    # 15. Agent graph invocation — capture initial_state + return fixed result.
    async def _capture_ainvoke(initial_state: dict, config: dict | None = None) -> dict:
        capture.agent_invocations.append(
            {
                "initial_state": _normalize_state_for_snapshot(initial_state),
                "callbacks_kind": _summarize_callbacks((config or {}).get("callbacks", [])),
            },
        )
        return _agent_result_stub()

    monkeypatch.setattr(f"{chat_mod}.agent_app.ainvoke", _capture_ainvoke)

    # 16. WS manager — capture emit calls (assistant + human_mode).
    async def _capture_ws_emit(tenant_uuid: str, payload: dict) -> None:
        capture.ws_emissions.append(
            {
                "tenant_id": tenant_uuid,
                "payload": _serialize(payload),
            },
        )

    ws_module = "src.modules.sales_agent.infrastructure.ws_manager"
    monkeypatch.setattr(f"{ws_module}.ws_manager.emit", _capture_ws_emit)

    # 17. OutputManager — capture the actual delivery to the lead.
    async def _capture_output(
        user_id: str,
        text: str,
        _adapter: Any,
        channel_type: str,
    ) -> None:
        capture.output_manager_calls.append(
            {
                "user_id": user_id,
                "text": text,
                "channel_type": channel_type,
            },
        )

    monkeypatch.setattr(f"{chat_mod}.OutputManager.process_response", _capture_output)


def build_capturing_channel_adapter(capture: FlowCapture) -> Any:
    """Async-mock adapter that records ``set_typing_status`` + ``send_message``."""
    adapter = MagicMock(name="channel_adapter")

    async def _set_typing(user_id: str) -> None:
        capture.channel_adapter_calls.append(
            {"method": "set_typing_status", "user_id": user_id},
        )

    async def _send_message(msg: Any) -> None:
        capture.channel_adapter_calls.append(
            {
                "method": "send_message",
                "user_id": getattr(msg, "user_id", None),
                "text_preview": getattr(msg, "text", "")[:80],
            },
        )

    adapter.set_typing_status = _set_typing
    adapter.send_message = _send_message
    adapter.normalize_payload = MagicMock()
    return adapter


# ── Serialization ──────────────────────────────────────────────────────


_VOLATILE_STATE_KEYS = frozenset(
    {
        # Mock fixtures inject seed UUID in session_id; deterministic but
        # we keep an explicit allowlist so future fields are visible in
        # the snapshot diff.
    },
)


def _normalize_state_for_snapshot(state: dict[str, Any]) -> dict[str, Any]:
    """Project ``initial_state`` into a snapshot-stable shape.

    ``_tool_dedup_tracker`` lives on the state and has its own ``repr``
    stub; everything else is JSON-serializable after :func:`_serialize`.
    """
    cleaned = {k: v for k, v in state.items() if k not in _VOLATILE_STATE_KEYS}
    if "_tool_dedup_tracker" in cleaned:
        cleaned["_tool_dedup_tracker"] = repr(cleaned["_tool_dedup_tracker"])
    return _serialize(cleaned)


def _summarize_callbacks(callbacks: list[Any]) -> list[str]:
    """Return a stable string for each callback handler in the config."""
    return [getattr(cb, "name", type(cb).__name__) for cb in callbacks]


def _serialize(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_serialize(v) for v in value]
    if isinstance(value, SimpleNamespace):
        # Use only public attributes — mocks pollute __dict__ with internals.
        return {k: _serialize(v) for k, v in vars(value).items() if not k.startswith("_")}
    return value


def render_snapshot(capture: FlowCapture) -> str:
    """Render the captured flow as deterministic JSON."""
    payload = {
        "audit_log_messages": capture.audit_log_messages,
        "journey_events": capture.journey_events,
        "domain_events": capture.domain_events,
        "ws_emissions": capture.ws_emissions,
        "output_manager_calls": capture.output_manager_calls,
        "state_checkpoint_saves": capture.state_checkpoint_saves,
        "agent_invocations": capture.agent_invocations,
        "customer_traits_updates": capture.customer_traits_updates,
        "channel_adapter_calls": capture.channel_adapter_calls,
    }
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


# ── Snapshot file IO ───────────────────────────────────────────────────


def assert_matches_snapshot(actual: str, baseline_filename: str) -> None:
    """Compare ``actual`` JSON against the baseline file (byte-equal)."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    baseline_path = SNAPSHOT_DIR / baseline_filename
    if not baseline_path.exists():
        baseline_path.write_text(actual, encoding="utf-8")
        msg = f"Baseline {baseline_path} created. Commit it and re-run; this fail is expected on first run only."
        raise AssertionError(msg)

    expected = baseline_path.read_text(encoding="utf-8")
    if actual != expected:
        msg = (
            f"Snapshot diff vs {baseline_path}. The orchestrator changed "
            "shape — investigate before updating the baseline. If the new "
            "shape is intentional (Sub-sprint B refactor), manually "
            f"overwrite the file with this output:\n\n{actual}"
        )
        raise AssertionError(msg)


__all__ = [
    "CUSTOMER_ID",
    "FROZEN_NOW",
    "LEAD_ID",
    "SESSION_UUID_SEED",
    "SNAPSHOT_DIR",
    "TENANT_ID",
    "AsyncMock",
    "FlowCapture",
    "assert_matches_snapshot",
    "build_capturing_channel_adapter",
    "install_chat_module_patches",
    "render_snapshot",
]
