"""F9 — workflow metric KPI tracking compliance.

# [COPILOT-WORKFLOW-METRIC-F9] -> docs/domains/copilot/redesign-2026-04/phases/F9-quality-observability.md

Every workflow declared by a ``WorkflowProvider`` MUST be trackable in the
``copilot_workflow_metric`` schema:

* ``workflow_id`` is a non-empty string ≤64 chars (column type TEXT, but
  a hard cap keeps the admin dashboard table renderable).
* ``workflow_id`` matches the snake_case identifier shape that the ARQ
  task uses to bucket samples.

The ARQ task additionally accepts ``_no_workflow`` as a sentinel for
ungrouped chats — that one is exempt from the convention check (it's a
sentinel, not a declared workflow).
"""

from __future__ import annotations

import re

from luana_core_copilot.application.discovery import discover_providers
from luana_core_copilot.application.workflows.registry import collect_workflows

# Snake_case identifier shape (alpha + digit + underscore, starts with
# alpha). Mirrors the dotted-path enforcement in `WorkflowNode.handler_ref`.
_WORKFLOW_ID_RE = re.compile(r"^[a-z][a-z0-9_]{2,63}$")


def test_every_declared_workflow_has_valid_id_for_kpi_tracking() -> None:
    """Workflow ids must be valid for the ``copilot_workflow_metric.workflow_id`` column."""
    providers = discover_providers()
    workflows = collect_workflows(providers)
    invalid: list[tuple[str, str]] = []
    for wf_id, wf in workflows.items():
        if not _WORKFLOW_ID_RE.match(wf_id):
            invalid.append((wf_id, "fails snake_case shape"))
        if wf.id != wf_id:
            invalid.append((wf_id, f"registry key {wf_id!r} != wf.id {wf.id!r}"))
    assert not invalid, "Workflow ids violate KPI compliance:\n" + "\n".join(
        f"  - {name}: {reason}" for name, reason in invalid
    )


def test_workflow_metric_has_required_columns() -> None:
    """``copilot_workflow_metric`` must declare the columns the dashboard reads."""
    from luana_core_copilot.infrastructure.models.workflow_metric_model import (
        WorkflowMetricModel,
    )

    required = {
        "id",
        "tenant_id",
        "workflow_id",
        "period_start",
        "period_end",
        "started_count",
        "completed_count",
        "abandoned_count",
        "judge_avg_score",
        "judge_sample_size",
    }
    cols = {col.name for col in WorkflowMetricModel.__table__.columns}
    missing = required - cols
    assert not missing, f"WorkflowMetricModel missing columns: {sorted(missing)}"


def test_workflow_metric_uniqueness_constraint() -> None:
    """``(tenant_id, workflow_id, period_start)`` is the natural key — must be unique."""
    from luana_core_copilot.infrastructure.models.workflow_metric_model import (
        WorkflowMetricModel,
    )

    table = WorkflowMetricModel.__table__
    expected_cols = {"tenant_id", "workflow_id", "period_start"}
    found = False
    for constraint in table.constraints:
        cols = {c.name for c in getattr(constraint, "columns", [])}
        if cols == expected_cols:
            found = True
            break
    assert found, "WorkflowMetricModel must declare a UNIQUE constraint on (tenant_id, workflow_id, period_start)."
