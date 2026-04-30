"""TDD — offer_section_tools refactor preserves external contract.

Verifies that after the Q1 EXPANSION refactor (static suggestions[] removed,
engine.get_suggestions called), the public tool signatures and response JSON
shapes are unchanged.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4


def _make_session():
    """Return a fake session that satisfies the tools' pattern."""
    session = MagicMock()
    session.execute = MagicMock(
        return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None))))
    )
    return session


class TestOfferSectionToolsContractPreserved:
    def test_validate_preset_coherence_still_returns_json_with_suggestions(self) -> None:
        """validate_preset_coherence must return JSON with 'suggestions' key."""
        import json

        from src.modules.copilot.application.tools.offer_section_tools import (
            validate_preset_coherence,
        )

        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=uuid4()),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools.SessionLocal", return_value=_make_session()
            ),
            patch("src.modules.copilot.application.tools.offer_section_tools._offer_preset_flags", return_value=[]),
        ):
            result = validate_preset_coherence.invoke({"current_promise": "Mi promesa clara", "offer_id": ""})

        data = json.loads(result)
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)

    def test_high_ticket_tiering_template_still_returns_json_with_draft_fields(self) -> None:
        """high_ticket_tiering_template must return JSON with 'draft_fields' key."""
        import json

        from src.modules.copilot.application.tools.offer_section_tools import (
            high_ticket_tiering_template,
        )

        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=uuid4()),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools.SessionLocal", return_value=_make_session()
            ),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._offer_preset_flags",
                return_value=["high_ticket"],
            ),
        ):
            result = high_ticket_tiering_template.invoke({"offer_id": ""})

        data = json.loads(result)
        assert "draft_fields" in data
        assert "suggestions" in data

    def test_recurring_billing_setup_still_returns_json_with_draft_fields(self) -> None:
        """recurring_billing_setup must return JSON with 'draft_fields' key."""
        import json

        from src.modules.copilot.application.tools.offer_section_tools import (
            recurring_billing_setup,
        )

        with (
            patch("src.modules.copilot.application.tools.offer_section_tools.get_tenant_id", return_value=uuid4()),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools.SessionLocal", return_value=_make_session()
            ),
            patch(
                "src.modules.copilot.application.tools.offer_section_tools._offer_preset_flags",
                return_value=["recurring_billing"],
            ),
        ):
            result = recurring_billing_setup.invoke({"offer_id": ""})

        data = json.loads(result)
        assert "draft_fields" in data
        assert "suggestions" in data

    def test_offer_section_tools_exported_list_unchanged(self) -> None:
        """OFFER_SECTION_TOOLS list must still export all 18 tools."""
        from src.modules.copilot.application.tools.offer_section_tools import (
            OFFER_SECTION_TOOLS,
        )

        assert len(OFFER_SECTION_TOOLS) == 18
