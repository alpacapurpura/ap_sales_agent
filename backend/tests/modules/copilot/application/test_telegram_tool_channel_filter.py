"""Unit tests for tool registry channel filter (PI-5 PR-1).

Covers D-PI5-023..025: web-only groups filter when channel != "web".
"""

from __future__ import annotations

from luana_core_copilot.application.tools.registry import (
    TOOL_GROUP_META,
    ToolGroupMeta,
    is_group_available_in_channel,
)


def test_navigation_is_web_only() -> None:
    assert is_group_available_in_channel("navigation", "web") is True
    assert is_group_available_in_channel("navigation", "telegram") is False


def test_guided_is_web_only() -> None:
    assert is_group_available_in_channel("guided", "web") is True
    assert is_group_available_in_channel("guided", "telegram") is False


def test_landing_is_web_only() -> None:
    assert is_group_available_in_channel("landing", "web") is True
    assert is_group_available_in_channel("landing", "telegram") is False


def test_offer_section_is_web_only() -> None:
    assert is_group_available_in_channel("offer_section", "web") is True
    assert is_group_available_in_channel("offer_section", "telegram") is False


def test_unknown_group_defaults_all_channels() -> None:
    """Groups not in TOOL_GROUP_META default to all channels."""
    assert is_group_available_in_channel("nonexistent_group", "web") is True
    assert is_group_available_in_channel("nonexistent_group", "telegram") is True
    assert is_group_available_in_channel("nonexistent_group", "whatsapp") is True


def test_analytics_telegram_allowed() -> None:
    """Analytics works on Telegram (research §5)."""
    assert is_group_available_in_channel("analytics", "telegram") is True


def test_crm_telegram_allowed() -> None:
    """CRM consultas work on Telegram."""
    assert is_group_available_in_channel("crm", "telegram") is True


def test_tool_group_meta_immutable() -> None:
    """ToolGroupMeta is frozen — cannot mutate post-creation."""
    meta = ToolGroupMeta("test_group", available_channels=frozenset({"web"}))
    import dataclasses
    import pytest

    with pytest.raises(dataclasses.FrozenInstanceError):
        meta.name = "modified"  # type: ignore[misc]


def test_meta_default_includes_telegram_and_whatsapp() -> None:
    """Default meta includes web + telegram + whatsapp."""
    default = ToolGroupMeta("foo")
    assert "web" in default.available_channels
    assert "telegram" in default.available_channels
    assert "whatsapp" in default.available_channels
