"""DTOs for the Bowtie summary endpoint.

Provides lightweight KPI data for the 8 individual stages,
consumed by the frontend to render the Bowtie funnel row
without needing full detail data.
"""

from pydantic import BaseModel
from typing import Optional


class StageSummaryKpiDTO(BaseModel):
    stage: str
    main_kpi: float
    main_label: str
    main_unit: Optional[str] = None
    secondary_kpi: float
    secondary_label: str
    secondary_unit: Optional[str] = None


class BowtiesSummaryDTO(BaseModel):
    stages: list[StageSummaryKpiDTO]
    period: str
    last_updated: Optional[str] = None
