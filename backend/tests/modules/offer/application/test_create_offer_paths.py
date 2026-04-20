"""Sprint 15.2 — regression tests for the three ``OfferService.create_offer`` paths.

The wizard now drives three distinct creation flows:

1. **Preset path** (~95%): wizard sends ``preset_id`` and the service derives
   ``archetype`` + ``value_level`` from ``OFFER_TYPE_PRESET_CATALOG``.
2. **Custom (Otra / A medida) path**: wizard sends ``archetype`` + explicit
   ``value_level``, no ``preset_id``. The legacy archetype-only path handles it.
3. **Lead-magnet preset path**: ``IS_LEAD_MAGNET`` flag forces
   ``value_level=LEAD_MAGNET`` and ``is_lead_magnet=True`` regardless of input.

Each path is asserted end-to-end at the service layer (no API roundtrip) so
the dashboard ladder grouping always lands the offer on the right rung.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.offer.application.offer_service import OfferService
from src.modules.offer.domain.enums import OfferArchetype, OfferValueLevel

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session


class TestPresetPath:
    """When ``preset_id`` is provided, archetype and value_level are derived."""

    def test_preset_drives_archetype_and_value_level(self, db: Session, tenant_a: uuid.UUID) -> None:
        svc = OfferService(db)
        # coach_paquete_sesiones is TRANSFORMACION + PROGRAMA per the catalog.
        offer = svc.create_offer(
            name="Mi paquete coaching",
            tenant_id=tenant_a,
            preset_id="coach_paquete_sesiones",
        )
        assert offer.archetype is OfferArchetype.PROGRAMA
        assert offer.value_level is OfferValueLevel.TRANSFORMACION
        assert offer.is_lead_magnet is False
        assert offer.preset_id == "coach_paquete_sesiones"

    def test_preset_lead_magnet_forces_lead_magnet_flag(self, db: Session, tenant_a: uuid.UUID) -> None:
        svc = OfferService(db)
        # coach_challenge_gratis carries IS_LEAD_MAGNET in default_flags.
        offer = svc.create_offer(
            name="Mi challenge",
            tenant_id=tenant_a,
            preset_id="coach_challenge_gratis",
        )
        assert offer.is_lead_magnet is True
        assert offer.value_level is OfferValueLevel.LEAD_MAGNET

    def test_preset_overrides_caller_value_level(self, db: Session, tenant_a: uuid.UUID) -> None:
        """Caller-supplied value_level is honored when preset doesn't specify
        IS_LEAD_MAGNET — but the preset's typical_value_level is the fallback
        when the caller passes None.
        """
        svc = OfferService(db)
        offer = svc.create_offer(
            name="Override test",
            tenant_id=tenant_a,
            preset_id="coach_sesion_unica",  # ACTIVACION typical
            value_level=OfferValueLevel.MAXIMIZACION,  # caller wants premium
        )
        # Caller wins — preset's typical_value_level only fills when None.
        assert offer.value_level is OfferValueLevel.MAXIMIZACION


class TestCustomPath:
    """Sprint 15.2 — Otra / A medida flow: no preset, explicit archetype + rung."""

    def test_custom_archetype_only_with_explicit_value_level(self, db: Session, tenant_a: uuid.UUID) -> None:
        svc = OfferService(db)
        offer = svc.create_offer(
            name="Mi programa custom",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PROGRAMA,
            value_level=OfferValueLevel.MAXIMIZACION,
        )
        assert offer.preset_id is None
        assert offer.archetype is OfferArchetype.PROGRAMA
        assert offer.value_level is OfferValueLevel.MAXIMIZACION
        assert offer.is_lead_magnet is False

    def test_custom_corporativo_landing_on_corporativo_rung(self, db: Session, tenant_a: uuid.UUID) -> None:
        """Regression: the user picks Otra in the Corporativo group → the
        offer must persist as CORPORATIVO, not silently fallback to ACTIVACION.
        This was the bug that motivated Sprint 15.
        """
        svc = OfferService(db)
        offer = svc.create_offer(
            name="Convenio empresarial custom",
            tenant_id=tenant_a,
            archetype=OfferArchetype.MEMBRESIA,
            value_level=OfferValueLevel.CORPORATIVO,
        )
        assert offer.value_level is OfferValueLevel.CORPORATIVO
        assert offer.preset_id is None

    def test_custom_lead_magnet_rung_forces_is_lead_magnet(self, db: Session, tenant_a: uuid.UUID) -> None:
        """When the user picks Otra in the Lead Magnet group, the wizard
        passes value_level=LEAD_MAGNET. The service normalizes
        is_lead_magnet=True to keep the invariant in sync.
        """
        svc = OfferService(db)
        offer = svc.create_offer(
            name="Mi lead magnet custom",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PRODUCTO,
            value_level=OfferValueLevel.LEAD_MAGNET,
        )
        assert offer.is_lead_magnet is True
        assert offer.value_level is OfferValueLevel.LEAD_MAGNET
