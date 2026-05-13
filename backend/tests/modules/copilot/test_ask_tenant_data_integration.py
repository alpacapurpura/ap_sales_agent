"""F5 — ask_tenant_data integration tests (full pipeline, real DB seeds, stub LLMs)."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

import pytest

from luana_core_platform.core.context import set_tenant_id
from luana_core_copilot.application.data_access import (
    ConversationDataAccessProvider,
)
from luana_core_copilot.application.tools.ask_tenant_data.tool import (
    _ask_tenant_data_impl,
)
from luana_core_copilot.infrastructure.cache.data_query_cache import DataQueryCache
from luana_core_copilot.infrastructure.models.conversation_model import (
    CopilotConversationModel,
)
from luana_core_crm.copilot_provider.data_access import CrmDataAccessProvider
from luana_core_offer_studio.copilot_provider.data_access import OfferDataAccessProvider
from luana_core_platform.infrastructure.models.crm import LeadModel
from tests.modules.offer.conftest import create_product_model

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.orm import Session

TENANT = uuid.UUID("0b51bee5-0000-4000-8000-000000000001")
USER = uuid.UUID("0b51bee5-1111-4000-8000-000000000001")


@pytest.fixture
def tenant_context() -> Iterator[None]:
    set_tenant_id(TENANT)
    try:
        yield
    finally:
        set_tenant_id(None)


@dataclass
class _StubResp:
    content: str


class _ScriptedLLM:
    """LLM stub returning a different payload per invocation."""

    def __init__(self, scripts: list[str]) -> None:
        self.scripts = list(scripts)
        self.calls: list[Any] = []

    def invoke(self, messages: Any, **_kwargs: Any) -> _StubResp:
        # ``**_kwargs`` absorbs LangChain's ``config={"tags": [...]}`` (TP3 B1
        # internal-LLM stream filter) so the stub stays a drop-in replacement.
        self.calls.append(messages)
        return _StubResp(content=self.scripts.pop(0))


def _seed_offer(db: Session, name: str = "Programa Propósito y Prosperidad") -> None:
    offer = create_product_model(TENANT, name=name, status="active")
    offer.created_at = datetime.now(timezone.utc) - timedelta(days=3)
    db.add(offer)
    db.flush()


def _seed_leads(db: Session, count: int) -> None:
    # Spread leads across the past few minutes (not days) so every row
    # lands inside the current ISO week regardless of which weekday the
    # suite happens to run on. Using ``days=i % 5`` previously broke the
    # ``esta semana`` assertion every Monday because the ISO week resets
    # at 00:00 Mon and the older rows landed in the prior week.
    now = datetime.now(timezone.utc)
    for i in range(count):
        db.add(
            LeadModel(
                id=uuid.uuid4(),
                tenant_id=TENANT,
                whatsapp_id=f"wa-int-{i}",
                fit_score=0,
                intent_score=0,
                temperature="COLD",
                is_blacklisted=False,
                last_interaction_date=now - timedelta(minutes=i),
                profile_data={},
                key_objections_history=[],
            ),
        )
    db.flush()


def _seed_conversations(db: Session, count: int) -> None:
    # Same weekday-independence rationale as ``_seed_leads`` — spread
    # across minutes so every row stays inside the current ISO week.
    now = datetime.now(timezone.utc)
    for i in range(count):
        db.add(
            CopilotConversationModel(
                id=uuid.uuid4(),
                tenant_id=TENANT,
                user_id=USER,
                title=f"Conv {i}",
                messages=[],
                created_at=now - timedelta(minutes=i),
                updated_at=now - timedelta(minutes=i),
                message_count=0,
                total_tokens=0,
                title_auto_generated=False,
            ),
        )
    db.flush()


def _accessors(db: Session) -> tuple:
    return (
        ConversationDataAccessProvider(db_factory=lambda: db),
        OfferDataAccessProvider(db_factory=lambda: db),
        CrmDataAccessProvider(db_factory=lambda: db),
    )


@pytest.mark.asyncio
async def test_lead_count_question_returns_number(
    db: Session,
    tenant_context: None,
) -> None:
    _seed_leads(db, count=4)

    intent_llm = _ScriptedLLM(
        [
            json.dumps(
                {
                    "kind": "lead_count",
                    "name_query": None,
                    "period_phrase": "esta semana",
                    "channel": None,
                    "confidence": 0.9,
                },
            ),
        ],
    )
    synth_llm = _ScriptedLLM(["Esta semana te escribieron 4 personas."])

    payload = await _ask_tenant_data_impl(
        question="cuántas personas escribieron esta semana",
        output_channel="chat",
        db=db,
        llm_intent=intent_llm,
        llm_synth=synth_llm,
        accessors=_accessors(db),
        cache=DataQueryCache(redis=None),
    )
    data = json.loads(payload)
    assert data["status"] == "ok"
    assert data["kind"] == "lead_count"
    assert data["metadata"]["result_count"] == 4
    assert "4" in data["answer"]


@pytest.mark.asyncio
async def test_offer_lookup_returns_summary_for_fuzzy_match(
    db: Session,
    tenant_context: None,
) -> None:
    _seed_offer(db, name="Programa Propósito y Prosperidad")

    intent_llm = _ScriptedLLM(
        [
            json.dumps(
                {
                    "kind": "offer_lookup",
                    "name_query": "propósito",
                    "period_phrase": None,
                    "channel": None,
                    "confidence": 0.95,
                },
            ),
        ],
    )
    synth_llm = _ScriptedLLM(
        ["Programa Propósito y Prosperidad: oferta activa de Nicolify."],
    )

    payload = await _ask_tenant_data_impl(
        question="dame resumen del programa propósito",
        output_channel="chat",
        db=db,
        llm_intent=intent_llm,
        llm_synth=synth_llm,
        accessors=_accessors(db),
        cache=DataQueryCache(redis=None),
    )
    data = json.loads(payload)
    assert data["status"] == "ok"
    assert data["kind"] == "offer_lookup"
    assert data["metadata"]["result_count"] >= 1


@pytest.mark.asyncio
async def test_conversation_count_question(
    db: Session,
    tenant_context: None,
) -> None:
    _seed_conversations(db, count=3)

    intent_llm = _ScriptedLLM(
        [
            json.dumps(
                {
                    "kind": "conversation_count",
                    "name_query": None,
                    "period_phrase": "esta semana",
                    "channel": None,
                    "confidence": 0.85,
                },
            ),
        ],
    )
    synth_llm = _ScriptedLLM(["Tuviste 3 conversaciones esta semana."])

    payload = await _ask_tenant_data_impl(
        question="cuántas conversaciones tuve esta semana",
        output_channel="chat",
        db=db,
        llm_intent=intent_llm,
        llm_synth=synth_llm,
        accessors=_accessors(db),
        cache=DataQueryCache(redis=None),
    )
    data = json.loads(payload)
    assert data["status"] == "ok"
    assert data["kind"] == "conversation_count"
    assert data["metadata"]["result_count"] == 3


@pytest.mark.asyncio
async def test_zero_results_short_circuits_without_synth_llm(
    db: Session,
    tenant_context: None,
) -> None:
    """No leads in window → synthesizer's deterministic empty_window reply."""
    intent_llm = _ScriptedLLM(
        [
            json.dumps(
                {
                    "kind": "lead_count",
                    "name_query": None,
                    "period_phrase": "esta semana",
                    "channel": None,
                    "confidence": 0.8,
                },
            ),
        ],
    )
    synth_llm = _ScriptedLLM(["LLM should not be called for empty_window"])

    payload = await _ask_tenant_data_impl(
        question="cuántas personas escribieron esta semana",
        output_channel="chat",
        db=db,
        llm_intent=intent_llm,
        llm_synth=synth_llm,
        accessors=_accessors(db),
        cache=DataQueryCache(redis=None),
    )
    data = json.loads(payload)
    assert data["status"] == "ok"
    assert data["metadata"]["result_count"] == 0
    assert data["metadata"]["flags"]["empty_window"] is True
    assert synth_llm.calls == []  # short-circuit confirmed


@pytest.mark.asyncio
async def test_unknown_intent_short_circuits(
    db: Session,
    tenant_context: None,
) -> None:
    intent_llm = _ScriptedLLM(
        [
            json.dumps(
                {
                    "kind": "no-existe",  # unknown
                    "name_query": None,
                    "period_phrase": None,
                    "channel": None,
                    "confidence": 0.1,
                },
            ),
        ],
    )
    synth_llm = _ScriptedLLM(["LLM should not be called for unknown intent"])

    payload = await _ask_tenant_data_impl(
        question="recomendame un postre",
        output_channel="chat",
        db=db,
        llm_intent=intent_llm,
        llm_synth=synth_llm,
        accessors=_accessors(db),
        cache=DataQueryCache(redis=None),
    )
    data = json.loads(payload)
    assert data["kind"] == "unknown"
    assert "no entendí" in data["answer"].lower()
    assert synth_llm.calls == []


@pytest.mark.asyncio
async def test_no_tenant_returns_error_payload(db: Session) -> None:
    """No tenant_id in context → graceful error response."""
    set_tenant_id(None)
    payload = await _ask_tenant_data_impl(
        question="cuántas",
        db=db,
        accessors=_accessors(db),
        cache=DataQueryCache(redis=None),
    )
    data = json.loads(payload)
    assert data["status"] == "error"
    assert "tenant" in data["message"].lower()


@pytest.mark.asyncio
async def test_cache_hit_returns_cached_payload_without_llm_calls(
    db: Session,
    tenant_context: None,
) -> None:
    cached_payload = json.dumps(
        {
            "status": "ok",
            "kind": "lead_count",
            "answer": "Cached answer (12).",
            "metadata": {"result_count": 12},
            "llm_content": "Cached answer (12).",
        },
    )

    class _PreloadedCache:
        def __init__(self) -> None:
            self.set_calls: list[Any] = []

        def get(self, key: str) -> str | None:
            return cached_payload

        def set(self, *a: Any, **k: Any) -> None:
            self.set_calls.append((a, k))

    intent_llm = _ScriptedLLM(["LLM must not be called on cache hit"])
    synth_llm = _ScriptedLLM(["LLM must not be called on cache hit"])

    payload = await _ask_tenant_data_impl(
        question="cuántas personas escribieron esta semana",
        output_channel="chat",
        db=db,
        llm_intent=intent_llm,
        llm_synth=synth_llm,
        accessors=_accessors(db),
        cache=_PreloadedCache(),
    )
    assert payload == cached_payload
    assert intent_llm.calls == []
    assert synth_llm.calls == []
