"""Eval-simulator concurrency primitives (T-6, H4 rate-limiting).

A single global ``asyncio.Semaphore`` caps the number of concurrent customer
LLM calls per worker. Story B suite is small (4-5 archetypes x happy
scenario), but the harness must scale to 1000+ tenants x 5 personas x 3 trials
= 15k simulations driven by ``asyncio.gather`` (story F mass-eval). The cap
default (10) protects the LiteLLM Proxy + upstream LLM provider from a
thundering-herd burst.

Per-worker semantics
====================

The semaphore is **module-level**, so it lives in the worker process that
imports the simulator module. Pytest workers (``pytest -n``), CI shards, or
the eval orchestrator each get their own semaphore — fan-out across workers
multiplies the cap. This matches the design philosophy of
``shared/billing/application/llm_guards.py::OutboundRateLimiter`` (per-worker
sliding window, not cluster-wide).

Env override
============

``EVAL_SIMULATOR_MAX_CONCURRENCY`` (int, default ``10``) at module load. Tests
that need a deterministic cap (e.g. T-10 property test) monkeypatch the
``EVAL_SIMULATOR_SEMAPHORE`` symbol with a fresh ``asyncio.Semaphore(N)``
instance. The accessor ``get_eval_simulator_semaphore()`` returns the current
binding — test mocks therefore propagate transparently.

Tessl rule alignment
====================

* ``tessl__graceful-degradation`` Rule 5 — per-dependency error isolation:
  this semaphore covers ONLY the customer LLM call (not the agent runtime,
  not DB writes). Customer LLM saturation does not block agent_bridge.
* ``tessl__langgraph`` "Stateless Nodes" anti-pattern: nodes return partial
  state dicts; the semaphore is operational state for the LLM dependency,
  not application state mutated by the graph.
"""

from __future__ import annotations

import asyncio
import os

EVAL_SIMULATOR_MAX_CONCURRENCY: int = int(
    os.environ.get("EVAL_SIMULATOR_MAX_CONCURRENCY", "10"),
)
"""Maximum concurrent customer LLM calls per worker process.

Default ``10``. Override via ``EVAL_SIMULATOR_MAX_CONCURRENCY`` env var at
module load. The cap is intentionally moderate so a single CI shard does
not exhaust LiteLLM Proxy worker slots; story F multiplies via parallel
shards instead of raising the cap.
"""


EVAL_SIMULATOR_SEMAPHORE: asyncio.Semaphore = asyncio.Semaphore(
    EVAL_SIMULATOR_MAX_CONCURRENCY,
)
"""Module-singleton ``asyncio.Semaphore`` consumed by ``customer_node``.

Acquired via ``async with`` around the LLM call. NEVER used outside the
customer LLM dispatch — agent_bridge has its own dependency isolation
(per Rule 5).
"""


def get_eval_simulator_semaphore() -> asyncio.Semaphore:
    """Return the current customer-LLM semaphore (test-mock friendly).

    Tests can ``monkeypatch.setattr(concurrency_module,
    "EVAL_SIMULATOR_SEMAPHORE", asyncio.Semaphore(N))`` to install a
    deterministic cap; consumers that route through this accessor will pick
    up the override. The customer node imports the symbol directly for hot
    path performance, so callers wanting a deterministic mock should ALSO
    monkeypatch the customer_node module's binding (paridad pattern from
    T-5 observability tests).
    """
    return EVAL_SIMULATOR_SEMAPHORE


__all__ = [
    "EVAL_SIMULATOR_MAX_CONCURRENCY",
    "EVAL_SIMULATOR_SEMAPHORE",
    "get_eval_simulator_semaphore",
]
