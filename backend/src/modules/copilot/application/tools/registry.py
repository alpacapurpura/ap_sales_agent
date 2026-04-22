"""Tool Registry — route-based tool selection for the copilot.

Maps frontend routes to the subset of tools the LLM should have access to.
This keeps the tool set focused and reduces noise for the LLM.
"""

from src.modules.copilot.application.tools.analytics_tools import ANALYTICS_TOOLS
from src.modules.copilot.application.tools.assets_tools import ASSETS_TOOLS  # [COPILOT-OUTBOUND-ASSETS]
from src.modules.copilot.application.tools.awareness import AWARENESS_TOOLS
from src.modules.copilot.application.tools.connections_tools import CONNECTIONS_TOOLS
from src.modules.copilot.application.tools.crm_tools import CRM_TOOLS
from src.modules.copilot.application.tools.document_tools import DOCUMENT_TOOLS  # [COPILOT-READ-DOCUMENT]
from src.modules.copilot.application.tools.interview import INTERVIEW_TOOLS
from src.modules.copilot.application.tools.knowledge_tools import KNOWLEDGE_TOOLS
from src.modules.copilot.application.tools.landing_tools import LANDING_TOOLS
from src.modules.copilot.application.tools.module_tools import MODULE_TOOLS
from src.modules.copilot.application.tools.mutations import MUTATION_TOOLS
from src.modules.copilot.application.tools.navigation import NAVIGATION_TOOLS
from src.modules.copilot.application.tools.offer_ladder_tools import OFFER_LADDER_TOOLS
from src.modules.copilot.application.tools.offer_section_tools import OFFER_SECTION_TOOLS
from src.modules.copilot.application.tools.procedure_tools import PROCEDURE_TOOLS
from src.modules.copilot.application.tools.sales_agent_tools import SALES_AGENT_TOOLS

# Named tool groups for route mapping
TOOL_GROUPS: dict[str, list] = {
    "navigation": NAVIGATION_TOOLS,
    "awareness": AWARENESS_TOOLS,
    "mutation": MUTATION_TOOLS,
    "module_data": MODULE_TOOLS,
    "analytics": ANALYTICS_TOOLS,
    "crm": CRM_TOOLS,
    "sales_agent": SALES_AGENT_TOOLS,
    "connections": CONNECTIONS_TOOLS,
    "landing": LANDING_TOOLS,
    "procedure": PROCEDURE_TOOLS,
    "knowledge": KNOWLEDGE_TOOLS,
    "offer_ladder": OFFER_LADDER_TOOLS,
    "offer_section": OFFER_SECTION_TOOLS,
    "interview": INTERVIEW_TOOLS,
    # Outbound asset tools — allow assistant to reference existing tenant assets.
    "assets": ASSETS_TOOLS,
    # Document reading — lazy access to text extracted from uploaded docs/audios.
    # Globally available: if the user attached a file in any route, the LLM can
    # fetch its content on demand.
    "document": DOCUMENT_TOOLS,
}

# Route prefix -> which tool groups are available.
# More specific routes should be listed before generic ones.
# "*" is the fallback for any unmatched route.
ROUTE_TOOL_MAP: dict[str, list[str]] = {
    "brand-studio/interview/buyer-persona": ["interview", "knowledge"],
    "brand-studio/interview": ["interview", "knowledge"],
    "brand-studio": [
        "navigation",
        "awareness",
        "mutation",
        "module_data",
        "procedure",
        "knowledge",
        "assets",  # brand studio can reference assets (logos, photos, etc.)
    ],
    "offer-studio/interview": ["interview", "knowledge"],
    "offer-studio": [
        "navigation",
        "awareness",
        "mutation",
        "module_data",
        "procedure",
        "knowledge",
        "offer_ladder",
        "offer_section",
        "assets",  # offer studio can reference flyers, images, etc.
    ],
    "growth-studio": [
        "navigation",
        "awareness",
        "module_data",
        "analytics",
        "crm",
        "procedure",
        "knowledge",
    ],
    "sales/studio": [
        "navigation",
        "awareness",
        "module_data",
        "sales_agent",
        "crm",
        "procedure",
        "knowledge",
    ],
    "sales": [
        "navigation",
        "awareness",
        "module_data",
        "sales_agent",
        "crm",
        "procedure",
        "knowledge",
    ],
    "connections": [
        "navigation",
        "awareness",
        "module_data",
        "connections",
        "procedure",
        "knowledge",
    ],
    "landing": [
        "navigation",
        "awareness",
        "module_data",
        "landing",
        "procedure",
        "knowledge",
        "assets",  # landing studio can reference uploaded images/docs.
    ],
    "assets": [
        "navigation",
        "awareness",
        "module_data",
        "procedure",
        "knowledge",
        "assets",  # assets studio: full access to asset tools.
    ],
    "settings": ["navigation", "awareness", "module_data", "procedure", "knowledge"],
    "*": [
        "navigation",
        "awareness",
        "mutation",
        "module_data",
        "procedure",
        "knowledge",
        "assets",  # globally available — assistant can reference assets anywhere.
    ],
}


# Tool groups that must be available in every route regardless of the
# ROUTE_TOOL_MAP entry. Uploads (document/audio) can happen from any screen,
# so read_document must always be bindable.
ALWAYS_AVAILABLE_GROUPS: tuple[str, ...] = ("document",)


def get_tools_for_route(route: str | None) -> list:
    """Return the flat list of tool functions for a given route.

    Args:
        route: The current frontend route (e.g. "/tenant-id/brand-settings").

    Returns:
        List of LangChain tool functions.

    """
    matched_groups = list(_match_route(route))
    for always in ALWAYS_AVAILABLE_GROUPS:
        if always not in matched_groups:
            matched_groups.append(always)
    tools = []
    seen = set()
    for group_name in matched_groups:
        group_tools = TOOL_GROUPS.get(group_name, [])
        for t in group_tools:
            if t.name not in seen:
                tools.append(t)
                seen.add(t.name)
    return tools


def get_tool_names_for_route(route: str | None) -> list[str]:
    """Return tool names for a route (useful for state/logging)."""
    return [t.name for t in get_tools_for_route(route)]


def get_all_tools() -> list:
    """Return all available tools (used for schema binding fallback)."""
    tools = []
    seen = set()
    for group_tools in TOOL_GROUPS.values():
        for t in group_tools:
            if t.name not in seen:
                tools.append(t)
                seen.add(t.name)
    return tools


def _collect_groups(group_names: tuple[str, ...]) -> list:
    """Collect tools from the given group names, deduplicating by name."""
    tools = []
    seen: set[str] = set()
    for group_name in group_names:
        for t in TOOL_GROUPS.get(group_name, []):
            if t.name not in seen:
                tools.append(t)
                seen.add(t.name)
    return tools


def get_tools_for_context(context: dict | None) -> list:
    """Return tools based on mode (interview > chat).

    Mode is determined by context fields:
    - ``interview_session_id`` present → Interview mode (interview + knowledge).
    - Otherwise → Chat mode (route-based selection).

    Focus mode was retired on 2026-04-21: per-entity scoped edits now rely on
    ``selected_fields`` + the per-conversation mutation journal. See
    CONTRACT §5 and ``.claude/rules/copilot-resilience.md``.
    """
    if not context:
        return get_tools_for_route(None)

    # Interview mode: interview + knowledge tools only
    if context.get("interview_session_id"):
        return _collect_groups(("interview", "knowledge"))

    # Chat mode: route-based selection
    return get_tools_for_route(context.get("current_route"))


def _match_route(route: str | None) -> list[str]:
    """Find which tool groups match the current route."""
    if not route:
        return ROUTE_TOOL_MAP["*"]

    route_lower = route.lower()
    for prefix, groups in ROUTE_TOOL_MAP.items():
        if prefix != "*" and prefix in route_lower:
            return groups

    return ROUTE_TOOL_MAP["*"]
