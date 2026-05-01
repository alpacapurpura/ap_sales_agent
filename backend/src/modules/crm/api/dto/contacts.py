"""CRM contacts DTOs — response schemas para /api/v1/contacts/*.

PR-10 PI-1 S4: Forward-compat schemas. UI lite usa subset; PI-3 reusan
el mismo schema sin modificar BE.

PII: ContactListItem y ContactDetail exponen email/phone porque la UI tabla
los muestra explícitamente (caso de uso visualización user-facing documentado).
Logs NO incluyen estos campos (solo UUIDs).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.shared.domain.enums import LifecycleStage


class ContactListItem(BaseModel):
    """Subset de campos para tabla principal lite.

    PI-3 expande agregando columnas adicionales sin cambiar este schema.
    PII: email/phone expuestos porque la UI tabla los visualiza (uso legítimo).
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    full_name: str | None
    # PII: email visible en tabla UI — uso legítimo visualización del dueño del negocio.
    primary_email: str | None
    # PII: teléfono visible en tabla UI — uso legítimo visualización del dueño del negocio.
    primary_phone: str | None
    lifecycle_stage: LifecycleStage
    lead_score: float
    is_inactive: bool
    last_activity_at: datetime | None
    lead_source: str | None
    country: str | None
    # Channel identifiers (presencia booleana; valor real solo en Detail)
    has_telegram_id: bool
    has_whatsapp_id: bool
    has_instagram_id: bool
    has_tiktok_id: bool
    has_email: bool
    has_phone: bool
    # Campaign engagement summary (None = no se aplicó lookup; bool = computado si filter aplicado)
    has_recent_campaign_engagement: bool | None
    created_at: datetime


class ContactIdentity(BaseModel):
    """Multi-channel identifier — subset seguro para serialización.

    PII: 'value' puede contener email/teléfono. Expuesto en Detail porque
    el owner del negocio consulta sus propios contactos.
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    type: str  # IdentityType.value
    # PII: valor de identidad (email, phone, etc.) — expuesto en Detail, uso legítimo owner.
    value: str
    is_primary: bool
    verification_status: str
    last_seen_at: datetime


class ContactDetail(BaseModel):
    """Detail rico — drawer hoy + página completa PI-3 usan el MISMO schema.

    PII: múltiples campos PII expuestos. Scope: dueño del negocio consultando
    su propia base de contactos. Logs de auditoría NO incluyen estos valores.
    """

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    full_name: str | None
    # PII: email del contacto — expuesto en Detail, uso legítimo owner negocio.
    primary_email: str | None
    # PII: teléfono del contacto — expuesto en Detail, uso legítimo owner negocio.
    primary_phone: str | None
    lifecycle_stage: LifecycleStage
    lead_score: float
    rfm_segment: str | None
    lifetime_value: float
    is_inactive: bool
    first_conversion_at: datetime | None
    first_seen_at: datetime | None
    last_activity_at: datetime | None
    lead_source: str | None
    lead_source_detail: str | None
    traits: dict[str, object]
    computed_traits: dict[str, object]
    created_at: datetime
    updated_at: datetime | None

    # Lead-level data (None si no hay Lead row asociado)
    lead_id: UUID | None
    # PII: IDs de canales — expuesto en Detail, uso legítimo owner negocio.
    telegram_id: str | None
    whatsapp_id: str | None
    instagram_id: str | None
    tiktok_id: str | None
    api_id: str | None
    fit_score: int | None
    intent_score: int | None
    temperature: str | None
    is_blacklisted: bool | None
    last_interaction_date: datetime | None
    country: str | None
    conversation_summary: str | None

    # Multi-channel identities (CustomerIdentityModel)
    identities: list[ContactIdentity]


class DeferredEndpointResponse(BaseModel):
    """Schema canonical para endpoints declarados pero deferred PI-3.

    Retornado con HTTP 501. Permite al FE detectar el estado y mostrar
    mensaje apropiado. canonical_path documenta la URL que retornará 200 en PI-3.
    """

    model_config = ConfigDict(extra="forbid")

    detail: str
    deferred_until: str  # "PI-3"
    canonical_path: str
    expected_response_model: str  # nombre de la clase Pydantic que retornará 200 (info doc)


class FilterFieldMeta(BaseModel):
    """Metadata de un campo de filtro para construcción dinámica de UI."""

    model_config = ConfigDict(extra="forbid")

    name: str
    type: str  # "enum_list" | "int_range" | "bool" | "datetime" | "string"
    enum_values: list[str] | None
    description: str | None


class FilterSchemaResponse(BaseModel):
    """Respuesta del endpoint _filter-schema — metadata para UI dinámica de filtros."""

    model_config = ConfigDict(extra="forbid")

    version: str  # "1.0" — bump cuando shape cambia
    fields: list[FilterFieldMeta]
