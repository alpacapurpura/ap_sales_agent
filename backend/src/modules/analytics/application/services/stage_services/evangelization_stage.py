"""Evangelization stage service — extracted from MetricsService.

Handles get_evangelization_metrics() logic: K-Factor, referrals,
NPS, UGC, bottleneck detection.
"""

from datetime import UTC
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.analytics.application.dto.capture_dto import MiniFunnelDTO
from src.modules.analytics.application.dto.evangelization_dto import (
    CandidatoDTO,
    EvangelistDTO,
    EvangelizationDetailDTO,
    EvangelizationHeaderKpisDTO,
    NpsSummaryDTO,
)
from src.modules.analytics.application.dto.opportunity_dto import BottleneckDTO
from src.modules.analytics.domain.ports import ConnectionPort, OfferReadPort
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache


class EvangelizationStageService:
    """Provides evangelization stage metrics for the Bowtie dashboard."""

    def __init__(
        self,
        db: Session,
        cache: MetricsCache | None = None,
        connection_port: ConnectionPort | None = None,
        offer_port: OfferReadPort | None = None,
    ):
        self.db = db
        self.cache = cache
        self.connection_port = connection_port
        self.offer_port = offer_port

    async def get_metrics(
        self,
        tenant_id: UUID,
        start_date: "object",
        end_date: "object",
    ) -> EvangelizationDetailDTO:
        """Return evangelization-stage (Stage 7) metrics.

        Flow:
        1. Check MetricsCache (300s TTL for evangelization stage)
        2. On miss: query EvangelizationRepository for referral/NPS/UGC data
        3. Compute bottlenecks (low K-Factor, low NPS response rate)
        4. Assemble EvangelizationDetailDTO
        5. Cache result and return
        """
        from datetime import datetime as dt_cls

        from src.modules.analytics.infrastructure.repositories.evangelization_repository import (
            EvangelizationRepository,
        )

        # 1. Check cache
        if self.cache is not None:
            cached = await self.cache.get(
                str(tenant_id), "evangelization", "last_30_days"
            )
            if cached is not None:
                return EvangelizationDetailDTO(**cached)

        # 2. Query repository
        repo = EvangelizationRepository(self.db)
        data = await repo.get_evangelization_data(tenant_id, start_date, end_date)

        # 3. Compute bottlenecks
        bottlenecks: list[BottleneckDTO] = []

        k_factor = data.get("k_factor", 0.0)
        if k_factor < 0.5:
            bottlenecks.append(
                BottleneckDTO(
                    type="low_k_factor",
                    metric_label="K-Factor bajo",
                    current_rate=k_factor,
                    severity="critical",
                    threshold=0.5,
                    tip="Incentiva a tus mejores clientes a compartir su codigo de referido. Ofrece descuentos o beneficios exclusivos.",
                )
            )
        elif k_factor < 1.0:
            bottlenecks.append(
                BottleneckDTO(
                    type="low_k_factor",
                    metric_label="K-Factor bajo",
                    current_rate=k_factor,
                    severity="warning",
                    threshold=1.0,
                    tip="Incentiva a tus mejores clientes a compartir su codigo de referido. Ofrece descuentos o beneficios exclusivos.",
                )
            )

        nps_response_rate = data.get("nps_response_rate_pct", 0.0)
        surveys_sent = data.get("surveys_sent", 0)
        if surveys_sent > 0:
            if nps_response_rate < 15:
                bottlenecks.append(
                    BottleneckDTO(
                        type="low_nps_response",
                        metric_label="Pocas respuestas NPS",
                        current_rate=nps_response_rate,
                        severity="critical",
                        threshold=15,
                        tip="Envia mas encuestas de satisfaccion. Los clientes que responden tienden a ser tus mejores promotores.",
                    )
                )
            elif nps_response_rate < 30:
                bottlenecks.append(
                    BottleneckDTO(
                        type="low_nps_response",
                        metric_label="Pocas respuestas NPS",
                        current_rate=nps_response_rate,
                        severity="warning",
                        threshold=30,
                        tip="Envia mas encuestas de satisfaccion. Los clientes que responden tienden a ser tus mejores promotores.",
                    )
                )

        # 4. Assemble DTO
        now = dt_cls.now(UTC)

        result = EvangelizationDetailDTO(
            header_kpis=EvangelizationHeaderKpisDTO(**data["header_kpis"]),
            mini_funnel=MiniFunnelDTO(**data["mini_funnel"]),
            referidos=[EvangelistDTO(**e) for e in data.get("referidos", [])],
            candidatos=[CandidatoDTO(**c) for c in data.get("candidatos", [])],
            nps_summary=NpsSummaryDTO(**data["nps_summary"]),
            ugc_count=data.get("ugc_count", 0),
            ugc_written=data.get("ugc_written", 0),
            ugc_audio=data.get("ugc_audio", 0),
            bottlenecks=bottlenecks,
            period="last_30_days",
            last_updated=now.isoformat(),
        )

        # 5. Set cache
        if self.cache is not None:
            await self.cache.set(
                str(tenant_id),
                "evangelization",
                "last_30_days",
                result.model_dump(),
            )

        return result
