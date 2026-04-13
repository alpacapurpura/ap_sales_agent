"""Interview tool group for the Interview Engine."""

from src.modules.copilot.application.tools.interview.advance_block import advance_block
from src.modules.copilot.application.tools.interview.checkpoint import checkpoint
from src.modules.copilot.application.tools.interview.clarify import clarify
from src.modules.copilot.application.tools.interview.complete_interview import (
    complete_interview,
)
from src.modules.copilot.application.tools.interview.extract_structured import (
    extract_structured,
)
from src.modules.copilot.application.tools.interview.offer_alternatives import (
    offer_alternatives,
)
from src.modules.copilot.application.tools.interview.revert_to_block import (
    revert_to_block,
)
from src.modules.copilot.application.tools.interview.web_research import web_research

INTERVIEW_TOOLS = [
    extract_structured,
    offer_alternatives,
    clarify,
    checkpoint,
    advance_block,
    complete_interview,
    revert_to_block,
    web_research,
]
