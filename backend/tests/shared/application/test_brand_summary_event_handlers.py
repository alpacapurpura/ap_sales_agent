"""F3 — handler subscribes to ``brand_section_updated`` and enqueues regen."""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from luana_core_platform.application.brand_summary_event_handlers import (
    _build_job_id,
    _enqueue_regen,
    handle_brand_section_updated,
    register_brand_summary_event_handlers,
)
from luana_core_platform.domain.events import BrandSectionUpdatedEvent, EventBus


@pytest.fixture(autouse=True)
def _clear_bus():
    EventBus.clear()
    yield
    EventBus.clear()


class _StubArqPool:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def enqueue_job(self, *args, **kwargs):
        self.calls.append({"args": args, "kwargs": kwargs})


def test_register_subscribes_handler_idempotently() -> None:
    register_brand_summary_event_handlers()
    register_brand_summary_event_handlers()
    handlers = EventBus._handlers.get("brand_section_updated", [])
    # Should have exactly one registration (idempotent).
    assert handlers.count(handle_brand_section_updated) == 1


def test_enqueue_regen_passes_dedupe_key_and_debounce(monkeypatch) -> None:
    pool = _StubArqPool()
    from luana_core_platform.core import arq_pool as arq_pool_mod

    monkeypatch.setattr(arq_pool_mod, "_arq_pool", pool)

    tenant_id = uuid4()
    event = BrandSectionUpdatedEvent.create(
        tenant_id=tenant_id,
        section="identity",
    )

    asyncio.run(_enqueue_regen(event))

    assert len(pool.calls) == 1
    call = pool.calls[0]
    assert call["args"] == ("regen_brand_summary", str(tenant_id), "identity")
    assert call["kwargs"]["_job_id"] == _build_job_id(str(tenant_id))
    assert call["kwargs"]["_defer_by"] == 30


def test_enqueue_swallows_arq_unavailable(monkeypatch) -> None:
    from luana_core_platform.core import arq_pool as arq_pool_mod

    monkeypatch.setattr(arq_pool_mod, "_arq_pool", None)

    event = BrandSectionUpdatedEvent.create(tenant_id=uuid4())
    # Must not raise.
    asyncio.run(_enqueue_regen(event))


def test_handler_dispatches_via_bus(monkeypatch) -> None:
    pool = _StubArqPool()
    from luana_core_platform.core import arq_pool as arq_pool_mod

    monkeypatch.setattr(arq_pool_mod, "_arq_pool", pool)

    register_brand_summary_event_handlers()
    tenant_id = uuid4()
    EventBus.publish(
        BrandSectionUpdatedEvent.create(tenant_id=tenant_id, section="voice"),
    )

    # handle_brand_section_updated runs sync (via asyncio.run since no loop)
    # so by the time publish returns the call should be recorded.
    assert any(call["args"][1] == str(tenant_id) for call in pool.calls)
