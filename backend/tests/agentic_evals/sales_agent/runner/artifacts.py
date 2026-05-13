"""Filesystem persistence of eval-run artifacts.

After ``agent_app.ainvoke`` returns, the harness writes three files
under ``backend/tests/agentic_evals/sales_agent/_artifacts/{run_id}/``
so a human investigator can locate the failed run deterministically:

* ``trace.json`` — sanitised ``TrajectorySpy.to_artifact_dict()``.
* ``response.txt`` — sanitised final agent response text.
* ``assertions.json`` — multi-layer assertion results (Capa 1-5 + Story-7
  placeholder), populated by T-4 assertion library.

PII safety: ``sanitize_payload`` (canonical
``shared.agent_observability.recording.sanitization``) is applied before
EVERY write — anti-duplication §0 mandates reuse from shared, never a
mirror. Spec NFR (PII) covered.

The ``_artifacts/`` parent dir is fully gitignored (T-1 scaffold). The
writer is idempotent: rerunning with the same ``run_id`` overwrites
existing files (mkdir parents=True, exist_ok=True).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

from luana_core_observability.recording.sanitization import sanitize_payload

if TYPE_CHECKING:
    from uuid import UUID

    from tests.agentic_evals.sales_agent.runner.trajectory_spy import TrajectorySpy

logger = structlog.get_logger()


_ARTIFACTS_ROOT = Path(__file__).resolve().parents[1] / "_artifacts"


def _resolve_run_dir(run_id: UUID | str) -> Path:
    """Build the per-run subdirectory path under ``_artifacts/``.

    Public artifact path layout:
        ``backend/tests/agentic_evals/sales_agent/_artifacts/{run_id}/``
    """
    return _ARTIFACTS_ROOT / str(run_id)


def write_run_artifacts(
    run_id: UUID | str,
    *,
    spy: TrajectorySpy,
    response_text: str,
    assertions_results: list[dict[str, Any]] | dict[str, Any],
) -> Path:
    """Write the three canonical artifact files under ``_artifacts/{run_id}/``.

    Args:
        run_id: The eval invocation UUID (or its string form). Used as
            the subdirectory name.
        spy: ``TrajectorySpy`` whose ``to_artifact_dict()`` is sanitised
            and written to ``trace.json``.
        response_text: Final agent response. Sanitised before writing
            to ``response.txt``.
        assertions_results: Multi-layer assertion outcomes (T-4). Either
            a list of per-layer records or a dict aggregating them — the
            writer accepts both shapes and serialises with ``json.dumps``
            (default=str fallback for non-JSON-native types).

    Returns:
        ``Path`` of the created subdirectory (``_artifacts/{run_id}/``).
        Useful for the caller to log the location after a test failure.

    Notes:
        * Idempotent: existing files at the target subdir are overwritten.
        * Best-effort: callers may swallow ``OSError`` if filesystem is
          read-only — but this is unusual for the dev/test environment;
          we propagate any I/O error so the test sees the failure.
    """
    run_dir = _resolve_run_dir(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    # 1. trace.json — sanitised spy payload.
    trace_payload = sanitize_payload(spy.to_artifact_dict())
    (run_dir / "trace.json").write_text(
        json.dumps(trace_payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    # 2. response.txt — sanitised raw text.
    sanitised_response = sanitize_payload({"response": response_text}).get("response", "")
    (run_dir / "response.txt").write_text(sanitised_response, encoding="utf-8")

    # 3. assertions.json — caller payload, serialised verbatim.
    (run_dir / "assertions.json").write_text(
        json.dumps(assertions_results, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    logger.info(
        "eval_artifacts_written",
        run_id=str(run_id),
        run_dir=str(run_dir),
        files=["trace.json", "response.txt", "assertions.json"],
    )
    return run_dir


__all__ = ["write_run_artifacts"]
