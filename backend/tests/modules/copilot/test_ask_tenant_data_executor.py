"""F5 — executor tests (dispatch plan to first matching DataAccessProvider)."""

from __future__ import annotations

import uuid

import pytest

from luana_core_copilot.application.tools.ask_tenant_data.executor import (
    NoAccessorError,
    execute_plan,
)
from luana_core_copilot.domain.ports import DataQueryPlan, DataQueryResult

TENANT = uuid.UUID("e0eee0ee-0000-4000-8000-000000000001")


class _FakeAccessor:
    def __init__(self, supported: str, payload: DataQueryResult) -> None:
        self._supported = supported
        self._payload = payload
        self.calls: list[DataQueryPlan] = []

    def supports(self, kind: str) -> bool:
        return kind == self._supported

    async def execute(self, *, tenant_id, plan, context=None):
        self.calls.append(plan)
        return self._payload


@pytest.mark.asyncio
async def test_execute_plan_dispatches_to_first_supporting_accessor() -> None:
    offer_acc = _FakeAccessor(
        "offer_lookup",
        DataQueryResult(rows=[{"id": "1"}], metadata={"count": 1}),
    )
    lead_acc = _FakeAccessor(
        "lead_count",
        DataQueryResult(rows=[], metadata={"count": 5}),
    )
    plan = DataQueryPlan(kind="offer_lookup", filters={})
    result = await execute_plan(
        plan=plan,
        tenant_id=TENANT,
        accessors=(offer_acc, lead_acc),
    )
    assert result.metadata["count"] == 1
    assert offer_acc.calls == [plan]
    assert lead_acc.calls == []


@pytest.mark.asyncio
async def test_execute_plan_skips_non_supporting_accessor() -> None:
    no_match = _FakeAccessor("conversation_count", DataQueryResult())
    match = _FakeAccessor(
        "lead_count",
        DataQueryResult(rows=[], metadata={"count": 7}),
    )
    plan = DataQueryPlan(kind="lead_count", filters={})
    result = await execute_plan(
        plan=plan,
        tenant_id=TENANT,
        accessors=(no_match, match),
    )
    assert result.metadata["count"] == 7
    assert no_match.calls == []


@pytest.mark.asyncio
async def test_execute_plan_raises_when_no_accessor_supports_kind() -> None:
    no_match = _FakeAccessor("offer_lookup", DataQueryResult())
    plan = DataQueryPlan(kind="conversation_count", filters={})
    with pytest.raises(NoAccessorError):
        await execute_plan(
            plan=plan,
            tenant_id=TENANT,
            accessors=(no_match,),
        )


@pytest.mark.asyncio
async def test_execute_plan_propagates_db_into_context() -> None:
    captured: dict = {}

    class _RecordingAcc:
        def supports(self, kind: str) -> bool:
            return kind == "offer_lookup"

        async def execute(self, *, tenant_id, plan, context=None):
            captured["context"] = context
            return DataQueryResult()

    fake_db = object()
    plan = DataQueryPlan(kind="offer_lookup", filters={})
    await execute_plan(
        plan=plan,
        tenant_id=TENANT,
        accessors=(_RecordingAcc(),),
        db=fake_db,
    )
    assert captured["context"]["db"] is fake_db
