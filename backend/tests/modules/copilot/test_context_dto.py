"""Tests for ``ClientContextDTO``.

Focus mode was retired on 2026-04-21; the standalone interview engine was
retired on 2026-04-22. Only base context fields remain: the guided-setup
flag is derived server-side and never sent by the frontend.
"""

from src.modules.copilot.api.dto import ClientContextDTO


class TestClientContextDTO:
    def test_client_context_defaults(self) -> None:
        dto = ClientContextDTO(current_route="/brand-studio")
        assert dto.current_route == "/brand-studio"
        assert dto.selected_fields == []
        assert dto.form_data == {}
        assert dto.locale == "es"

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

    def test_client_context_no_longer_accepts_interview_session_id(self) -> None:
        """Arch guard: the legacy interview_session_id field must stay removed."""
        assert "interview_session_id" not in ClientContextDTO.model_fields
