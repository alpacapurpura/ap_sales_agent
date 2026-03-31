"""Tests for OutputManager._parse_response.

Validates that internal blocks are stripped, JSON arrays are parsed,
paragraph chunking works, and edge cases are handled.
"""

from src.modules.sales_agent.infrastructure.external.output_manager import OutputManager


class TestParseResponseBlockStripping:
    """Internal blocks must never reach the user."""

    def test_strip_qualification_data_block(self):
        raw = (
            "Hola, ¿cómo estás? "
            '[QUALIFICATION_DATA: {"budget": "5000", "timeline": "Q3"}]'
        )
        chunks = OutputManager._parse_response(raw)
        joined = " ".join(chunks)
        assert "QUALIFICATION_DATA" not in joined
        assert "Hola" in joined

    def test_strip_signals_block(self):
        raw = (
            "Me alegra que te interese. "
            '[SIGNALS: {"intent": "high", "urgency": true}]'
        )
        chunks = OutputManager._parse_response(raw)
        joined = " ".join(chunks)
        assert "SIGNALS" not in joined
        assert "Me alegra" in joined

    def test_strip_tool_request_block(self):
        raw = (
            "Déjame revisar tu agenda. "
            '[TOOL_REQUEST: {"tool": "check_calendar", "args": {"date": "2026-04-01"}}]'
        )
        chunks = OutputManager._parse_response(raw)
        joined = " ".join(chunks)
        assert "TOOL_REQUEST" not in joined
        assert "agenda" in joined

    def test_strip_multiple_blocks(self):
        raw = (
            "Perfecto, ya tengo tu info.\n\n"
            '[QUALIFICATION_DATA: {"name": "Ana"}]\n'
            '[SIGNALS: {"score": 80}]\n'
            '[TOOL_REQUEST: {"tool": "send_link"}]\n'
            "Te envío el enlace ahora."
        )
        chunks = OutputManager._parse_response(raw)
        joined = " ".join(chunks)
        assert "QUALIFICATION_DATA" not in joined
        assert "SIGNALS" not in joined
        assert "TOOL_REQUEST" not in joined
        assert "Perfecto" in joined
        assert "enlace" in joined

    def test_empty_after_strip(self):
        """If the message is only internal blocks, return empty list."""
        raw = '[QUALIFICATION_DATA: {"budget": "5000"}][SIGNALS: {"intent": "high"}]'
        chunks = OutputManager._parse_response(raw)
        assert chunks == []


class TestParseResponseChunking:
    """Paragraph splitting and JSON array parsing."""

    def test_paragraph_chunking(self):
        raw = "Primer párrafo con info.\n\nSegundo párrafo con más detalle.\n\nTercer punto."
        chunks = OutputManager._parse_response(raw)
        assert len(chunks) == 3
        assert chunks[0] == "Primer párrafo con info."
        assert chunks[1] == "Segundo párrafo con más detalle."
        assert chunks[2] == "Tercer punto."

    def test_json_array_parsing(self):
        raw = '["Hola, ¿cómo estás?", "Te cuento sobre nuestro programa."]'
        chunks = OutputManager._parse_response(raw)
        assert len(chunks) == 2
        assert chunks[0] == "Hola, ¿cómo estás?"
        assert chunks[1] == "Te cuento sobre nuestro programa."

    def test_single_chunk_fallback(self):
        raw = "Un solo mensaje sin separadores."
        chunks = OutputManager._parse_response(raw)
        assert len(chunks) == 1
        assert chunks[0] == "Un solo mensaje sin separadores."


class TestParseResponseMarkdown:
    """Markdown code block removal."""

    def test_markdown_code_block_removal(self):
        raw = '```json\n["Mensaje uno", "Mensaje dos"]\n```'
        chunks = OutputManager._parse_response(raw)
        assert len(chunks) == 2
        assert chunks[0] == "Mensaje uno"
        assert chunks[1] == "Mensaje dos"

    def test_markdown_code_block_plain_text(self):
        raw = "```\nTexto dentro de code block\n```"
        chunks = OutputManager._parse_response(raw)
        assert len(chunks) == 1
        assert "Texto dentro de code block" in chunks[0]
        assert "```" not in chunks[0]
