"""PlanConfig value object — global billing plan catalog row.

Globally shared catalog (no tenant_id). USD by design (Chris charges in USD).
`llm_budget_total_usd` suffix declares currency — no `currency` field per
architectural decision D18 (see CONTRACT.md §11).

PR-2 / PI-1 S0: plan tiers + tenant_subscription primitives.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PlanConfig(BaseModel):
    """Catalog row → in-memory VO. Globally shared (not per-tenant).

    Five plans ship via migration seed (Free/Básico/Intermedio/Avanzado/Ultra).
    Editable via Streamlit admin `/planes-billing` without migration.

    PM Q6: exactly-one-default invariant enforced via partial unique index
    `uq_plan_config_one_default ON plan_config (is_default) WHERE is_default = TRUE`.
    """

    model_config = ConfigDict(frozen=True, from_attributes=True)

    plan_id: str = Field(..., min_length=2, max_length=32)
    display_name: str = Field(..., min_length=1, max_length=64)
    llm_budget_total_usd: Decimal = Field(..., gt=Decimal(0), max_digits=10, decimal_places=2)
    sales_agent_reserved_pct: Decimal = Field(
        default=Decimal("0.50"),
        ge=Decimal(0),
        le=Decimal(1),
        max_digits=4,
        decimal_places=3,
    )
    max_outbound_msg_per_day: int | None = Field(default=None, ge=0)
    max_campaigns_active: int | None = Field(default=None, ge=0)
    max_segment_size: int | None = Field(default=None, ge=0)
    max_contacts_total: int | None = Field(default=None, ge=0)
    features: dict[str, bool] = Field(default_factory=dict)
    is_active: bool = True
    is_default: bool = False  # PM Q6: exactly-one-default enforced at DB level

    @field_validator("sales_agent_reserved_pct")
    @classmethod
    def validate_pct(cls, v: Decimal) -> Decimal:
        """Enforce [0, 1] range with Decimal precision."""
        if v < Decimal(0) or v > Decimal(1):
            msg = "sales_agent_reserved_pct must be between 0 and 1"
            raise ValueError(msg)
        return v

    @property
    def sa_pool_usd(self) -> Decimal:
        """SA reserved pool for the cycle (USD)."""
        return (self.llm_budget_total_usd * self.sales_agent_reserved_pct).quantize(Decimal("0.01"))

    @property
    def others_pool_usd(self) -> Decimal:
        """Non-SA pool (copilot + future agents).

        Computed as total minus SA pool to avoid floating-point drift.
        """
        return (self.llm_budget_total_usd - self.sa_pool_usd).quantize(Decimal("0.01"))
