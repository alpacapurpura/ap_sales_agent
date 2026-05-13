"""CRM Contact Query Service — PR-10 PI-1 S4.

Read-only query service sobre customer_profiles + leads.
SQLA 2.0 async + tenant isolation en cada query.
Cross-module engagement lookup via CampaignsLookupPort (DDD boundary respetado).

Observability: structlog — NO incluye email/phone/telegram_id en logs (solo UUIDs).
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any
from uuid import UUID  # noqa: TC003 — UUID used in runtime signatures

import structlog
from luana_core_campaigns.application.dtos.pagination import PaginatedResponse
from luana_core_crm.api.dto.contacts import (
    ContactDetail,
    ContactIdentity,
    ContactListItem,
)
from luana_core_platform.infrastructure.models.crm import (
    CustomerIdentityModel,
    CustomerProfileModel,
    LeadModel,
)
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002 — used in runtime __init__ signature
from sqlalchemy.orm import load_only

if TYPE_CHECKING:
    from luana_core_crm.api.dto.contact_filters import ContactFilterParams
    from luana_core_platform.links.ports.campaigns import CampaignsLookupPort

logger = structlog.get_logger(__name__)

# ── Tipo utilitario ────────────────────────────────────────────────────────────

_SelectQuery = Select[tuple[CustomerProfileModel]]  # alias SQLA 2.0 tipado


class ContactQueryService:
    """Read-only query service sobre customer_profiles. SQLA 2.0 async.

    Tenant isolation: cada query filtra customer_profiles.tenant_id == tenant_id.
    """

    def __init__(
        self,
        session: AsyncSession,
        campaigns_lookup: CampaignsLookupPort,
        *,
        campaign_engagement_window_days: int = 90,
    ) -> None:
        """Inicializar servicio de consulta de contactos.

        Args:
            session: AsyncSession provista por el caller (scoped per-request).
            campaigns_lookup: Puerto cross-módulo para lookup de engagement.
            campaign_engagement_window_days: Ventana en días para considerar
                un lead como "engaged" con alguna campaña. Default: 90 días.
        """
        self._session = session
        self._campaigns_lookup = campaigns_lookup
        self._engagement_window_days = campaign_engagement_window_days

    async def list_contacts(
        self,
        *,
        tenant_id: UUID,
        filters: ContactFilterParams,
        limit: int,
        offset: int,
    ) -> PaginatedResponse[ContactListItem]:
        """Listar contactos paginados con filtros forward-compat.

        Aplica TODOS los filtros de ContactFilterParams. El filtro
        has_campaign_engagement usa 2-step batch para evitar N+1.

        Args:
            tenant_id: UUID del tenant (aislamiento obligatorio).
            filters: Parámetros de filtro del request.
            limit: Máximo de items a retornar (1..100).
            offset: Offset para paginación.

        Returns:
            PaginatedResponse con items, total_count, limit, offset, has_more.
        """
        t_start = time.perf_counter()

        # ── Step 1: construir query base con todos los filters MENOS engagement ──
        base_query = self._build_base_query(tenant_id=tenant_id, filters=filters)

        # ── Step 2: has_campaign_engagement — 2-step batch ────────────────────
        engagement_map: dict[UUID, object] | None = None

        if filters.has_campaign_engagement is not None:
            engagement_map = await self._resolve_engagement_filter(
                base_query=base_query,
                tenant_id=tenant_id,
                filters=filters,
            )

            engaged_profile_ids = set(engagement_map.keys())

            if filters.has_campaign_engagement is True:
                base_query = base_query.where(CustomerProfileModel.id.in_(engaged_profile_ids))
            else:
                base_query = base_query.where(CustomerProfileModel.id.not_in(engaged_profile_ids))

        # ── Step 3: count total ───────────────────────────────────────────────
        count_q = select(func.count()).select_from(base_query.subquery())
        total = (await self._session.execute(count_q)).scalar_one()

        # ── Step 4: page results ──────────────────────────────────────────────
        paged_q = (
            base_query.order_by(
                CustomerProfileModel.last_activity_at.desc().nulls_last(),
                CustomerProfileModel.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        page_rows = (await self._session.execute(paged_q)).scalars().all()

        # ── Step 5: enrich with lead channel presence ─────────────────────────
        # Cast ids to UUID — legacy Column[UUID] attrs in shared CRM models
        profile_ids: list[UUID] = [p.id for p in page_rows]  # type: ignore[misc]
        lead_presence = await self._get_lead_channel_presence(
            tenant_id=tenant_id,
            profile_ids=profile_ids,
        )

        # ── Step 6: to items ──────────────────────────────────────────────────
        items = [
            self._to_list_item(
                profile=p,
                lead_data=lead_presence.get(p.id),  # type: ignore[call-overload]
                engagement_map=engagement_map,
            )
            for p in page_rows
        ]

        filter_count = sum(1 for v in filters.model_dump().values() if v is not None)
        latency_ms = (time.perf_counter() - t_start) * 1000
        logger.info(
            "contact_query_listed",
            tenant_id=str(tenant_id),
            filter_count=filter_count,
            result_count=len(items),
            total_count=total,
            latency_ms=round(latency_ms, 1),
        )

        return PaginatedResponse(
            items=items,
            total_count=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        )

    async def get_contact_detail(
        self,
        *,
        tenant_id: UUID,
        contact_id: UUID,
    ) -> ContactDetail | None:
        """Obtener detalle completo de un contacto.

        Tenant isolation: si contact_id existe pero pertenece a otro tenant,
        retorna None (404 — no leakea existencia).

        Args:
            tenant_id: UUID del tenant (aislamiento obligatorio).
            contact_id: UUID del CustomerProfile.

        Returns:
            ContactDetail si encontrado y pertenece al tenant, None si no.
        """
        q = select(CustomerProfileModel).where(
            CustomerProfileModel.id == contact_id,
            CustomerProfileModel.tenant_id == tenant_id,
        )
        profile = (await self._session.execute(q)).scalars().first()

        if profile is None:
            logger.info(
                "contact_detail_fetched",
                tenant_id=str(tenant_id),
                contact_id=str(contact_id),
                found=False,
            )
            return None

        lead_q = (
            select(LeadModel)
            .where(
                LeadModel.customer_id == profile.id,
                LeadModel.tenant_id == tenant_id,
            )
            .order_by(LeadModel.created_at.desc())
            .limit(1)
        )
        lead = (await self._session.execute(lead_q)).scalars().first()

        identities_q = select(CustomerIdentityModel).where(
            CustomerIdentityModel.profile_id == profile.id,
            CustomerIdentityModel.tenant_id == tenant_id,
        )
        identities = (await self._session.execute(identities_q)).scalars().all()

        logger.info(
            "contact_detail_fetched",
            tenant_id=str(tenant_id),
            contact_id=str(contact_id),
            found=True,
        )

        return self._to_detail(
            profile=profile,
            lead=lead,
            identities=list(identities),
        )

    # ── Helpers privados ──────────────────────────────────────────────────────

    def _build_base_query(
        self,
        *,
        tenant_id: UUID,
        filters: ContactFilterParams,
    ) -> _SelectQuery:
        """Construir query base con todos los filtros excepto has_campaign_engagement.

        Dividido en sub-métodos para respetar McCabe ≤12 por función.
        """
        q = select(CustomerProfileModel).where(
            CustomerProfileModel.tenant_id == tenant_id,
        )
        q = self._apply_lifecycle_score_filters(q, filters)
        q = self._apply_identity_filters(q, tenant_id, filters)
        q = self._apply_channel_presence_filters(q, tenant_id, filters)
        q = self._apply_temporal_filters(q, filters)
        q = self._apply_geo_search_filters(q, tenant_id, filters)
        return q

    def _apply_lifecycle_score_filters(
        self,
        q: _SelectQuery,
        filters: ContactFilterParams,
    ) -> _SelectQuery:
        """Aplicar filtros de lifecycle stage y scoring."""
        if filters.lifecycle_stage_in is not None:
            q = q.where(CustomerProfileModel.lifecycle_stage.in_([s.value for s in filters.lifecycle_stage_in]))
        if filters.score_min is not None:
            q = q.where(CustomerProfileModel.lead_score >= filters.score_min)
        if filters.score_max is not None:
            q = q.where(CustomerProfileModel.lead_score <= filters.score_max)
        if filters.source_in is not None:
            q = q.where(CustomerProfileModel.lead_source.in_(filters.source_in))
        return q

    def _apply_identity_filters(
        self,
        q: _SelectQuery,
        tenant_id: UUID,
        filters: ContactFilterParams,
    ) -> _SelectQuery:
        """Aplicar filtros de presencia de email y teléfono (campos directos)."""
        if filters.has_email is True:
            q = q.where(CustomerProfileModel.primary_email.is_not(None))
        elif filters.has_email is False:
            q = q.where(CustomerProfileModel.primary_email.is_(None))

        if filters.has_phone is True:
            q = q.where(CustomerProfileModel.primary_phone.is_not(None))
        elif filters.has_phone is False:
            q = q.where(CustomerProfileModel.primary_phone.is_(None))

        return q

    def _apply_channel_exists(
        self,
        q: _SelectQuery,
        tenant_id: UUID,
        channel_col: Any,  # noqa: ANN401  # SQLA legacy Column — typed as Any pragmatically
        flag: bool | None,
    ) -> _SelectQuery:
        """Aplicar filtro EXISTS para un canal de Lead (telegram, whatsapp, etc.)."""
        if flag is None:
            return q
        exists_q = (
            select(LeadModel.id)
            .where(
                LeadModel.customer_id == CustomerProfileModel.id,
                LeadModel.tenant_id == tenant_id,
                channel_col.is_not(None),
            )
            .exists()
        )
        return q.where(exists_q) if flag is True else q.where(~exists_q)

    def _apply_channel_presence_filters(
        self,
        q: _SelectQuery,
        tenant_id: UUID,
        filters: ContactFilterParams,
    ) -> _SelectQuery:
        """Aplicar filtros de presencia de canales via correlated EXISTS sobre leads."""
        q = self._apply_channel_exists(q, tenant_id, LeadModel.telegram_id, filters.has_telegram_id)
        q = self._apply_channel_exists(q, tenant_id, LeadModel.whatsapp_id, filters.has_whatsapp_id)
        q = self._apply_channel_exists(q, tenant_id, LeadModel.instagram_id, filters.has_instagram_id)
        q = self._apply_channel_exists(q, tenant_id, LeadModel.tiktok_id, filters.has_tiktok_id)
        return q

    def _apply_temporal_filters(
        self,
        q: _SelectQuery,
        filters: ContactFilterParams,
    ) -> _SelectQuery:
        """Aplicar filtros temporales (fechas creación y actividad, inactividad)."""
        if filters.created_after is not None:
            q = q.where(CustomerProfileModel.created_at >= filters.created_after)
        if filters.created_before is not None:
            q = q.where(CustomerProfileModel.created_at <= filters.created_before)
        if filters.last_activity_after is not None:
            q = q.where(CustomerProfileModel.last_activity_at >= filters.last_activity_after)
        if filters.last_activity_before is not None:
            q = q.where(CustomerProfileModel.last_activity_at <= filters.last_activity_before)
        if filters.is_inactive is not None:
            q = q.where(CustomerProfileModel.is_inactive == filters.is_inactive)
        return q

    def _apply_geo_search_filters(
        self,
        q: _SelectQuery,
        tenant_id: UUID,
        filters: ContactFilterParams,
    ) -> _SelectQuery:
        """Aplicar filtros de país y búsqueda textual."""
        if filters.country_in is not None:
            country_exists_q = (
                select(LeadModel.id)
                .where(
                    LeadModel.customer_id == CustomerProfileModel.id,
                    LeadModel.tenant_id == tenant_id,
                    LeadModel.country.in_(filters.country_in),
                )
                .exists()
            )
            q = q.where(country_exists_q)

        if filters.q is not None and filters.q.strip():
            pattern = f"%{filters.q.strip()}%"
            q = q.where(
                or_(
                    CustomerProfileModel.full_name.ilike(pattern),
                    CustomerProfileModel.primary_email.ilike(pattern),
                    CustomerProfileModel.primary_phone.ilike(pattern),
                )
            )
        return q

    async def _resolve_engagement_filter(
        self,
        *,
        base_query: _SelectQuery,
        tenant_id: UUID,
        filters: ContactFilterParams,
    ) -> dict[UUID, object]:
        """2-step batch engagement lookup.

        Step A: IDs de todos los profiles candidatos (con otros filtros, sin limit).
        Step B: Lead IDs → CampaignsLookupPort batch lookup (90d window).

        Returns:
            Mapa profile_id → CampaignTaskLookupResult para profiles engaged.
        """
        # Step A: todos los profile_ids candidatos (sin limit)
        # legacy Column[UUID] attrs — cast via type: ignore
        id_only_q = base_query.options(load_only(CustomerProfileModel.id))  # type: ignore[arg-type]
        candidate_profiles = (await self._session.execute(id_only_q)).scalars().all()
        candidate_profile_ids: list[UUID] = [p.id for p in candidate_profiles]  # type: ignore[misc]

        if not candidate_profile_ids:
            return {}

        # Step B: Lead IDs para los profiles candidatos
        leads_q = select(LeadModel.id, LeadModel.customer_id).where(
            LeadModel.tenant_id == tenant_id,
            LeadModel.customer_id.in_(candidate_profile_ids),
        )
        leads_rows = (await self._session.execute(leads_q)).all()
        all_lead_ids: list[UUID] = [row.id for row in leads_rows]

        if not all_lead_ids:
            return {}

        window_hours = self._engagement_window_days * 24
        engagement_map = await self._campaigns_lookup.find_recent_campaign_tasks_for_leads(
            tenant_id=tenant_id,
            lead_ids=all_lead_ids,
            window_hours=window_hours,
            session=self._session,
        )

        lead_id_to_profile_id: dict[UUID, UUID] = {row.id: row.customer_id for row in leads_rows}

        profile_engagement: dict[UUID, object] = {}
        for lead_id, result in engagement_map.items():
            profile_id = lead_id_to_profile_id.get(lead_id)
            if profile_id is not None:
                profile_engagement[profile_id] = result

        return profile_engagement

    async def _get_lead_channel_presence(
        self,
        *,
        tenant_id: UUID,
        profile_ids: list[UUID],
    ) -> dict[UUID, LeadModel]:
        """Obtener el Lead más reciente por profile para presencia de canales.

        Returns:
            Mapa profile_id → LeadModel (solo el más reciente si hay múltiples).
        """
        if not profile_ids:
            return {}

        leads_q = (
            select(LeadModel)
            .where(
                LeadModel.tenant_id == tenant_id,
                LeadModel.customer_id.in_(profile_ids),
            )
            .order_by(LeadModel.created_at.desc())
        )
        all_leads = (await self._session.execute(leads_q)).scalars().all()

        presence: dict[UUID, LeadModel] = {}
        for lead in all_leads:
            if lead.customer_id not in presence:
                presence[lead.customer_id] = lead  # type: ignore[index]

        return presence

    def _to_list_item(
        self,
        *,
        profile: CustomerProfileModel,
        lead_data: LeadModel | None,
        engagement_map: dict[UUID, object] | None,
    ) -> ContactListItem:
        """Mapear CustomerProfileModel + LeadModel a ContactListItem.

        Nota: los modelos CRM usan Column() legacy (no Mapped[]) — cast a Any
        para mapeo seguro. El runtime de Pydantic valida types correctamente.
        """
        # Cast to Any — legacy Column() defs en shared/infrastructure/models/crm.py
        p: Any = profile
        ld: Any = lead_data

        has_recent_engagement: bool | None = None
        if engagement_map is not None:
            has_recent_engagement = p.id in engagement_map

        return ContactListItem(
            id=p.id,
            full_name=p.full_name,
            primary_email=p.primary_email,
            primary_phone=p.primary_phone,
            lifecycle_stage=p.lifecycle_stage,
            lead_score=p.lead_score or 0.0,
            is_inactive=p.is_inactive or False,
            last_activity_at=p.last_activity_at,
            lead_source=p.lead_source,
            country=ld.country if ld else None,
            has_telegram_id=bool(ld and ld.telegram_id),
            has_whatsapp_id=bool(ld and ld.whatsapp_id),
            has_instagram_id=bool(ld and ld.instagram_id),
            has_tiktok_id=bool(ld and ld.tiktok_id),
            has_email=bool(p.primary_email),
            has_phone=bool(p.primary_phone),
            has_recent_campaign_engagement=has_recent_engagement,
            created_at=p.created_at,
        )

    def _to_detail(
        self,
        *,
        profile: CustomerProfileModel,
        lead: LeadModel | None,
        identities: list[CustomerIdentityModel],
    ) -> ContactDetail:
        """Mapear models a ContactDetail.

        Nota: los modelos CRM usan Column() legacy (no Mapped[]) — cast a Any
        para mapeo seguro. El runtime de Pydantic valida types correctamente.
        """
        # Cast to Any — legacy Column() defs en shared/infrastructure/models/crm.py
        p: Any = profile
        lx: Any = lead

        identity_items = [
            ContactIdentity(
                type=str(identity.type),
                value=str(identity.value),
                is_primary=bool(identity.is_primary),
                verification_status=str(identity.verification_status or "unverified"),
                last_seen_at=identity.last_seen_at,  # type: ignore[arg-type]
            )
            for identity in identities
        ]

        return ContactDetail(
            id=p.id,
            full_name=p.full_name,
            primary_email=p.primary_email,
            primary_phone=p.primary_phone,
            lifecycle_stage=p.lifecycle_stage,
            lead_score=p.lead_score or 0.0,
            rfm_segment=p.rfm_segment,
            lifetime_value=p.lifetime_value or 0.0,
            is_inactive=p.is_inactive or False,
            first_conversion_at=p.first_conversion_at,
            first_seen_at=p.first_seen_at,
            last_activity_at=p.last_activity_at,
            lead_source=p.lead_source,
            lead_source_detail=p.lead_source_detail,
            traits=p.traits or {},
            computed_traits=p.computed_traits or {},
            created_at=p.created_at,
            updated_at=p.updated_at,
            lead_id=lx.id if lx else None,
            telegram_id=lx.telegram_id if lx else None,
            whatsapp_id=lx.whatsapp_id if lx else None,
            instagram_id=lx.instagram_id if lx else None,
            tiktok_id=lx.tiktok_id if lx else None,
            api_id=lx.api_id if lx else None,
            fit_score=lx.fit_score if lx else None,
            intent_score=lx.intent_score if lx else None,
            temperature=lx.temperature if lx else None,
            is_blacklisted=lx.is_blacklisted if lx else None,
            last_interaction_date=lx.last_interaction_date if lx else None,
            country=lx.country if lx else None,
            conversation_summary=lx.conversation_summary if lx else None,
            identities=identity_items,
        )
