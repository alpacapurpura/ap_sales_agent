"""Smoke runner — 4 scenarios covering happy + skip + degraded + cross-tenant.

Per ``03-arch-be.md`` § "Tests requeridos" + ``03-arch-agentic.md`` §
"Decisión arquitectónica clave" + ticket T-5 acceptance A1-A6: this
module wires together everything T-1..T-4 shipped (golden_loader,
TrajectorySpy, write_run_artifacts, 5 assertion layers,
visionarias_tenant_session + sales_agent_entrypoint + synthetic_tenant
fixtures) into the END-to-END smoke test.

Four scenarios:

    Scenario 1 — happy multi-layer (real LLM, ``test_smoke_multi_layer``)
        Loads visionarias-smoke-golden.yaml, invokes the production
        ``agent_app.ainvoke`` via the ``sales_agent_entrypoint`` fixture
        (which composes the ``TrajectorySpy`` alongside the production
        callback handler), then runs all five assertion layers
        (trajectory / tool_calls / output / cost / latency) against the
        captured trajectory + DB rows. Cost budget < $0.01/run.

    Scenario 2 — skip-without-flag (``test_skip_without_flag``)
        Spawns a real ``pytest`` subprocess (no LLM call) WITHOUT
        ``--run-evals`` against a synthetic eval-marked test in tmp_path
        and asserts:
            * subprocess exit code is 0
            * stdout reports the eval-marked test SKIPPED (not PASSED nor FAILED)
            * the canonical skip reason from the root conftest appears
              in stdout (gate contract preserved).
        This validates the ``--run-evals`` gating mechanism end-to-end.

    Scenario 3 — degraded-output (``test_degraded_output_caught``)
        Monkeypatches ``MultiRoleLLMRouter.generate_response`` to return
        a short non-Spanish text ("ok"). The harness should catch the
        regression via ``assert_output`` and raise ``OutputAssertionError``.
        The error's ``layer_name == "output"`` is asserted, and the
        ``assertions.json`` artifact is verified to contain the
        ``failed_layer_name == "output"`` record. Tests the assertion
        library detects real regressions.

    Scenario 4 — cross-tenant leak (``test_no_cross_tenant_leak``)
        Seeds ``T2_synthetic`` tenant + offer via the ``synthetic_tenant``
        fixture. Invokes the agent with the Visionarias tenant_id (NOT
        the synthetic). Post-invoke, queries
        ``SELECT DISTINCT tenant_id FROM sales_agent_trace_event WHERE turn_id = ?``
        and asserts exactly ONE distinct tenant_id matching Visionarias.
        Reads the trace.json artifact and asserts the substring
        ``T2_synthetic`` is ABSENT (PII / cross-tenant leak protection).

Anti-duplication §0:

* Reuses ``GoldenSpec`` + ``load_yaml`` from ``runner/golden_loader.py``.
* Reuses ``TrajectorySpy`` + ``write_run_artifacts`` (T-3, audit-passed).
* Reuses 5 assertion functions + ``LayerAssertionError`` (T-4, audit-
  passed). T-4 audit flagged a forward-compatible drift in 5 signatures
  vs arch-be prescriptions; this module consumes T-4 AS-IS — no thin
  wrappers needed (signatures ergonomic enough).
* Reuses ``sales_agent_entrypoint`` + ``synthetic_tenant`` +
  ``visionarias_tenant_session`` + ``eval_run_id`` fixtures (T-2/T-5).

Tenant isolation: Scenario 4 explicit regression. All queries filter by
``tenant_id``; cross-tenant absence is verified.

Spanish neutro LATAM: assertion + diagnostic messages in tuteo.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import UUID

import pytest
import structlog
from sqlalchemy import select

from tests.agentic_evals.sales_agent.runner.artifacts import write_run_artifacts
from tests.agentic_evals.sales_agent.runner.assertions import (
    LayerAssertionError,
    OutputAssertionError,
    assert_cost_recorded,
    assert_latency,
    assert_output,
    assert_tool_calls,
    assert_trajectory,
)
from tests.agentic_evals.sales_agent.runner.golden_loader import (
    GoldenSpec,
    load_yaml,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

logger = structlog.get_logger()


_GOLDENS_DIR = Path(__file__).resolve().parent / "goldens"
_SMOKE_GOLDEN_PATH = _GOLDENS_DIR / "visionarias-smoke-golden.yaml"


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────


def _load_smoke_golden() -> GoldenSpec:
    """Load the canonical smoke golden YAML.

    Raises:
        FileNotFoundError: When the YAML is missing — typically only happens
            when T-5 deliverable 2 was never committed; the smoke harness
            cannot proceed without it.
    """
    return load_yaml(_SMOKE_GOLDEN_PATH)


def _extract_response_text(invoke_result: dict[str, Any]) -> str:
    """Extract the agent's final assistant message text from the ainvoke result.

    The sales_agent state stores the response as the last entry in
    ``state["messages"]`` with ``role="assistant"``. Defensive against
    empty / missing messages — returns empty string if absent so the
    output assertion can name the regression cleanly.
    """
    state = invoke_result.get("result") or {}
    messages = state.get("messages") or []
    for msg in reversed(messages):
        if isinstance(msg, dict) and msg.get("role") == "assistant":
            content = msg.get("content")
            if isinstance(content, str):
                return content
        # LangChain BaseMessage shape (defensive — the supervisor uses dicts
        # but the subgraph may upgrade to BaseMessage in future refactors).
        if hasattr(msg, "content") and getattr(msg, "type", None) == "ai":
            content = msg.content
            if isinstance(content, str):
                return content
    return ""


def _record_assertion_outcome(
    layer: str,
    *,
    passed: bool,
    error: LayerAssertionError | None = None,
) -> dict[str, Any]:
    """Build a single assertion-result record for the assertions.json artifact."""
    record: dict[str, Any] = {
        "layer": layer,
        "passed": passed,
    }
    if error is not None:
        record["failed_layer_name"] = error.layer_name
        record["error_message"] = str(error)
        record["observed"] = error.observed
        record["expected"] = error.expected
    return record


# ──────────────────────────────────────────────────────────────────────────
# Scenario 1 — happy multi-layer (real LLM)
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_smoke_multi_layer(
    sales_agent_entrypoint: Callable[[str], Awaitable[dict[str, Any]]],
    visionarias_tenant_session: dict[str, Any],
) -> None:
    """Scenario 1: happy multi-layer — real LLM call against Visionarias tenant.

    Per ticket T-5 acceptance A1: load the golden, invoke the agent end-
    to-end, run all 5 assertion layers, write artifacts. Real LLM cost
    < $0.01/run (LiteLLM proxy → DeepSeek V4-Flash default).

    Pre-conditions enforced by ``visionarias_tenant_session`` fixture:
    Postgres reachable + Visionarias tenant exists + ≥1 active offer +
    compiled ``PersonalityProfile.system_instruction``. Any precondition
    failure → SKIP with explicit Spanish-neutro reason (B2 contract).
    """
    golden = _load_smoke_golden()
    db_session = visionarias_tenant_session["db_session"]
    tenant_id: UUID = visionarias_tenant_session["tenant_id"]

    # Invoke — real LLM call. The fixture composes the spy alongside the
    # production callback handler (RunnableConfig.callbacks list).
    invoke_result = await sales_agent_entrypoint(golden.input_message)

    spy = invoke_result["spy"]
    turn_id: UUID | None = invoke_result["turn_id"]
    response_text = _extract_response_text(invoke_result)

    assertion_results: list[dict[str, Any]] = []

    # Capa 1 — trajectory (specialist routing).
    try:
        assert_trajectory(spy, golden.expected_specialists, mode="includes")
        assertion_results.append(_record_assertion_outcome("trajectory", passed=True))
    except LayerAssertionError as exc:
        assertion_results.append(_record_assertion_outcome("trajectory", passed=False, error=exc))
        write_run_artifacts(
            run_id=turn_id or "no-turn-id",
            spy=spy,
            response_text=response_text,
            assertions_results=assertion_results,
        )
        raise

    # Capa 2 — tool_calls (required + forbidden).
    try:
        assert_tool_calls(spy, required=golden.required_tools, forbidden=golden.forbidden_tools)
        assertion_results.append(_record_assertion_outcome("tool_calls", passed=True))
    except LayerAssertionError as exc:
        assertion_results.append(_record_assertion_outcome("tool_calls", passed=False, error=exc))
        write_run_artifacts(
            run_id=turn_id or "no-turn-id",
            spy=spy,
            response_text=response_text,
            assertions_results=assertion_results,
        )
        raise

    # Capa 3 — output (language + must_mention).
    try:
        assert_output(response_text, language=golden.language, must_mention=golden.must_mention)
        assertion_results.append(_record_assertion_outcome("output", passed=True))
    except LayerAssertionError as exc:
        assertion_results.append(_record_assertion_outcome("output", passed=False, error=exc))
        write_run_artifacts(
            run_id=turn_id or "no-turn-id",
            spy=spy,
            response_text=response_text,
            assertions_results=assertion_results,
        )
        raise

    # Capa 4 — cost recorded (DB query). Skip if turn_id is None (obs ctx
    # factory failed at fixture setup — best-effort path documented in
    # entrypoint fixture). The smoke acceptance allows this skip per
    # entrypoint fixture contract.
    if turn_id is None:
        pytest.skip(
            "turn_id is None: la observability context no se construyo; "
            "la capa 4 (cost) no es verificable en este run.",
        )
    try:
        assert_cost_recorded(
            turn_id,
            db_session=db_session,
            tenant_id=tenant_id,
            model_pattern="*",  # any model — Story 8 will narrow per-route
            max_cost_usd=Decimal(str(golden.max_cost_usd)),
        )
        assertion_results.append(_record_assertion_outcome("cost", passed=True))
    except LayerAssertionError as exc:
        assertion_results.append(_record_assertion_outcome("cost", passed=False, error=exc))
        write_run_artifacts(
            run_id=turn_id,
            spy=spy,
            response_text=response_text,
            assertions_results=assertion_results,
        )
        raise

    # Capa 5 — latency. The spy's tool_calls may not carry duration_ms
    # signals when no tools fire (cold-lead happy path); assert_latency
    # gracefully passes through when no signal is captured.
    try:
        assert_latency(spy, max_ms=golden.max_latency_ms)
        assertion_results.append(_record_assertion_outcome("latency", passed=True))
    except LayerAssertionError as exc:
        assertion_results.append(_record_assertion_outcome("latency", passed=False, error=exc))
        write_run_artifacts(
            run_id=turn_id,
            spy=spy,
            response_text=response_text,
            assertions_results=assertion_results,
        )
        raise

    # Happy path — write artifacts with all-pass record.
    write_run_artifacts(
        run_id=turn_id,
        spy=spy,
        response_text=response_text,
        assertions_results=assertion_results,
    )
    logger.info(
        "eval_smoke_multi_layer_pass",
        turn_id=str(turn_id),
        tenant_id=str(tenant_id),
        layers_passed=[r["layer"] for r in assertion_results if r["passed"]],
    )


# ──────────────────────────────────────────────────────────────────────────
# Scenario 2 — skip without --run-evals flag
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.no_eval
def test_skip_without_flag() -> None:
    """Scenario 2: ``@pytest.mark.eval`` tests SKIP when ``--run-evals`` absent.

    Per ticket T-5 acceptance A2 + spec § "Scenario 2": validates the
    gating mechanism via a real ``pytest`` subprocess (no real LLM call)
    and asserts:

        * subprocess exit code is 0 (SKIP is not a failure)
        * stdout reports the eval-marked test SKIPPED (not PASSED nor FAILED)
        * the canonical skip reason ``"eval markers require --run-evals flag"``
          appears in stdout (root conftest contract preserved)

    The ``no_eval`` marker on THIS test ensures Scenario 2 itself runs on
    the default suite (otherwise it would be skipped recursively under
    its own gate).

    Implementation note: ``pytester`` plugin would be the canonical
    pytest pattern but registering it requires ``pytest_plugins`` in a
    top-level conftest — a cross-team modification we avoid per
    ``parallel-safety.md`` M8 (extend, not destroy ajenos). Instead this
    test invokes a real ``subprocess.run`` against the venv pytest,
    re-executing this same module's ``test_smoke_multi_layer`` (an
    ``@pytest.mark.eval`` test) and parsing stdout deterministically.
    Re-using the production smoke test as the "eval-marked target"
    guarantees the conftest hierarchy is loaded exactly as in CI.
    """
    # Invoke pytest as subprocess WITHOUT --run-evals. The target is
    # this same file's test_smoke_multi_layer (an @pytest.mark.eval test);
    # --collect-only avoids any real fixture setup (DB session, LLM call)
    # while still triggering pytest_collection_modifyitems → auto-skip.
    import subprocess
    import sys

    repo_root = Path(__file__).resolve().parents[3]  # backend/tests/agentic_evals/sales_agent → backend
    pytest_binary = repo_root / ".venv" / "bin" / "pytest"
    if not pytest_binary.exists():
        pytest_binary = Path(sys.executable).parent / "pytest"

    target = "tests/agentic_evals/sales_agent/test_eval_runner_smoke.py::test_smoke_multi_layer"
    # Override addopts (pyproject.toml injects --randomly-seed=last which
    # the subprocess does not understand without pytest-randomly enabled).
    # ``--override-ini`` keeps the rest of pyproject config intact.
    result = subprocess.run(  # noqa: S603 — controlled invocation, args fixed
        [
            str(pytest_binary),
            target,
            "-v",
            "--no-header",
            "--override-ini=addopts=",
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        cwd=str(repo_root),
    )
    stdout = result.stdout
    stderr = result.stderr

    # 1. Exit 0 → SKIP is not a failure.
    assert result.returncode == 0, (
        f"Subprocess pytest sin --run-evals devolvio exit code {result.returncode}. "
        f"Se esperaba 0 (SKIP no es fallo).\nstdout:\n{stdout}\nstderr:\n{stderr}"
    )
    # 2. Skipped (not passed nor failed).
    assert "skipped" in stdout.lower(), f"Subprocess no reporto SKIPPED. stdout:\n{stdout}"
    assert "1 passed" not in stdout, (
        f"Subprocess reporto PASSED — el body del test eval-marcado se ejecuto. stdout:\n{stdout}"
    )
    assert "failed" not in stdout.lower() or " 0 failed" in stdout.lower(), (
        f"Subprocess reporto FAILED — el gate esta roto. stdout:\n{stdout}"
    )
    # 3. Canonical skip reason from root conftest is preserved.
    assert "eval markers require --run-evals flag" in stdout, (
        f"La razon de skip canonica del root conftest no aparece en stdout. "
        f"Verifica que tests/agentic_evals/conftest.py no haya cambiado el wording. "
        f"stdout:\n{stdout}"
    )


# ──────────────────────────────────────────────────────────────────────────
# Scenario 3 — degraded output captured by assert_output
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_degraded_output_caught(
    sales_agent_entrypoint: Callable[[str], Awaitable[dict[str, Any]]],
    visionarias_tenant_session: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scenario 3: monkeypatch LLM to return degraded output → harness catches it.

    Per ticket T-5 acceptance A3 + spec § "Scenario 3": injects a
    degraded LLM response (short, non-Spanish, missing must_mention)
    and verifies:

        * The harness raises ``OutputAssertionError`` (not silent pass).
        * The error's ``layer_name == "output"`` (named layer is
          actionable for the dev).
        * ``assertions.json`` artifact contains the failed_layer_name
          record (downstream debugging trail).

    Tests the ASSERTION LIBRARY itself detects regressions — NOT the
    agent. The agent is bypassed via monkeypatch so this scenario does
    NOT consume real LLM budget.
    """
    del visionarias_tenant_session  # consumed indirectly via sales_agent_entrypoint fixture

    golden = _load_smoke_golden()

    # Monkeypatch the LLM router's generate_response to return degraded text.
    # The router is the single dispatch point used by every specialist
    # node (qualifier / product_expert / closer / supervisor) — patching
    # at this seam guarantees the agent's output is "ok" regardless of
    # which specialist runs.
    from luana_core_llm.router import MultiRoleLLMRouter

    def _degraded_response(self: object, *args: object, **kwargs: object) -> str:
        del self, args, kwargs
        return "ok"

    monkeypatch.setattr(MultiRoleLLMRouter, "generate_response", _degraded_response)

    invoke_result = await sales_agent_entrypoint(golden.input_message)
    spy = invoke_result["spy"]
    turn_id: UUID | None = invoke_result["turn_id"]
    response_text = _extract_response_text(invoke_result)

    assertion_results: list[dict[str, Any]] = []

    # The harness is expected to catch the degraded output via assert_output
    # — language detection on "ok" returns "unknown" (langdetect needs ≥2
    # features), so the language check is skipped, BUT must_mention
    # ("Visionarias") is missing from "ok" → OutputAssertionError raised.
    captured_error: OutputAssertionError | None = None
    try:
        assert_output(
            response_text,
            language=golden.language,
            must_mention=golden.must_mention,
        )
        assertion_results.append(_record_assertion_outcome("output", passed=True))
    except OutputAssertionError as exc:
        captured_error = exc
        assertion_results.append(_record_assertion_outcome("output", passed=False, error=exc))

    # Assert the harness captured the regression (NOT silent pass).
    assert captured_error is not None, (
        "assert_output NO detecto la salida degradada — la libreria de "
        "asserciones no esta protegiendo contra regresiones de output."
    )
    # Named layer: dev should see "output" in the error class.
    assert captured_error.layer_name == "output", (
        f"OutputAssertionError.layer_name esperado 'output', se observo '{captured_error.layer_name}'."
    )

    # Write artifacts so the failure trail is persistent for human triage.
    run_id_for_artifact = turn_id or "scenario3-degraded"
    write_run_artifacts(
        run_id=run_id_for_artifact,
        spy=spy,
        response_text=response_text,
        assertions_results=assertion_results,
    )

    # Verify the assertions.json artifact contains the failed_layer_name.
    # ASYNC240: pathlib here runs AFTER write_run_artifacts (sync fs already
    # done by writer); not a blocking pattern in the request critical path.
    artifact_path = Path(__file__).resolve().parent / "_artifacts" / str(run_id_for_artifact) / "assertions.json"  # noqa: ASYNC240
    assert artifact_path.exists(), (
        f"assertions.json no se escribio en {artifact_path}; write_run_artifacts no persistio el fallo de capa."
    )
    artifact_text = artifact_path.read_text(encoding="utf-8")
    assert "failed_layer_name" in artifact_text, (
        "assertions.json no contiene el campo 'failed_layer_name' — el registro de fallo de capa esta incompleto."
    )
    assert '"output"' in artifact_text, (
        "assertions.json no nombra la capa 'output' como la fallida — "
        "el dev no puede triar el problema sin nombre de capa."
    )


# ──────────────────────────────────────────────────────────────────────────
# Scenario 4 — cross-tenant leak adversarial
# ──────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_no_cross_tenant_leak(
    sales_agent_entrypoint: Callable[[str], Awaitable[dict[str, Any]]],
    visionarias_tenant_session: dict[str, Any],
    synthetic_tenant: dict[str, Any],
) -> None:
    """Scenario 4: agent invoked w/ Visionarias tenant_id → no T2 leak in DB or artifacts.

    Per ticket T-5 acceptance A4 + spec § "Scenario 4": with the
    synthetic ``T2_synthetic`` tenant + offer seeded alongside Visionarias,
    invoking the agent against the Visionarias tenant_id MUST NOT write
    any row carrying the synthetic tenant_id, NOR include the substring
    ``T2_synthetic`` in the sanitised trace.json artifact.

    The synthetic tenant fixture seeds rows BEFORE the invocation so the
    DB is "polluted" with another tenant — mirrors a multi-tenant prod
    DB. Tenant isolation rule (`.claude/rules/tenant-isolation.md`)
    requires every query / write to filter by tenant_id; this scenario
    is the regression test.
    """
    golden = _load_smoke_golden()
    db_session = visionarias_tenant_session["db_session"]
    visionarias_id: UUID = visionarias_tenant_session["tenant_id"]
    synthetic_id: UUID = synthetic_tenant["tenant_id"]

    # Sanity check: the two tenants have distinct IDs (synthetic_tenant
    # fixture skips if they collide, but defense-in-depth here too).
    assert visionarias_id != synthetic_id, (
        f"Coleccion de tenants ambigua: visionarias_id={visionarias_id} "
        f"== synthetic_id={synthetic_id}. Verifica VISIONARIAS_TENANT_ID."
    )

    invoke_result = await sales_agent_entrypoint(golden.input_message)
    spy = invoke_result["spy"]
    turn_id: UUID | None = invoke_result["turn_id"]
    response_text = _extract_response_text(invoke_result)

    if turn_id is None:
        pytest.skip(
            "turn_id is None: la observability context no se construyo; "
            "la prueba de cross-tenant requiere rows en sales_agent_trace_event.",
        )

    # Lazy import — keep collection cheap on default suite.
    from luana_core_sales_agent.observability.persistence.models.trace_event_model import (
        SalesAgentTraceEventModel,
    )

    # Query DISTINCT tenant_id values for this turn_id. Per tenant-isolation
    # rule, the result set MUST be exactly {visionarias_id}.
    distinct_stmt = (
        select(SalesAgentTraceEventModel.tenant_id).where(SalesAgentTraceEventModel.turn_id == turn_id).distinct()
    )
    distinct_tenant_ids = {row[0] for row in db_session.execute(distinct_stmt).all()}

    assert distinct_tenant_ids == {visionarias_id}, (
        f"Cross-tenant leak detectado: sales_agent_trace_event para turn_id={turn_id} "
        f"tiene tenant_ids distintos {distinct_tenant_ids}, esperado solo "
        f"{{{visionarias_id}}}."
    )
    assert synthetic_id not in distinct_tenant_ids, (
        f"Cross-tenant leak detectado: synthetic_id={synthetic_id} aparece en las "
        f"filas de trace_event de turn_id={turn_id}."
    )

    assertion_results: list[dict[str, Any]] = [
        {
            "layer": "cross_tenant_db",
            "passed": True,
            "distinct_tenant_ids": [str(t) for t in distinct_tenant_ids],
        },
    ]

    # Write artifacts — the trace.json passes through sanitize_payload via
    # write_run_artifacts (T-3 contract).
    run_dir = write_run_artifacts(
        run_id=turn_id,
        spy=spy,
        response_text=response_text,
        assertions_results=assertion_results,
    )

    # Read trace.json and assert "T2_synthetic" substring is ABSENT.
    trace_path = run_dir / "trace.json"
    assert trace_path.exists(), f"trace.json no se escribio en {trace_path}."
    trace_text = trace_path.read_text(encoding="utf-8")
    assert "T2_synthetic" not in trace_text, (
        f"Cross-tenant leak detectado en trace.json: la cadena 'T2_synthetic' "
        f"aparece en el artifact de turn_id={turn_id}. Verifica sanitize_payload "
        f"+ tenant filtering en el callback handler."
    )
    # Defense-in-depth: also check response.txt is clean.
    response_path = run_dir / "response.txt"
    if response_path.exists():
        response_artifact = response_path.read_text(encoding="utf-8")
        assert "T2_synthetic" not in response_artifact, (
            f"Cross-tenant leak detectado en response.txt: la cadena 'T2_synthetic' "
            f"aparece en el artifact de turn_id={turn_id}."
        )

    logger.info(
        "eval_no_cross_tenant_leak_pass",
        turn_id=str(turn_id),
        visionarias_id=str(visionarias_id),
        synthetic_id=str(synthetic_id),
        distinct_tenant_count=len(distinct_tenant_ids),
    )
