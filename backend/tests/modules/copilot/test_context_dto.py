"""Tests for ``ClientContextDTO``.

Focus mode was retired on 2026-04-21; only interview mode + base context
fields remain. See CONTRACT §5 and ``.claude/rules/copilot-resilience.md``.
"""

from uuid import uuid4

from src.modules.copilot.api.dto import ClientContextDTO


class TestClientContextDTO:
    def test_client_context_defaults(self) -> None:
        dto = ClientContextDTO(current_route="/brand-studio")
        assert dto.current_route == "/brand-studio"
        assert dto.interview_session_id is None
        assert dto.selected_fields == []
        assert dto.form_data == {}
        assert dto.locale == "es"

    def test_client_context_with_interview_session_id(self) -> None:
        sid = str(uuid4())
        dto = ClientContextDTO(
            current_route="/brand-studio/interview",
            interview_session_id=sid,
        )
        assert dto.interview_session_id == sid

    def test_client_context_with_selected_fields(self) -> None:
        fields = [{"field_id": "uvp", "field_label": "Propuesta", "field_value": "hola"}]
        dto = ClientContextDTO(
            current_route="/brand-studio",
            selected_fields=fields,
        )
        assert dto.selected_fields == fields

    def test_client_context_with_form_data(self) -> None:
        form = {"uvp": "original"}
        dto = ClientContextDTO(current_route="/brand-studio", form_data=form)
        assert dto.form_data == form

    def test_client_context_with_custom_locale(self) -> None:
        dto = ClientContextDTO(current_route="/brand-studio", locale="pt")
        assert dto.locale == "pt"
