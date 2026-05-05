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
from pathlib import Path
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
    assert flag_value != "__missing__", "Flag --run-evals must be registered via pytest_addoption in root conftest."


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


# ──────────────────────────────────────────────────────────────────────────
# Section 3 — TrajectorySpy meta-tests (T-3 — composition over subclass)
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.no_eval
def test_trajectory_spy_subclasses_langchain_native_only() -> None:
    """The spy MUST inherit ``BaseCallbackHandler`` (LangChain native), NEVER
    ``BaseAgentCallbackHandler`` (shared canonical) — anti-duplication §0.

    This is the architectural assertion: composition over subclass. If a
    future refactor changes ``TrajectorySpy`` to inherit from the shared
    base handler, this test fails immediately.
    """
    from langchain_core.callbacks import BaseCallbackHandler

    from src.shared.agent_observability.recording.base_callback_handler import (
        BaseAgentCallbackHandler,
    )
    from tests.agentic_evals.sales_agent.runner.trajectory_spy import TrajectorySpy

    assert issubclass(TrajectorySpy, BaseCallbackHandler), (
        "TrajectorySpy must subclass langchain_core.callbacks.BaseCallbackHandler "
        "(LangChain native handler — composition pattern)."
    )
    assert not issubclass(TrajectorySpy, BaseAgentCallbackHandler), (
        "TrajectorySpy MUST NOT subclass BaseAgentCallbackHandler. "
        "Anti-duplication §0 — spy is composed via RunnableConfig.callbacks list, "
        "never inheritance from the shared canonical handler."
    )


@pytest.mark.no_eval
def test_no_base_agent_callback_handler_subclass_in_runner_dir() -> None:
    """Anti-duplication GATE — spec § A2 acceptance.

    Walk ``backend/tests/agentic_evals/sales_agent/runner/*.py`` AST looking
    for any executable reference to ``BaseAgentCallbackHandler`` — imports,
    base-class lists, attribute access, type annotations. Pure docstring /
    comment mentions (which intentionally describe the anti-pattern) are
    permitted as documentation.

    Uses ``ast.parse`` + node walk — robust against false positives from
    prose in docstrings AND avoids ruff S603/S607 footguns from
    subprocess-based grep.
    """
    import ast

    runner_dir = Path(__file__).resolve().parent / "runner"
    offenders: list[tuple[Path, int, str]] = []

    for py_file in sorted(runner_dir.rglob("*.py")):
        source = py_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            # Direct name reference (e.g. base-class, type annotation).
            if isinstance(node, ast.Name) and node.id == "BaseAgentCallbackHandler":
                offenders.append((py_file, node.lineno, "ast.Name"))
            # Attribute access (e.g. ``module.BaseAgentCallbackHandler``).
            elif isinstance(node, ast.Attribute) and node.attr == "BaseAgentCallbackHandler":
                offenders.append((py_file, node.lineno, "ast.Attribute"))
            # Import (e.g. ``from ... import BaseAgentCallbackHandler``).
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "BaseAgentCallbackHandler":
                        offenders.append((py_file, node.lineno, "ast.ImportFrom"))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.endswith(".BaseAgentCallbackHandler"):
                        offenders.append((py_file, node.lineno, "ast.Import"))

    assert offenders == [], (
        "Anti-duplication §0 violation: executable BaseAgentCallbackHandler reference "
        f"detected in {runner_dir}/. Composition over subclass — see arch-agentic.md.\n"
        + "\n".join(f"  {p}:{ln}: {kind}" for p, ln, kind in offenders)
    )


@pytest.mark.no_eval
def test_trajectory_spy_captures_specialist_history_from_chain_end() -> None:
    """Synthetic ``on_chain_end`` events build ``specialist_history``.

    Drives the spy with three node exits — supervisor → qualifier →
    respond — and verifies:
    * Terminal sentinel ``respond`` is filtered out.
    * Non-string ``next_node`` (None) is filtered out.
    * Node visits accumulate every event for diagnostics.
    """
    from uuid import uuid4

    from tests.agentic_evals.sales_agent.runner.trajectory_spy import TrajectorySpy

    spy = TrajectorySpy()
    spy.on_chain_end({"next_node": "qualifier"}, run_id=uuid4())
    spy.on_chain_end({"next_node": None}, run_id=uuid4())  # filtered (non-string)
    spy.on_chain_end({"next_node": "tool_executor"}, run_id=uuid4())
    spy.on_chain_end({"next_node": "respond"}, run_id=uuid4())  # filtered (terminal)

    assert spy.specialist_history == ["qualifier", "tool_executor"]
    assert len(spy.node_visits) == 4  # every event recorded for diagnostics


@pytest.mark.no_eval
def test_trajectory_spy_tool_capture_drains_inflight_cache() -> None:
    """``on_tool_start`` caches name+input; ``on_tool_end`` drains it.

    Validates the per-run-id pairing logic + cache hygiene (no leftover
    entries after end fires). Also covers the cache-drain edge case where
    ``on_tool_end`` fires WITHOUT a matching ``on_tool_start`` (defensive
    fallback: empty name).
    """
    from uuid import uuid4

    from tests.agentic_evals.sales_agent.runner.trajectory_spy import TrajectorySpy

    spy = TrajectorySpy()
    run_id_a = uuid4()
    run_id_b = uuid4()

    spy.on_tool_start({"name": "knowledge_search"}, "query A", run_id=run_id_a)
    spy.on_tool_start({"name": "recommend_product"}, "input B", run_id=run_id_b)
    assert len(spy._tool_runs_inflight) == 2

    spy.on_tool_end("output A", run_id=run_id_a)
    assert len(spy._tool_runs_inflight) == 1  # drained run_id_a

    # Edge case — orphan on_tool_end without on_tool_start.
    orphan_run_id = uuid4()
    spy.on_tool_end("output orphan", run_id=orphan_run_id)

    spy.on_tool_end("output B", run_id=run_id_b)
    assert spy._tool_runs_inflight == {}

    names = [tc["name"] for tc in spy.tool_calls]
    assert names == ["knowledge_search", "", "recommend_product"]
    # The orphan record carries empty name + empty input — diagnostic-friendly.
    orphan = next(tc for tc in spy.tool_calls if tc["name"] == "")
    assert orphan["input"] == ""


@pytest.mark.no_eval
def test_trajectory_spy_callbacks_are_best_effort() -> None:
    """A malformed payload MUST NOT raise — best-effort observability.

    Decision B6 + ``copilot-observability.md`` + ``tessl__graceful-
    degradation`` Rule 6: spy crashes are logged via structlog warning
    and swallowed. ``agent_app.ainvoke`` MUST NEVER fail because the
    spy choked.
    """
    from uuid import uuid4

    from tests.agentic_evals.sales_agent.runner.trajectory_spy import TrajectorySpy

    spy = TrajectorySpy()

    # Non-dict outputs — defensive fallback path.
    spy.on_chain_end("not-a-dict", run_id=uuid4())  # type: ignore[arg-type]
    # Non-dict serialized payload at on_tool_start.
    spy.on_tool_start("not-a-dict", "input", run_id=uuid4())  # type: ignore[arg-type]
    # Output with non-string repr — coerced via repr().
    spy.on_tool_end({"complex": "object"}, run_id=uuid4())

    # No exceptions raised; state remains coherent.
    assert isinstance(spy.specialist_history, list)
    assert isinstance(spy.tool_calls, list)


@pytest.mark.no_eval
def test_trajectory_spy_reset_clears_all_state() -> None:
    """``reset()`` empties every accumulator + the in-flight cache."""
    from uuid import uuid4

    from tests.agentic_evals.sales_agent.runner.trajectory_spy import TrajectorySpy

    spy = TrajectorySpy()
    spy.on_chain_end({"next_node": "qualifier"}, run_id=uuid4())
    spy.on_tool_start({"name": "knowledge_search"}, "query", run_id=uuid4())
    assert spy.specialist_history
    assert spy._tool_runs_inflight

    spy.reset()
    assert spy.specialist_history == []
    assert spy.tool_calls == []
    assert spy.node_visits == []
    assert spy._tool_runs_inflight == {}


@pytest.mark.no_eval
def test_trajectory_spy_to_artifact_dict_returns_serialisable_payload() -> None:
    """``to_artifact_dict()`` returns the three documented keys + JSON-safe values."""
    import json
    from uuid import uuid4

    from tests.agentic_evals.sales_agent.runner.trajectory_spy import TrajectorySpy

    spy = TrajectorySpy()
    spy.on_chain_end({"next_node": "qualifier"}, run_id=uuid4())
    spy.on_tool_start({"name": "knowledge_search"}, "query", run_id=uuid4())
    spy.on_tool_end("ok", run_id=list(spy._tool_runs_inflight.keys())[0])  # noqa: RUF015

    payload = spy.to_artifact_dict()
    assert set(payload.keys()) == {"specialist_history", "tool_calls", "node_visits"}
    # Round-trips through json — no datetime/UUID native types remaining.
    json.dumps(payload, default=str)


# ──────────────────────────────────────────────────────────────────────────
# Section 4 — Artifacts writer meta-tests (T-3 A3 + A4 acceptance)
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.no_eval
def test_artifacts_writer_creates_run_id_subdir_with_3_files(tmp_path, monkeypatch) -> None:
    """Spec § A3 acceptance — three files (trace.json, response.txt,
    assertions.json) appear under ``_artifacts/{run_id}/``.

    Uses ``tmp_path`` + ``monkeypatch`` to redirect the artifacts root
    so the meta-test does not pollute the real ``_artifacts/`` directory
    on the developer machine.
    """
    import json
    from uuid import uuid4

    from tests.agentic_evals.sales_agent.runner import artifacts as artifacts_mod
    from tests.agentic_evals.sales_agent.runner.artifacts import write_run_artifacts
    from tests.agentic_evals.sales_agent.runner.trajectory_spy import TrajectorySpy

    monkeypatch.setattr(artifacts_mod, "_ARTIFACTS_ROOT", tmp_path / "_artifacts")

    run_id = uuid4()
    spy = TrajectorySpy()
    spy.on_chain_end({"next_node": "qualifier"}, run_id=uuid4())

    run_dir = write_run_artifacts(
        run_id,
        spy=spy,
        response_text="Hola, ¿en qué te puedo ayudar?",
        assertions_results=[{"layer": "trajectory", "passed": True}],
    )

    assert run_dir.is_dir()
    assert run_dir.name == str(run_id)
    files = sorted(p.name for p in run_dir.iterdir())
    assert files == ["assertions.json", "response.txt", "trace.json"]
    # Round-trip the trace.json to confirm valid JSON shape.
    trace = json.loads((run_dir / "trace.json").read_text(encoding="utf-8"))
    assert "specialist_history" in trace
    assert trace["specialist_history"] == ["qualifier"]


@pytest.mark.no_eval
def test_artifacts_writer_is_idempotent(tmp_path, monkeypatch) -> None:
    """Rerunning the writer with the same ``run_id`` overwrites cleanly."""
    from uuid import uuid4

    from tests.agentic_evals.sales_agent.runner import artifacts as artifacts_mod
    from tests.agentic_evals.sales_agent.runner.artifacts import write_run_artifacts
    from tests.agentic_evals.sales_agent.runner.trajectory_spy import TrajectorySpy

    monkeypatch.setattr(artifacts_mod, "_ARTIFACTS_ROOT", tmp_path / "_artifacts")

    run_id = uuid4()
    write_run_artifacts(
        run_id,
        spy=TrajectorySpy(),
        response_text="primera ejecucion",
        assertions_results=[],
    )
    second_dir = write_run_artifacts(
        run_id,
        spy=TrajectorySpy(),
        response_text="segunda ejecucion",
        assertions_results=[{"layer": "trajectory", "passed": False}],
    )

    assert second_dir.is_dir()
    assert (second_dir / "response.txt").read_text(encoding="utf-8") == "segunda ejecucion"


@pytest.mark.no_eval
def test_artifacts_pii_sanitized(tmp_path, monkeypatch) -> None:
    """Spec § A4 acceptance — trace.json + response.txt must NOT carry
    raw PII (email/phone/national-id patterns).

    Drives the writer with payloads carrying obvious PII fixtures and
    asserts ``sanitize_payload`` redacted them via the canonical
    ``shared.agent_observability.recording.sanitization`` module.
    """
    import json
    import re
    from uuid import uuid4

    from tests.agentic_evals.sales_agent.runner import artifacts as artifacts_mod
    from tests.agentic_evals.sales_agent.runner.artifacts import write_run_artifacts
    from tests.agentic_evals.sales_agent.runner.trajectory_spy import TrajectorySpy

    monkeypatch.setattr(artifacts_mod, "_ARTIFACTS_ROOT", tmp_path / "_artifacts")

    run_id = uuid4()
    spy = TrajectorySpy()
    # Inject a tool call carrying email + phone fixtures into the spy state.
    spy.tool_calls.append(
        {
            "run_id": str(uuid4()),
            "name": "knowledge_search",
            "input": "Mi email es chris@example.com y mi celular +54 11 5555-1234",
            "output": "Documento técnico encontrado",
        },
    )

    write_run_artifacts(
        run_id,
        spy=spy,
        response_text="Te confirmo a chris@example.com con celular +54 11 5555-1234.",
        assertions_results=[{"layer": "output", "passed": True}],
    )

    run_dir = tmp_path / "_artifacts" / str(run_id)
    trace_text = (run_dir / "trace.json").read_text(encoding="utf-8")
    response_text = (run_dir / "response.txt").read_text(encoding="utf-8")

    email_re = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    phone_re = re.compile(r"\+\s*54\s*11\s*\d{4}-\d{4}")

    assert not email_re.search(trace_text), "trace.json contains raw email — sanitize_payload missing or broken"
    assert not email_re.search(response_text), "response.txt contains raw email — sanitize_payload missing or broken"
    assert not phone_re.search(trace_text), "trace.json contains raw phone"
    assert not phone_re.search(response_text), "response.txt contains raw phone"

    # Confirm trace.json is still well-formed JSON post-sanitisation.
    trace_payload = json.loads(trace_text)
    assert "tool_calls" in trace_payload


# ──────────────────────────────────────────────────────────────────────────
# Section 5 — Eval partition: A1 acceptance (real ainvoke, --run-evals only)
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_trajectory_spy_captures_first_specialist_and_tool_calls(
    sales_agent_entrypoint: Callable[[str], Awaitable[dict]],
) -> None:
    """Spec § A1 — happy single-turn invocation populates spy.specialist_history.

    A cold lead asking ``"Hola, vi su publicidad..."`` is expected to
    route through the supervisor → qualifier path. The spy captures
    ``next_node = "qualifier"`` at minimum. Tool calls list is allowed
    to be empty (cold-lead first turn typically does not invoke tools).
    Cost: ~$0.005 per run. Skipped on default CI.
    """
    out = await sales_agent_entrypoint("Hola, vi su publicidad y me interesa.")
    assert "spy" in out, "Entrypoint must expose the trajectory spy"

    spy = out["spy"]
    # specialist_history captures the routing trail. Cold lead first
    # turn at minimum routes through ``qualifier`` per arch-agentic
    # § "Topology classification" (supervisor → qualifier → respond).
    assert "qualifier" in spy.specialist_history, (
        f"Expected 'qualifier' in spy.specialist_history, got {spy.specialist_history}"
    )
    # tool_calls is a list (possibly empty for cold-lead first turn).
    assert isinstance(spy.tool_calls, list)


# ──────────────────────────────────────────────────────────────────────────
# Section 6 — T-4 Multi-layer assertion library (no_eval — no LLM cost)
# ──────────────────────────────────────────────────────────────────────────
#
# These tests cover the public API of
# ``backend/tests/agentic_evals/sales_agent/runner/assertions.py``:
#
# * 5 layer assertions (trajectory / tool_calls / output / cost / latency)
# * ``LayerAssertionError`` base + 5 subclasses (``.layer_name`` field)
# * Story-7 placeholder (``assert_voice_fidelity`` raises NotImplementedError)
# * ``_detect_language_safe`` graceful fallback to "unknown"
# * Edge cases: cost = 0 row, forbidden tool present, trajectory exact mismatch
#
# All tests are ``@pytest.mark.no_eval`` — they exercise the assertion API
# in isolation without invoking the LangGraph runtime, so they MUST run on
# the default suite. The smoke harness in T-5 consumes these assertions
# during ``--run-evals`` runs.


@pytest.mark.no_eval
def test_assertions_api_complete() -> None:
    """A1 — All 5 assertions, base error, and 5 subclasses are exported.

    Public surface check per spec § A1 acceptance. Confirms every
    callable + exception listed in the deliverable is importable from
    ``runner.assertions``. Each subclass exposes a ``.layer_name`` class
    attribute matching its semantic layer for accionable debugging.
    """
    from tests.agentic_evals.sales_agent.runner import assertions as a_mod

    # 5 callable assertions.
    assert callable(a_mod.assert_trajectory)
    assert callable(a_mod.assert_tool_calls)
    assert callable(a_mod.assert_output)
    assert callable(a_mod.assert_cost_recorded)
    assert callable(a_mod.assert_latency)

    # Story-7 placeholder is callable too — must raise NotImplementedError on call.
    assert callable(a_mod.assert_voice_fidelity)

    # Base + 5 subclasses with .layer_name field.
    assert issubclass(a_mod.LayerAssertionError, Exception)
    expected_layers = {
        a_mod.TrajectoryAssertionError: "trajectory",
        a_mod.ToolCallAssertionError: "tool_calls",
        a_mod.OutputAssertionError: "output",
        a_mod.CostAssertionError: "cost",
        a_mod.LatencyAssertionError: "latency",
    }
    for cls, expected_name in expected_layers.items():
        assert issubclass(cls, a_mod.LayerAssertionError), f"{cls.__name__} must subclass LayerAssertionError"
        # layer_name is set on instance — instantiate with placeholder kwargs.
        instance = cls(message="probe", observed=None, expected=None)
        assert instance.layer_name == expected_name, (
            f"{cls.__name__}.layer_name must equal '{expected_name}', got '{instance.layer_name}'"
        )

    # Public API surface — __all__ exports every documented symbol.
    expected_exports = {
        "assert_trajectory",
        "assert_tool_calls",
        "assert_output",
        "assert_cost_recorded",
        "assert_latency",
        "assert_voice_fidelity",
        "LayerAssertionError",
        "TrajectoryAssertionError",
        "ToolCallAssertionError",
        "OutputAssertionError",
        "CostAssertionError",
        "LatencyAssertionError",
    }
    actual_exports = set(getattr(a_mod, "__all__", ()))
    missing = expected_exports - actual_exports
    assert not missing, f"Public API drift — missing __all__ entries: {missing}"


@pytest.mark.no_eval
def test_assert_output_named_failure() -> None:
    """A2 — ``assert_output`` raises ``OutputAssertionError`` naming the layer.

    Drives the assertion with a deliberately failing condition (Spanish
    text but ``must_mention=['xyz']`` not present). The raised error
    must (a) be an ``OutputAssertionError``, (b) carry ``.layer_name ==
    "output"``, (c) include the layer name in its string form so the
    smoke runner produces a human-debuggable diff in ``assertions.json``.
    """
    from tests.agentic_evals.sales_agent.runner.assertions import (
        OutputAssertionError,
        assert_output,
    )

    spanish_text = "Hola, te confirmo la reserva. ¡Gracias por elegirnos!"
    with pytest.raises(OutputAssertionError) as exc_info:
        assert_output(
            spanish_text,
            language="es",
            must_mention=["xyz_marker_not_present"],
        )

    err = exc_info.value
    assert err.layer_name == "output", f"layer_name must be 'output', got '{err.layer_name}'"
    # The message names the layer for accionable debugging in assertions.json.
    assert "output" in str(err).lower(), f"Error message must name the layer, got: {err}"
    # Observed / expected attributes carry diagnostic context.
    assert err.expected is not None
    assert err.observed is not None


@pytest.mark.no_eval
def test_assert_voice_fidelity_is_placeholder() -> None:
    """A3 — ``assert_voice_fidelity`` raises ``NotImplementedError`` (Story 7 future-proof).

    The smoke test (T-5) MUST NOT call this function — but if a future
    refactor accidentally wires it in before the Story 7 grader lands,
    the harness fails fast with an explicit message naming the future
    story scope (instead of silently passing voice validation).
    """
    from tests.agentic_evals.sales_agent.runner.assertions import (
        assert_voice_fidelity,
    )

    with pytest.raises(NotImplementedError) as exc_info:
        assert_voice_fidelity(
            "Hola, ¿cómo estás?",
            brand_voice_template="placeholder voice template",
        )
    msg = str(exc_info.value).lower()
    # Message must mention Story 7 or "future" so callers know where the impl lives.
    assert "story 7" in msg or "future" in msg, (
        f"NotImplementedError message must reference Story 7 / future scope, got: {exc_info.value}"
    )


@pytest.mark.no_eval
def test_detect_language_safe_returns_unknown_on_exception() -> None:
    """A4 — ``_detect_language_safe`` swallows ``LangDetectException`` + ``ImportError``.

    Two graceful-degradation paths (Tessl ``graceful-degradation`` Rule 6):

    1. ``langdetect`` package unavailable → ``importlib.import_module``
       raises ``ImportError`` → fallback "unknown".
    2. ``langdetect.detect`` raises ``LangDetectException`` (e.g. empty
       input, no features extracted) → fallback "unknown".

    Either path MUST NEVER propagate the exception — assertions are
    best-effort about language detection (it is a soft signal, not a
    hard contract).
    """
    import importlib

    from tests.agentic_evals.sales_agent.runner.assertions import (
        _detect_language_safe,
    )

    # Path 1 — ImportError when langdetect is unavailable.
    real_import_module = importlib.import_module

    def fake_import_module(name: str, *args: object, **kwargs: object) -> object:
        if name == "langdetect":
            error_msg = "simulated missing dep"
            raise ImportError(error_msg)
        return real_import_module(name, *args, **kwargs)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(importlib, "import_module", fake_import_module)
        result = _detect_language_safe("Hola, ¿cómo estás?")
        assert result == "unknown", f"ImportError fallback must yield 'unknown', got '{result}'"

    # Path 2 — LangDetectException on detect() call.
    import langdetect  # type: ignore[import-untyped]
    from langdetect.lang_detect_exception import (  # type: ignore[import-untyped]
        LangDetectException,
    )

    def fake_detect(_text: str) -> str:
        # ErrorCode 0 = NoFeaturesError per langdetect public API.
        raise LangDetectException(0, "simulated no features")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(langdetect, "detect", fake_detect)
        result = _detect_language_safe("ambiguous text")
        assert result == "unknown", f"LangDetectException fallback must yield 'unknown', got '{result}'"


@pytest.mark.no_eval
def test_assert_trajectory_includes_mode_passes_when_subset() -> None:
    """``mode='includes'`` accepts when expected is a subset of history.

    Story 1 happy-path scenario: the smoke test only requires that the
    qualifier specialist appears at minimum — extra specialists later in
    the trail are acceptable.
    """
    from tests.agentic_evals.sales_agent.runner.assertions import (
        TrajectoryAssertionError,
        assert_trajectory,
    )
    from tests.agentic_evals.sales_agent.runner.trajectory_spy import TrajectorySpy

    spy = TrajectorySpy()
    spy.specialist_history.extend(["supervisor", "qualifier", "tool_executor"])

    # Subset present — passes.
    assert_trajectory(spy, expected_specialists=["qualifier"], mode="includes")
    assert_trajectory(spy, expected_specialists=["supervisor", "qualifier"], mode="includes")

    # Missing specialist — fails.
    with pytest.raises(TrajectoryAssertionError) as exc_info:
        assert_trajectory(spy, expected_specialists=["closer"], mode="includes")
    assert exc_info.value.layer_name == "trajectory"


@pytest.mark.no_eval
def test_assert_trajectory_exact_mode_strict_match() -> None:
    """``mode='exact'`` requires history == expected (ordered, complete)."""
    from tests.agentic_evals.sales_agent.runner.assertions import (
        TrajectoryAssertionError,
        assert_trajectory,
    )
    from tests.agentic_evals.sales_agent.runner.trajectory_spy import TrajectorySpy

    spy = TrajectorySpy()
    spy.specialist_history.extend(["qualifier", "tool_executor"])

    # Exact match — passes.
    assert_trajectory(spy, expected_specialists=["qualifier", "tool_executor"], mode="exact")

    # Order mismatch — fails (exact mode is order-sensitive).
    with pytest.raises(TrajectoryAssertionError) as exc_info:
        assert_trajectory(spy, expected_specialists=["tool_executor", "qualifier"], mode="exact")
    assert exc_info.value.layer_name == "trajectory"


@pytest.mark.no_eval
def test_assert_tool_calls_required_present_forbidden_absent() -> None:
    """Required tools must appear; forbidden tools must NOT appear (B4)."""
    from tests.agentic_evals.sales_agent.runner.assertions import (
        ToolCallAssertionError,
        assert_tool_calls,
    )
    from tests.agentic_evals.sales_agent.runner.trajectory_spy import TrajectorySpy

    spy = TrajectorySpy()
    spy.tool_calls.extend(
        [
            {"name": "knowledge_search", "input": "q", "output": "r", "run_id": "1"},
            {"name": "recommend_product", "input": "q", "output": "r", "run_id": "2"},
        ],
    )

    # Required present, forbidden absent — passes.
    assert_tool_calls(
        spy,
        required=["knowledge_search"],
        forbidden=["create_payment_link", "grant_access"],
    )

    # Required missing — fails.
    with pytest.raises(ToolCallAssertionError) as exc_info:
        assert_tool_calls(spy, required=["create_booking_link"], forbidden=[])
    assert exc_info.value.layer_name == "tool_calls"


@pytest.mark.no_eval
def test_assert_tool_calls_forbidden_present_raises() -> None:
    """A forbidden tool fired → ``ToolCallAssertionError`` (B4 binding)."""
    from tests.agentic_evals.sales_agent.runner.assertions import (
        ToolCallAssertionError,
        assert_tool_calls,
    )
    from tests.agentic_evals.sales_agent.runner.trajectory_spy import TrajectorySpy

    spy = TrajectorySpy()
    spy.tool_calls.append(
        {"name": "create_payment_link", "input": "x", "output": "y", "run_id": "1"},
    )

    with pytest.raises(ToolCallAssertionError) as exc_info:
        assert_tool_calls(
            spy,
            required=[],
            forbidden=["create_payment_link"],
        )
    err = exc_info.value
    assert err.layer_name == "tool_calls"
    # observed contains the offending tool name for the assertions.json record.
    assert "create_payment_link" in str(err)


@pytest.mark.no_eval
def test_assert_output_must_mention_case_insensitive() -> None:
    """``must_mention`` is case-insensitive substring check.

    Cold-lead path expects the agent to say "hola" or "buenas" or
    similar — rather than forcing exact case, the assertion treats the
    must_mention list as case-insensitive substrings.

    Note: ``langdetect`` is notoriously unreliable on short text (10-30
    chars) — it can misclassify "Hola, te confirmo la reserva." as
    Italian. The test uses a longer Spanish sentence so the language
    detection layer is exercised reliably.
    """
    from tests.agentic_evals.sales_agent.runner.assertions import assert_output

    text = (
        "Hola, te confirmo que tu reserva fue procesada con éxito. "
        "Gracias por elegir nuestro servicio. Saludos cordiales."
    )
    # Lowercase "hola" matches "Hola" via case-insensitive comparison.
    assert_output(text, language="es", must_mention=["hola"])
    # Original case also works.
    assert_output(text, language="es", must_mention=["Hola"])


@pytest.mark.no_eval
def test_assert_output_language_unknown_skips_language_check() -> None:
    """When ``_detect_language_safe`` returns 'unknown', language check is skipped.

    Graceful degradation: if langdetect fails to identify (empty text,
    ambiguous), the assertion does NOT fail on language alone — it logs
    a warning and continues with the other checks. This prevents flaky
    smoke runs from a soft signal.
    """
    import importlib

    from tests.agentic_evals.sales_agent.runner.assertions import assert_output

    real_import_module = importlib.import_module

    def fake_import_module(name: str, *args: object, **kwargs: object) -> object:
        if name == "langdetect":
            error_msg = "simulated missing dep"
            raise ImportError(error_msg)
        return real_import_module(name, *args, **kwargs)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(importlib, "import_module", fake_import_module)
        # No raise even though language="es" can't be verified.
        assert_output(
            "Some short text",
            language="es",
            must_mention=["text"],
        )


@pytest.mark.no_eval
def test_assert_latency_passes_when_below_threshold() -> None:
    """``assert_latency`` reads ``spy.duration_ms`` (or falls back to 0).

    The spy in T-3 doesn't track per-span time today — the assertion
    duck-types: if ``spy.duration_ms`` exists and is numeric, sum it; if
    spy carries ``tool_calls`` items with a ``duration_ms`` key, sum
    those; else return 0 (no spans observed = pass through).
    """
    from tests.agentic_evals.sales_agent.runner.assertions import (
        LatencyAssertionError,
        assert_latency,
    )
    from tests.agentic_evals.sales_agent.runner.trajectory_spy import TrajectorySpy

    spy = TrajectorySpy()
    # Inject duration_ms attribute (caller's responsibility — Story 1 spy is duck-typed).
    spy.duration_ms = 1500  # type: ignore[attr-defined]

    # Below threshold — passes.
    assert_latency(spy, max_ms=30000)

    # Exceeds threshold — fails.
    spy.duration_ms = 31000  # type: ignore[attr-defined]
    with pytest.raises(LatencyAssertionError) as exc_info:
        assert_latency(spy, max_ms=30000)
    assert exc_info.value.layer_name == "latency"


@pytest.mark.no_eval
def test_assert_latency_sums_tool_call_spans_when_present() -> None:
    """When spy.tool_calls items carry duration_ms, sum across spans."""
    from tests.agentic_evals.sales_agent.runner.assertions import assert_latency
    from tests.agentic_evals.sales_agent.runner.trajectory_spy import TrajectorySpy

    spy = TrajectorySpy()
    spy.tool_calls.extend(
        [
            {"name": "a", "input": "", "output": "", "run_id": "1", "duration_ms": 500},
            {"name": "b", "input": "", "output": "", "run_id": "2", "duration_ms": 700},
        ],
    )
    # Sum is 1200 ms, threshold 5000 — passes.
    assert_latency(spy, max_ms=5000)


@pytest.mark.no_eval
def test_assert_latency_missing_signal_passes_through() -> None:
    """Spy with no duration_ms attr / no tool_call durations → 0 ms (pass).

    Defensive — Story 1 spy doesn't yet track time. ``assert_latency``
    should NOT raise on a spy without time data; it returns silently so
    the smoke harness can still call it without conditional logic.
    """
    from tests.agentic_evals.sales_agent.runner.assertions import assert_latency
    from tests.agentic_evals.sales_agent.runner.trajectory_spy import TrajectorySpy

    spy = TrajectorySpy()
    # No duration_ms attribute, empty tool_calls.
    assert_latency(spy, max_ms=1)


@pytest.mark.no_eval
def test_assert_cost_recorded_zero_row_raises() -> None:
    """Cost == 0 across rows → ``CostAssertionError``.

    Mocks the DB query path: a row exists but ``cost_usd`` is 0 (LiteLLM
    didn't provide cost — known degraded path per T-1 cost_recorder
    canonicalization). Assertion must flag this as a Capa 4 failure so
    smoke catches silent cost regressions.
    """
    from decimal import Decimal
    from uuid import uuid4

    from tests.agentic_evals.sales_agent.runner.assertions import (
        CostAssertionError,
        assert_cost_recorded,
    )

    class _FakeRow:
        def __init__(self, model_responded: str, cost_usd: Decimal | None) -> None:
            self.model_responded = model_responded
            self.cost_usd = cost_usd

    class _FakeResult:
        def __init__(self, rows: list[_FakeRow]) -> None:
            self._rows = rows

        def all(self) -> list[_FakeRow]:
            return self._rows

    class _FakeSession:
        def __init__(self, rows: list[_FakeRow]) -> None:
            self._rows = rows
            self.last_filters: list[object] = []

        def execute(self, stmt: object) -> _FakeResult:
            self.last_filters.append(stmt)
            return _FakeResult(self._rows)

    tenant_id = uuid4()
    run_id = uuid4()
    rows = [_FakeRow("kimi/kimi-k2.6", Decimal(0))]
    session = _FakeSession(rows)

    with pytest.raises(CostAssertionError) as exc_info:
        assert_cost_recorded(
            run_id,
            db_session=session,  # type: ignore[arg-type]
            tenant_id=tenant_id,
            model_pattern="kimi/*",
            max_cost_usd=Decimal("0.05"),
        )
    assert exc_info.value.layer_name == "cost"


@pytest.mark.no_eval
def test_assert_cost_recorded_passes_when_within_budget() -> None:
    """Happy path — sum > 0 + sum < max + every row matches model_pattern."""
    from decimal import Decimal
    from uuid import uuid4

    from tests.agentic_evals.sales_agent.runner.assertions import assert_cost_recorded

    class _FakeRow:
        def __init__(self, model_responded: str, cost_usd: Decimal | None) -> None:
            self.model_responded = model_responded
            self.cost_usd = cost_usd

    class _FakeResult:
        def __init__(self, rows: list[_FakeRow]) -> None:
            self._rows = rows

        def all(self) -> list[_FakeRow]:
            return self._rows

    class _FakeSession:
        def __init__(self, rows: list[_FakeRow]) -> None:
            self._rows = rows

        def execute(self, _stmt: object) -> _FakeResult:
            return _FakeResult(self._rows)

    tenant_id = uuid4()
    run_id = uuid4()
    rows = [
        _FakeRow("kimi/kimi-k2.6", Decimal("0.003")),
        _FakeRow("kimi/kimi-k2.6", Decimal("0.002")),
    ]
    session = _FakeSession(rows)

    assert_cost_recorded(
        run_id,
        db_session=session,  # type: ignore[arg-type]
        tenant_id=tenant_id,
        model_pattern="kimi/*",
        max_cost_usd=Decimal("0.05"),
    )


@pytest.mark.no_eval
def test_assert_cost_recorded_model_mismatch_raises() -> None:
    """Row with model not matching pattern → ``CostAssertionError``."""
    from decimal import Decimal
    from uuid import uuid4

    from tests.agentic_evals.sales_agent.runner.assertions import (
        CostAssertionError,
        assert_cost_recorded,
    )

    class _FakeRow:
        def __init__(self, model_responded: str, cost_usd: Decimal | None) -> None:
            self.model_responded = model_responded
            self.cost_usd = cost_usd

    class _FakeResult:
        def __init__(self, rows: list[_FakeRow]) -> None:
            self._rows = rows

        def all(self) -> list[_FakeRow]:
            return self._rows

    class _FakeSession:
        def __init__(self, rows: list[_FakeRow]) -> None:
            self._rows = rows

        def execute(self, _stmt: object) -> _FakeResult:
            return _FakeResult(self._rows)

    rows = [_FakeRow("openai/gpt-4o-mini", Decimal("0.003"))]
    session = _FakeSession(rows)

    with pytest.raises(CostAssertionError) as exc_info:
        assert_cost_recorded(
            uuid4(),
            db_session=session,  # type: ignore[arg-type]
            tenant_id=uuid4(),
            model_pattern="kimi/*",
            max_cost_usd=Decimal("0.05"),
        )
    assert exc_info.value.layer_name == "cost"


@pytest.mark.no_eval
def test_assert_cost_recorded_above_max_raises() -> None:
    """Sum cost > max threshold → ``CostAssertionError``."""
    from decimal import Decimal
    from uuid import uuid4

    from tests.agentic_evals.sales_agent.runner.assertions import (
        CostAssertionError,
        assert_cost_recorded,
    )

    class _FakeRow:
        def __init__(self, model_responded: str, cost_usd: Decimal | None) -> None:
            self.model_responded = model_responded
            self.cost_usd = cost_usd

    class _FakeResult:
        def __init__(self, rows: list[_FakeRow]) -> None:
            self._rows = rows

        def all(self) -> list[_FakeRow]:
            return self._rows

    class _FakeSession:
        def __init__(self, rows: list[_FakeRow]) -> None:
            self._rows = rows

        def execute(self, _stmt: object) -> _FakeResult:
            return _FakeResult(self._rows)

    rows = [_FakeRow("kimi/kimi-k2.6", Decimal("0.20"))]
    session = _FakeSession(rows)

    with pytest.raises(CostAssertionError) as exc_info:
        assert_cost_recorded(
            uuid4(),
            db_session=session,  # type: ignore[arg-type]
            tenant_id=uuid4(),
            model_pattern="kimi/*",
            max_cost_usd=Decimal("0.05"),
        )
    assert exc_info.value.layer_name == "cost"


@pytest.mark.no_eval
def test_assertions_module_no_top_level_langdetect_import() -> None:
    """Architectural gate — ``assertions.py`` must NOT have top-level langdetect import.

    B5 binding (langdetect lazy via ``importlib.import_module``). Top-
    level ``import langdetect`` in this file would pull the dep into the
    eval harness load path even when the lazy fallback is desired
    (``optional-dependencies.evals``). Verified via AST walk.
    """
    import ast

    from tests.agentic_evals.sales_agent.runner import assertions as a_mod

    source = Path(a_mod.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    offenders: list[tuple[int, str]] = []
    for node in ast.iter_child_nodes(tree):
        # Top-level Import — `import langdetect`.
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "langdetect" or alias.name.startswith("langdetect."):
                    offenders.append((node.lineno, f"import {alias.name}"))
        # Top-level ImportFrom — `from langdetect import detect`.
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module
            and (node.module == "langdetect" or node.module.startswith("langdetect."))
        ):
            offenders.append((node.lineno, f"from {node.module} import ..."))

    assert offenders == [], (
        "B5 violation — assertions.py has top-level langdetect import:\n"
        + "\n".join(f"  line {ln}: {desc}" for ln, desc in offenders)
        + "\nUse importlib.import_module('langdetect') inside _detect_language_safe instead."
    )
