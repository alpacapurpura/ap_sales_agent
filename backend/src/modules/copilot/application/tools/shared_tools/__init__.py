"""Shared copilot tools — reusable primitives available across routes.

Unlike module-specific groups (offer_section, analytics, crm, ...), tools in
this group operate on conversational primitives or infrastructure-backed
generic queries: clarification, public-web search. They must not import
from feature modules.
"""

from src.modules.copilot.application.tools.shared_tools.clarify import clarify
from src.modules.copilot.application.tools.shared_tools.web_research import web_research

SHARED_TOOLS = [clarify, web_research]

__all__ = ["SHARED_TOOLS", "clarify", "web_research"]
