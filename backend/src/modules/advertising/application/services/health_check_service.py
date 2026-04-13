"""Compute the Meta Ads account health check.

This service consolidates three signals:
- Campaign objectives (what Meta is optimizing for)
- Active associations (what the tenant expects to see)
- Recent metrics (whether reality matches expectations)

Output is a MetaHealthCheckDTO with a human-readable narrative, active
campaigns annotated with their expected outcomes, offer coverage, unassigned
targets, and actionable recommendations.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

from src.modules.advertising.application.dto.association_dto import AssociationDTO
from src.modules.advertising.application.dto.health_check_dto import (
    CampaignHealthDTO,
    MetaHealthCheckDTO,
    OfferCoverageDTO,
    RecommendationDTO,
    UnassignedTargetDTO,
)
from src.modules.advertising.domain.enums import (
    OfferExpectedMetric,
    expected_metric_for_objective,
    expected_metric_label_es,
    objective_label_es,
    resolve_expected_metric,
)
from src.modules.advertising.infrastructure.repositories.association_repository import (
    AssociationRepository,
)
from src.modules.advertising.infrastructure.repositories.meta_catalog_repository import (
    CampaignSnapshot,
    MetaCatalogRepository,
)
from src.modules.advertising.infrastructure.repositories.metrics_repository import (
    MetricsRepository,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.modules.advertising.infrastructure.models.ad_offer_association_model import (
        AdOfferAssociationModel,
    )
    from src.shared.domain.ports import OfferReadDTO, OfferReadPort

ACTIVE_STATUSES = {"ACTIVE", "LIMITED"}
BROKEN_EXPECTATION_DAYS = 7
PURCHASE_METRICS = {"conversions", "meta_purchase_roas"}


class HealthCheckService:
    """Build the MetaHealthCheckDTO for a tenant."""

    def __init__(self, db: Session, offer_read_port: OfferReadPort) -> None:
        self._db = db
        self._offer_read_port = offer_read_port
        self._catalog_repo = MetaCatalogRepository(db)
        self._association_repo = AssociationRepository(db)
        self._metrics_repo = MetricsRepository(db)

    async def run(self, tenant_id: UUID) -> MetaHealthCheckDTO:
        catalog = self._catalog_repo.load(tenant_id)
        all_offers = await self._offer_read_port.get_offers_by_tenant(tenant_id)
        active_offers = [
            o for o in all_offers if (o.status or "active") not in {"archived", "draft"}
        ]
        associations = self._association_repo.list_active(tenant_id)
        assoc_by_target: dict[tuple[str, str], AdOfferAssociationModel] = {
            (a.target_type, a.target_external_id): a for a in associations
        }
        offer_by_id = {o.id: o for o in active_offers}

        # 1) Active campaigns annotated with health info
        active_campaigns_health: list[CampaignHealthDTO] = []
        for campaign in catalog.campaigns:
            if (campaign.effective_status or "").upper() not in ACTIVE_STATUSES:
                continue
            active_campaigns_health.append(
                self._build_campaign_health(
                    campaign=campaign,
                    tenant_id=tenant_id,
                    assoc_by_target=assoc_by_target,
                    offer_by_id=offer_by_id,
                )
            )

        # 2) Offer coverage
        offers_coverage = self._build_offer_coverage(active_offers, associations)

        # 3) Unassigned targets (ACTIVE only, excludes anything with association)
        unassigned = self._collect_unassigned(catalog, assoc_by_target)

        # 4) Recommendations
        recommendations = self._build_recommendations(
            active_campaigns_health=active_campaigns_health,
            offers_coverage=offers_coverage,
            unassigned=unassigned,
        )

        overall_status, summary_text = self._derive_status(
            active_campaigns_health=active_campaigns_health,
            offers_coverage=offers_coverage,
            unassigned=unassigned,
            recommendations=recommendations,
        )

        return MetaHealthCheckDTO(
            overall_status=overall_status,
            active_campaigns=active_campaigns_health,
            offers_coverage=offers_coverage,
            unassigned_targets=unassigned,
            recommendations=recommendations,
            summary_text=summary_text,
        )

    # ── builders ───────────────────────────────────────────────────────────
    def _build_campaign_health(
        self,
        *,
        campaign: CampaignSnapshot,
        tenant_id: UUID,
        assoc_by_target: dict[tuple[str, str], AdOfferAssociationModel],
        offer_by_id: dict[UUID, OfferReadDTO],
    ) -> CampaignHealthDTO:
        assoc_model = assoc_by_target.get(("campaign", campaign.external_id))
        assoc_dto = (
            _association_to_dto(assoc_model, offer_by_id) if assoc_model else None
        )

        expected = expected_metric_for_objective(campaign.objective)
        expected_es = self._expected_outcome_text(campaign.objective, expected)

        has_issue = False
        issue_text: str | None = None

        if expected == OfferExpectedMetric.PURCHASE and not self._has_recent_purchases(
            tenant_id, campaign.external_id
        ):
            has_issue = True
            issue_text = (
                "Esta campaña busca ventas pero no registramos ninguna compra "
                "en los últimos 7 días. Revisá la configuración del píxel."
            )

        return CampaignHealthDTO(
            external_id=campaign.external_id,
            name=campaign.name,
            objective=campaign.objective,
            objective_label_es=objective_label_es(campaign.objective),
            status=campaign.effective_status,
            offer_association=assoc_dto,
            expected_outcome_es=expected_es,
            has_issue=has_issue,
            issue_text=issue_text,
        )

    def _build_offer_coverage(
        self,
        offers: list[OfferReadDTO],
        associations: list[AdOfferAssociationModel],
    ) -> list[OfferCoverageDTO]:
        assoc_by_offer: dict[UUID, list[AdOfferAssociationModel]] = {}
        for a in associations:
            if a.offer_id is None:
                continue
            assoc_by_offer.setdefault(a.offer_id, []).append(a)

        coverage: list[OfferCoverageDTO] = []
        offer_by_id = {o.id: o for o in offers}
        for offer in offers:
            expected = resolve_expected_metric(
                archetype=offer.offer_type,
                onboarding_action=offer.onboarding_action,
                is_lead_magnet=offer.is_lead_magnet,
                has_checkout_url=bool(offer.checkout_page_url),
            )
            targets = assoc_by_offer.get(offer.id, [])
            dtos = [_association_to_dto(t, offer_by_id) for t in targets]
            coverage.append(
                OfferCoverageDTO(
                    offer_id=offer.id,
                    offer_name=offer.public_name,
                    archetype=offer.offer_type,
                    expected_metric=expected.value,
                    expected_metric_label_es=expected_metric_label_es(expected.value),
                    has_active_campaign=bool(targets),
                    associated_targets=dtos,
                )
            )
        return coverage

    def _collect_unassigned(
        self,
        catalog,
        assoc_by_target: dict[tuple[str, str], AdOfferAssociationModel],
    ) -> list[UnassignedTargetDTO]:
        out: list[UnassignedTargetDTO] = []
        for campaign in catalog.campaigns:
            if (campaign.effective_status or "").upper() not in ACTIVE_STATUSES:
                continue
            if ("campaign", campaign.external_id) in assoc_by_target:
                continue
            out.append(
                UnassignedTargetDTO(
                    target_type="campaign",
                    external_id=campaign.external_id,
                    name=campaign.name,
                    objective=campaign.objective,
                    status=campaign.effective_status,
                )
            )
        return out

    def _build_recommendations(
        self,
        *,
        active_campaigns_health: list[CampaignHealthDTO],
        offers_coverage: list[OfferCoverageDTO],
        unassigned: list[UnassignedTargetDTO],
    ) -> list[RecommendationDTO]:
        out: list[RecommendationDTO] = []

        # Broken expectations → critical
        out.extend(
            RecommendationDTO(
                type="configure_pixel",
                severity="critical",
                title=f"Revisá el píxel de '{c.name}'",
                body=c.issue_text,
                action_label="Diagnosticar píxel",
                action_url=None,
                related_offer_id=None,
                related_target_id=c.external_id,
            )
            for c in active_campaigns_health
            if c.has_issue and c.issue_text
        )

        # Offers without campaigns → warning
        out.extend(
            RecommendationDTO(
                type="create_campaign",
                severity="warning",
                title=f"'{cov.offer_name}' no tiene campaña activa",
                body=(
                    f"Esta offer espera generar "
                    f"{cov.expected_metric_label_es.lower()}s "
                    f"pero no tenés ninguna campaña asociada. Creá una "
                    f"campaña con el objetivo correcto para empezar a "
                    f"medirla."
                ),
                action_label="Crear campaña",
                action_url=None,
                related_offer_id=cov.offer_id,
                related_target_id=None,
            )
            for cov in offers_coverage
            if not cov.has_active_campaign
        )

        # Unassigned active targets → info
        if unassigned:
            out.append(
                RecommendationDTO(
                    type="assign_offer",
                    severity="info",
                    title=f"Tenés {len(unassigned)} campaña(s) sin offer asignada",
                    body=(
                        "Asociá cada campaña activa con la offer que promociona "
                        "(o marcala como branding) para ver métricas agrupadas por producto."
                    ),
                    action_label="Asociar campañas",
                    action_url=None,
                    related_offer_id=None,
                    related_target_id=None,
                )
            )

        # Objective mismatch per covered offer
        for cov in offers_coverage:
            if not cov.has_active_campaign or not cov.associated_targets:
                continue
            for target in cov.associated_targets:
                if target.target_type != "campaign":
                    continue
                campaign_health = next(
                    (
                        c
                        for c in active_campaigns_health
                        if c.external_id == target.target_external_id
                    ),
                    None,
                )
                if campaign_health is None:
                    continue
                campaign_expected = expected_metric_for_objective(
                    campaign_health.objective
                )
                if (
                    campaign_expected is not None
                    and campaign_expected.value != cov.expected_metric
                ):
                    out.append(
                        RecommendationDTO(
                            type="fix_objective",
                            severity="warning",
                            title=(
                                f"La campaña de '{cov.offer_name}' tiene el "
                                f"objetivo equivocado"
                            ),
                            body=(
                                f"'{cov.offer_name}' espera {cov.expected_metric_label_es.lower()}, "
                                f"pero la campaña '{campaign_health.name}' está buscando "
                                f"{expected_metric_label_es(campaign_expected.value).lower()}. "
                                f"Cambiá el objetivo para medirla correctamente."
                            ),
                            action_label="Cambiar objetivo",
                            action_url=None,
                            related_offer_id=cov.offer_id,
                            related_target_id=campaign_health.external_id,
                        )
                    )

        return out

    def _derive_status(
        self,
        *,
        active_campaigns_health,
        offers_coverage,
        unassigned,
        recommendations,
    ) -> tuple[str, str]:
        critical = any(r.severity == "critical" for r in recommendations)
        warnings = [r for r in recommendations if r.severity == "warning"]
        if critical:
            status = "critical"
            summary = (
                "Tu cuenta tiene problemas críticos de configuración que están "
                "afectando la medición de resultados."
            )
        elif warnings:
            status = "needs_attention"
            summary = (
                f"Tu cuenta está operativa pero hay {len(warnings)} ajuste(s) "
                f"pendiente(s) para obtener métricas completas."
            )
        elif unassigned:
            status = "needs_attention"
            summary = (
                f"Todo funciona, pero tenés {len(unassigned)} campaña(s) sin asociar "
                f"a una offer. Asignalas para ver mejor tus métricas."
            )
        else:
            status = "healthy"
            if not active_campaigns_health:
                summary = "No tenés campañas activas ahora mismo."
            else:
                summary = (
                    f"{len(active_campaigns_health)} campaña(s) activa(s), "
                    f"todo correctamente configurado."
                )
        return status, summary

    # ── helpers ────────────────────────────────────────────────────────────
    def _expected_outcome_text(
        self, objective: str | None, expected: OfferExpectedMetric | None
    ) -> str:
        if not objective:
            return "Sin objetivo definido."
        label = objective_label_es(objective)
        if expected is None:
            upper = objective.upper()
            if upper == "OUTCOME_TRAFFIC":
                return "Esperá: visitas a tu landing, CTR alto, CPC bajo. NO esperés: ventas atribuidas ni mensajes."
            if upper == "OUTCOME_ENGAGEMENT":
                return "Esperá: likes, comentarios, shares. NO esperés: clicks a tu web ni conversiones."
            if upper in {"OUTCOME_AWARENESS", "REACH", "BRAND_AWARENESS"}:
                return "Esperá: alcance amplio y frecuencia controlada. NO esperés: clicks ni conversiones."
            return f"Objetivo: {label}."
        if expected == OfferExpectedMetric.PURCHASE:
            return (
                "Esperá: ventas atribuidas y ROAS medible (requiere píxel configurado)."
            )
        if expected == OfferExpectedMetric.LEAD:
            return "Esperá: leads capturados (formulario o suscripción)."
        if expected == OfferExpectedMetric.MESSAGE:
            return "Esperá: conversaciones iniciadas por DM o Messenger."
        return f"Objetivo: {label}."

    def _has_recent_purchases(self, tenant_id: UUID, campaign_external_id: str) -> bool:
        today = date.today()
        start = today - timedelta(days=BROKEN_EXPECTATION_DAYS)
        rows = self._metrics_repo.load_rows(
            tenant_id,
            start_date=start,
            end_date=today,
            metric_names=list(PURCHASE_METRICS),
        )
        return any(r.campaign_id == campaign_external_id and r.value > 0 for r in rows)


def _association_to_dto(
    row: AdOfferAssociationModel,
    offer_by_id: dict[UUID, OfferReadDTO],
) -> AssociationDTO:
    offer = offer_by_id.get(row.offer_id) if row.offer_id else None
    return AssociationDTO(
        id=row.id,
        tenant_id=row.tenant_id,
        target_type=row.target_type,  # type: ignore[arg-type]
        target_external_id=row.target_external_id,
        offer_id=row.offer_id,
        offer_name=offer.public_name if offer else None,
        offer_archetype=offer.offer_type if offer else None,
        association_type=row.association_type,
        confidence=row.confidence,
        notes=row.notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


__all__ = ["HealthCheckService"]
