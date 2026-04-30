"""Architectural fitness — campaign audit log retention worker contract.

Verifies:
1. Module backend/src/modules/campaigns/workers/audit_retention_task.py exists
   and defines async function purge_old_campaigns_audit(ctx).
2. Function source references env var CAMPAIGNS_AUDIT_RETENTION_DAYS
   (literal string in source — verifies tunable contract).
3. Function source contains literal CAMPAIGN_AUDIT_TABLE = 'campaign_audit'
   OR references CampaignAuditModel.__tablename__ (verifies target table binding).
4. Cron registration: parse settings.py AST, verify cron(purge_old_campaigns_audit, ...)
   exists in SchedulerSettings.cron_jobs with hour=4, minute=30.

# [CAMPAIGNS-AUDIT-LOG-RETENTION-PR5-S2]
"""

from __future__ import annotations

import ast
import inspect
import pathlib

_RETENTION_TASK_PATH = pathlib.Path("src/modules/campaigns/workers/audit_retention_task.py")
_SETTINGS_PATH = pathlib.Path("src/workers/settings.py")

_EXPECTED_RETENTION_ENV_VAR = "CAMPAIGNS_AUDIT_RETENTION_DAYS"
_EXPECTED_AUDIT_TABLE = "campaign_audit"
_EXPECTED_CRON_HOUR = 4
_EXPECTED_CRON_MINUTE = 30


class TestCampaignAuditLogRetention:
    """Audit log retention worker must exist, be env-tunable, and be cron-registered."""

    def test_audit_retention_task_module_exists(self) -> None:
        """audit_retention_task.py exists at expected path."""
        assert _RETENTION_TASK_PATH.exists(), (
            f"audit_retention_task.py not found at {_RETENTION_TASK_PATH}. PR-5 must ship the audit retention worker."
        )

    def test_purge_old_campaigns_audit_is_importable_and_async(self) -> None:
        """purge_old_campaigns_audit is importable and is an async function."""
        from src.modules.campaigns.workers.audit_retention_task import (
            purge_old_campaigns_audit,
        )

        assert inspect.iscoroutinefunction(purge_old_campaigns_audit), (
            "purge_old_campaigns_audit must be an async function (coroutinefunction). ARQ workers must be async."
        )

    def test_purge_function_has_ctx_parameter(self) -> None:
        """purge_old_campaigns_audit(ctx) accepts ARQ context as first parameter."""
        from src.modules.campaigns.workers.audit_retention_task import (
            purge_old_campaigns_audit,
        )

        sig = inspect.signature(purge_old_campaigns_audit)
        params = list(sig.parameters)
        assert params[0] == "ctx", (
            f"purge_old_campaigns_audit first parameter must be 'ctx' (ARQ context). Found: {params}."
        )

    def test_retention_env_var_referenced_in_source(self) -> None:
        """audit_retention_task.py references CAMPAIGNS_AUDIT_RETENTION_DAYS env var.

        The env var must appear as a literal string in the source so that:
        (a) The tunable contract is verifiable by humans reading the code.
        (b) ops tooling can grep for env var names to audit configuration surface.
        """
        source = _RETENTION_TASK_PATH.read_text()
        assert _EXPECTED_RETENTION_ENV_VAR in source, (
            f"audit_retention_task.py must reference the env var literal string "
            f"'{_EXPECTED_RETENTION_ENV_VAR}'. This documents the tunable contract and "
            f"allows ops tooling to discover configuration surface. "
            f"Expected: os.environ.get('{_EXPECTED_RETENTION_ENV_VAR}', '90')."
        )

    def test_audit_table_name_referenced_in_source(self) -> None:
        """audit_retention_task.py references 'campaign_audit' table name.

        Either as CAMPAIGN_AUDIT_TABLE = 'campaign_audit' constant or as a
        reference to CampaignAuditModel.__tablename__. Prevents silent mismatch
        where the worker targets the wrong table.
        """
        source = _RETENTION_TASK_PATH.read_text()
        assert _EXPECTED_AUDIT_TABLE in source, (
            f"audit_retention_task.py must reference the table name '{_EXPECTED_AUDIT_TABLE}'. "
            "This ensures the retention worker targets the correct table. "
            "Either define CAMPAIGN_AUDIT_TABLE = 'campaign_audit' or reference "
            "CampaignAuditModel.__tablename__."
        )

    def test_cron_registered_in_scheduler_settings(self) -> None:
        """SchedulerSettings.cron_jobs includes cron(purge_old_campaigns_audit, ...).

        The cron job must be registered so the scheduler actually runs it daily.
        """
        source = _SETTINGS_PATH.read_text()
        tree = ast.parse(source)

        scheduler_class: ast.ClassDef | None = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "SchedulerSettings":
                scheduler_class = node
                break

        assert scheduler_class is not None, "ClassDef 'SchedulerSettings' not found in settings.py."

        # Find cron_jobs assignment and check for purge_old_campaigns_audit entry
        found_cron = False
        for node in ast.walk(scheduler_class):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "cron_jobs" and isinstance(node.value, ast.List):
                        for elt in node.value.elts:
                            if (
                                isinstance(elt, ast.Call)
                                and elt.args
                                and isinstance(elt.args[0], ast.Name)
                                and elt.args[0].id == "purge_old_campaigns_audit"
                            ):
                                found_cron = True
                                break

        assert found_cron, (
            "SchedulerSettings.cron_jobs must include a cron() entry for "
            "purge_old_campaigns_audit. Expected: "
            "cron(purge_old_campaigns_audit, hour=4, minute=30)."
        )

    def test_cron_uses_hour_4_minute_30(self) -> None:
        """cron(purge_old_campaigns_audit, ...) is scheduled at hour=4, minute=30.

        04:30 UTC is offset from copilot purge_expired_trace_rows (04:00 UTC)
        to avoid DB connection contention during the daily maintenance window.
        """
        source = _SETTINGS_PATH.read_text()
        tree = ast.parse(source)

        scheduler_class: ast.ClassDef | None = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "SchedulerSettings":
                scheduler_class = node
                break

        assert scheduler_class is not None

        cron_hour: int | None = None
        cron_minute: int | None = None

        for node in ast.walk(scheduler_class):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "cron_jobs" and isinstance(node.value, ast.List):
                        for elt in node.value.elts:
                            if (
                                isinstance(elt, ast.Call)
                                and elt.args
                                and isinstance(elt.args[0], ast.Name)
                                and elt.args[0].id == "purge_old_campaigns_audit"
                            ):
                                # Extract keyword args
                                for kw in elt.keywords:
                                    if (
                                        kw.arg == "hour"
                                        and isinstance(kw.value, ast.Constant)
                                        and isinstance(kw.value.value, int)
                                    ):
                                        cron_hour = kw.value.value
                                    elif (
                                        kw.arg == "minute"
                                        and isinstance(kw.value, ast.Constant)
                                        and isinstance(kw.value.value, int)
                                    ):
                                        cron_minute = kw.value.value

        assert cron_hour == _EXPECTED_CRON_HOUR, (
            f"purge_old_campaigns_audit cron must use hour={_EXPECTED_CRON_HOUR}. "
            f"Found hour={cron_hour}. "
            "04:30 UTC offsets from copilot purge (04:00) to avoid DB contention."
        )
        assert cron_minute == _EXPECTED_CRON_MINUTE, (
            f"purge_old_campaigns_audit cron must use minute={_EXPECTED_CRON_MINUTE}. Found minute={cron_minute}."
        )
