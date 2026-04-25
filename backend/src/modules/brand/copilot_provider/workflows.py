"""Brand workflows — placeholder until F6.

F6 introduces the unified ``Workflow`` declarative model that subsumes
``guided`` + ``procedure`` + ``extraction_card_flow``. Brand-specific flows
(``setup_brand_from_url``, ``audit_brand_voice``) ship there. F1 keeps the
contract surface only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from src.modules.copilot.domain.ports import Workflow


class BrandWorkflowProvider:
    """Returns the brand workflows registered for the copilot (F6 will populate)."""

    def workflows(self) -> Sequence[Workflow]:
        return ()
