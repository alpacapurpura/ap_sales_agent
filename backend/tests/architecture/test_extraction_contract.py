"""Architectural fitness: ETL extraction contract enforcement.

Verifies that ``EXTRACTION_CONTRACTS`` in
``src/modules/analytics/domain/extraction_contract.py`` stays in sync with
reality:

1. Every entry references a real provider class that imports cleanly.
2. ``contract.provider_name`` matches ``ProviderClass().provider_name()``.
3. ``contract.has_period_extraction`` matches the class.
4. Every provider in ``PROVIDER_REGISTRY`` has a contract entry.
5. Every metric in ``metric_catalog`` whose ``providers`` tuple lists a
   provider has at least one matching :class:`ChannelOutput` entry under
   that provider in the contract.
6. The cron task names referenced in ``WORKER_SCHEDULE_DOC`` still exist as
   importable functions in their original modules (so the docs cannot drift
   from the workers without the test catching it).
7. The Markdown doc at ``docs/etl/extraction-contract.md`` is up-to-date —
   regenerating it from the current contract should produce the same bytes
   that are committed.

Run natively (not via Docker):

    cd backend && .venv/bin/pytest tests/architecture/test_extraction_contract.py -x -q
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from luana_core_analytics_engine.domain.extraction_contract import (
    EXTRACTION_CONTRACTS,
    WORKER_SCHEDULE_DOC,
    ProviderContract,
)
from luana_core_analytics_engine.domain.metric_catalog import METRIC_CATALOG
from luana_core_analytics_engine.infrastructure.providers.registry import PROVIDER_REGISTRY

REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATED_DOC_PATH = REPO_ROOT / "docs" / "etl" / "extraction-contract.md"


# ---------------------------------------------------------------------------
# 1. Every contract entry resolves to a real, importable class
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name,contract", sorted(EXTRACTION_CONTRACTS.items()))
def test_contract_class_importable(name: str, contract: ProviderContract) -> None:
    module = importlib.import_module(contract.module_path)
    assert hasattr(module, contract.class_name), (
        f"Contract for '{name}' references {contract.module_path}."
        f"{contract.class_name} but the class was not found in the module."
    )


@pytest.mark.parametrize("name,contract", sorted(EXTRACTION_CONTRACTS.items()))
def test_contract_provider_name_matches_class(
    name: str,
    contract: ProviderContract,
) -> None:
    module = importlib.import_module(contract.module_path)
    cls = getattr(module, contract.class_name)
    instance = cls() if contract.provider_name != "manychat" else cls(db=None)
    assert instance.provider_name() == contract.provider_name == name, (
        f"Contract key '{name}' / provider_name='{contract.provider_name}' "
        f"does not match {contract.class_name}().provider_name()="
        f"'{instance.provider_name()}'."
    )


@pytest.mark.parametrize("name,contract", sorted(EXTRACTION_CONTRACTS.items()))
def test_contract_has_period_extraction_matches_class(
    name: str,
    contract: ProviderContract,
) -> None:
    module = importlib.import_module(contract.module_path)
    cls = getattr(module, contract.class_name)
    instance = cls() if name != "manychat" else cls(db=None)
    actual = instance.has_period_extraction()
    assert actual == contract.has_period_extraction, (
        f"Contract for '{name}' declares has_period_extraction="
        f"{contract.has_period_extraction} but the class returns {actual}."
    )


# ---------------------------------------------------------------------------
# 2. Every registered provider has a contract entry
# ---------------------------------------------------------------------------


def test_every_registered_provider_has_contract() -> None:
    registered = set(PROVIDER_REGISTRY.keys())
    contracted = set(EXTRACTION_CONTRACTS.keys())
    missing = registered - contracted
    assert not missing, (
        f"Providers registered in PROVIDER_REGISTRY but missing from "
        f"EXTRACTION_CONTRACTS: {sorted(missing)}. Add an entry to "
        f"backend/src/modules/analytics/domain/extraction_contract.py."
    )


def test_every_contract_entry_is_registered() -> None:
    """A contract entry that is not registered is dead documentation."""
    registered = set(PROVIDER_REGISTRY.keys())
    contracted = set(EXTRACTION_CONTRACTS.keys())
    extra = contracted - registered
    assert not extra, (
        f"Contract entries that are NOT registered in PROVIDER_REGISTRY: "
        f"{sorted(extra)}. Either register the provider in "
        f"infrastructure/providers/registry.py or remove the contract entry."
    )


# ---------------------------------------------------------------------------
# 3. Every metric_catalog ↔ contract relationship is consistent
# ---------------------------------------------------------------------------


def _contract_metric_names(contract: ProviderContract) -> set[str]:
    """Set of canonical metric names this provider's contract claims to emit."""
    names: set[str] = set()
    for channel in contract.channel_outputs:
        for metric in channel.metrics:
            names.add(metric.canonical_name)
    return names


def test_catalog_metrics_appear_in_contract() -> None:
    """If metric_catalog says provider X emits metric M, the contract for X
    must also list M.

    This is the contract drift guard for metric naming changes — if a metric
    is renamed in catalog or in the provider, this test fails.

    Note: providers like ``mailchimp`` and ``activecampaign`` appear in the
    catalog as aliases of MailerLite. They are not separately registered, so
    we resolve them through MailerLite's contract.
    """
    catalog_to_contract_provider = {
        "mailchimp": "mailerlite",
        "activecampaign": "mailerlite",
    }

    missing: list[str] = []
    for metric in METRIC_CATALOG.values():
        for catalog_provider in metric.providers:
            contract_provider = catalog_to_contract_provider.get(
                catalog_provider,
                catalog_provider,
            )
            contract = EXTRACTION_CONTRACTS.get(contract_provider)
            if contract is None:
                # Provider in catalog but not in contracts — separate test
                # catches this; skip here so we report it once.
                continue
            if metric.name not in _contract_metric_names(contract):
                missing.append(
                    f"{contract_provider}/{metric.name} (declared in catalog by '{catalog_provider}')",
                )

    # Allowlist for KNOWN gaps that we are tracking and intentionally tolerate.
    # Each entry MUST have an audit reference. Shrink this list over time —
    # never grow it without justification.
    #
    # All previously known gaps were resolved on 2026-04-15:
    # - Derived metrics (ig_engagement_rate, churn_rate, deliverability_rate,
    #   forward_rate, list_growth_rate, completion_rate, response_rate) had
    #   their providers= tuple set to () since they are computed at read time,
    #   not extracted by the ETL.
    # - tiktok/ctr was removed from metric_catalog.ctr.providers because
    #   TikTokProvider does not extract impressions (only reach/clicks/
    #   conversions/spend), making CTR uncomputable from extracted data.
    KNOWN_CATALOG_CONTRACT_GAPS: set[str] = set()

    surprising = [m for m in missing if m not in KNOWN_CATALOG_CONTRACT_GAPS]
    assert not surprising, (
        "metric_catalog declares metrics whose provider's contract does NOT "
        "list them. Either add them to the contract's ChannelOutput, remove "
        "the catalog declaration, or add to KNOWN_CATALOG_CONTRACT_GAPS with "
        "a reference. Missing:\n  - " + "\n  - ".join(sorted(surprising))
    )


def test_catalog_providers_exist_in_contract() -> None:
    """Every provider name referenced in metric_catalog must either have a
    contract entry or be a documented alias."""
    aliases = {"mailchimp", "activecampaign"}
    catalog_providers: set[str] = set()
    for metric in METRIC_CATALOG.values():
        catalog_providers.update(metric.providers)

    unknown = catalog_providers - set(EXTRACTION_CONTRACTS.keys()) - aliases
    assert not unknown, (
        f"metric_catalog references providers that have no contract entry "
        f"and are not documented aliases: {sorted(unknown)}. "
        f"Either add a contract entry or list the alias in this test."
    )


# ---------------------------------------------------------------------------
# 4. Worker schedule references real, importable functions
# ---------------------------------------------------------------------------


_TASK_FUNCTION_LOCATIONS = {
    "run_tick_scheduler": "luana_core_analytics_engine.workers.scheduler",
    "run_tenant_extraction": "luana_core_analytics_engine.workers.tasks",
    "run_campaign_sync": "luana_core_analytics_engine.workers.tasks",
    "run_period_extraction": "luana_core_analytics_engine.workers.tasks",
    "run_initial_load": "luana_core_analytics_engine.workers.tasks",
    "run_mailerlite_etl_sync": "luana_core_analytics_engine.workers.tasks",
    "run_inactivity_detection": "luana_core_analytics_engine.workers.tasks",
    "run_frozen_detection": "luana_core_sales_agent.workers.frozen_detection",
    "cleanup_old_events": "luana_core_copilot.application.services.event_cleanup",
    "poll_domain_verification": "luana_core_tenant_domains.workers.tasks",
}


@pytest.mark.parametrize("task_name", sorted(WORKER_SCHEDULE_DOC.keys()))
def test_worker_schedule_function_exists(task_name: str) -> None:
    module_path = _TASK_FUNCTION_LOCATIONS.get(task_name)
    assert module_path, (
        f"WORKER_SCHEDULE_DOC mentions task '{task_name}' but the test does "
        f"not know where to look for it. Add it to _TASK_FUNCTION_LOCATIONS."
    )
    module = importlib.import_module(module_path)
    assert hasattr(module, task_name), (
        f"WORKER_SCHEDULE_DOC says task '{task_name}' lives in "
        f"{module_path} but the function was not found there. Either fix the "
        f"location, rename the docs key, or move the function back."
    )


# ---------------------------------------------------------------------------
# 5. Generated Markdown is up to date
# ---------------------------------------------------------------------------


def test_generated_markdown_is_up_to_date() -> None:
    """The committed Markdown doc must match what the generator produces now.

    If this fails, run::

        cd backend && .venv/bin/python scripts/generate_extraction_contract_doc.py

    and commit the updated file.
    """
    import sys

    backend_root = Path(__file__).resolve().parents[2]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))
    from scripts.generate_extraction_contract_doc import render

    if not GENERATED_DOC_PATH.exists():
        pytest.skip(f"{GENERATED_DOC_PATH} not present (docs/ not mounted in this environment)")
    expected = render()
    actual = GENERATED_DOC_PATH.read_text(encoding="utf-8")
    assert actual == expected, (
        "docs/etl/extraction-contract.md is out of date. Regenerate with:\n"
        "  cd backend && .venv/bin/python scripts/generate_extraction_contract_doc.py"
    )
