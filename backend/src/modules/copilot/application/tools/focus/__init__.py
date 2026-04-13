"""Focus tool group for Focus Mode entity editing."""

from src.modules.copilot.application.tools.focus.entity_read import entity_read
from src.modules.copilot.application.tools.focus.entity_undo_all import entity_undo_all
from src.modules.copilot.application.tools.focus.entity_write import entity_write

FOCUS_TOOLS = [entity_write, entity_read, entity_undo_all]
