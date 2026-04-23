"""Guided setup tools — replaces the standalone interview engine.

The flow is dynamic: blocks come from the editable-field catalog
(``src.shared.links.ports.editable_fields``), state lives inside
``copilot_conversations.procedure_state["guided"]`` — no separate
session table.

Tool surface:

* ``start_guided_setup``  — activates guided mode for a domain/entity.
* ``advance_guided_block`` — marks a block complete and moves forward.
* ``end_guided_setup``    — clears guided state (user abandons or finishes).
* ``extract_structured``  — silent field extractor (unchanged semantics from
                            the old interview tool, minus ``session_id``).
* ``extract_document_to_fields`` — bulk extraction of an uploaded asset
                            into the current domain's fields.
"""

from src.modules.copilot.application.tools.guided.advance import advance_guided_block
from src.modules.copilot.application.tools.guided.end import end_guided_setup
from src.modules.copilot.application.tools.guided.extract import (
    extract_document_to_fields,
    extract_structured,
)
from src.modules.copilot.application.tools.guided.start import start_guided_setup

GUIDED_TOOLS = [
    start_guided_setup,
    advance_guided_block,
    end_guided_setup,
    extract_structured,
    extract_document_to_fields,
]

__all__ = ["GUIDED_TOOLS"]
