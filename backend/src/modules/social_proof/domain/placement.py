"""Placement domain entity — links a social-proof item to a surface."""

from __future__ import annotations

from typing import TYPE_CHECKING

from luana_core_platform.domain.base_entity import BaseEntity
from luana_core_social_proof.domain.enums import SourceTable, SurfaceType
from pydantic import model_validator

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

_SURFACES_REQUIRING_REF_ID: frozenset[SurfaceType] = frozenset(
    {
        SurfaceType.OFFER,
        SurfaceType.LANDING_PAGE,
        SurfaceType.EMAIL_SEQUENCE,
    },
)


class Placement(BaseEntity):
    """Records that a testimonial / authority / team_member is shown on a surface."""

    id: UUID
    tenant_id: UUID
    source_table: SourceTable
    source_id: UUID
    surface_type: SurfaceType
    surface_ref_id: UUID | None = None
    sort_order: int = 0
    is_visible: bool = True

    deleted_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def _validate_surface_ref_id(self) -> Placement:
        """Enforce ref_id presence rules per surface_type.

        brand_homepage and sales_agent_kb are tenant-wide; ref_id MUST be None.
        offer / landing_page / email_sequence point at a concrete row; ref_id required.
        """
        if self.surface_type in _SURFACES_REQUIRING_REF_ID:
            if self.surface_ref_id is None:
                msg = f"surface_ref_id is required when surface_type={self.surface_type.value!r}"
                raise ValueError(msg)
        elif self.surface_ref_id is not None:
            msg = f"surface_ref_id must be None when surface_type={self.surface_type.value!r} (tenant-wide surface)"
            raise ValueError(msg)
        return self
