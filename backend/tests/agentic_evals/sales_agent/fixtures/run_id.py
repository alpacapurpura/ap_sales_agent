"""Per-invocation run-id fixture.

Each test that consumes ``eval_run_id`` gets a fresh UUID4 used as the
artifacts subdirectory name (``_artifacts/{run_id}/{trace.json,...}``).
Per spec § Scenario 1 grader, artifacts persist with the ``run_id`` as
filesystem anchor so a human investigator can locate the failed run
deterministically.

Function-scoped on purpose: every test invocation is an independent
experiment per ``.claude/rules/parallel-safety.md`` semantics (no
session-leak between tests).
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest


@pytest.fixture
def eval_run_id() -> UUID:
    """Allocate one UUID4 per test invocation.

    Returns:
        Fresh :class:`uuid.UUID` (UUID4) used by the artifacts writer
        (T-3 ``runner/artifacts.py``) as the subdir name under
        ``_artifacts/``. Two invocations of this fixture in sibling tests
        return distinct UUIDs (verified by meta-test).
    """
    return uuid4()
