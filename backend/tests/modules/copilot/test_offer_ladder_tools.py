"""Tests for offer_ladder_tools — session safety and output correctness."""

from unittest.mock import MagicMock, patch

from luana_core_copilot.application.tools.offer_ladder_tools import (
    OFFER_LADDER_TOOLS,
    _build_current_status,
    _build_gap_analysis,
    _calculate_completeness,
    _fetch_brand_context,
    _fetch_offers,
    _group_by_level,
    analyze_offer_ladder,
)

# ---------------------------------------------------------------------------
# Registry test
# ---------------------------------------------------------------------------


def test_offer_ladder_tools_registered() -> None:
    assert len(OFFER_LADDER_TOOLS) == 1
    assert OFFER_LADDER_TOOLS[0].name == "analyze_offer_ladder"


# ---------------------------------------------------------------------------
# _group_by_level
# ---------------------------------------------------------------------------


def test_group_by_level_all_empty() -> None:
    groups = _group_by_level([])
    assert set(groups.keys()) == {"lead_magnet", "activacion", "transformacion", "maximizacion", "corporativo"}
    for offers in groups.values():
        assert offers == []


def test_group_by_level_routes_correctly() -> None:
    offers = [
        {"name": "Guia", "offer_value_level": "lead_magnet"},
        {"name": "Masterclass", "offer_value_level": "activacion"},
        {"name": "Unknown", "offer_value_level": "nonexistent_level"},
    ]
    groups = _group_by_level(offers)
    assert len(groups["lead_magnet"]) == 1
    assert len(groups["activacion"]) == 1
    # Unknown levels are silently discarded
    assert sum(len(v) for v in groups.values()) == 2


# ---------------------------------------------------------------------------
# _build_current_status
# ---------------------------------------------------------------------------


def test_build_current_status_empty_ladder() -> None:
    groups = _group_by_level([])
    result = _build_current_status(groups)
    assert "_Vacio_" in result
    assert "Lead Magnet" in result


def test_build_current_status_with_offers() -> None:
    offers = [{"name": "Mi Guia", "offer_value_level": "lead_magnet"}]
    groups = _group_by_level(offers)
    result = _build_current_status(groups)
    assert "Mi Guia" in result
    assert "1 oferta" in result


# ---------------------------------------------------------------------------
# _build_gap_analysis
# ---------------------------------------------------------------------------


def test_build_gap_analysis_full_ladder() -> None:
    groups = {
        "lead_magnet": [{"name": "A"}],
        "activacion": [{"name": "B"}],
        "transformacion": [{"name": "C"}],
        "maximizacion": [{"name": "D"}],
        "corporativo": [{"name": "E"}],
    }
    result = _build_gap_analysis(groups, brand=None)
    assert "No hay gaps" in result


def test_build_gap_analysis_missing_levels() -> None:
    groups = _group_by_level([])
    result = _build_gap_analysis(groups, brand=None)
    assert "CRITICO" in result
    assert "lead_magnet" in result.lower() or "Lead Magnet" in result


def test_build_gap_analysis_uses_brand_niche() -> None:
    groups = _group_by_level([])
    brand = {"niche": "Bienestar", "industry": "Salud", "target_audience": "Mujeres"}
    result = _build_gap_analysis(groups, brand=brand)
    assert "Bienestar" in result


# ---------------------------------------------------------------------------
# _calculate_completeness
# ---------------------------------------------------------------------------


def test_calculate_completeness_zero() -> None:
    groups = _group_by_level([])
    result = _calculate_completeness(groups)
    assert "0/5" in result
    assert "0%" in result


def test_calculate_completeness_full() -> None:
    groups = {
        "lead_magnet": [{"name": "A"}],
        "activacion": [{"name": "B"}],
        "transformacion": [{"name": "C"}],
        "maximizacion": [{"name": "D"}],
        "corporativo": [{"name": "E"}],
    }
    result = _calculate_completeness(groups)
    assert "5/5" in result
    assert "100%" in result


# ---------------------------------------------------------------------------
# _fetch_brand_context — sync session safety
# ---------------------------------------------------------------------------


def test_fetch_brand_context_returns_none_on_error() -> None:
    """_fetch_brand_context must return None (not raise) when DB fails."""
    mock_db = MagicMock()
    mock_db.execute.side_effect = AttributeError("DB unavailable")
    result = _fetch_brand_context(mock_db, "some-tenant-id")
    assert result is None


def test_fetch_brand_context_returns_dict_when_found() -> None:
    mock_db = MagicMock()
    mock_row = {"niche": "Fitness", "industry": "Salud", "target_audience": "Hombres 30+"}
    mock_db.execute.return_value.mappings.return_value.first.return_value = mock_row
    result = _fetch_brand_context(mock_db, "some-tenant-id")
    assert result == mock_row


def test_fetch_brand_context_returns_none_when_not_found() -> None:
    mock_db = MagicMock()
    mock_db.execute.return_value.mappings.return_value.first.return_value = None
    result = _fetch_brand_context(mock_db, "some-tenant-id")
    assert result is None


# ---------------------------------------------------------------------------
# _fetch_offers — sync session safety
# ---------------------------------------------------------------------------


def test_fetch_offers_returns_empty_on_error() -> None:
    """_fetch_offers must return [] (not raise) when DB fails."""
    mock_db = MagicMock()
    mock_db.execute.side_effect = AttributeError("connection refused")
    result = _fetch_offers(mock_db, "some-tenant-id")
    assert result == []


def test_fetch_offers_returns_list_when_found() -> None:
    mock_db = MagicMock()
    raw_rows = [
        {
            "id": "uuid-1",
            "name": "Guia Gratuita",
            "archetype": "producto",
            "format_hint": None,
            "offer_value_level": "lead_magnet",
            "delivery_model": "digital",
            "status": "active",
        }
    ]
    mock_db.execute.return_value.mappings.return_value.all.return_value = raw_rows
    result = _fetch_offers(mock_db, "some-tenant-id")
    assert len(result) == 1
    assert result[0]["name"] == "Guia Gratuita"


# ---------------------------------------------------------------------------
# analyze_offer_ladder — session lifecycle (D3: _safe_session context manager)
# ---------------------------------------------------------------------------


def test_analyze_offer_ladder_returns_error_when_no_tenant() -> None:
    """If get_tenant_id returns None, tool returns an error string — no DB hit."""
    with patch("luana_core_copilot.application.tools.offer_ladder_tools.get_tenant_id", return_value=None):
        result = analyze_offer_ladder.invoke({})
    assert "Error" in result or "error" in result.lower()


def test_analyze_offer_ladder_session_closed_on_success() -> None:
    """Session must be closed even when the tool succeeds (D3 regression test)."""
    mock_session = MagicMock()
    # Simulate empty DB (no offers, no brand)
    mock_session.execute.return_value.mappings.return_value.first.return_value = None
    mock_session.execute.return_value.mappings.return_value.all.return_value = []

    with (
        patch("luana_core_copilot.application.tools.offer_ladder_tools.get_tenant_id", return_value="t-123"),
        patch("luana_core_copilot.application.tools.offer_ladder_tools.SessionLocal", return_value=mock_session),
    ):
        result = analyze_offer_ladder.invoke({})

    # Session must have been closed via the context manager
    mock_session.close.assert_called_once()
    assert isinstance(result, str)


def test_analyze_offer_ladder_session_closed_on_db_error() -> None:
    """Session must be closed even when DB raises (D3 regression test)."""
    mock_session = MagicMock()
    mock_session.execute.side_effect = ValueError("connection lost")

    with (
        patch("luana_core_copilot.application.tools.offer_ladder_tools.get_tenant_id", return_value="t-123"),
        patch("luana_core_copilot.application.tools.offer_ladder_tools.SessionLocal", return_value=mock_session),
    ):
        result = analyze_offer_ladder.invoke({})

    # Session still closed despite error
    mock_session.close.assert_called_once()
    # Tool must return a string (graceful degradation), not raise
    assert isinstance(result, str)


def test_analyze_offer_ladder_returns_markdown_with_gaps() -> None:
    """Full happy path: empty DB produces markdown with gap analysis."""
    mock_session = MagicMock()
    mock_session.execute.return_value.mappings.return_value.first.return_value = None
    mock_session.execute.return_value.mappings.return_value.all.return_value = []

    with (
        patch("luana_core_copilot.application.tools.offer_ladder_tools.get_tenant_id", return_value="t-123"),
        patch("luana_core_copilot.application.tools.offer_ladder_tools.SessionLocal", return_value=mock_session),
    ):
        result = analyze_offer_ladder.invoke({})

    assert "Offer Ladder" in result
    assert "CRITICO" in result
    assert "0/5" in result or "0%" in result
