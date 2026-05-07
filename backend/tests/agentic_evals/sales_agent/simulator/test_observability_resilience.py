"""T-5 acceptance tests — EvalSimulator observability subclass resilience.

Covers acceptance criteria:

* **A1** — ``EvalSimulator{ObservabilityContext,CallbackHandler}`` subclass
  the shared ``BaseObservabilityContext`` / ``BaseAgentCallbackHandler``
  (anti-duplication §0 — NO mirror).
* **A2** — Mandatory H5 ``eval_metadata`` jsonb fields enforced per row
  written (eval_run_kind / archetype_slug / actor_profile_id / trial_n /
  simulation_id / run_id).
* **A3** — Best-effort writes: a persist failure logs a structured
  warning and lets the simulation continue (per
  ``.claude/rules/copilot-observability.md`` cement).

Out of scope here (covered by T-9 arch fitness gates):

* ``test_simulator_no_mirrors_shared.py`` — basename anti-mirror scan
* ``test_simulator_writes_eval_kind_tag.py`` — DB property test for tag
* ``test_eval_simulator_observability_invariants.py`` — spec registry +
  table existence + post-bootstrap symbol resolution

Tests opt out of the ``eval`` autouse marker via ``pytestmark =
pytest.mark.no_eval`` so they run on default CI without ``--run-evals``.

# voseo-allowed: docstring quotes glossary check artifact for arch fitness gate
"""

# NO ``from __future__ import annotations`` — story-wide cement (T-4).

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from src.shared.agent_observability.recording.base_callback_handler import (
    BaseAgentCallbackHandler,
)
from src.shared.agent_observability.recording.turn_envelope import (
    BaseObservabilityContext,
)
from tests.agentic_evals.sales_agent.simulator._internal.observability import (
    EvalSimulatorCallbackHandler,
    EvalSimulatorLlmCallRepository,
    EvalSimulatorObservabilityContext,
    EvalSimulatorTraceEventRepository,
    build_eval_metadata,
    build_eval_simulator_observability_context,
)

# Opt out of the ``eval`` autouse marker so this runs on default CI.
pytestmark = pytest.mark.no_eval


# ───────────────────────────────────────────────────────────────────────
# Fixtures — shared eval_metadata + factory helpers
# ───────────────────────────────────────────────────────────────────────


@pytest.fixture
def simulation_ids() -> dict[str, Any]:
    """Return a deterministic-shape dict of UUIDs + scalars for one sim."""
    return {
        "simulation_id": uuid4(),
        "run_id": uuid4(),
        "tenant_id": uuid4(),
        "archetype_slug": "ecommerce-fashion-beauty",
        "actor_profile_id": "lead_frio_impaciente_v1",
        "trial_n": 0,
    }


@pytest.fixture
def valid_eval_metadata(simulation_ids: dict[str, Any]) -> dict[str, Any]:
    """Build the H5-complete metadata dict via the canonical helper."""
    return build_eval_metadata(
        archetype_slug=simulation_ids["archetype_slug"],
        actor_profile_id=simulation_ids["actor_profile_id"],
        trial_n=simulation_ids["trial_n"],
        simulation_id=simulation_ids["simulation_id"],
        run_id=simulation_ids["run_id"],
    )


@pytest.fixture
def fake_session() -> MagicMock:
    """Sync SQLAlchemy ``Session`` mock — captures ``add`` / ``flush`` /
    ``commit`` / ``rollback`` for assertions without touching a real DB."""
    session = MagicMock()
    session.add = MagicMock()
    session.flush = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.execute = MagicMock()
    return session


# ───────────────────────────────────────────────────────────────────────
# A1 — Subclass inheritance (anti-mirror discipline)
# ───────────────────────────────────────────────────────────────────────


class TestSubclassInheritance:
    """Acceptance A1 — subclasses inherit from shared base, no mirror."""

    def test_observability_context_subclasses_shared_base(self) -> None:
        """``EvalSimulatorObservabilityContext`` MUST inherit from shared base."""
        assert issubclass(
            EvalSimulatorObservabilityContext,
            BaseObservabilityContext,
        ), (
            "EvalSimulatorObservabilityContext MUST subclass "
            "BaseObservabilityContext (shared/agent_observability) — "
            "see anti-duplication.md §0 (NO mirror, only subclass)."
        )

    def test_callback_handler_subclasses_shared_base(self) -> None:
        """``EvalSimulatorCallbackHandler`` MUST inherit from shared base."""
        assert issubclass(
            EvalSimulatorCallbackHandler,
            BaseAgentCallbackHandler,
        ), "EvalSimulatorCallbackHandler MUST subclass BaseAgentCallbackHandler — anti-duplication.md §0."

    def test_callback_handler_overrides_only_two_abstract_persisters(self) -> None:
        """Template Method discipline — only the 2 persisters overridden.

        The 8 LangChain callbacks (``on_chat_model_start`` / ``on_llm_end`` / etc)
        + ``_persist_llm_call`` skeleton MUST stay on the shared base. If
        the subclass redefines them, the LangChain plumbing diverges and
        the anti-mirror gate fails.
        """
        own_funcs = {
            name
            for name, val in vars(EvalSimulatorCallbackHandler).items()
            if callable(val) and not name.startswith("__")
        }
        # Whitelist: 2 abstract overrides per Template Method contract.
        # Anything else means the subclass is duplicating shared logic.
        expected = {"_persist_llm_call_row", "_persist_trace_event_row"}
        unexpected = own_funcs - expected
        assert not unexpected, (
            "EvalSimulatorCallbackHandler must override ONLY "
            f"{sorted(expected)} (Template Method). Got extras: {sorted(unexpected)}. "
            "Move logic to shared base or add to whitelist with rationale."
        )

    def test_observability_context_overrides_only_three_abstract_hooks(self) -> None:
        """Lifecycle locked methods stay on shared base; subclass overrides 3 hooks."""
        own_funcs = {
            name
            for name, val in vars(EvalSimulatorObservabilityContext).items()
            if callable(val) and not name.startswith("__")
        }
        expected = {
            "_add_trace_event",
            "_aggregate_totals",
            "_legacy_compat_keys_or_empty",
            "_most_used_model",  # private helper for _aggregate_totals
            "start",  # factory @classmethod
        }
        unexpected = own_funcs - expected
        assert not unexpected, (
            "EvalSimulatorObservabilityContext must override ONLY the 3 abstract "
            f"hooks (+ private _most_used_model + start factory). Got extras: {sorted(unexpected)}. "
            "Move logic to shared base — observe_turn / _write_turn_* / set_turn_* / "
            "langchain_config / _commit_session are LOCKED on the base."
        )


# ───────────────────────────────────────────────────────────────────────
# A2 — Mandatory H5 metadata enforcement (per row)
# ───────────────────────────────────────────────────────────────────────


class TestMandatoryEvalMetadata:
    """Acceptance A2 — H5 mandatory keys per row written.

    Defense in depth — validation at 3 levels:
    1. ``build_eval_metadata`` returns the 6 keys verbatim.
    2. ``EvalSimulatorCallbackHandler.__post_init__`` rejects partial dicts.
    3. ``EvalSimulatorTraceEventRepository.add`` re-asserts before persisting.
    """

    def test_build_eval_metadata_emits_six_canonical_keys(
        self,
        simulation_ids: dict[str, Any],
    ) -> None:
        """The helper output is the SSoT shape consumed by the registry."""
        meta = build_eval_metadata(
            archetype_slug=simulation_ids["archetype_slug"],
            actor_profile_id=simulation_ids["actor_profile_id"],
            trial_n=simulation_ids["trial_n"],
            simulation_id=simulation_ids["simulation_id"],
            run_id=simulation_ids["run_id"],
        )
        assert set(meta) == {
            "eval_run_kind",
            "archetype_slug",
            "actor_profile_id",
            "trial_n",
            "simulation_id",
            "run_id",
        }
        # eval_run_kind is the constant the arch fitness gate filters on.
        assert meta["eval_run_kind"] == "simulator"
        assert meta["archetype_slug"] == simulation_ids["archetype_slug"]
        assert meta["actor_profile_id"] == simulation_ids["actor_profile_id"]
        assert isinstance(meta["trial_n"], int)
        # UUIDs serialised to str for jsonb storage.
        assert meta["simulation_id"] == str(simulation_ids["simulation_id"])
        assert meta["run_id"] == str(simulation_ids["run_id"])

    def test_callback_handler_rejects_partial_metadata_at_construction(
        self,
        simulation_ids: dict[str, Any],
        fake_session: MagicMock,
    ) -> None:
        """Missing any of the 6 H5 keys raises at __post_init__."""
        partial_meta = {"eval_run_kind": "simulator"}  # missing 5
        with pytest.raises(ValueError, match="missing mandatory H5 keys"):
            EvalSimulatorCallbackHandler(
                tenant_id=simulation_ids["tenant_id"],
                turn_id=uuid4(),
                pricing_resolver=MagicMock(),
                fx_resolver=MagicMock(),
                tenant_currency="USD",
                role="agent",
                llm_call_repo=EvalSimulatorLlmCallRepository(fake_session),
                trace_repo=EvalSimulatorTraceEventRepository(fake_session),
                db_session=fake_session,
                eval_metadata=partial_meta,
            )

    def test_observability_context_rejects_partial_metadata_at_construction(
        self,
        simulation_ids: dict[str, Any],
        fake_session: MagicMock,
    ) -> None:
        """Same H5 invariant on the context subclass __post_init__."""
        partial_meta = {"eval_run_kind": "simulator"}
        with pytest.raises(ValueError, match="missing mandatory H5 keys"):
            EvalSimulatorObservabilityContext(
                tenant_id=simulation_ids["tenant_id"],
                turn_id=uuid4(),
                callback_handler=MagicMock(),
                trace_repo=EvalSimulatorTraceEventRepository(fake_session),
                llm_call_repo=EvalSimulatorLlmCallRepository(fake_session),
                eval_metadata=partial_meta,
            )

    def test_trace_event_repo_rejects_partial_metadata_at_persist(
        self,
        simulation_ids: dict[str, Any],
        fake_session: MagicMock,
    ) -> None:
        """Defense-in-depth at row write — even if construction was bypassed."""
        repo = EvalSimulatorTraceEventRepository(fake_session)
        with pytest.raises(ValueError, match="missing mandatory H5 keys"):
            repo.add(
                tenant_id=simulation_ids["tenant_id"],
                turn_id=uuid4(),
                span_id=uuid4(),
                event_type="turn_start",
                eval_metadata={"eval_run_kind": "simulator"},  # partial
            )

    def test_callback_handler_persisters_inject_metadata_into_kwargs(
        self,
        simulation_ids: dict[str, Any],
        valid_eval_metadata: dict[str, Any],
        fake_session: MagicMock,
    ) -> None:
        """``_persist_llm_call_row`` + ``_persist_trace_event_row`` MUST
        propagate eval_metadata + channel_type='eval_simulator' to repos."""
        llm_repo = MagicMock(spec=EvalSimulatorLlmCallRepository)
        trace_repo = MagicMock(spec=EvalSimulatorTraceEventRepository)
        handler = EvalSimulatorCallbackHandler(
            tenant_id=simulation_ids["tenant_id"],
            turn_id=uuid4(),
            pricing_resolver=MagicMock(),
            fx_resolver=MagicMock(),
            tenant_currency="USD",
            role="agent",
            llm_call_repo=llm_repo,
            trace_repo=trace_repo,
            db_session=fake_session,
            eval_metadata=valid_eval_metadata,
        )

        # Drive the override directly with synthetic kwargs (the shared
        # base would call us with the full row payload).
        handler._persist_llm_call_row(
            tenant_id=simulation_ids["tenant_id"],
            turn_id=uuid4(),
            span_id=uuid4(),
            provider="openai",
            model_requested="gpt-5-nano",
            model_responded="gpt-5-nano",
            input_tokens=42,
            output_tokens=10,
            cached_read_tokens=0,
            cached_write_tokens=0,
            reasoning_tokens=0,
            pricing_version_id=uuid4(),
            input_unit_cost_usd=Decimal("0.0000001"),
            output_unit_cost_usd=Decimal("0.0000004"),
            cached_read_unit_cost_usd=Decimal(0),
            cost_usd=Decimal("0.000001"),
            tenant_currency="USD",
            fx_rate_to_tenant=Decimal(1),
            fx_rate_source="constant",
            cost_tenant_currency=Decimal("0.000001"),
            started_at=datetime.now(tz=timezone.utc),
            duration_ms=100,
            status="ok",
            error_type=None,
            role="agent",
        )
        # llm_call_repo.add was called with eval_metadata + channel_type
        assert llm_repo.add.call_count == 1
        kwargs = llm_repo.add.call_args.kwargs
        assert kwargs["channel_type"] == "eval_simulator"
        assert kwargs["lead_id"] is None
        assert kwargs["eval_metadata"] == valid_eval_metadata

        handler._persist_trace_event_row(
            tenant_id=simulation_ids["tenant_id"],
            turn_id=uuid4(),
            span_id=uuid4(),
            event_type="llm_call",
            name="openai.gpt-5-nano",
            data={"foo": "bar"},
            duration_ms=120,
            status="ok",
        )
        assert trace_repo.add.call_count == 1
        kwargs = trace_repo.add.call_args.kwargs
        assert kwargs["channel_type"] == "eval_simulator"
        assert kwargs["eval_metadata"] == valid_eval_metadata
        assert kwargs["event_type"] == "llm_call"


# ───────────────────────────────────────────────────────────────────────
# A3 — Best-effort writes — failure logs warning, never raises
# ───────────────────────────────────────────────────────────────────────


@dataclass
class _ExplodingRepo:
    """Trace repo stub that raises on every ``add`` call.

    Exercises the inherited ``BaseObservabilityContext._write_turn_*``
    outer try/except wrapper: the structured warning lands and the body
    returns normally — caller (the simulation loop) never sees the
    exception.
    """

    db: Any = None

    def __post_init__(self) -> None:
        """Provide a fake session so ``_commit_session`` doesn't NPE."""
        if self.db is None:
            session = MagicMock()
            session.commit = MagicMock(return_value=None)
            self.db = session

    def add(self, **_kwargs: Any) -> None:
        """Always blow up to simulate a DB outage / model-class mismatch."""
        msg = "synthetic persist failure (simulator A3 resilience probe)"
        raise RuntimeError(msg)


class TestPersistFailureResilience:
    """Acceptance A3 — best-effort writes, simulation continues on failure."""

    def test_persist_failure_logs_warning_no_raise(
        self,
        simulation_ids: dict[str, Any],
        valid_eval_metadata: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Headline acceptance test — required by 06-tickets.yaml T-5 A3.

        Wiring: ``EvalSimulatorObservabilityContext._add_trace_event``
        catches its own ``trace_repo.add`` failure AND the inherited
        ``_write_turn_start`` adds a second-layer ``try/except`` so the
        outer caller (simulation loop) never sees an exception.

        Asserts:
        1. No exception bubbles out of ``_write_turn_start``.
        2. structlog warning event ``eval_simulator_obs_add_trace_event_failed``
           is emitted by our subclass override.

        We monkeypatch the module-level ``logger.warning`` directly because
        structlog's default configuration emits via a ``ConsoleRenderer``
        pipeline that does not flow through pytest's ``caplog`` (caplog
        hooks the stdlib ``logging`` root only). This pattern is
        consistent with how the wider codebase asserts structlog events
        (e.g. ``backend/tests/modules/sales_agent/observability/test_callback_handler.py``).
        """
        from tests.agentic_evals.sales_agent.simulator._internal import (
            observability as obs_mod,
        )

        captured_events: list[tuple[str, dict[str, Any]]] = []

        def _capturing_warning(event: str, **kw: Any) -> None:
            captured_events.append((event, kw))

        monkeypatch.setattr(obs_mod.logger, "warning", _capturing_warning)

        ctx = EvalSimulatorObservabilityContext(
            tenant_id=simulation_ids["tenant_id"],
            turn_id=uuid4(),
            callback_handler=MagicMock(),
            trace_repo=_ExplodingRepo(),
            llm_call_repo=MagicMock(),
            eval_metadata=valid_eval_metadata,
        )

        # No exception propagates — best-effort contract.
        ctx._write_turn_start(
            message="hola, queremos info",
            route="sales_agent",
            attachments=[],
        )

        # Structured warning emitted by our subclass override.
        warning_events = [evt for evt, _ in captured_events]
        assert "eval_simulator_obs_add_trace_event_failed" in warning_events, (
            f"Expected structlog warning 'eval_simulator_obs_add_trace_event_failed' "
            f"to be emitted. Captured events: {warning_events}"
        )

        # Verify structured fields carried the breadcrumbs operators need.
        matched = [kw for evt, kw in captured_events if evt == "eval_simulator_obs_add_trace_event_failed"]
        assert matched, "warning event captured but no kwargs"
        assert matched[0]["event_type"] == "turn_start"
        assert "synthetic persist failure" in matched[0]["error"]
        assert matched[0]["simulation_id"] == valid_eval_metadata["simulation_id"]

    def test_aggregate_totals_failure_returns_empty_no_raise(
        self,
        simulation_ids: dict[str, Any],
        valid_eval_metadata: dict[str, Any],
    ) -> None:
        """``_aggregate_totals`` catches DB query failure and returns zeros.

        Same best-effort discipline applied to the turn_end path — without
        this, a stale schema on the test DB would propagate to the caller
        and break the simulation mid-loop.
        """
        broken_session = MagicMock()
        broken_session.execute = MagicMock(side_effect=RuntimeError("boom"))
        broken_session.flush = MagicMock(return_value=None)

        broken_repo = MagicMock()
        broken_repo.db = broken_session

        ctx = EvalSimulatorObservabilityContext(
            tenant_id=simulation_ids["tenant_id"],
            turn_id=uuid4(),
            callback_handler=MagicMock(),
            trace_repo=MagicMock(),
            llm_call_repo=broken_repo,
            eval_metadata=valid_eval_metadata,
        )
        # Returns zero shape, never raises — observability never breaks turn.
        totals = ctx._aggregate_totals()
        assert totals["llm_call_count"] == 0
        assert totals["total_input_tokens"] == 0
        assert totals["total_output_tokens"] == 0
        assert totals["total_cost_usd"] == "0"

    def test_factory_swallows_construction_failure_returns_none(
        self,
        simulation_ids: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``build_eval_simulator_observability_context`` returns None on
        construction failure rather than raising — the simulator falls
        back to running without observability (per copilot-resilience cement).
        """
        # Monkeypatch ``TenantBillingConfigRepository`` to raise on construction.
        from tests.agentic_evals.sales_agent.simulator._internal import observability as obs_mod

        def _exploding_billing_repo(_db: Any) -> Any:
            msg = "synthetic billing repo construction failure"
            raise RuntimeError(msg)

        monkeypatch.setattr(
            obs_mod,
            "TenantBillingConfigRepository",
            _exploding_billing_repo,
        )

        result = build_eval_simulator_observability_context(
            db=MagicMock(),
            tenant_id=simulation_ids["tenant_id"],
            archetype_slug=simulation_ids["archetype_slug"],
            actor_profile_id=simulation_ids["actor_profile_id"],
            trial_n=simulation_ids["trial_n"],
            simulation_id=simulation_ids["simulation_id"],
            run_id=simulation_ids["run_id"],
            turn_id=uuid4(),
        )
        assert result is None, (
            "Factory must swallow construction failure and return None per "
            "best-effort observability cement — caller falls back to "
            "running without obs."
        )

    def test_factory_returns_none_when_tenant_id_missing(
        self,
        simulation_ids: dict[str, Any],
    ) -> None:
        """Hard precondition — tenant_id None means no observability wired."""
        result = build_eval_simulator_observability_context(
            db=MagicMock(),
            tenant_id=None,  # type: ignore[arg-type]
            archetype_slug=simulation_ids["archetype_slug"],
            actor_profile_id=simulation_ids["actor_profile_id"],
            trial_n=simulation_ids["trial_n"],
            simulation_id=simulation_ids["simulation_id"],
            run_id=simulation_ids["run_id"],
            turn_id=uuid4(),
        )
        assert result is None
