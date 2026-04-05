"""Evangelization metrics repository -- CRM queries for Stage 7.

Queries ReferralCodeModel, NpsSurveyModel, NpsResponseModel, SaleModel,
and CustomerProfileModel for:
- Active evangelists with referral codes
- Per-evangelist referral stats (referrals_sent, conversions, revenue)
- K-Factor computation
- NPS summary (promoters, passives, detractors, response rate)
- Evangelist candidates (NPS >= 9, not yet EVANGELIST)
- UGC counts (testimonials with consent)
- MiniFunnel (Active Customers -> Evangelists)
- Referral revenue

All queries use SQLAlchemy 2.0 select() syntax with tenant_id isolation.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from src.modules.crm.infrastructure.models.customer_model import CustomerProfileModel
from src.modules.crm.infrastructure.models.nps_models import (
    NpsResponseModel,
    NpsSurveyModel,
)
from src.modules.crm.infrastructure.models.referral_code_model import ReferralCodeModel
from src.modules.crm.infrastructure.models.sale_model import SaleModel
from src.shared.domain.enums import LifecycleStage, SaleStatus


class EvangelizationRepository:
    """CRM aggregate queries for evangelization (Stage 7) metrics."""

    def __init__(self, db: Session):
        self.db = db

    async def get_evangelization_data(
        self, tenant_id: UUID, start_date: datetime, end_date: datetime
    ) -> dict:
        """Aggregate all evangelization data for the metrics endpoint.

        Returns dict with keys matching DTO structure:
        - header_kpis, mini_funnel, referidos, candidatos,
        - nps_summary, ugc_count, ugc_written, ugc_audio,
        - k_factor, nps_response_rate_pct, surveys_sent
        """
        # 1. Active evangelists with referral codes
        evangelists = self._get_active_evangelists(tenant_id)

        # 2. Per-evangelist referral stats
        referidos = []
        for ev in evangelists:
            stats = self._get_referral_stats_for_code(
                tenant_id, ev["code"], start_date, end_date
            )
            referidos.append(
                {
                    "customer_id": str(ev["customer_id"]),
                    "full_name": ev["full_name"] or "Sin nombre",
                    "referral_code": ev["code"],
                    "referrals_sent": stats["referrals_sent"],
                    "conversions": stats["conversions"],
                    "revenue_attributed": stats["revenue"],
                    "currency": stats["currency"],
                    "is_active": ev["is_active"],
                }
            )

        # 3. K-Factor
        k_factor_data = self._compute_k_factor(tenant_id, start_date, end_date)

        # 4. NPS summary
        nps_data = self._get_nps_summary(tenant_id)

        # 5. Evangelist candidates
        candidatos = self._get_evangelist_candidates(tenant_id)

        # 6. UGC counts
        ugc_data = self._get_ugc_counts(tenant_id)

        # 7. MiniFunnel
        mini_funnel = self._get_mini_funnel(tenant_id)

        # 8. Referral revenue
        referral_revenue = self._get_referral_revenue(tenant_id, start_date, end_date)

        # Assemble header KPIs
        header_kpis = {
            "k_factor": k_factor_data["k_factor"],
            "referral_conversions": k_factor_data["referral_conversions"],
            "nps_score": nps_data["nps_score"],
            "referral_revenue": referral_revenue["amount"],
            "currency": referral_revenue["currency"],
            "active_evangelists": len(evangelists),
        }

        return {
            "header_kpis": header_kpis,
            "mini_funnel": mini_funnel,
            "referidos": referidos,
            "candidatos": candidatos,
            "nps_summary": nps_data,
            "ugc_count": ugc_data["total"],
            "ugc_written": ugc_data["written"],
            "ugc_audio": ugc_data["audio"],
            "k_factor": k_factor_data["k_factor"],
            "nps_response_rate_pct": nps_data["response_rate_pct"],
            "surveys_sent": nps_data["surveys_sent"],
        }

    def _get_active_evangelists(self, tenant_id: UUID) -> list[dict]:
        """Get evangelists with active referral codes."""
        stmt = (
            select(
                CustomerProfileModel.id,
                CustomerProfileModel.full_name,
                ReferralCodeModel.code,
                ReferralCodeModel.is_active,
            )
            .join(
                ReferralCodeModel,
                CustomerProfileModel.id == ReferralCodeModel.customer_id,
            )
            .where(
                CustomerProfileModel.tenant_id == tenant_id,
                ReferralCodeModel.tenant_id == tenant_id,
                CustomerProfileModel.lifecycle_stage == LifecycleStage.EVANGELIST,
                ReferralCodeModel.is_active == True,  # noqa: E712
            )
        )
        results = self.db.execute(stmt).all()
        return [
            {
                "customer_id": row[0],
                "full_name": row[1],
                "code": row[2],
                "is_active": row[3],
            }
            for row in results
        ]

    def _get_referral_stats_for_code(
        self,
        tenant_id: UUID,
        referral_code: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """Get referral stats for a specific referral code.

        Counts sales where metadata_info->>'referral_code' matches.
        """
        # All sales attributed to this referral code
        stmt = (
            select(
                func.count(SaleModel.id).label("total"),
                func.count(SaleModel.id)
                .filter(SaleModel.status == SaleStatus.COMPLETED)
                .label("conversions"),
                func.coalesce(
                    func.sum(SaleModel.amount).filter(
                        SaleModel.status == SaleStatus.COMPLETED
                    ),
                    0.0,
                ).label("revenue"),
                SaleModel.currency,
            )
            .where(
                SaleModel.tenant_id == tenant_id,
                func.jsonb_extract_path_text(SaleModel.metadata_info, "referral_code")
                == referral_code,
            )
            .group_by(SaleModel.currency)
        )
        results = self.db.execute(stmt).all()

        if not results:
            return {
                "referrals_sent": 0,
                "conversions": 0,
                "revenue": 0.0,
                "currency": "MXN",
            }

        # Aggregate across currencies
        total_sent = sum(int(r[0]) for r in results)
        total_conversions = sum(int(r[1]) for r in results)
        total_revenue = sum(float(r[2]) for r in results)
        primary_currency = results[0][3] or "MXN"

        return {
            "referrals_sent": total_sent,
            "conversions": total_conversions,
            "revenue": total_revenue,
            "currency": primary_currency,
        }

    def _compute_k_factor(
        self, tenant_id: UUID, start_date: datetime, end_date: datetime
    ) -> dict:
        """Compute K-Factor for the period.

        K = (total_referrals_sent / evangelists_with_codes) *
            (referral_conversions / total_referrals_sent)

        With division-by-zero protection.
        """
        # Count active referral codes
        codes_stmt = select(func.count(ReferralCodeModel.id)).where(
            ReferralCodeModel.tenant_id == tenant_id,
            ReferralCodeModel.is_active == True,  # noqa: E712
        )
        evangelists_with_codes = self.db.execute(codes_stmt).scalar() or 0

        # Count all sales with referral_code in metadata_info within date range
        referral_sales_stmt = select(
            func.count(SaleModel.id).label("total"),
            func.count(SaleModel.id)
            .filter(SaleModel.status == SaleStatus.COMPLETED)
            .label("conversions"),
        ).where(
            SaleModel.tenant_id == tenant_id,
            SaleModel.occurred_at >= start_date,
            SaleModel.occurred_at <= end_date,
            func.jsonb_extract_path_text(
                SaleModel.metadata_info, "referral_code"
            ).isnot(None),
        )
        result = self.db.execute(referral_sales_stmt).first()
        total_referrals_sent = int(result[0]) if result else 0
        referral_conversions = int(result[1]) if result else 0

        # K = (total_referrals_sent / evangelists_with_codes) *
        #     (referral_conversions / total_referrals_sent)
        if evangelists_with_codes == 0 or total_referrals_sent == 0:
            k_factor = 0.0
        else:
            k_factor = round(
                (total_referrals_sent / evangelists_with_codes)
                * (referral_conversions / total_referrals_sent),
                2,
            )

        return {
            "k_factor": k_factor,
            "total_referrals_sent": total_referrals_sent,
            "referral_conversions": referral_conversions,
            "evangelists_with_codes": evangelists_with_codes,
        }

    def _get_nps_summary(self, tenant_id: UUID) -> dict:
        """Aggregate NPS data: score distribution, average, standard NPS, response rate."""
        # Count by score ranges using case expressions
        stmt = select(
            func.count(NpsResponseModel.id).label("total"),
            func.count(
                case(
                    (NpsResponseModel.score >= 9, NpsResponseModel.id),
                )
            ).label("promoters"),
            func.count(
                case(
                    (
                        and_(
                            NpsResponseModel.score >= 7,
                            NpsResponseModel.score <= 8,
                        ),
                        NpsResponseModel.id,
                    ),
                )
            ).label("passives"),
            func.count(
                case(
                    (NpsResponseModel.score <= 6, NpsResponseModel.id),
                )
            ).label("detractors"),
            func.avg(NpsResponseModel.score).label("avg_score"),
        ).where(NpsResponseModel.tenant_id == tenant_id)
        result = self.db.execute(stmt).first()

        total = int(result[0]) if result else 0
        promoters = int(result[1]) if result else 0
        passives = int(result[2]) if result else 0
        detractors = int(result[3]) if result else 0
        avg_score = (
            round(float(result[4]), 1) if result and result[4] is not None else None
        )

        # Standard NPS: ((promoters - detractors) / total) * 100
        standard_nps = None
        if total > 0:
            standard_nps = round(((promoters - detractors) / total) * 100, 1)

        # Surveys sent (non-pending)
        surveys_stmt = select(func.count(NpsSurveyModel.id)).where(
            NpsSurveyModel.tenant_id == tenant_id,
            NpsSurveyModel.status != "pending",
        )
        surveys_sent = self.db.execute(surveys_stmt).scalar() or 0

        # Response rate
        response_rate = (
            round((total / surveys_sent * 100), 1) if surveys_sent > 0 else 0.0
        )

        return {
            "nps_score": avg_score,
            "standard_nps": standard_nps,
            "promoter_count": promoters,
            "passive_count": passives,
            "detractor_count": detractors,
            "total_responses": total,
            "surveys_sent": surveys_sent,
            "response_rate_pct": response_rate,
        }

    def _get_evangelist_candidates(self, tenant_id: UUID) -> list[dict]:
        """Get customers with NPS >= 9 not yet EVANGELIST lifecycle stage."""
        stmt = (
            select(
                CustomerProfileModel.id,
                CustomerProfileModel.full_name,
                NpsResponseModel.score,
                NpsResponseModel.responded_at,
            )
            .join(
                CustomerProfileModel,
                NpsResponseModel.customer_id == CustomerProfileModel.id,
            )
            .where(
                NpsResponseModel.tenant_id == tenant_id,
                CustomerProfileModel.tenant_id == tenant_id,
                NpsResponseModel.score >= 9,
                CustomerProfileModel.lifecycle_stage != LifecycleStage.EVANGELIST,
            )
            .order_by(
                NpsResponseModel.score.desc(), NpsResponseModel.responded_at.desc()
            )
        )
        results = self.db.execute(stmt).all()
        return [
            {
                "customer_id": str(row[0]),
                "full_name": row[1] or "Sin nombre",
                "nps_score": int(row[2]),
                "responded_at": row[3].isoformat() if row[3] else None,
            }
            for row in results
        ]

    def _get_ugc_counts(self, tenant_id: UUID) -> dict:
        """Count UGC: testimonials with consent_public_use = true."""
        stmt = select(
            func.count(NpsResponseModel.id)
            .filter(
                NpsResponseModel.consent_public_use == True,  # noqa: E712
                NpsResponseModel.testimonial_text.isnot(None),
            )
            .label("written"),
            func.count(NpsResponseModel.id)
            .filter(
                NpsResponseModel.consent_public_use == True,  # noqa: E712
                NpsResponseModel.testimonial_audio_url.isnot(None),
            )
            .label("audio"),
        ).where(NpsResponseModel.tenant_id == tenant_id)
        result = self.db.execute(stmt).first()
        written = int(result[0]) if result else 0
        audio = int(result[1]) if result else 0

        return {
            "total": written + audio,
            "written": written,
            "audio": audio,
        }

    def _get_mini_funnel(self, tenant_id: UUID) -> dict:
        """MiniFunnel: Clientes Activos -> Evangelistas."""
        # Source: active customers (CUSTOMER or EVANGELIST, not inactive)
        source_stmt = select(func.count(CustomerProfileModel.id)).where(
            CustomerProfileModel.tenant_id == tenant_id,
            CustomerProfileModel.lifecycle_stage.in_(
                [
                    LifecycleStage.CUSTOMER,
                    LifecycleStage.EVANGELIST,
                ]
            ),
            CustomerProfileModel.is_inactive == False,  # noqa: E712
        )
        source_value = self.db.execute(source_stmt).scalar() or 0

        # Target: evangelists
        target_stmt = select(func.count(CustomerProfileModel.id)).where(
            CustomerProfileModel.tenant_id == tenant_id,
            CustomerProfileModel.lifecycle_stage == LifecycleStage.EVANGELIST,
        )
        target_value = self.db.execute(target_stmt).scalar() or 0

        conversion_rate = (
            round((target_value / source_value * 100), 1) if source_value > 0 else 0.0
        )

        return {
            "source_label": "Clientes Activos",
            "source_value": source_value,
            "target_label": "Evangelistas",
            "target_value": target_value,
            "conversion_rate": conversion_rate,
        }

    def _get_referral_revenue(
        self, tenant_id: UUID, start_date: datetime, end_date: datetime
    ) -> dict:
        """Sum revenue from completed sales with referral_code in metadata_info."""
        stmt = (
            select(
                func.coalesce(func.sum(SaleModel.amount), 0.0).label("amount"),
                SaleModel.currency,
            )
            .where(
                SaleModel.tenant_id == tenant_id,
                SaleModel.status == SaleStatus.COMPLETED,
                SaleModel.occurred_at >= start_date,
                SaleModel.occurred_at <= end_date,
                func.jsonb_extract_path_text(
                    SaleModel.metadata_info, "referral_code"
                ).isnot(None),
            )
            .group_by(SaleModel.currency)
        )
        results = self.db.execute(stmt).all()

        if not results:
            return {"amount": 0.0, "currency": "MXN"}

        total_amount = sum(float(r[0]) for r in results)
        primary_currency = results[0][1] or "MXN"

        return {"amount": total_amount, "currency": primary_currency}
