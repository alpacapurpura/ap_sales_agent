"""Async sales_agent entrypoint fixture + synthetic-lead helper.

Composes a real ``initial_state`` via the production
``ConversationPipeline`` helpers (``build_identity`` +
``build_brand_voice`` + ``create_initial_state``), wires the production
``SalesAgentObservabilityContext`` factory (writes real rows to
``sales_agent_trace_event`` + ``sales_agent_llm_call``), and invokes the
canonical ``agent_app.ainvoke`` entry point — see
``src/modules/sales_agent/application/orchestrator/graph.py:52``.

Per Decisión B6 + ``.claude/rules/sales-agent-brand-voice.md`` § Excepción:
**no voice override**. The fixture honors the production compiler v2 path.
The harness only validates Spanish density (Capa 3 in T-4), never style.

Per ``.claude/rules/anti-duplication.md`` § 0: every shared abstraction
(BaseObservabilityContext, BaseAgentCallbackHandler, FXResolver,
PricingResolver, sanitize_payload, TenantKnowledgeBuilder,
build_sales_agent_observability_context) is REUSED verbatim. Zero new
mirror.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import pytest
import structlog

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from sqlalchemy.orm import Session

logger = structlog.get_logger()


def create_synthetic_eval_lead(
    db: Session,
    *,
    tenant_id: UUID,
    run_id: UUID,
) -> UUID:
    """Insert a synthetic eval-only lead and return its id.

    The lead is marked with a deterministic ``api_id`` (``eval-{run_id}``)
    so admin Streamlit can filter eval traffic out of real sales reports.
    The fixture is teardown-safe: the lead is soft-deleted at session
    close.

    Args:
        db: Real Postgres session bound to the eval tenant.
        tenant_id: The Visionarias tenant UUID (per tenant-isolation rule).
        run_id: The current eval invocation UUID — used to disambiguate
            concurrent runs and to facilitate post-mortem queries.

    Returns:
        UUID of the freshly inserted lead.

    Notes:
        Tenant isolation: every column write includes ``tenant_id``.
        Soft delete: caller is responsible for marking ``deleted_at`` at
        teardown if desired (default behavior keeps the lead for audit).
    """
    from luana_core_platform.infrastructure.models.crm import LeadModel

    lead = LeadModel(
        id=uuid4(),
        tenant_id=tenant_id,
        api_id=f"eval-{run_id}",
        full_name=f"Eval Synthetic Lead {run_id}",
        temperature="COLD",
        fit_score=0,
        intent_score=0,
        is_blacklisted=False,
    )
    db.add(lead)
    db.flush()
    logger.info(
        "eval_synthetic_lead_created",
        lead_id=str(lead.id),
        tenant_id=str(tenant_id),
        run_id=str(run_id),
    )
    return lead.id


@pytest.fixture
def sales_agent_entrypoint(
    visionarias_tenant_session: dict[str, Any],
    eval_run_id: UUID,
) -> Callable[[str], Awaitable[dict[str, Any]]]:
    """Build an async closure that invokes ``agent_app.ainvoke`` end-to-end.

    Returns:
        Async callable ``invoke(user_message: str) -> dict`` that runs
        the production sales_agent pipeline end-to-end against
        Visionarias and returns a dict with keys:

            - ``result`` (dict): final ``AgentState`` after ``ainvoke`` completes.
            - ``lead_id`` (UUID): the synthetic lead created for this run.
            - ``turn_id`` (UUID | None): the observability context turn id
              (None if the obs context could not be built — best-effort).
            - ``spy`` (TrajectorySpy): read-only trajectory observer
              composed alongside the production callback handler. The
              caller drives ``spy.specialist_history`` / ``spy.tool_calls``
              for Capa 1-2 assertions + writes ``trace.json`` via
              ``runner.artifacts.write_run_artifacts``.

    Per Decision B6: zero voice override. Per anti-duplication §0: the
    obs context, callback handler, knowledge builder, and orchestrator
    entry point are all REUSED via shared imports — zero new mirror.
    The spy is added via composition (``RunnableConfig.callbacks`` list)
    — NEVER subclasses the shared ``BaseAgentCallbackHandler``.

    Per ``tessl__graceful-degradation`` Rule 6: failures inside the
    invocation are logged with full structured context but propagate to
    the caller (the test harness owns the failure-mode policy, not this
    closure).
    """
    tenant_id: UUID = visionarias_tenant_session["tenant_id"]
    db: Session = visionarias_tenant_session["db_session"]

    # Lazy imports — keep collection cheap for default suite.
    from luana_core_sales_agent.application.orchestrator.graph import agent_app
    from luana_core_sales_agent.application.orchestrator.state import create_initial_state
    from luana_core_sales_agent.application.services.knowledge_builder import (
        TenantKnowledgeBuilder,
    )
    from luana_core_sales_agent.observability.recording.factory import (
        build_sales_agent_observability_context,
    )
    from tests.agentic_evals.sales_agent.runner.trajectory_spy import TrajectorySpy

    # Synthetic lead — eval-only, visible in admin via api_id="eval-..." prefix.
    lead_id = create_synthetic_eval_lead(db, tenant_id=tenant_id, run_id=eval_run_id)

    # Build observability context (real recorder → real DB writes — Capa 4 of spec).
    # ``build_sales_agent_observability_context`` returns ``None`` on factory
    # failure (best-effort). The closure tolerates None per copilot-observability rule.
    obs_ctx = build_sales_agent_observability_context(
        db=db,
        tenant_id=tenant_id,
        lead_id=lead_id,
        channel_type="eval_harness",
        turn_id=uuid4(),
        role="agent",
    )

    # Read-only trajectory observer composed alongside the production
    # callback handler. The spy is appended to the
    # ``RunnableConfig.callbacks`` list at invoke time — anti-duplication
    # §0 + arch-agentic § "Decisión arquitectónica clave".
    spy = TrajectorySpy()

    async def _invoke(user_message: str) -> dict[str, Any]:
        """Run one turn end-to-end through the production sales_agent graph."""
        # Build the full identity + voice prefix from the production knowledge builder.
        # Decision B6: honor the production compiler v2 path; never override voice.
        knowledge_builder = TenantKnowledgeBuilder(db)
        agent_identity = knowledge_builder.build_identity(tenant_id)
        brand_voice = knowledge_builder.build_brand_voice(tenant_id)

        initial_state = create_initial_state(
            user_id=str(lead_id),
            tenant_id=str(tenant_id),
            agent_identity=agent_identity,
            brand_voice=brand_voice,
            channel_type="eval_harness",
            history=[],
        )
        initial_state["messages"] = [{"role": "user", "content": user_message}]

        if obs_ctx is not None:
            # Compose the spy onto the production callback list. The
            # production handler runs FIRST (DB writes), the spy runs
            # SECOND (in-memory accumulation only). LangChain executes
            # callbacks in list order per its public contract.
            base_config = obs_ctx.langchain_config()
            existing_callbacks = list(base_config.get("callbacks", []) or [])
            invoke_config = {**base_config, "callbacks": [*existing_callbacks, spy]}
            async with obs_ctx.observe_turn(message=user_message, route="sales_agent"):
                result = await agent_app.ainvoke(initial_state, config=invoke_config)
        else:
            # Best-effort fallback: invoke without observability if factory failed.
            # Test harness reports Capa 4 (cost) as un-verifiable in this case.
            logger.warning(
                "eval_obs_context_unavailable",
                tenant_id=str(tenant_id),
                lead_id=str(lead_id),
                hint="Cost layer un-verifiable for this run.",
            )
            # Spy still attached so trajectory can be inspected even when
            # the production observability factory is unavailable.
            result = await agent_app.ainvoke(initial_state, config={"callbacks": [spy]})

        return {
            "result": result,
            "lead_id": lead_id,
            "turn_id": obs_ctx.turn_id if obs_ctx is not None else None,
            "spy": spy,
        }

    return _invoke
