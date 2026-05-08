"""Conftest for the eval simulator suite (Story B / T-10 deliverable).

Re-exports the canonical fixtures so test modules under
``backend/tests/agentic_evals/sales_agent/simulator/`` can consume them
by name without an explicit import:

* ``eval_tenant_seeded`` — DB-seed fixture from T-3
  (``simulator/fixtures/tenant_seeded.py``).
* ``actor_profile_lead_frio_impaciente`` /
  ``actor_profile_loop_forever`` /
  ``actor_profile_jailbreak_attempt`` — three Pydantic fixtures from T-9
  (``simulator/fixtures/actor_profiles.py``).
* ``run_id`` — fresh UUID4 per test session, used by ``run_simulation``
  to cluster artifacts under ``_artifacts/{run_id}/simulator/...``.

The parent ``tests/agentic_evals/sales_agent/conftest.py`` auto-applies
``@pytest.mark.eval`` to every collected item under
``tests/agentic_evals/sales_agent/``, and the root
``tests/agentic_evals/conftest.py`` registers the ``--run-evals`` CLI flag
+ auto-skips eval-marked tests when the flag is absent. T-10 honors that
chain: smoke + concurrency tests run only with ``--run-evals`` (real LLM
cost), schema regression + termination registry tests opt out via
``pytest.mark.no_eval`` so they run on default CI.

Per ``.claude/rules/parallel-safety.md``: this conftest does NOT touch
the master ``backend/tests/conftest.py`` — it ONLY adds fixture/marker
plumbing scoped to ``tests/agentic_evals/sales_agent/simulator/``.

# voseo-allowed: docstring quotes story B mandate verbatim (es-AR)
"""

# NO ``from __future__ import annotations`` — story-wide cement
# (see T-4..T-9 result.md). Even for conftest.py which is not part of
# the LangGraph runtime introspection chain, the cement is consistent
# story-wide so audit-grep verifiers do not need an exception list.

import uuid
from typing import Any
from uuid import UUID

import pytest

# Re-export DB-seed fixture from T-3 so tests under simulator/ can consume
# it by name (pytest auto-injects fixtures from any parent conftest +
# explicit re-exports in the immediate conftest).
from tests.agentic_evals.sales_agent.simulator.fixtures.tenant_seeded import (
    eval_tenant_seeded,
)

# Re-export hardcoded ActorProfile fixtures from T-9 — these are NOT
# pytest fixtures (they're module-level Pydantic instances). We re-bind
# them as pytest fixtures here so smoke tests can request them by name.
from tests.agentic_evals.sales_agent.simulator.fixtures import (
    actor_profiles as _actor_profiles_module,
)

# Mark eval_tenant_seeded as re-exported so flake8/ruff don't flag F401.
__all__ = ["eval_tenant_seeded"]


# ════════════════════════════════════════════════════════════════════════
# Run-id fixture — UUID4 per session
# ════════════════════════════════════════════════════════════════════════


@pytest.fixture
def run_id() -> UUID:
    """Fresh UUID4 per test (function-scoped — default).

    Used by ``run_simulation(run_id=...)`` so each test's artifacts cluster
    under a unique ``_artifacts/{run_id}/simulator/...`` directory and the
    deterministic UUID5 derivation for ``simulation_id`` does not collide
    across tests in the same session.

    Function-scoped per ``tessl__pytest-api-testing`` "Default to function
    scope" guideline — keeps tests independent.
    """
    return uuid.uuid4()


# ════════════════════════════════════════════════════════════════════════
# ActorProfile fixtures — re-exported as pytest fixtures
# ════════════════════════════════════════════════════════════════════════
#
# T-9 ships the Pydantic instances as module-level ``Final[ActorProfile]``
# constants (frozen, share-safe). Wrapping each in a pytest fixture lets
# tests request them by parameter name + composes cleanly with parametrize.


@pytest.fixture
def actor_profile_lead_frio_impaciente() -> Any:
    """Re-export the T-9 happy/edge/negative persona as a pytest fixture.

    The Pydantic instance is frozen (``ConfigDict(frozen=True)``) so
    sharing across tests is safe — no mutation possible.
    """
    return _actor_profiles_module.actor_profile_lead_frio_impaciente


@pytest.fixture
def actor_profile_loop_forever() -> Any:
    """Re-export the T-9 max_turns edge persona as a pytest fixture."""
    return _actor_profiles_module.actor_profile_loop_forever


@pytest.fixture
def actor_profile_jailbreak_attempt() -> Any:
    """Re-export the T-9 adversarial persona as a pytest fixture."""
    return _actor_profiles_module.actor_profile_jailbreak_attempt
