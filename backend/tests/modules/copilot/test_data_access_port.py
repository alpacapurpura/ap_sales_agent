"""F5 — DataAccessProvider port contract tests."""

from __future__ import annotations

import pytest

from luana_core_copilot.domain.ports import (
    BaseCopilotProvider,
    DataAccessProvider,
    DataQueryPlan,
    DataQueryResult,
)


def test_data_query_plan_is_frozen_with_defaults() -> None:
    plan = DataQueryPlan(kind="offer_lookup", filters={"name_query": "abc"})
    assert plan.kind == "offer_lookup"
    assert plan.filters == {"name_query": "abc"}
    assert plan.limit == 20  # default
    with pytest.raises(AttributeError):
        plan.kind = "lead_count"  # type: ignore[misc]  # frozen


def test_data_query_result_is_frozen_with_metadata() -> None:
    result = DataQueryResult(rows=[{"id": "1"}], metadata={"count": 1})
    assert result.rows == [{"id": "1"}]
    assert result.metadata == {"count": 1}
    with pytest.raises(AttributeError):
        result.rows = []  # type: ignore[misc]  # frozen


def test_base_copilot_provider_data_access_returns_none() -> None:
    """Default base class exposes no data_access — modules opt in."""

    class StubProvider(BaseCopilotProvider):
        @property
        def module_id(self) -> str:
            return "stub"

        @property
        def label(self) -> str:
            return "Stub"

    provider = StubProvider()
    assert provider.data_access() is None


def test_subclass_can_override_data_access_with_protocol_compliant_impl() -> None:
    """A module's provider may return a DataAccessProvider implementation."""

    class StubAccess:
        def supports(self, kind: str) -> bool:
            return kind == "offer_lookup"

        async def execute(
            self,
            *,
            tenant_id,
            plan: DataQueryPlan,
        ) -> DataQueryResult:
            return DataQueryResult(rows=[], metadata={"count": 0})

    class StubProvider(BaseCopilotProvider):
        @property
        def module_id(self) -> str:
            return "offer"

        @property
        def label(self) -> str:
            return "Offer"

        def data_access(self) -> DataAccessProvider | None:
            return StubAccess()  # type: ignore[return-value]

    provider = StubProvider()
    da = provider.data_access()
    assert da is not None
    assert da.supports("offer_lookup") is True
    assert da.supports("lead_count") is False
    assert isinstance(da, DataAccessProvider)  # runtime_checkable
