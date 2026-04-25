"""F5 — Spanish LatAm period parser tests.

Covers the recurring user phrasings: "esta semana", "última semana",
"este mes", "mes pasado", "hoy", "ayer", "antier", "últimos N días",
"Q1 2026", month-only, ISO date.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from src.modules.copilot.application.tools.ask_tenant_data.date_parser import (
    parse_period,
)

# Anchor: Saturday 2026-04-25 14:00 UTC (matches CLAUDE.md current_date).
NOW = datetime(2026, 4, 25, 14, 0, 0, tzinfo=timezone.utc)


def _between(value: datetime, lo: datetime, hi: datetime) -> bool:
    return lo <= value <= hi


def test_default_when_phrase_is_none() -> None:
    since, until = parse_period(None, now=NOW)
    # Current ISO week (Mon 2026-04-20 00:00 → Sun 2026-04-26 23:59:59)
    assert since.weekday() == 0  # Monday
    assert since.hour == 0 and since.minute == 0
    assert until > since


def test_esta_semana_returns_current_iso_week() -> None:
    since, until = parse_period("esta semana", now=NOW)
    # Saturday 2026-04-25 → Mon 2026-04-20 to Sun 2026-04-26
    assert since == datetime(2026, 4, 20, 0, 0, 0, tzinfo=timezone.utc)
    assert until.date() == date(2026, 4, 26)


def test_semana_pasada_returns_previous_iso_week() -> None:
    since, until = parse_period("semana pasada", now=NOW)
    assert since == datetime(2026, 4, 13, 0, 0, 0, tzinfo=timezone.utc)
    assert until.date() == date(2026, 4, 19)


def test_ultima_semana_synonym() -> None:
    since, until = parse_period("última semana", now=NOW)
    assert since == datetime(2026, 4, 13, 0, 0, 0, tzinfo=timezone.utc)
    assert until.date() == date(2026, 4, 19)


def test_hoy() -> None:
    since, until = parse_period("hoy", now=NOW)
    assert since == datetime(2026, 4, 25, 0, 0, 0, tzinfo=timezone.utc)
    assert until.date() == date(2026, 4, 25)


def test_ayer() -> None:
    since, until = parse_period("ayer", now=NOW)
    assert since.date() == date(2026, 4, 24)
    assert until.date() == date(2026, 4, 24)


def test_antier() -> None:
    since, _until = parse_period("antier", now=NOW)
    assert since.date() == date(2026, 4, 23)


def test_anteayer_synonym() -> None:
    since, _ = parse_period("anteayer", now=NOW)
    assert since.date() == date(2026, 4, 23)


def test_este_mes() -> None:
    since, until = parse_period("este mes", now=NOW)
    assert since == datetime(2026, 4, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert until.date() == date(2026, 4, 30)


def test_mes_pasado() -> None:
    since, until = parse_period("mes pasado", now=NOW)
    assert since == datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert until.date() == date(2026, 3, 31)


def test_ultimos_n_dias() -> None:
    since, until = parse_period("últimos 7 días", now=NOW)
    expected_since = (NOW - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    assert _between(since, expected_since - timedelta(seconds=2), expected_since + timedelta(seconds=2))
    assert until.date() == NOW.date()


def test_ultimos_n_dias_sin_tilde() -> None:
    since, _ = parse_period("ultimos 30 dias", now=NOW)
    expected_since = (NOW - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
    assert _between(since, expected_since - timedelta(seconds=2), expected_since + timedelta(seconds=2))


def test_q1_2026() -> None:
    since, until = parse_period("Q1 2026", now=NOW)
    assert since == datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert until.date() == date(2026, 3, 31)


def test_q2_2026() -> None:
    since, until = parse_period("Q2 2026", now=NOW)
    assert since == datetime(2026, 4, 1, 0, 0, 0, tzinfo=timezone.utc)
    assert until.date() == date(2026, 6, 30)


def test_month_only_marzo() -> None:
    """'marzo' alone resolves to the current year's March."""
    since, until = parse_period("marzo", now=NOW)
    assert since.year == 2026
    assert since.month == 3
    assert until.month == 3
    assert until.day == 31


def test_unknown_phrase_falls_back_to_default() -> None:
    """Garbled phrase falls back to the default (current ISO week)."""
    since, until = parse_period("alabampa", now=NOW)
    assert since.weekday() == 0
    assert until > since


@pytest.mark.parametrize(
    "phrase",
    ["", "   ", "—"],
)
def test_empty_phrases_fall_back(phrase: str) -> None:
    since, until = parse_period(phrase, now=NOW)
    assert until > since
