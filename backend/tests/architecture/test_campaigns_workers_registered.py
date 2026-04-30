"""Architectural fitness — PR-5 ARQ workers registered in WorkerSettings + SchedulerSettings.

AST scan:
  1. Parses backend/src/workers/settings.py.
  2. Finds ClassDef WorkerSettings → assignment to 'functions' (list).
     Verifies every REQUIRED_FUNCTIONS name appears as Name.id in the list.
  3. Finds ClassDef SchedulerSettings → assignment to 'cron_jobs' (list).
     Each list item is a Call (cron(...)). Extracts the first positional arg
     Name.id from each cron() call. Asserts REQUIRED_CRON_FNS is a subset.

Ratchet: shrink-only KNOWN_MISSING (initially empty).

# [CAMPAIGNS-WORKERS-REGISTERED-PR5-S2]
"""

from __future__ import annotations

import ast
import pathlib

_SETTINGS_PATH = pathlib.Path("src/workers/settings.py")

REQUIRED_FUNCTIONS: frozenset[str] = frozenset(
    {
        "run_campaign_execution_task",
        "run_campaign_scheduler_tick",
        "run_segment_refresh_tick",
        "purge_old_campaigns_audit",
    }
)

REQUIRED_CRON_FNS: frozenset[str] = frozenset(
    {
        "run_campaign_scheduler_tick",
        "run_segment_refresh_tick",
        "purge_old_campaigns_audit",
    }
)

# Shrink-only allowlist. Functions that have not yet been registered should be
# justified here with a comment explaining the timeline.
KNOWN_MISSING: frozenset[str] = frozenset({})


def _collect_list_name_ids(list_node: ast.List) -> list[str]:
    """Return Name.id values from a list literal (handles nested lists too)."""
    names: list[str] = []
    for elt in list_node.elts:
        if isinstance(elt, ast.Name):
            names.append(elt.id)
        elif isinstance(elt, ast.List):
            names.extend(_collect_list_name_ids(elt))
    return names


def _find_functions_list(class_node: ast.ClassDef) -> list[str]:
    """Find assignment `functions = [...]` in a ClassDef and return Name ids."""
    for node in ast.walk(class_node):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "functions" and isinstance(node.value, ast.List):
                    return _collect_list_name_ids(node.value)
    return []


def _find_cron_jobs_fns(class_node: ast.ClassDef) -> list[str]:
    """Find cron_jobs = [...] in a ClassDef; extract first positional arg Name.id per cron()."""
    fn_names: list[str] = []
    for node in ast.walk(class_node):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "cron_jobs" and isinstance(node.value, ast.List):
                    for elt in node.value.elts:
                        # Each element should be a Call: cron(fn_name, ...)
                        if isinstance(elt, ast.Call) and elt.args:
                            first_arg = elt.args[0]
                            if isinstance(first_arg, ast.Name):
                                fn_names.append(first_arg.id)
    return fn_names


class TestCampaignWorkersRegistered:
    """PR-5 ARQ workers must appear in WorkerSettings.functions + SchedulerSettings cron_jobs."""

    def test_settings_file_exists(self) -> None:
        """backend/src/workers/settings.py exists."""
        assert _SETTINGS_PATH.exists(), f"workers/settings.py not found at {_SETTINGS_PATH}."

    def test_worker_settings_has_required_functions(self) -> None:
        """WorkerSettings.functions contains all 4 PR-5 campaign worker functions."""
        source = _SETTINGS_PATH.read_text()
        tree = ast.parse(source)

        worker_class: ast.ClassDef | None = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "WorkerSettings":
                worker_class = node
                break

        assert worker_class is not None, "ClassDef 'WorkerSettings' not found in settings.py."

        registered_fns = set(_find_functions_list(worker_class))
        missing = REQUIRED_FUNCTIONS - registered_fns - KNOWN_MISSING

        assert not missing, (
            f"WorkerSettings.functions is missing campaign worker functions: {missing}. "
            "All 4 PR-5 campaign workers must appear in the functions list so ARQ can "
            "route jobs to them: run_campaign_execution_task, run_campaign_scheduler_tick, "
            "run_segment_refresh_tick, purge_old_campaigns_audit."
        )

    def test_scheduler_settings_has_required_functions(self) -> None:
        """SchedulerSettings.functions contains all 4 PR-5 campaign worker functions.

        ARQ reads __dict__ (not inherited attrs), so SchedulerSettings must re-declare
        the functions list explicitly (noted in settings.py comment).
        """
        source = _SETTINGS_PATH.read_text()
        tree = ast.parse(source)

        scheduler_class: ast.ClassDef | None = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "SchedulerSettings":
                scheduler_class = node
                break

        assert scheduler_class is not None, "ClassDef 'SchedulerSettings' not found in settings.py."

        registered_fns = set(_find_functions_list(scheduler_class))
        missing = REQUIRED_FUNCTIONS - registered_fns - KNOWN_MISSING

        assert not missing, (
            f"SchedulerSettings.functions is missing campaign worker functions: {missing}. "
            "ARQ scheduler reads __dict__ so functions must be re-declared here too."
        )

    def test_scheduler_settings_has_required_cron_jobs(self) -> None:
        """SchedulerSettings.cron_jobs contains entries for all 3 PR-5 scheduled workers."""
        source = _SETTINGS_PATH.read_text()
        tree = ast.parse(source)

        scheduler_class: ast.ClassDef | None = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "SchedulerSettings":
                scheduler_class = node
                break

        assert scheduler_class is not None, "ClassDef 'SchedulerSettings' not found in settings.py."

        cron_fns = set(_find_cron_jobs_fns(scheduler_class))
        missing = REQUIRED_CRON_FNS - cron_fns - KNOWN_MISSING

        assert not missing, (
            f"SchedulerSettings.cron_jobs is missing cron entries for: {missing}. "
            "Required cron schedule: "
            "run_campaign_scheduler_tick (minute={5,15,25,35,45,55}), "
            "run_segment_refresh_tick (hourly), "
            "purge_old_campaigns_audit (hour=4, minute=30)."
        )

    def test_known_missing_ratchet(self) -> None:
        """KNOWN_MISSING allowlist is empty (ratchet: shrink-only)."""
        assert frozenset() == KNOWN_MISSING, (
            f"KNOWN_MISSING is not empty: {KNOWN_MISSING}. "
            "All required campaign workers must be registered. "
            "Remove entries from KNOWN_MISSING once the function is registered."
        )
