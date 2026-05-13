"""Atomic switch invariants — Phase 2.

The switch wires the new observability module into the orchestrator hot
path and removes ``trace_recorder`` / ``node_trace`` / ``usage_tracking``.
These tests guard the resulting invariants:

1. The legacy modules don't exist.
2. The legacy symbols (``recorder.record``, ``UsageAccumulator``,
   ``_PRICING``) don't appear in ``backend/src/`` anymore.
3. The hot path (``chat.py``) imports from the new module
   (``ObservabilityContext``) and from ``copilot.domain.events`` /
   ``shared.domain.events.EventBus``.
4. ``extraction_card_flow.py`` publishes ``CardEmitted`` events instead
   of calling the recorder directly.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

BACKEND_SRC = Path(__file__).resolve().parents[4] / "src"
CHAT_PY = BACKEND_SRC / "modules/copilot/application/orchestrator/chat.py"
EXTRACTION_PY = BACKEND_SRC / "modules/copilot/application/extraction_card_flow.py"


# ── 1. Legacy modules deleted ────────────────────────────────────────


class TestLegacyModulesDeleted:
    def test_trace_recorder_module_gone(self) -> None:
        spec = importlib.util.find_spec(
            "luana_core_copilot.application.observability.trace_recorder",
        )
        assert spec is None, "trace_recorder.py must be deleted in atomic switch"

    def test_node_trace_module_gone(self) -> None:
        spec = importlib.util.find_spec(
            "luana_core_copilot.application.observability.node_trace",
        )
        assert spec is None, "node_trace.py must be deleted in atomic switch"

    def test_usage_tracking_module_gone(self) -> None:
        spec = importlib.util.find_spec(
            "luana_core_copilot.application.orchestrator.usage_tracking",
        )
        assert spec is None, "usage_tracking.py must be deleted in atomic switch"


# ── 2. Legacy symbols absent from backend/src/ ────────────────────────

LEGACY_PATTERN = re.compile(r"\brecorder\.record\b|\bUsageAccumulator\b|\b_PRICING\b")


def _walk_py_files(root: Path):
    for path in root.rglob("*.py"):
        if "__pycache__" in str(path):
            continue
        yield path


class TestLegacySymbolsAbsent:
    def test_no_recorder_record_or_usage_accumulator_or_pricing_constant(self) -> None:
        offenders: list[str] = []
        for py in _walk_py_files(BACKEND_SRC):
            text = py.read_text()
            if LEGACY_PATTERN.search(text):
                offenders.append(str(py.relative_to(BACKEND_SRC)))
        assert not offenders, "Legacy observability symbols still present in backend/src:\n" + "\n".join(
            sorted(offenders)
        )


# ── 3. chat.py imports the new module ────────────────────────────────


class TestChatHotPathImportsNewModule:
    def test_imports_observability_context(self) -> None:
        text = CHAT_PY.read_text()
        assert "ObservabilityContext" in text, "chat.py must import ObservabilityContext from copilot.observability"
        assert "from luana_core_copilot.observability" in text, "chat.py must use the new observability module"

    def test_imports_domain_events(self) -> None:
        text = CHAT_PY.read_text()
        for symbol in ("CardEmitted", "RoutingDecided"):
            assert symbol in text, f"chat.py must publish {symbol} events"

    def test_imports_event_bus(self) -> None:
        text = CHAT_PY.read_text()
        assert "EventBus" in text, "chat.py must import EventBus to publish events"

    def test_does_not_import_legacy_modules(self) -> None:
        text = CHAT_PY.read_text()
        legacy_imports = [
            "from src.modules.copilot.application.observability.trace_recorder",
            "from src.modules.copilot.application.observability.node_trace",
            "from src.modules.copilot.application.orchestrator.usage_tracking",
            "from src.modules.copilot.application.observability import trace_recorder",
        ]
        for imp in legacy_imports:
            assert imp not in text, f"chat.py still imports legacy: {imp}"

    def test_passes_callback_handler_via_runnable_config(self) -> None:
        text = CHAT_PY.read_text()
        assert "langchain_config" in text, "chat.py must pass obs.langchain_config() to graph.astream_events"


# ── 4. extraction_card_flow publishes CardEmitted ─────────────────────


class TestExtractionCardFlowPublishesEvent:
    def test_extraction_card_flow_publishes_card_emitted(self) -> None:
        text = EXTRACTION_PY.read_text()
        assert "CardEmitted" in text, (
            "extraction_card_flow.py must publish CardEmitted events instead of calling trace_recorder.record"
        )

    def test_extraction_card_flow_does_not_import_trace_recorder(self) -> None:
        text = EXTRACTION_PY.read_text()
        assert "trace_recorder" not in text, "extraction_card_flow.py must not import trace_recorder anymore"
