"""Root conftest of the agentic eval suite.

Owns the ``--run-evals`` flag + the ``@pytest.mark.eval`` marker registration
+ the auto-skip of eval-marked tests when the flag is absent. Lives at the
root of ``tests/agentic_evals/`` so EVERY agentic eval suite (sales_agent,
copilot if added later) inherits the same gating without duplicating
plumbing.

Decisión arquitectónica B (PI-12 S1 sales-agent-eval-runner-foundation):
default CI must NEVER burn LLM budget by accident. The suite stays gated
behind an explicit flag so ``cd backend && .venv/bin/pytest`` runs the
full default suite without invoking ``agent_app.ainvoke`` real once.

Per ``.claude/rules/sales-agent-brand-voice.md`` § Excepción + Decisión B6
the harness honors the production ``PersonalityProfile.system_instruction``
runtime — the marker / flag does NOT override voice, NOR should fixtures
seed test-only personality data.
"""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register the ``--run-evals`` CLI flag.

    The flag is a boolean off-by-default. When omitted (CI default,
    contributor's quick local push), every test marked ``@pytest.mark.eval``
    auto-skips with explicit reason — see :func:`pytest_collection_modifyitems`.
    """
    parser.addoption(
        "--run-evals",
        action="store_true",
        default=False,
        help=(
            "Run agentic evaluation suite (real LLM calls, ~$0.005/run). Off by default to keep CI default cost-zero."
        ),
    )


def pytest_configure(config: pytest.Config) -> None:
    """Register the ``eval`` marker so pytest does not warn ``PytestUnknownMarkWarning``.

    Defensive note: registering at the agentic_evals root is enough — pytest
    propagates registered markers to all sub-packages. The marker registration
    happens regardless of the flag value, which lets test discovery and AST
    walkers (linters, mypy) recognize the marker even on default runs.
    """
    config.addinivalue_line(
        "markers",
        "eval: agentic eval suite — requires --run-evals flag (real LLM cost).",
    )
    config.addinivalue_line(
        "markers",
        "no_eval: opt-out of auto-eval-marking; runs on default CI without --run-evals.",
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Auto-skip ``@pytest.mark.eval``-decorated tests when ``--run-evals`` is absent.

    Pytest contract: ``pytest_collection_modifyitems`` runs once after
    collection completes. We add a ``skip`` marker to every collected item
    whose keywords include ``eval`` when the gate flag is not set.

    The skip reason string ``"eval markers require --run-evals flag"`` is
    asserted verbatim in the smoke scenario 2 grader (spec § Scenario 2 then-
    clause), so DO NOT change the wording without updating that test.
    """
    if config.getoption("--run-evals"):
        return
    skip_marker = pytest.mark.skip(reason="eval markers require --run-evals flag")
    for item in items:
        if "eval" in item.keywords:
            item.add_marker(skip_marker)
