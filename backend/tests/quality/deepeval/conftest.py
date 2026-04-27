"""Conftest for DeepEval-as-code suite (testing-2026-04 plan).

Centralizes:
- Judge model selection (NANO from copilot model catalog).
- Opt-in flag ``RUN_DEEPEVAL=1`` so corridas pesadas no disparan en CI default.
- Skip marker para escenarios que requieren OPENAI_API_KEY.

Per-TP test modules importan fixtures de aquí.
"""

from __future__ import annotations

import os

import pytest


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip todo el árbol DeepEval salvo que ``RUN_DEEPEVAL=1`` esté seteado.

    DeepEval evals consumen tokens reales (NANO judge). NO corre en CI default.
    Local: ``RUN_DEEPEVAL=1 .venv/bin/pytest tests/quality/deepeval/ -v``.
    """
    if os.getenv("RUN_DEEPEVAL") == "1":
        return
    skip_marker = pytest.mark.skip(reason="DeepEval suite opt-in (set RUN_DEEPEVAL=1)")
    for item in items:
        if "tests/quality/deepeval/" in str(item.fspath):
            item.add_marker(skip_marker)


@pytest.fixture(scope="session", autouse=True)
def _configure_deepeval_judge() -> None:
    """Pin DeepEval judge a NANO model (gpt-4o-mini equivalent del catálogo).

    Override via env: ``DEEPEVAL_JUDGE_MODEL=<model_id>``.
    """
    os.environ.setdefault("DEEPEVAL_JUDGE_MODEL", "gpt-4o-mini")


@pytest.fixture
def require_openai_key() -> None:
    """Skip si no hay OPENAI_API_KEY (judge necesita LLM real)."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY no presente — DeepEval judge requiere clave real")
