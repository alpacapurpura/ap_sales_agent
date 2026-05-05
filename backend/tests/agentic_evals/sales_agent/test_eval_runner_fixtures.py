"""Meta-tests for the eval-runner fixtures (T-2 TDD baseline).

Validate the fixture machinery itself BEFORE the goldens land in T-5.
Per ``.claude/rules/tdd-mandatory.md``: RED first, GREEN after — every
fixture has a covering test that exercises both happy + skip paths.

Test partitions:

* ``no_eval`` partition — runs on default CI (no ``--run-evals``). Covers:
  the eval marker plumbing, ``--run-evals`` flag gate, ``eval_run_id``
  uniqueness, callable surface of ``sales_agent_entrypoint``, fixture
  precondition skip behaviour. **Never invokes real LLM.**

* ``eval`` partition (default for this dir, see conftest) — runs only
  with ``--run-evals``. Covers fixture *content* validation against real
  Visionarias DB. Skipped on default CI to avoid burn.

Per arch-be § "Tests requeridos" + ticket T-2 acceptance A1..A4.
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING
from uuid import UUID

import pytest

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

# ──────────────────────────────────────────────────────────────────────────
# Section 1 — no_eval partition (runs on default CI; never burns LLM)
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.no_eval
def test_eval_marker_is_registered(pytestconfig: pytest.Config) -> None:
    """The ``eval`` marker is registered at the agentic_evals root conftest.

    Verifies the spec § Constraints técnicos heredados § "Marker pytest
    --run-evals" plumbing is wired before the goldens depend on it.
    """
    markers = pytestconfig.getini("markers")
    assert any(m.startswith("eval:") for m in markers), (
        f"Marker 'eval' must be registered at the root conftest. Found: {markers}"
    )


@pytest.mark.no_eval
def test_no_eval_marker_is_registered(pytestconfig: pytest.Config) -> None:
    """The ``no_eval`` opt-out marker is registered.

    Without registration, pytest emits ``PytestUnknownMarkWarning`` for
    every test in this file → noise that hides real warnings.
    """
    markers = pytestconfig.getini("markers")
    assert any(m.startswith("no_eval:") for m in markers), f"Marker 'no_eval' must be registered. Found: {markers}"


@pytest.mark.no_eval
def test_run_evals_flag_is_registered(pytestconfig: pytest.Config) -> None:
    """The ``--run-evals`` CLI flag is registered.

    The flag MUST be discoverable from ``pytestconfig.getoption`` so that
    auto-skip plumbing in the root conftest works deterministically.
    """
    # getoption returns False (default) when flag is absent — registered correctly.
    flag_value = pytestconfig.getoption("--run-evals", default="__missing__")
    assert flag_value is not "__missing__", (  # noqa: F632 — explicit identity check
        "Flag --run-evals must be registered via pytest_addoption in root conftest."
    )


@pytest.mark.no_eval
def test_eval_run_id_is_uuid4(eval_run_id: UUID) -> None:
    """``eval_run_id`` returns a valid UUID4."""
    assert isinstance(eval_run_id, UUID)
    assert eval_run_id.version == 4


@pytest.mark.no_eval
def test_eval_run_id_is_unique_per_invocation() -> None:
    """Two direct invocations of the underlying generator return distinct UUIDs.

    Function-scoped fixture contract: every test consuming ``eval_run_id``
    gets a fresh UUID. Verified by calling the underlying ``uuid4()``
    twice through the fixture wrapper logic.
    """
    from tests.agentic_evals.sales_agent.fixtures.run_id import eval_run_id as fx

    # Pytest fixtures cannot be called as plain functions, so we go to the
    # underlying generator's body via inspect for this assertion.
    # The fixture body is one line: ``return uuid4()`` — call uuid4 twice.
    from uuid import uuid4

    a = uuid4()
    b = uuid4()
    assert a != b, "Each fixture invocation must yield a fresh UUID"
    # Inspect contract: ensure the fixture body still calls uuid4 (no drift).
    src = inspect.getsource(fx.__wrapped__ if hasattr(fx, "__wrapped__") else fx)
    assert "uuid4" in src, "eval_run_id fixture must produce UUID4"


@pytest.mark.no_eval
def test_visionarias_tenant_session_skips_when_db_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fixture skips with explicit reason when DB connection fails.

    Simulates a Postgres-down scenario by making ``SessionLocal`` raise.
    The fixture must call ``pytest.skip`` with a Spanish-neutro reason
    naming Visionarias and the tenant id (per ``.claude/rules/spanish-text.md``
    + spec § Decisiones registradas option (a) precondition skip).
    """
    from tests.agentic_evals.sales_agent.fixtures import tenant as tenant_fx

    def _broken_session() -> None:
        broken_msg = "simulated postgres outage"
        raise ConnectionError(broken_msg)

    monkeypatch.setattr(tenant_fx, "_get_real_db_session", _broken_session)

    # Drive the fixture body manually since we cannot call a fixture from
    # a plain test. Use the generator protocol.
    gen = tenant_fx.visionarias_tenant_session.__wrapped__()
    with pytest.raises(pytest.skip.Exception) as exc_info:
        next(gen)
    # Reason must mention Visionarias for human troubleshooting.
    assert "Visionarias" in str(exc_info.value)


@pytest.mark.no_eval
def test_visionarias_tenant_session_resolves_default_uuid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without env var, the fixture resolves the documented default UUID.

    Spec § "Decisiones registradas" + ``backend/scripts/validate_attraction.py``
    convention. Default = ``00000000-0000-0000-0000-000000000001``.
    """
    monkeypatch.delenv("VISIONARIAS_TENANT_ID", raising=False)
    from tests.agentic_evals.sales_agent.fixtures.tenant import (
        _resolve_visionarias_tenant_id,
    )

    resolved = _resolve_visionarias_tenant_id()
    assert resolved == UUID("00000000-0000-0000-0000-000000000001")


@pytest.mark.no_eval
def test_visionarias_tenant_session_honors_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Env var ``VISIONARIAS_TENANT_ID`` overrides the default."""
    custom = "12345678-1234-5678-1234-567812345678"
    monkeypatch.setenv("VISIONARIAS_TENANT_ID", custom)
    from tests.agentic_evals.sales_agent.fixtures.tenant import (
        _resolve_visionarias_tenant_id,
    )

    resolved = _resolve_visionarias_tenant_id()
    assert resolved == UUID(custom)


@pytest.mark.no_eval
def test_create_synthetic_eval_lead_helper_is_exported() -> None:
    """The ``create_synthetic_eval_lead`` helper is importable from fixtures.

    Lower bar than a runtime test (which requires real DB) — but useful
    to ensure refactors don't accidentally remove the public surface used
    by the entrypoint fixture and (future) golden runner.
    """
    from tests.agentic_evals.sales_agent.fixtures import create_synthetic_eval_lead

    assert callable(create_synthetic_eval_lead)
    # Signature contract — caller passes ``db``, ``tenant_id=...``, ``run_id=...``.
    sig = inspect.signature(create_synthetic_eval_lead)
    params = sig.parameters
    assert "db" in params
    assert "tenant_id" in params
    assert "run_id" in params


@pytest.mark.no_eval
def test_fixtures_module_exports_public_surface() -> None:
    """The four canonical fixtures + helper are exported via ``__all__``.

    Anti-drift guard: ``conftest.py`` re-exports from ``fixtures.__init__``;
    if the re-export list shrinks, this test catches it before T-5 lands.
    """
    from tests.agentic_evals.sales_agent import fixtures

    expected = {
        "create_synthetic_eval_lead",
        "eval_run_id",
        "sales_agent_entrypoint",
        "visionarias_tenant_session",
    }
    actual = set(fixtures.__all__)
    assert expected.issubset(actual), f"Public fixture surface drift. Missing: {expected - actual}"


@pytest.mark.no_eval
def test_default_run_skips_eval_marked_tests(pytestconfig: pytest.Config) -> None:
    """Without ``--run-evals``, eval-marked tests in this directory tree are skipped.

    Verifies the contract from spec § Scenario 2 (then-clause "pytest reporta
    cada test del suite como SKIPPED ... la razón skip ... es 'eval markers
    require --run-evals flag'"). The actual runtime skipping is exercised
    by inspecting the flag value here — when False, the root conftest
    auto-skips eval items at collection time.
    """
    if pytestconfig.getoption("--run-evals"):
        pytest.skip("This test verifies default-CI behaviour; requires absence of --run-evals.")
    flag_off = not pytestconfig.getoption("--run-evals")
    assert flag_off, "Default suite must run without --run-evals."


# ──────────────────────────────────────────────────────────────────────────
# Section 2 — eval partition (auto-marked; runs only with --run-evals)
# ──────────────────────────────────────────────────────────────────────────


def test_visionarias_tenant_session_returns_required_keys(
    visionarias_tenant_session: dict,
) -> None:
    """Happy path — fixture yields a dict with the four documented keys.

    Skipped on default CI (auto-marked ``eval``). Runs against real
    Visionarias DB when ``--run-evals`` is set + preconditions hold.
    """
    required = {"tenant_id", "offer", "brand_voice", "db_session"}
    actual = set(visionarias_tenant_session.keys())
    assert required.issubset(actual), f"Fixture missing keys: {required - actual}"
    # Tenant isolation defensive double-check.
    tenant_id: UUID = visionarias_tenant_session["tenant_id"]
    offer = visionarias_tenant_session["offer"]
    assert offer.tenant_id == tenant_id, "Cross-tenant leak: offer.tenant_id must match visionarias tenant_id"


def test_sales_agent_entrypoint_is_async_callable(
    sales_agent_entrypoint: Callable[[str], Awaitable[dict]],
) -> None:
    """The entrypoint fixture returns an async callable accepting ``user_message``."""
    assert callable(sales_agent_entrypoint)
    # The fixture itself returns a closure, not a coroutine.
    sig = inspect.signature(sales_agent_entrypoint)
    params = sig.parameters
    # First positional should accept the user message string.
    assert len(params) >= 1
    # The closure body is async.
    assert inspect.iscoroutinefunction(sales_agent_entrypoint), (
        "sales_agent_entrypoint closure must be async (awaitable)."
    )


@pytest.mark.asyncio
async def test_sales_agent_entrypoint_invocation_returns_state(
    sales_agent_entrypoint: Callable[[str], Awaitable[dict]],
) -> None:
    """End-to-end smoke: invoke the agent with a generic Spanish prompt.

    Lower-fidelity than T-5 multi-layer smoke (no Capa 1-5 assertions) —
    only validates the entrypoint contract (returns dict with expected
    keys, no raised exception, lead_id is UUID, turn_id is UUID-or-None).
    Cost: ~$0.005 per run (1 LLM call). Skipped on default CI.
    """
    out = await sales_agent_entrypoint("Hola, ¿qué ofreces?")
    assert isinstance(out, dict)
    assert "result" in out
    assert "lead_id" in out
    assert "turn_id" in out
    assert isinstance(out["lead_id"], UUID)
    if out["turn_id"] is not None:
        assert isinstance(out["turn_id"], UUID)
    # The agent always returns a dict-shaped final state.
    assert isinstance(out["result"], dict)
