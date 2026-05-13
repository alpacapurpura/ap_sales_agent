"""Guided toolset must include the extraction group.

Regresión bug de traza ``376850f5-27aa-42e6-8e70-a03a2e6a9501``: el copilot en
guided mode NO podía llamar ``extract_from_url`` porque el toolset guided solo
incluía ``(guided, knowledge, shared_tools, document)``. El LLM cayó en un
loop de 8 ``extract_structured`` con los mismos args.

Fix: incluir ``extraction`` en el toolset guided para que ``extract_from_url``
y ``extract_from_doc`` estén disponibles cuando el user pasa una URL durante
un flujo guiado.
"""

from __future__ import annotations

from luana_core_copilot.application.tools.registry import get_tools_for_context


class TestGuidedModeIncludesExtractionTools:
    def test_guided_mode_exposes_extract_from_url(self) -> None:
        tools = get_tools_for_context({"guided_mode": True})
        names = {t.name for t in tools}
        assert "extract_from_url" in names, (
            "extract_from_url must be bindable in guided mode — "
            "otherwise the LLM loops on extract_structured when a URL arrives."
        )

    def test_guided_mode_exposes_extract_from_doc(self) -> None:
        tools = get_tools_for_context({"guided_mode": True})
        names = {t.name for t in tools}
        assert "extract_from_doc" in names, (
            "extract_from_doc must be bindable in guided mode — required when the user uploads a brief/doc mid-flow."
        )

    def test_guided_mode_keeps_narrow_core(self) -> None:
        """Adding extraction must not leak mutation/analytics/etc. — scope stays tight."""
        tools = get_tools_for_context({"guided_mode": True})
        names = {t.name for t in tools}

        from luana_core_copilot.application.tools.registry import TOOL_GROUPS

        for t in TOOL_GROUPS.get("mutation", []):
            assert t.name not in names, f"mutation tool leaked into guided mode: {t.name!r}"
        for t in TOOL_GROUPS.get("analytics", []):
            assert t.name not in names, f"analytics tool leaked into guided mode: {t.name!r}"

    def test_guided_mode_still_exposes_guided_tools(self) -> None:
        """Guard against accidentally dropping the guided group when adding extraction."""
        tools = get_tools_for_context({"guided_mode": True})
        names = {t.name for t in tools}
        from luana_core_copilot.application.tools.registry import TOOL_GROUPS

        for t in TOOL_GROUPS["guided"]:
            assert t.name in names, f"Missing guided tool: {t.name}"
