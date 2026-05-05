"""Conftest for the sales_agent eval harness.

Re-exports the four canonical fixtures (``visionarias_tenant_session``,
``eval_run_id``, ``sales_agent_entrypoint``, ``create_synthetic_eval_lead``)
from ``fixtures/`` so test modules can consume them by name without an
explicit import.

Auto-marks every test in this directory tree with ``@pytest.mark.eval``
unless the test already declares ``@pytest.mark.no_eval`` (used by the
fixture meta-tests in ``test_eval_runner_fixtures.py`` that exercise the
fixtures' precondition path without burning real LLM budget — those tests
must run on default CI to give immediate red signal).

Per ``.claude/rules/parallel-safety.md``: this conftest does NOT touch
the master ``backend/tests/conftest.py`` — it ONLY adds fixture/marker
plumbing scoped to ``tests/agentic_evals/sales_agent/``.
"""

from __future__ import annotations

import pytest

# Re-export public fixtures for direct test consumption.
from tests.agentic_evals.sales_agent.fixtures import (
    create_synthetic_eval_lead,
    eval_run_id,
    sales_agent_entrypoint,
    visionarias_tenant_session,
)


_HARNESS_DIR = "tests/agentic_evals/sales_agent"


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Auto-apply the ``eval`` marker to every test in THIS directory tree.

    Pytest invokes ``pytest_collection_modifyitems`` from every conftest
    in the chain with the FULL session item list, so we MUST scope the
    iteration to items whose path is inside ``tests/agentic_evals/sales_agent/``.
    Without the path filter, this hook would mark unrelated tests under
    ``tests/modules/sales_agent/`` as ``eval`` and break the default suite.

    Tests that legitimately need to run on default CI (e.g. fixture meta-
    tests that only exercise the skip path without invoking LLM) MUST
    declare ``@pytest.mark.no_eval`` explicitly to opt out. The opt-out
    is preserved through the auto-skip step in the root conftest.

    Note: pytest runs the conftests deepest-first. The root
    ``tests/agentic_evals/conftest.py`` runs after this hook and applies
    the actual ``skip`` marker when ``--run-evals`` is absent. So the
    order is: (a) here add ``eval`` to items, then (b) root adds skip.
    """
    del config  # not used at this layer — root conftest owns the flag
    for item in items:
        # Scope: only items inside this harness directory.
        if _HARNESS_DIR not in str(item.fspath):
            continue
        if "no_eval" in item.keywords:
            continue
        if "eval" not in item.keywords:
            item.add_marker(pytest.mark.eval)
