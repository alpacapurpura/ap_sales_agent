"""Interview tool group for the Interview Engine."""

from src.modules.copilot.application.tools.interview.extract_structured import (
    extract_structured,
)
from src.modules.copilot.application.tools.interview.offer_alternatives import (
    offer_alternatives,
)

INTERVIEW_TOOLS = [
    extract_structured,
    offer_alternatives,
]
