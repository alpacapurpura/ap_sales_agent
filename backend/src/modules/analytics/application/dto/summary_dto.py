"""DTOs for the Bowtie summary endpoint.

Provides lightweight KPI data for the 8 individual stages,
consumed by the frontend to render the Bowtie funnel row
without needing full detail data.
"""

from pydantic import BaseModel


class StageSummaryKpiDTO(BaseModel):
    """Data transfer object for stage summary kpi."""

    stage: str
    main_kpi: float
    main_label: str
    main_unit: str | None = None
    secondary_kpi: float
    secondary_label: str
    secondary_unit: str | None = None


class BowtiesSummaryDTO(BaseModel):
    """Data transfer object for bowties summary."""

    stages: list[StageSummaryKpiDTO]
    period: str
    last_updated: str | None = None
