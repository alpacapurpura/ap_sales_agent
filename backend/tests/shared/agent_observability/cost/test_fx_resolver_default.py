"""Tests for :meth:`FXResolver.default` factory (PR-2 PI-1.1).

Encapsulates the ``lambda: httpx.Client(timeout=10)`` boilerplate
duplicated across orchestrators. Per ``tessl__graceful-degradation``
Rule 1: explicit timeout on every external call.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal


class TestFXResolverDefault:
    def test_default_returns_fxresolver_instance(self) -> None:
        from src.shared.agent_observability.cost.fx_resolver import FXResolver

        resolver = FXResolver.default()
        assert isinstance(resolver, FXResolver)

    def test_default_factory_yields_callable_client(self) -> None:
        """The factory must produce a client with a ``.get(...)`` method.

        We don't assert on internals (timeout) — httpx version-agnostic.
        """
        from src.shared.agent_observability.cost.fx_resolver import FXResolver

        resolver = FXResolver.default()
        client = resolver.http_client_factory()
        assert hasattr(client, "get") and callable(client.get)
        # Smoke close (httpx.Client is a context manager).
        if hasattr(client, "close"):
            client.close()

    def test_default_passthrough_for_usd(self) -> None:
        """USD does not call the network — short-circuits to ``Decimal(1)``."""
        from src.shared.agent_observability.cost.fx_resolver import FXResolver

        resolver = FXResolver.default()
        rate, source = resolver.resolve(currency_code="USD", at_ts=dt.datetime.now(tz=dt.UTC))
        assert rate == Decimal(1)
        assert source == "passthrough"
