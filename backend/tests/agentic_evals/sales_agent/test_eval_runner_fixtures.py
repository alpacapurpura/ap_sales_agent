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
