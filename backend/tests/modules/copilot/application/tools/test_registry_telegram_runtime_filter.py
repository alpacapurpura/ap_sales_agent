"""Runtime channel filter for ``get_tools_for_context`` (PI-5 PR-2).

D-PI5-023..025 SSoT: ``ToolGroupMeta.available_channels`` declares which
channels can operate each tool group. Telegram MUST exclude:
    - navigation (UI-only)
    - guided (wizard requires preview)
    - landing (visual editor)
    - offer_section (multi-field mass mutations)

Telegram MUST include the transversal/data-query groups so the agent can
still answer questions, run analytics, search the KB, format output, etc.

Web baseline MUST keep ALL groups (no exclusions) for backward compat.
"""

from __future__ import annotations

from src.modules.copilot.application.tools.registry import (
    TOOL_GROUPS,
    get_tools_for_context,
)


def _route_ctx(route: str) -> dict:
    return {"current_route": route, "guided_mode": False}


def _names(tools: list) -> set[str]:
    return {t.name for t in tools}


# ── Telegram exclusion (web-only groups dropped) ────────────────────────


def test_telegram_excludes_navigation_group() -> None:
    """``navigation`` group is web-only — its tools must NOT be present on Telegram."""
    nav_tool_names = {t.name for t in TOOL_GROUPS.get("navigation", [])}
    assert nav_tool_names, "fixture invariant — navigation group must have tools"

    telegram_tools = _names(get_tools_for_context(_route_ctx("brand-studio"), channel="telegram"))
    assert telegram_tools.isdisjoint(nav_tool_names), (
        f"navigation tools leaked into Telegram toolset: {telegram_tools & nav_tool_names}"
    )


def test_telegram_excludes_guided_group() -> None:
    guided_tool_names = {t.name for t in TOOL_GROUPS.get("guided", [])}
    assert guided_tool_names, "fixture invariant — guided group must have tools"

    telegram_tools = _names(get_tools_for_context(_route_ctx("brand-studio"), channel="telegram"))
    assert telegram_tools.isdisjoint(guided_tool_names), (
        f"guided tools leaked into Telegram toolset: {telegram_tools & guided_tool_names}"
    )


def test_telegram_excludes_landing_group() -> None:
    landing_tool_names = {t.name for t in TOOL_GROUPS.get("landing", [])}
    assert landing_tool_names, "fixture invariant — landing group must have tools"

    telegram_tools = _names(get_tools_for_context(_route_ctx("landing"), channel="telegram"))
    assert telegram_tools.isdisjoint(landing_tool_names), (
        f"landing tools leaked into Telegram toolset: {telegram_tools & landing_tool_names}"
    )


def test_telegram_excludes_offer_section_group() -> None:
    section_tool_names = {t.name for t in TOOL_GROUPS.get("offer_section", [])}
    assert section_tool_names, "fixture invariant — offer_section group must have tools"

    telegram_tools = _names(get_tools_for_context(_route_ctx("offer-studio"), channel="telegram"))
    assert telegram_tools.isdisjoint(section_tool_names), (
        f"offer_section tools leaked into Telegram toolset: {telegram_tools & section_tool_names}"
    )


# ── Telegram inclusion (data + transversal groups available) ────────────


def test_telegram_includes_awareness_analytics_crm() -> None:
    """Data + agent-overview groups MUST be available from Telegram."""
    awareness_names = {t.name for t in TOOL_GROUPS.get("awareness", [])}
    analytics_names = {t.name for t in TOOL_GROUPS.get("analytics", [])}
    crm_names = {t.name for t in TOOL_GROUPS.get("crm", [])}

    # awareness lives in growth-studio + brand-studio routes
    growth_tools = _names(get_tools_for_context(_route_ctx("growth-studio"), channel="telegram"))
    assert awareness_names.issubset(growth_tools), (
        f"awareness missing from Telegram (growth-studio): {awareness_names - growth_tools}"
    )
    assert analytics_names.issubset(growth_tools), (
        f"analytics missing from Telegram (growth-studio): {analytics_names - growth_tools}"
    )
    assert crm_names.issubset(growth_tools), f"crm missing from Telegram (growth-studio): {crm_names - growth_tools}"


def test_telegram_includes_always_available_data_groups() -> None:
    """``data_query``, ``channel_format``, ``url_context``, ``document``,
    ``shared_tools`` are ALWAYS_AVAILABLE_GROUPS — must reach Telegram."""
    expected = ["data_query", "channel_format", "url_context", "document", "shared_tools"]
    telegram_tools = _names(get_tools_for_context(_route_ctx("brand-studio"), channel="telegram"))
    for group in expected:
        group_names = {t.name for t in TOOL_GROUPS.get(group, [])}
        assert group_names, f"fixture invariant — group {group!r} must have tools"
        assert group_names.issubset(telegram_tools), (
            f"always-available group {group!r} missing from Telegram: {group_names - telegram_tools}"
        )


def test_telegram_includes_knowledge_search() -> None:
    """``knowledge`` group (carries ``knowledge_search``) reaches Telegram."""
    knowledge_names = {t.name for t in TOOL_GROUPS.get("knowledge", [])}
    assert knowledge_names, "fixture invariant — knowledge group must have tools"

    telegram_tools = _names(get_tools_for_context(_route_ctx("brand-studio"), channel="telegram"))
    assert knowledge_names.issubset(telegram_tools), (
        f"knowledge tools missing from Telegram: {knowledge_names - telegram_tools}"
    )


def test_telegram_includes_offer_ladder_query() -> None:
    """``offer_ladder`` is consult-only on Telegram (per channel context block)."""
    ladder_names = {t.name for t in TOOL_GROUPS.get("offer_ladder", [])}
    assert ladder_names, "fixture invariant — offer_ladder group must have tools"

    telegram_tools = _names(get_tools_for_context(_route_ctx("offer-studio"), channel="telegram"))
    assert ladder_names.issubset(telegram_tools), (
        f"offer_ladder tools missing from Telegram: {ladder_names - telegram_tools}"
    )


def test_telegram_includes_extraction() -> None:
    """``extraction`` group (URL-to-studio) reaches Telegram for "extrae de esta URL" flows."""
    extraction_names = {t.name for t in TOOL_GROUPS.get("extraction", [])}
    assert extraction_names, "fixture invariant — extraction group must have tools"

    telegram_tools = _names(get_tools_for_context(_route_ctx("brand-studio"), channel="telegram"))
    assert extraction_names.issubset(telegram_tools), (
        f"extraction tools missing from Telegram: {extraction_names - telegram_tools}"
    )


# ── Web baseline (no exclusions) ────────────────────────────────────────


def test_web_baseline_includes_navigation() -> None:
    nav_names = {t.name for t in TOOL_GROUPS.get("navigation", [])}
    web_tools = _names(get_tools_for_context(_route_ctx("brand-studio"), channel="web"))
    assert nav_names.issubset(web_tools), f"navigation MUST be on web baseline: missing {nav_names - web_tools}"


def test_web_baseline_includes_guided() -> None:
    guided_names = {t.name for t in TOOL_GROUPS.get("guided", [])}
    web_tools = _names(get_tools_for_context(_route_ctx("brand-studio"), channel="web"))
    assert guided_names.issubset(web_tools), f"guided MUST be on web baseline: missing {guided_names - web_tools}"


def test_web_baseline_includes_landing_on_landing_route() -> None:
    landing_names = {t.name for t in TOOL_GROUPS.get("landing", [])}
    web_tools = _names(get_tools_for_context(_route_ctx("landing"), channel="web"))
    assert landing_names.issubset(web_tools), (
        f"landing MUST be on web/landing baseline: missing {landing_names - web_tools}"
    )


def test_web_baseline_includes_offer_section_on_offer_route() -> None:
    section_names = {t.name for t in TOOL_GROUPS.get("offer_section", [])}
    web_tools = _names(get_tools_for_context(_route_ctx("offer-studio"), channel="web"))
    assert section_names.issubset(web_tools), (
        f"offer_section MUST be on web/offer-studio baseline: missing {section_names - web_tools}"
    )
