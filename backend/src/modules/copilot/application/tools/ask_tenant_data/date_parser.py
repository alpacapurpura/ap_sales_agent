"""Spanish LatAm period parser for ``ask_tenant_data``.

Handles the common phrasings tenants use without rounding to a single point:
returns ``(since, until)`` UTC datetimes for relative phrases ("ayer",
"esta semana", "mes pasado", "últimos 7 días"), absolute quarters
("Q1 2026"), and bare month names ("marzo"). Falls back to the current ISO
week when the phrase is empty / unrecognised — the synthesizer can then
explain in the answer that no period was specified.

The parser deliberately wraps :mod:`dateparser` only for the long tail of
phrasings; the recurring buckets are handled with deterministic Python so
unit tests stay fast and free of locale-data flakiness.
"""

from __future__ import annotations

import calendar
import re
import unicodedata
from datetime import datetime, timedelta, timezone

import dateparser

_DAY_MS = 86_399_999_999  # microseconds in a day minus 1us → end-of-day stamp
_DEFAULT_LOCALE = ["es"]
_QUARTER_MONTHS: dict[int, tuple[int, int]] = {
    1: (1, 3),
    2: (4, 6),
    3: (7, 9),
    4: (10, 12),
}
_SPANISH_MONTHS: dict[str, int] = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


def _strip_accents(text: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch))


def _normalise(phrase: str) -> str:
    return _strip_accents(phrase.strip().lower())


def _start_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _end_of_day(dt: datetime) -> datetime:
    return _start_of_day(dt) + timedelta(microseconds=_DAY_MS)


def _iso_week(now: datetime, *, offset_weeks: int = 0) -> tuple[datetime, datetime]:
    today = _start_of_day(now)
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=offset_weeks)
    sunday_eod = _end_of_day(monday + timedelta(days=6))
    return monday, sunday_eod


def _calendar_month(year: int, month: int) -> tuple[datetime, datetime]:
    last_day = calendar.monthrange(year, month)[1]
    since = datetime(year, month, 1, tzinfo=timezone.utc)
    until = _end_of_day(datetime(year, month, last_day, tzinfo=timezone.utc))
    return since, until


def _quarter_range(year: int, quarter: int) -> tuple[datetime, datetime]:
    start_month, end_month = _QUARTER_MONTHS[quarter]
    since, _ = _calendar_month(year, start_month)
    _, until = _calendar_month(year, end_month)
    return since, until


def _default_window(now: datetime) -> tuple[datetime, datetime]:
    return _iso_week(now)


def parse_period(  # noqa: C901, PLR0911, PLR0912 — intentional flat case table; refactoring to dispatch dict hides the mapping with no readability win
    phrase: str | None,
    *,
    now: datetime | None = None,
) -> tuple[datetime, datetime]:
    """Parse a Spanish period phrase to ``(since, until)`` UTC datetimes.

    ``now`` defaults to ``datetime.now(timezone.utc)``; tests pass an anchor.
    Empty / unrecognised phrases fall back to the current ISO week.
    """
    anchor = now if now is not None else datetime.now(timezone.utc)
    if anchor.tzinfo is None:
        anchor = anchor.replace(tzinfo=timezone.utc)

    if not phrase or not phrase.strip() or phrase.strip() in {"—", "-"}:
        return _default_window(anchor)

    norm = _normalise(phrase)

    # Single-day buckets.
    if norm in {"hoy", "today"}:
        return _start_of_day(anchor), _end_of_day(anchor)
    if norm in {"ayer", "yesterday"}:
        d = anchor - timedelta(days=1)
        return _start_of_day(d), _end_of_day(d)
    if norm in {"antier", "anteayer"}:
        d = anchor - timedelta(days=2)
        return _start_of_day(d), _end_of_day(d)

    # Week buckets.
    if norm in {"esta semana", "this week"}:
        return _iso_week(anchor, offset_weeks=0)
    if norm in {
        "semana pasada",
        "ultima semana",
        "la semana pasada",
        "la ultima semana",
        "last week",
    }:
        return _iso_week(anchor, offset_weeks=-1)

    # Month buckets.
    if norm in {"este mes", "this month"}:
        return _calendar_month(anchor.year, anchor.month)
    if norm in {"mes pasado", "ultimo mes", "el mes pasado", "last month"}:
        if anchor.month == 1:
            return _calendar_month(anchor.year - 1, 12)
        return _calendar_month(anchor.year, anchor.month - 1)

    # "últimos N días" / "ultimos N dias".
    last_n_days = re.match(r"^ultimos?\s+(\d+)\s+d(ias?|ays?)$", norm)
    if last_n_days:
        n = int(last_n_days.group(1))
        since = _start_of_day(anchor - timedelta(days=n))
        return since, anchor

    # Quarter "Q1 2026".
    quarter_match = re.match(r"^q([1-4])\s*(\d{4})?$", norm)
    if quarter_match:
        q = int(quarter_match.group(1))
        year = int(quarter_match.group(2)) if quarter_match.group(2) else anchor.year
        return _quarter_range(year, q)

    # Bare month name ("marzo" / "marzo 2026").
    month_match = re.match(r"^([a-z]+)(?:\s+(\d{4}))?$", norm)
    if month_match:
        month_name = month_match.group(1)
        if month_name in _SPANISH_MONTHS:
            month = _SPANISH_MONTHS[month_name]
            year = int(month_match.group(2)) if month_match.group(2) else anchor.year
            return _calendar_month(year, month)

    # Final fallback: dateparser handles ISO-ish strings.
    parsed = dateparser.parse(
        phrase,
        languages=_DEFAULT_LOCALE,
        settings={
            "PREFER_DATES_FROM": "past",
            "RELATIVE_BASE": anchor.replace(tzinfo=None),
            "TIMEZONE": "UTC",
            "RETURN_AS_TIMEZONE_AWARE": True,
        },
    )
    if parsed is not None:
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return _start_of_day(parsed), _end_of_day(parsed)

    return _default_window(anchor)
