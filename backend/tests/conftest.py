import sys
import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# --- Mock missing optional dependencies for test environment ---
# passlib is only used at runtime for password hashing in IAM; not needed for tests.
for mod_name in ("passlib", "passlib.context", "passlib.hash"):
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

# --- Monkeypatch PostgreSQL Types for SQLite ---
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import CHAR, Text, TypeDecorator

from src.shared.domain.base_entity import Base


class MockJSONB(TypeDecorator):
    """SQLite doesn't support JSONB, so we map it to standard JSON or String"""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.JSONB())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        import json

        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        import json

        try:
            return json.loads(value)
        except Exception:  # noqa: BLE001 — test infrastructure resilience
            return {}


class MockUUID(TypeDecorator):
    """SQLite doesn't support UUID native type, map to CHAR(36)"""

    impl = CHAR(36)
    cache_ok = True

    def __init__(self, as_uuid=True):
        self.as_uuid = as_uuid
        super().__init__()

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.UUID(as_uuid=self.as_uuid))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if self.as_uuid:
            return uuid.UUID(value)
        return value


# Apply patches
postgresql.JSONB = MockJSONB
postgresql.UUID = MockUUID

# Importar el registry DESPUÉS del monkey-patch ``postgresql.JSONB/UUID``
# garantiza que cuando los modelos se cargan, sus columnas ya ven los Mock
# TypeDecorators (compatibles con SQLite). Si invertimos el orden, los
# modelos quedan ligados al ``postgresql.JSONB`` real → ``CompileError``
# al hacer ``Base.metadata.create_all`` sobre engine SQLite.
#
# Importar el registry acá también resuelve la flakiness de
# ``pytest-randomly``: SA evalúa ``relationship("OtherModel")`` strings
# durante ``configure_mappers()``; sin todos los modelos en el registro
# antes de la primera sesión, el primer test que dispare resolution
# crashea con ``InvalidRequestError`` (ej. ``LeadModel`` →
# ``AppointmentModel``). Patrón canónico exigido en ``main.py`` y
# ``admin/app.py``.
import src.shared.infrastructure.agent_observability_bootstrap
import src.shared.infrastructure.model_registry

# --- Fixtures ---


@pytest.fixture(autouse=True)
def _force_prompt_source_file(monkeypatch):
    """Force PROMPT_SOURCE=file for every test.

    Hermeticity: tests should not depend on DB availability for prompt resolution.
    Local dev has Docker postgres; CI test image does not. Without this fixture,
    tests that hit prompt_loader.render() fail in CI with connection errors.
    """
    from src.core.config import PromptSource, settings

    monkeypatch.setattr(settings, "PROMPT_SOURCE", PromptSource.FILE)


@pytest.fixture(autouse=True)
def _stub_copilot_observability_context(monkeypatch, request):
    """Stub ``ObservabilityContext`` so the orchestrator hot-path tests
    don't burn 30s of Postgres DNS retries trying to construct the real
    repos in a native WSL pytest run.

    Tests under ``tests/modules/copilot/observability/`` need the real
    context to assert persistence, so this fixture skips itself for that
    path — those tests use SQLite in-memory + explicit
    ``ObservabilityContext.start(...)`` calls.
    """
    if "tests/modules/copilot/observability" in request.fspath.strpath:
        return

    from contextlib import asynccontextmanager
    from unittest.mock import MagicMock

    @classmethod
    def _stub_start(cls, **kwargs):
        from uuid import uuid4

        @asynccontextmanager
        async def _noop_observe(**_kw):
            yield ctx

        ctx = MagicMock()
        ctx.tenant_id = kwargs.get("tenant_id") or uuid4()
        ctx.conversation_id = kwargs.get("conversation_id")
        ctx.user_id = kwargs.get("user_id")
        ctx.turn_id = kwargs.get("turn_id") or uuid4()
        ctx.langchain_config.return_value = {}
        ctx.set_turn_summary.return_value = None
        ctx.observe_turn = _noop_observe
        return ctx

    from src.modules.copilot.observability.recording.turn_envelope import (
        ObservabilityContext,
    )

    monkeypatch.setattr(ObservabilityContext, "start", _stub_start)


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Import all models to ensure they are registered and relationships can be resolved
    try:
        from src.modules.brand.infrastructure.models.avatar_model import (
            AvatarModel,
        )
        from src.modules.brand.infrastructure.models.brand_summary_model import (
            BrandSummaryModel,
        )
        from src.modules.brand.infrastructure.models.buyer_persona_model import (
            BuyerPersonaModel,
        )
        from src.modules.brand.infrastructure.models.extraction_trace_model import (
            BrandExtractionTrace,
        )
        from src.modules.brand.infrastructure.models.personality_model import (
            PersonalityProfileModel,
        )
        from src.modules.commercial_calendar.infrastructure.models.calendar_event_model import (
            CalendarEventModel,
        )
        from src.modules.connections.infrastructure.models.channel_connection_model import (
            ChannelConnectionModel,
        )
        from src.modules.copilot.infrastructure.models.conversation_model import (
            CopilotConversationModel,
        )
        from src.modules.copilot.infrastructure.models.inspiration_model import (
            CopilotInspirationModel,
        )
        from src.modules.copilot.infrastructure.models.mutation_journal_model import (
            MutationJournalModel,
        )
        from src.modules.copilot.infrastructure.models.pinned_memory_model import (
            CopilotPinnedMemoryModel,
        )
        from src.modules.copilot.infrastructure.models.routing_log_model import (
            RoutingLogModel,
        )
        from src.modules.copilot.infrastructure.models.trace_event_model import (
            CopilotTraceEventModel,
        )
        from src.modules.copilot.infrastructure.models.workflow_metric_model import (
            WorkflowMetricModel,
        )
        from src.modules.crm.infrastructure.models.lead_model import (
            LeadModel,
        )
        from src.modules.crm.infrastructure.models.lifecycle_transition_model import (
            LifecycleTransitionModel,
        )
        from src.modules.crm.infrastructure.models.nps_models import (
            NpsResponseModel,
            NpsSurveyModel,
        )
        from src.modules.crm.infrastructure.models.referral_code_model import (
            ReferralCodeModel,
        )
        from src.modules.crm.infrastructure.models.sale_model import (
            SaleModel,
        )
        from src.modules.iam.infrastructure.models.tenant_model import (
            TenantModel,
        )
        from src.modules.landing.infrastructure.models.landing_model import (
            LandingPageModel,
        )
        from src.modules.offer.infrastructure.models.knowledge_source_model import (
            KnowledgeSourceModel,
        )
        from src.modules.offer.infrastructure.models.launch_edition_model import (
            LaunchEditionModel,
        )
        from src.modules.offer.infrastructure.models.offer_asset_model import (
            OfferAssetModel,
        )
        from src.modules.offer.infrastructure.models.product_model import (
            ProductModel,
        )
        from src.modules.sales_agent.infrastructure.models.agent_state_checkpoint_model import (
            AgentStateCheckpointModel,
        )
        from src.modules.sales_agent.infrastructure.models.enrollment_model import (
            EnrollmentModel,
        )
        from src.modules.sales_agent.infrastructure.models.message_model import (
            MessageModel,
        )
        from src.modules.sales_agent.infrastructure.models.payment_grant_audit_model import (
            PaymentGrantAuditModel,
        )
        from src.modules.sales_agent.infrastructure.models.payment_link_model import (
            PaymentLinkModel,
        )
        from src.modules.sales_agent.infrastructure.models.payment_webhook_event_model import (
            PaymentWebhookEventModel,
        )
        from src.modules.sales_agent.infrastructure.models.scheduler_webhook_event_model import (
            SchedulerWebhookEventModel,
        )
        from src.modules.sales_agent.infrastructure.models.workflow_metric_model import (
            SalesAgentWorkflowMetricModel,
        )
        from src.modules.sales_agent.observability.persistence.models.llm_call_model import (
            SalesAgentLlmCallModel,
        )
        from src.modules.sales_agent.observability.persistence.models.routing_log_model import (
            SalesAgentRoutingLogModel,
        )
        from src.modules.sales_agent.observability.persistence.models.trace_event_model import (
            SalesAgentTraceEventModel,
        )
        from src.modules.scheduling.infrastructure.models.appointment_model import (
            AppointmentModel,
        )
        from src.modules.scheduling.infrastructure.models.booking_link import (
            BookingLink,
        )
        from src.modules.social_proof.infrastructure.models import (
            AuthorityItemModel,
            PlacementModel,
            TeamMemberModel,
            TestimonialModel,
        )
        from src.modules.tenant_domains.infrastructure.models.tenant_domain_model import (
            TenantDomainModel,
        )
        from src.modules.tenant_profile.infrastructure.models.tenant_profile_model import (
            TenantProfileModel,
        )
        from src.shared.infrastructure.llm.infrastructure.audit_model import (
            LLMConfigAuditModel,
        )
        from src.shared.infrastructure.llm.infrastructure.role_binding_model import (
            LLMRoleBindingModel,
        )
    except ImportError as e:
        print(f"Warning: Could not import some models: {e}")

    # Create tables
    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ──────────────────────────────────────────────────────────────────────────────
# Singleton isolation fixture (PI-11 PR-1 Fase 3, 2026-05-04)
#
# Class-level singletons leak state between tests.  Without this fixture:
#   - LLMFactory._instance holds a MultiRoleLLMRouter built with prod settings;
#     tests that monkeypatch settings see stale router.
#   - ChatOrchestrator._instance (sales_agent) persists buffer_service state
#     across tests → cross-test behaviour + SmartBufferService background leak.
#   - SemanticRouter._instance (sales_agent) caches routing rules per tenant;
#     next test with different tenant reuses stale rules.
#   - EventBus._handlers accumulates subscribers — origin PI.md § Origen
#     point 2 (TestDomainSubscribersRegistration leak).
#   - EventBusAdapter module-inference lru_cache retains stale filename→module
#     mappings when tests monkeypatch import structure.
#
# Singletons explicitly EXCLUDED (justified):
#   - ChannelRouterRegistry._instance (campaigns): bootstrap-once thread-safe
#     design; reset breaks campaigns tests that rely on pre-bootstrapped registry.
#   - MetaAPI._api_instance (connections): per-instance attribute (self._api_instance),
#     NOT class-level; garbage-collected with each test's instance.
#
# Ref: CONTRACT.md PR-1 § 1 (singleton inventory) + § 2 (fixture design)
# ──────────────────────────────────────────────────────────────────────────────


def _do_singleton_reset() -> None:
    """Perform class-level singleton + module-level cache resets.

    Called both pre-test (yield) and post-test (cleanup) to guarantee
    no state leaks INTO this test and no state leaks FROM this test.
    """
    # 1. LLMFactory._instance — MultiRoleLLMRouter holding ChatOpenAI clients
    #    with base_url/api_key from settings at construction time.
    #    Tests that monkeypatch settings need a clean factory to see the
    #    patched values when they call LLMFactory.get_service().
    from src.shared.infrastructure.llm.factory import LLMFactory

    LLMFactory._instance = None  # LLMFactory._instance — reset reason: stale router with prod settings

    # 2. ChatOrchestrator._instance (sales_agent) — compiled LangGraph +
    #    SmartBufferService with buffer state. Cross-test → next test reuses
    #    same orchestrator with leaked buffer state + _initialized=True flag.
    try:
        from src.modules.sales_agent.application.orchestrator.chat import ChatOrchestrator

        if ChatOrchestrator._instance is not None and hasattr(ChatOrchestrator._instance, "buffer_service"):
            # Clean up buffer_service before drop to prevent background task leak
            ChatOrchestrator._instance.buffer_service = None  # type: ignore[attr-defined]
        ChatOrchestrator._instance = (
            None  # ChatOrchestrator._instance — reset reason: buffer state + _initialized flag leak
        )
    except ImportError:
        pass  # sales_agent module may not be available in all test environments

    # 3. SemanticRouter._instance (sales_agent) — routing rules + tenant config
    #    snapshot. Tests with different tenants reuse stale routing rules.
    try:
        from src.modules.sales_agent.application.services.semantic_router import SemanticRouter

        SemanticRouter._instance = None  # SemanticRouter._instance — reset reason: tenant-scoped routing rules cached
    except ImportError:
        pass  # sales_agent module may not be available in all test environments

    # 4. EventBus._handlers — class-level dict accumulating subscribers.
    #    Origin PI.md § Origen point 2: TestDomainSubscribersRegistration leak
    #    causes handlers from test A to fire in test B (cross-test side effects).
    from src.shared.domain.events import EventBus

    EventBus.clear()  # EventBus._handlers — reset reason: subscriber handler leak cross-test (PI.md § Origen point 2)

    # 5. EventBusAdapter module-inference lru_cache — cached per calling-frame
    #    filename. Tests that monkeypatch import structure or run from different
    #    frame contexts get stale module name mappings.
    try:
        from src.shared.domain_events.outbox.application.event_bus_adapter import (
            _reset_module_inference_cache,
        )

        _reset_module_inference_cache()  # EventBusAdapter lru_cache — reset reason: stale filename→module mappings
    except ImportError:
        pass


def prime_cost_bridge(call_id: str, cost: "Decimal") -> None:  # noqa: F821 — Decimal imported lazily
    """Pre-stash a cost in the module-level TTL cache so callback handler tests
    can assert ``cost_usd > 0`` after T-1 LiteLLM cost bridge architecture.

    **Bridge architecture (PI-12 S1 T-1, 2026-05-05):**
    In production, ``CostRecorderCustomLogger.log_success_event()`` fires via the
    LiteLLM callback and calls ``_stash(litellm_call_id, cost)`` *before*
    LangChain's ``on_llm_end`` fires. Tests that mock ``LLMResult`` don't go through
    the LiteLLM proxy, so ``_stash`` is never called automatically.

    Test helpers call this function in test setup to simulate what the LiteLLM
    CustomLogger does in production: stash the cost in the shared TTL cache under
    ``call_id`` so that ``BaseAgentCallbackHandler._persist_llm_call()`` can
    retrieve it via ``pop_cost(call_id)`` during ``on_llm_end``.

    Decision D-T1bis-2 (04-tickets.yaml): using ``_stash`` from cost_recorder is
    the canonical bridge-priming mechanism for tests. Lifted to shared conftest per
    decision D-T1bis-3: pattern reused across sales_agent and copilot observability
    test suites.
    """
    from decimal import Decimal as _Decimal

    from src.shared.agent_observability.recording.cost_recorder import _stash

    _stash(call_id, _Decimal(str(cost)) if not isinstance(cost, _Decimal) else cost)


@pytest.fixture(autouse=True)
def _reset_singletons_between_tests() -> None:
    """Reset class-level singletons + module-level caches pre+post each test.

    PI-11 PR-1 Fase 3 (2026-05-04). Singleton inventory validated exhaustively
    via grep ``_instance = None|cls._instance|@lru_cache|@cache`` cross-codebase.

    See CONTRACT.md PR-1 § 1-2 for full singleton inventory + design rationale.
    """
    _do_singleton_reset()  # Pre-test reset
    yield
    _do_singleton_reset()  # Post-test cleanup (no state FROM this test leaks INTO next)
