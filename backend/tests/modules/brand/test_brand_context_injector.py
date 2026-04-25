"""F3 — ``BrandContextInjector`` route allowlist + summary fetch."""

from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

import pytest

from src.modules.brand.copilot_provider.context_inject import (
    BrandContextInjector,
    _route_in_allowlist,
)
from src.modules.brand.copilot_provider.summary import BrandSummaryProvider


class _StubSummary(BrandSummaryProvider):
    def __init__(self, output: str | None) -> None:
        self.output = output
        self.calls: list[UUID] = []

    async def summary(self, *, tenant_id):
        self.calls.append(tenant_id)
        return self.output


@pytest.mark.parametrize(
    "route",
    [
        "/abc/offer-studio",
        "/abc/offer-studio/offer/xyz",
        "/abc/landing",
        "/abc/sales/studio/inbox",
        "/abc/growth-studio/atraccion-captura",
        "/abc/campaigns/123",
    ],
)
def test_allowlist_matches_target_routes(route) -> None:
    assert _route_in_allowlist(route) is True


@pytest.mark.parametrize(
    "route",
    [
        "/abc/brand-studio/identity",
        "/abc/settings",
        "",
        None,
    ],
)
def test_allowlist_skips_off_target_routes(route) -> None:
    assert _route_in_allowlist(route) is False


def test_inject_for_returns_lighthouse_when_route_matches() -> None:
    stub = _StubSummary("Marca formación. Promesa clara. Voz directa.")
    injector = BrandContextInjector(summary_provider=stub)
    out = asyncio.run(
        injector.inject_for(target_route="/abc/offer-studio", tenant_id=uuid4()),
    )
    assert out is not None
    assert "## Brand Lighthouse" in out
    assert "Marca formación" in out
    assert "Toma decisiones desde aquí." in out


def test_inject_for_returns_none_off_route_without_calling_summary() -> None:
    stub = _StubSummary("anything")
    injector = BrandContextInjector(summary_provider=stub)
    out = asyncio.run(
        injector.inject_for(target_route="/abc/brand-studio/identity", tenant_id=uuid4()),
    )
    assert out is None
    assert stub.calls == []


def test_inject_for_returns_none_when_summary_missing() -> None:
    stub = _StubSummary(None)
    injector = BrandContextInjector(summary_provider=stub)
    out = asyncio.run(
        injector.inject_for(target_route="/abc/sales", tenant_id=uuid4()),
    )
    assert out is None
