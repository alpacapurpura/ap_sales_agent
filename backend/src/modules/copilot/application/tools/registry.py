"""Tool Registry — route-based tool selection for the copilot.

Maps frontend routes to the subset of tools the LLM should have access to.
This keeps the tool set focused and reduces noise for the LLM.

Integrity invariant: a tool *name* may be exported from multiple groups only
if the underlying tool object is the same. Two different objects sharing a
name raise ``ToolNameCollisionError`` at registration time so divergent
behavior can't be shadowed silently.

PI-5 PR-1: ``ToolGroupMeta.available_channels`` SSoT — D-PI5-023..025.
Web-only groups: ``navigation``, ``guided``, ``landing``,
``offer_section``. Telegram filters via ``channel`` param in
``get_tools_for_context()``.
"""

from dataclasses import dataclass, field
from typing import Final

from src.modules.copilot.application.tools.analytics_tools import ANALYTICS_TOOLS
from src.modules.copilot.application.tools.ask_tenant_data import ask_tenant_data
from src.modules.copilot.application.tools.assets_tools import ASSETS_TOOLS  # [COPILOT-OUTBOUND-ASSETS]
from src.modules.copilot.application.tools.awareness import AWARENESS_TOOLS
from src.modules.copilot.application.tools.connections_tools import CONNECTIONS_TOOLS
from src.modules.copilot.application.tools.crm_tools import CRM_TOOLS
from src.modules.copilot.application.tools.document_tools import DOCUMENT_TOOLS  # [COPILOT-READ-DOCUMENT]
from src.modules.copilot.application.tools.extraction_tools import EXTRACTION_TOOLS
from src.modules.copilot.application.tools.fetch_url import fetch_url
from src.modules.copilot.application.tools.guided import GUIDED_TOOLS
from src.modules.copilot.application.tools.knowledge_tools import KNOWLEDGE_TOOLS
from src.modules.copilot.application.tools.landing_tools import LANDING_TOOLS
from src.modules.copilot.application.tools.module_tools import MODULE_TOOLS
from src.modules.copilot.application.tools.mutations import MUTATION_TOOLS
from src.modules.copilot.application.tools.navigation import NAVIGATION_TOOLS
from src.modules.copilot.application.tools.offer_ladder_tools import OFFER_LADDER_TOOLS
from src.modules.copilot.application.tools.offer_section_tools import OFFER_SECTION_TOOLS
from src.modules.copilot.application.tools.pin_to_memory import pin_to_memory
from src.modules.copilot.application.tools.procedure_tools import PROCEDURE_TOOLS
from src.modules.copilot.application.tools.sales_agent_tools import SALES_AGENT_TOOLS
from src.modules.copilot.application.tools.shared_tools import SHARED_TOOLS
from src.shared.agent_observability.channels.format_for_channel import format_for_channel


class ToolNameCollisionError(RuntimeError):
    """Raised when two different tool objects share the same `name`.

    Re-exporting the same tool object under multiple groups is allowed and
    useful (e.g. ``clarify`` lives in ``shared_tools`` and is re-exported via
    a shim inside ``interview``). Two *different* objects with the same name
    are always a bug — the first would be bound, the second silently dropped.
    """


def _register_tool_groups(groups: dict[str, list]) -> dict[str, list]:
    """Validate that tool names do not collide across groups.

    Returns the same dict unchanged on success. Raises ``ToolNameCollisionError``
    on first collision with a descriptive message. Exposed (underscore-prefixed)
    for tests; production code reads ``TOOL_GROUPS`` directly.
    """
    seen: dict[str, tuple[str, int]] = {}
    for group_name, tools in groups.items():
        for t in tools:
            prior = seen.get(t.name)
            if prior is None:
                seen[t.name] = (group_name, id(t))
            elif prior[1] != id(t):
                msg = (
                    f"Tool name collision: {t.name!r} exported by "
                    f"{prior[0]!r} (id={prior[1]}) and {group_name!r} "
                    f"(id={id(t)}). Re-export the same object or rename one."
                )
                raise ToolNameCollisionError(msg)
    return groups


# Transversal tool groups owned by the copilot itself (navigation, awareness,
# mutation, knowledge, document, shared_tools, guided, extraction, procedure).
# Module-specific groups (offer_section, offer_ladder, analytics, crm, …) live
# here today and migrate to their owning module's CopilotProvider in later
# fases. The merge with provider-emitted groups happens in
# ``_build_tool_groups`` below so adding a domain-specific group from a
# provider is a no-op at the registry level.
_BASE_TOOL_GROUPS: dict[str, list] = {
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
    # Guided setup (replaces the retired interview engine, 2026-04-22).
    "guided": GUIDED_TOOLS,
    # Outbound asset tools — allow assistant to reference existing tenant assets.
    "assets": ASSETS_TOOLS,
    # Document reading — lazy access to text extracted from uploaded docs/audios.
    "document": DOCUMENT_TOOLS,
    # Conversational primitives: clarify, (future) confirm, (future) progress.
    "shared_tools": SHARED_TOOLS,
    # URL-to-studio extraction.
    "extraction": EXTRACTION_TOOLS,
    # URL contextual scratchpad — fetch_url + pin_to_memory (F4).
    "url_context": [fetch_url, pin_to_memory],
    # Q&A about the tenant's own data — ask_tenant_data subgraph (F5).
    "data_query": [ask_tenant_data],
    # Channel-aware output adaptation — format_for_channel (F7).
    "channel_format": [format_for_channel],
}


def _build_tool_groups() -> dict[str, list]:
    """Return the merged tool-group registry.

    Starts from the transversal ``_BASE_TOOL_GROUPS`` and folds in any tool
    groups exposed by discovered ``CopilotProvider`` plugins. Behaviour rules:

    * If a provider declares an existing group name, its tools are appended
      (deduplicated by ``tool.name``) — providers extend, never overwrite.
    * If a provider declares a new group name, it is inserted as-is.
    * The final dict is validated through ``_register_tool_groups`` so cross-
      module name collisions still raise ``ToolNameCollisionError``.
    """
    # Local import keeps tools/registry import-time light — discovery only
    # runs once per process and tolerates being called repeatedly (lru_cache).
    from src.modules.copilot.application.discovery import discover_providers

    merged: dict[str, list] = {name: list(tools) for name, tools in _BASE_TOOL_GROUPS.items()}

    for provider in discover_providers().values():
        tp = provider.tool_provider()
        if tp is None:
            continue
        for group_name, group_tools in tp.tool_groups().items():
            if not group_tools:
                continue
            bucket = merged.setdefault(group_name, [])
            seen_names = {existing.name for existing in bucket}
            for tool in group_tools:
                if tool.name not in seen_names:
                    bucket.append(tool)
                    seen_names.add(tool.name)

    return _register_tool_groups(merged)


# Named tool groups for route mapping (transversal + provider-contributed).
TOOL_GROUPS: dict[str, list] = _build_tool_groups()

# Base route → group mapping owned by copilot itself. Provider-contributed
# routes are merged on top via ``_build_route_tool_map`` so a new module can
# expose its tool groups per-route without editing this file (F1 promise —
# closed in TP10 after the pattern was verified end-to-end with a dummy
# provider declaring ``ProviderRoute(prefix="*", groups=("tp10_dummy",))``).
# More specific routes should be listed before generic ones.
# "*" is the fallback for any unmatched route.
_BASE_ROUTE_TOOL_MAP: dict[str, list[str]] = {
    "brand-studio": [
        "navigation",
        "awareness",
        "mutation",
        "module_data",
        "procedure",
        "knowledge",
        "assets",  # brand studio can reference assets (logos, photos, etc.)
        "extraction",  # "extrae de esta URL hacia brand studio"
        "guided",  # "guíame para completar mi marca"
    ],
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
        "extraction",  # "extrae de esta URL hacia mi oferta"
        "guided",  # "guíame para completar esta oferta"
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


def _build_route_tool_map() -> dict[str, list[str]]:
    """Return the merged route → group map (base + provider routes).

    Iterates discovered providers and folds each ``ProviderRoute`` entry into
    the base map. Group names already present at a given prefix are kept (no
    duplicates). Unknown prefixes introduced by providers create a new entry
    starting from an empty list — providers are responsible for declaring all
    transversal groups they need (e.g. add ``"navigation"`` if they want it).

    Closes the F1 plug-in promise: once a module exports a ``CopilotProvider``
    declaring ``routes()``, its tool groups land in the runtime route map at
    boot without any edit to this file (validated by TP10 with a dummy module
    plugged in via ``src.modules.tp10_dummy``).
    """
    # Local import keeps the module-level import graph thin — discovery is
    # cached and tolerates being called repeatedly.
    from src.modules.copilot.application.discovery import discover_providers

    merged: dict[str, list[str]] = {prefix: list(groups) for prefix, groups in _BASE_ROUTE_TOOL_MAP.items()}

    for provider in discover_providers().values():
        for route in provider.routes():
            bucket = merged.setdefault(route.prefix, [])
            for group_name in route.groups:
                if group_name not in bucket:
                    bucket.append(group_name)

    return merged


ROUTE_TOOL_MAP: dict[str, list[str]] = _build_route_tool_map()


# Tool groups that must be available in every route regardless of the
# ROUTE_TOOL_MAP entry. Uploads (document/audio) can happen from any screen,
# so read_document must always be bindable. shared_tools hosts
# conversational primitives like `clarify` that any route may need.
ALWAYS_AVAILABLE_GROUPS: tuple[str, ...] = (
    "document",
    "shared_tools",
    "guided",
    # URL-as-inspiration is transversal: a user can paste a competitor
    # link from any studio surface. F4 — keep available everywhere so
    # the LLM never has to "switch routes" to use it.
    "url_context",
    # Q&A about tenant data is transversal too: any screen the user is on,
    # they may ask "cuántas personas escribieron" or "dame resumen del
    # programa X" without having to navigate to a specific dashboard. F5.
    "data_query",
    # Channel formatter is transversal: from any screen the user can ask
    # "dame esto listo para whatsapp / email / sms". F7.
    "channel_format",
)


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


# ── PI-5 PR-1: Tool group metadata SSoT (D-PI5-023..025) ────────────────────


@dataclass(frozen=True, slots=True)
class ToolGroupMeta:
    """Metadata per tool group. PI-5 D-PI5-023..025.

    ``available_channels`` enumera canales donde el group es operable.
    Default = todos los canales. Restricción = subset explícito.
    """

    name: str
    available_channels: frozenset[str] = field(default_factory=lambda: frozenset({"web", "telegram", "whatsapp"}))


# SSoT explicit overrides for groups that are NOT available on Telegram.
# Reference: research file §5 + D-PI5-024.
TOOL_GROUP_META: Final[dict[str, ToolGroupMeta]] = {
    "navigation": ToolGroupMeta("navigation", available_channels=frozenset({"web"})),
    "guided": ToolGroupMeta("guided", available_channels=frozenset({"web"})),
    "landing": ToolGroupMeta("landing", available_channels=frozenset({"web"})),
    "offer_section": ToolGroupMeta("offer_section", available_channels=frozenset({"web"})),
    # All other groups inherit default = {"web", "telegram", "whatsapp"}
}


def _meta_for_group(name: str) -> ToolGroupMeta:
    """Return meta for ``name`` or default (all channels) if not configured."""
    return TOOL_GROUP_META.get(name, ToolGroupMeta(name))


def is_group_available_in_channel(group_name: str, channel: str) -> bool:
    """``True`` if ``group_name`` is operable on ``channel``."""
    return channel in _meta_for_group(group_name).available_channels


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


def _filter_groups_by_channel(group_names: tuple[str, ...], channel: str) -> tuple[str, ...]:
    """Drop groups whose meta excludes ``channel`` (D-PI5-023)."""
    return tuple(g for g in group_names if is_group_available_in_channel(g, channel))


def get_tools_for_context(
    context: dict | None,
    channel: str = "web",
) -> list:
    """Return tools based on context (guided flag > route-based) + channel filter.

    * ``guided_mode=True`` in context → guided + knowledge + shared + document.
      The narrow tool set keeps the LLM focused on the structured flow.
    * Otherwise → route-based selection with the always-available groups
      (document, shared_tools, guided) merged in.

    PI-5 PR-1: ``channel`` param filters web-only groups when ``channel !=
    "web"``. Default ``"web"`` = backward compat.

    Focus mode was retired on 2026-04-21; the standalone interview engine was
    retired on 2026-04-22 (state now lives inside the conversation itself).
    """
    if not context:
        return _collect_groups(_filter_groups_by_channel(_match_route(None), channel))

    if context.get("guided_mode"):
        # Guided keeps its narrow toolset but must include ``extraction`` so the
        # LLM can dispatch URL/doc analysis when the user pastes a link mid-flow.
        # Without this, the model falls back to extract_structured loops because
        # extract_from_url/doc are not bound (observed traza 376850f5).
        guided_groups: tuple[str, ...] = (
            "guided",
            "extraction",
            "knowledge",
            "shared_tools",
            "document",
        )
        return _collect_groups(_filter_groups_by_channel(guided_groups, channel))

    return _get_tools_for_route_filtered(context.get("current_route"), channel)


def _get_tools_for_route_filtered(route: str | None, channel: str) -> list:
    """Route-based tools filtered by channel (D-PI5-023)."""
    matched = _match_route(route)
    groups: tuple[str, ...] = tuple(matched)
    for always in ALWAYS_AVAILABLE_GROUPS:
        if always not in groups:
            groups = (*groups, always)
    return _collect_groups(_filter_groups_by_channel(groups, channel))


def _match_route(route: str | None) -> list[str]:
    """Find which tool groups match the current route."""
    if not route:
        return ROUTE_TOOL_MAP["*"]

    route_lower = route.lower()
    for prefix, groups in ROUTE_TOOL_MAP.items():
        if prefix != "*" and prefix in route_lower:
            return groups

    return ROUTE_TOOL_MAP["*"]
