"""Cycle-window math.

Pure-Python equivalent of the Postgres SQL function
``compute_cycle_start(p_tenant UUID, p_date DATE)`` so service code can
compute the cycle window without a roundtrip to the DB. Single source of
truth for "given a tenant's anchor day and a calendar date, which cycle
does the date belong to?".

The Nicolify default cycle is 25 → 25 (anchor day 25). Tenant overrides
live in ``tenant_billing_config.billing_cycle_anchor_day``.
"""

from __future__ import annotations

import datetime as dt
from calendar import monthrange

DEFAULT_ANCHOR_DAY: int = 25


def compute_cycle_start_py(
    anchor_day: int | None,
    target_date: dt.date,
) -> dt.date:
    """Return the start date of the billing cycle containing ``target_date``.

    Args:
        anchor_day: Day of month the cycle starts (1-31). ``None`` falls
            back to :data:`DEFAULT_ANCHOR_DAY`.
        target_date: The date whose cycle we want.

    Returns:
        First day of the cycle (anchor day of the relevant month).

    Raises:
        ValueError: ``anchor_day`` outside [1, 31].
    """
    anchor = DEFAULT_ANCHOR_DAY if anchor_day is None else int(anchor_day)
    if not (1 <= anchor <= 31):
        msg = f"anchor_day must be in [1, 31]; got {anchor_day!r}"
        raise ValueError(msg)

    safe_anchor = _clamp_to_month(target_date.year, target_date.month, anchor)
    if target_date.day >= safe_anchor:
        return dt.date(target_date.year, target_date.month, safe_anchor)

    # Roll back to previous month.
    if target_date.month == 1:
        prev_year, prev_month = target_date.year - 1, 12
    else:
        prev_year, prev_month = target_date.year, target_date.month - 1
    return dt.date(prev_year, prev_month, _clamp_to_month(prev_year, prev_month, anchor))


def compute_cycle_end_py(
    anchor_day: int | None,
    target_date: dt.date,
) -> dt.date:
    """Return the **exclusive** end date of the cycle containing ``target_date``.

    The end matches the start of the next cycle. Use as ``occurred_on <
    end_exclusive`` in range queries.
    """
    start = compute_cycle_start_py(anchor_day, target_date)
    # End = anchor day of the NEXT month.
    if start.month == 12:
        next_year, next_month = start.year + 1, 1
    else:
        next_year, next_month = start.year, start.month + 1
    anchor = DEFAULT_ANCHOR_DAY if anchor_day is None else int(anchor_day)
    return dt.date(next_year, next_month, _clamp_to_month(next_year, next_month, anchor))


def _clamp_to_month(year: int, month: int, anchor: int) -> int:
    """Clamp anchor day to the last day of a short month (Feb 30 → Feb 28/29)."""
    last_day = monthrange(year, month)[1]
    return min(anchor, last_day)


__all__ = [
    "DEFAULT_ANCHOR_DAY",
    "compute_cycle_end_py",
    "compute_cycle_start_py",
]
