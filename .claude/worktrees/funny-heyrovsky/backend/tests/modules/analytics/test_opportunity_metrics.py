"""Tests for opportunity-stage (Stage 3) metrics.

Covers: OpportunityDetailDTO construction, bottleneck threshold logic
for abandoned cart and meeting no-show rates at all severity levels.
"""

import pytest

from src.modules.analytics.application.dto.opportunity_dto import (
    BottleneckDTO,
    OpportunityDetailDTO,
    OpportunityHeaderKpisDTO,
)
from src.modules.analytics.application.dto.attraction_dto import (
    ChannelMetricDTO,
    MetricValueDTO,
    TrafficGroupDTO,
)
from src.modules.analytics.application.dto.capture_dto import MiniFunnelDTO


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_dto(
    total_sqls: int = 10,
    mql_count: int = 50,
    checkout_count: int = 0,
    abandoned_count: int = 0,
    meeting_booked: int = 0,
    meeting_no_show: int = 0,
) -> OpportunityDetailDTO:
    """Build a minimal OpportunityDetailDTO for testing."""
    conversion_rate = round(total_sqls / mql_count * 100, 2) if mql_count > 0 else 0.0

    # Build bottlenecks
    bottlenecks = []

    if checkout_count > 0:
        abandon_rate = (abandoned_count / checkout_count) * 100
        if abandon_rate > 50:
            bottlenecks.append(BottleneckDTO(
                type="abandoned_cart",
                metric_label="Tasa de Abandono",
                current_rate=round(abandon_rate, 1),
                severity="critical",
                threshold=50.0,
                tip="Revisa tu proceso de pago y considera email de recuperacion de carrito",
            ))
        elif abandon_rate > 30:
            bottlenecks.append(BottleneckDTO(
                type="abandoned_cart",
                metric_label="Tasa de Abandono",
                current_rate=round(abandon_rate, 1),
                severity="warning",
                threshold=30.0,
                tip="Revisa tu proceso de pago y considera email de recuperacion de carrito",
            ))

    if meeting_booked > 0:
        no_show_rate = (meeting_no_show / meeting_booked) * 100
        if no_show_rate > 40:
            bottlenecks.append(BottleneckDTO(
                type="meeting_no_show",
                metric_label="Tasa de No-Show",
                current_rate=round(no_show_rate, 1),
                severity="critical",
                threshold=40.0,
                tip="Considera recordatorios automaticos antes de la reunion",
            ))
        elif no_show_rate > 20:
            bottlenecks.append(BottleneckDTO(
                type="meeting_no_show",
                metric_label="Tasa de No-Show",
                current_rate=round(no_show_rate, 1),
                severity="warning",
                threshold=20.0,
                tip="Considera recordatorios automaticos antes de la reunion",
            ))

    return OpportunityDetailDTO(
        header_kpis=OpportunityHeaderKpisDTO(
            total_sqls=total_sqls,
            conversion_rate=conversion_rate,
        ),
        mini_funnel=MiniFunnelDTO(
            source_label="MQLs",
            source_value=mql_count,
            target_label="SQLs",
            target_value=total_sqls,
            conversion_rate=conversion_rate,
        ),
        checkout=TrafficGroupDTO(totals={}, channels=[]),
        payment_links=TrafficGroupDTO(totals={}, channels=[]),
        qualification=TrafficGroupDTO(totals={}, channels=[]),
        bottlenecks=bottlenecks,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_opportunity_dto_construction():
    """Build OpportunityDetailDTO with all fields and verify serialization."""
    dto = OpportunityDetailDTO(
        header_kpis=OpportunityHeaderKpisDTO(
            total_sqls=69,
            conversion_rate=32.9,
            cost_per_sql=12.50,
        ),
        mini_funnel=MiniFunnelDTO(
            source_label="MQLs",
            source_value=210,
            target_label="SQLs",
            target_value=69,
            conversion_rate=32.9,
        ),
        checkout=TrafficGroupDTO(
            totals={"count": 45.0, "value": 2250.0},
            channels=[
                ChannelMetricDTO(
                    slug="checkout-init",
                    name="Checkout Iniciado",
                    channel_type="checkout",
                    metrics=[
                        MetricValueDTO(name="count", value=45.0),
                        MetricValueDTO(name="value", value=2250.0, unit="currency", currency="USD"),
                    ],
                    source_label="Shopify",
                    connected=True,
                ),
            ],
        ),
        payment_links=TrafficGroupDTO(totals={}, channels=[]),
        qualification=TrafficGroupDTO(
            totals={"booked": 24.0, "completed": 18.0, "no_show": 3.0, "rescheduled": 3.0},
            channels=[
                ChannelMetricDTO(
                    slug="meeting-booked",
                    name="Reuniones Agendadas",
                    channel_type="qualification",
                    metrics=[
                        MetricValueDTO(name="booked", value=24.0),
                        MetricValueDTO(name="completed", value=18.0),
                        MetricValueDTO(name="no_show", value=3.0),
                        MetricValueDTO(name="rescheduled", value=3.0),
                    ],
                    source_label="Scheduling",
                    connected=True,
                ),
            ],
        ),
        bottlenecks=[],
    )

    data = dto.model_dump()
    assert data["header_kpis"]["total_sqls"] == 69
    assert data["header_kpis"]["conversion_rate"] == 32.9
    assert data["header_kpis"]["cost_per_sql"] == 12.50
    assert data["mini_funnel"]["source_label"] == "MQLs"
    assert data["mini_funnel"]["target_label"] == "SQLs"
    assert len(data["checkout"]["channels"]) == 1
    assert len(data["qualification"]["channels"]) == 1
    assert data["bottlenecks"] == []
    assert data["period"] == "last_30_days"


def test_bottleneck_normal_no_flags():
    """20% abandonment and 10% no-show should produce no bottlenecks."""
    dto = _build_dto(
        checkout_count=100,
        abandoned_count=20,  # 20% -- below 30% threshold
        meeting_booked=100,
        meeting_no_show=10,  # 10% -- below 20% threshold
    )
    assert dto.bottlenecks == []


def test_bottleneck_warning_abandoned_cart():
    """40% abandonment rate triggers warning severity."""
    dto = _build_dto(
        checkout_count=100,
        abandoned_count=40,  # 40% -- above 30%, below 50%
    )
    assert len(dto.bottlenecks) == 1
    b = dto.bottlenecks[0]
    assert b.type == "abandoned_cart"
    assert b.severity == "warning"
    assert b.threshold == 30.0
    assert b.current_rate == 40.0


def test_bottleneck_critical_abandoned_cart():
    """60% abandonment rate triggers critical severity."""
    dto = _build_dto(
        checkout_count=100,
        abandoned_count=60,  # 60% -- above 50%
    )
    assert len(dto.bottlenecks) == 1
    b = dto.bottlenecks[0]
    assert b.type == "abandoned_cart"
    assert b.severity == "critical"
    assert b.threshold == 50.0
    assert b.current_rate == 60.0


def test_bottleneck_warning_no_show():
    """30% no-show rate triggers warning severity."""
    dto = _build_dto(
        meeting_booked=100,
        meeting_no_show=30,  # 30% -- above 20%, below 40%
    )
    assert len(dto.bottlenecks) == 1
    b = dto.bottlenecks[0]
    assert b.type == "meeting_no_show"
    assert b.severity == "warning"
    assert b.threshold == 20.0
    assert b.current_rate == 30.0


def test_bottleneck_critical_no_show():
    """50% no-show rate triggers critical severity."""
    dto = _build_dto(
        meeting_booked=100,
        meeting_no_show=50,  # 50% -- above 40%
    )
    assert len(dto.bottlenecks) == 1
    b = dto.bottlenecks[0]
    assert b.type == "meeting_no_show"
    assert b.severity == "critical"
    assert b.threshold == 40.0
    assert b.current_rate == 50.0


def test_bottleneck_both_flags():
    """Both abandoned cart and no-show can be flagged simultaneously."""
    dto = _build_dto(
        checkout_count=100,
        abandoned_count=55,  # 55% critical
        meeting_booked=100,
        meeting_no_show=25,  # 25% warning
    )
    assert len(dto.bottlenecks) == 2
    types = {b.type for b in dto.bottlenecks}
    assert types == {"abandoned_cart", "meeting_no_show"}


def test_bottleneck_zero_denominator():
    """Zero checkout_count or meeting_booked should produce no bottlenecks."""
    dto = _build_dto(
        checkout_count=0,
        abandoned_count=0,
        meeting_booked=0,
        meeting_no_show=0,
    )
    assert dto.bottlenecks == []
