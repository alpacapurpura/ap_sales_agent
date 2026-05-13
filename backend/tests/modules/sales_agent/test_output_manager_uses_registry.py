"""S5 — OutputManager consumes channel registry, not hardcoded if-else.

§3 protected: ``OutputManager.process_response`` typing simulation + chunking
behavior intacto. S5 sólo wirea `_parse_response` para cap de chunk via
``ChannelFormat.chunk_size`` cuando el registry lo declara.

# [SALES-AGENT-CHANNEL-REGISTRY-S5]
"""

from __future__ import annotations

import ast
import inspect
import re
from pathlib import Path

import pytest

from luana_core_sales_agent.infrastructure.external import output_manager as om_module
from luana_core_sales_agent.infrastructure.external.output_manager import OutputManager
from luana_core_channels.format import (
    ChannelFormat,
    register_channel,
    reset_registry_for_tests,
)


@pytest.fixture(autouse=True)
def _reset_registry():
    reset_registry_for_tests()
    yield
    reset_registry_for_tests()


class TestOutputManagerConsumesRegistry:
    def test_parse_response_invokes_get_channel_format(self) -> None:
        """The implementation must call ``get_channel_format`` (or equivalent)
        instead of branching on string literals."""
        src = inspect.getsource(om_module)
        assert "get_channel_format" in src, (
            "OutputManager must consume the channel registry — expected "
            "import/use of `get_channel_format` from "
            "`src.shared.agent_observability.channels.format`."
        )

    def test_parse_response_chunks_long_content_under_chunk_size(self) -> None:
        """When the channel format declares ``chunk_size=N``, paragraphs longer
        than N are split further so each chunk respects the cap."""
        # Force a tiny chunk size for this test by overriding the registry.
        # whatsapp default already has a chunk_size; the test uses a custom
        # value to be explicit.
        long_paragraph = "palabra " * 100  # ~800 chars
        chunks = OutputManager._parse_response(long_paragraph, channel_type="whatsapp")
        # Resolve the cap via the registry to avoid duplicating the value.
        from luana_core_channels.format import get_channel_format

        cap = get_channel_format("whatsapp").chunk_size
        assert cap is not None and cap > 0, "whatsapp baseline must declare chunk_size"
        for chunk in chunks:
            assert len(chunk) <= cap, f"chunk {len(chunk)} chars exceeds {cap} cap"

    def test_parse_response_no_chunk_size_keeps_legacy_behavior(self) -> None:
        """Channels without ``chunk_size`` declared keep the legacy paragraph
        behavior — no length cap enforced. ``chat`` baseline does not declare
        chunk_size so any length passes through unchanged."""
        # Two short paragraphs split as before, no further chunking.
        raw = "Primer párrafo.\n\nSegundo párrafo."
        chunks = OutputManager._parse_response(raw, channel_type="chat")
        assert len(chunks) == 2

    def test_parse_response_unknown_channel_falls_back_safely(self) -> None:
        """Unknown channel resolves to ``chat`` fallback — no exception, no
        chunking enforced."""
        raw = "lorem " * 200
        chunks = OutputManager._parse_response(raw, channel_type="nonexistent")
        # No crash; at least one chunk emitted.
        assert chunks
        # No cap enforcement for chat (chunk_size None) — chunk preserved as one paragraph.
        assert len(chunks) == 1

    def test_parse_response_preserves_block_stripping(self) -> None:
        """§3 protected behavior — internal blocks still stripped regardless
        of registry wiring."""
        raw = 'Hola. [QUALIFICATION_DATA: {"name": "Ana"}] ¿Cómo estás?'
        chunks = OutputManager._parse_response(raw, channel_type="telegram")
        joined = " ".join(chunks)
        assert "QUALIFICATION_DATA" not in joined
        assert "Hola" in joined

    def test_chunk_size_split_respects_word_boundaries_when_possible(self) -> None:
        """Splitting a long paragraph should not chop mid-word when avoidable.
        Soft constraint — the implementation may emit a hard cut for words
        longer than chunk_size, but normal text should split at whitespace."""
        text = (
            "Estamos en un programa de ocho semanas que te lleva al resultado "
            "principal con mentoría grupal y módulos prácticos. " * 20
        )
        chunks = OutputManager._parse_response(text, channel_type="whatsapp")
        from luana_core_channels.format import get_channel_format

        cap = get_channel_format("whatsapp").chunk_size or 0
        # Each chunk fits under cap.
        assert all(len(c) <= cap for c in chunks)
        # Most chunks end with whitespace boundary or sentence punctuation.
        well_terminated = sum(1 for c in chunks if c.rstrip()[-1] in ".!?…\n " or c == chunks[-1])
        assert well_terminated >= len(chunks) - 1


class TestOutputManagerArchInvariant:
    """Static AST scan — no string-literal channel comparison in OutputManager.

    Mirror of S4 ``test_no_hardcoded_models_sales_agent`` ratchet pattern.
    """

    FORBIDDEN_CHANNEL_LITERALS = frozenset(
        {"whatsapp", "telegram", "instagram_dm", "instagram", "sms", "voice", "email", "chat"},
    )

    def test_no_if_compare_channel_string_literal(self) -> None:
        """No ``if channel == "whatsapp": ...`` style branches.

        The function signature default ``channel_type: str = "telegram"`` is
        allowed (a default parameter, not a comparison). What we forbid is
        comparison-against-literal as routing logic.
        """
        src_path = Path(om_module.__file__)
        tree = ast.parse(src_path.read_text(encoding="utf-8"))

        offenders: list[str] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            comparators = [node.left, *node.comparators]
            literals = [c.value for c in comparators if isinstance(c, ast.Constant) and isinstance(c.value, str)]
            for literal in literals:
                if literal.lower() in self.FORBIDDEN_CHANNEL_LITERALS:
                    offenders.append(
                        f"{src_path.name}:{node.lineno} — comparison against {literal!r}",
                    )

        assert not offenders, (
            "OutputManager must route channel logic through "
            "`shared.agent_observability.channels.format.get_channel_format`. "
            "Found hardcoded channel comparisons:\n  - " + "\n  - ".join(offenders)
        )

    def test_imports_get_channel_format(self) -> None:
        """Encourage explicit import for greppability."""
        src = Path(om_module.__file__).read_text(encoding="utf-8")
        # Either direct import from format module or via channels package.
        import_re = re.compile(
            r"from\s+src\.shared\.agent_observability\.channels(\.format)?\s+import\s+[^\n]*get_channel_format",
        )
        assert import_re.search(src), (
            "Expected `from src.shared.agent_observability.channels(.format) "
            "import get_channel_format` in output_manager.py."
        )
