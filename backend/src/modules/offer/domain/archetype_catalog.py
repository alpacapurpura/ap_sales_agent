"""Archetype Capabilities Catalog — single source of truth for offer archetypes.

This module declares what each ``OfferArchetype`` supports at the domain level:
edition capability, required fields for public publishing, default delivery
model, and user-facing labels.

Any scattered logic about archetypes (domain validators, interview configs,
frontend helpers) MUST delegate to this catalog via ``get_capabilities()``
instead of duplicating knowledge. The architecture test
``tests/architecture/test_archetype_catalog.py`` enforces that every
``OfferArchetype`` enum value is represented here.

Why a frozen ``dataclass`` constant and not a DB table:
- capabilities are invariants of the domain, not runtime config
- changing capabilities implies code changes (new validators, new UI)
- arch tests guarantee drift-free refactoring
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from src.modules.offer.domain.enums import (
    FulfillmentType,
    OfferArchetype,
    OfferDeliveryModel,
)


class EditionStructure(StrEnum):
    """How editions are modeled temporally for a given archetype."""

    NONE = "none"  # no editions (evergreen product / subscription)
    SINGLE_DATE = "single_date"  # one-off event at a date (workshop, masterclass)
    COHORT = "cohort"  # start → end window (bootcamp, group mentorship)
    RECURRING = "recurring"  # rolling batches (monthly service intake)


@dataclass(frozen=True, slots=True)
class ArchetypeCapabilities:
    """Capabilities and defaults for a single ``OfferArchetype``.

    The record is frozen to prevent mutation at runtime. All fields participate
    in the architecture test surface.
    """

    archetype: OfferArchetype

    # Edition capability
    supports_editions: bool
    edition_structure: EditionStructure
    edition_noun_es: str
    edition_noun_plural_es: str

    # Publishing constraints — enforced when an edition transitions to public
    requires_start_date_on_publish: bool
    requires_end_date_on_publish: bool
    requires_location_on_publish: bool
    supports_capacity: bool
    supports_waitlist: bool

    # Defaults propagated to the Offer entity at creation
    default_delivery: OfferDeliveryModel
    default_fulfillment: FulfillmentType

    # User-facing labels (Spanish — matches UI language)
    label_es: str
    icon_name: str  # lucide-react icon name for the frontend

    # Wizard copy for the "will this offer have editions?" question.
    # Present iff supports_editions is True — frontend renders the wizard step
    # only when all four fields are set.
    editions_wizard_title_es: str | None = None
    editions_wizard_description_es: str | None = None
    editions_wizard_yes_label_es: str | None = None
    editions_wizard_no_label_es: str | None = None


ARCHETYPE_CATALOG: dict[OfferArchetype, ArchetypeCapabilities] = {
    OfferArchetype.EXPERIENCIA: ArchetypeCapabilities(
        archetype=OfferArchetype.EXPERIENCIA,
        supports_editions=True,
        edition_structure=EditionStructure.SINGLE_DATE,
        edition_noun_es="salida",
        edition_noun_plural_es="salidas",
        requires_start_date_on_publish=True,
        requires_end_date_on_publish=False,
        requires_location_on_publish=True,
        supports_capacity=True,
        supports_waitlist=True,
        default_delivery=OfferDeliveryModel.DWY,
        default_fulfillment=FulfillmentType.MANUAL_PROVISIONING,
        label_es="Experiencia / Evento",
        icon_name="Calendar",
        editions_wizard_title_es="¿Tendrá varias salidas en fechas distintas?",
        editions_wizard_description_es=(
            "Si vas a repetir esta experiencia en distintas fechas (ej: cada trimestre), elegí Sí."
        ),
        editions_wizard_yes_label_es="Sí, con múltiples salidas programadas",
        editions_wizard_no_label_es="No, es una corrida única",
    ),
    OfferArchetype.PROGRAMA: ArchetypeCapabilities(
        archetype=OfferArchetype.PROGRAMA,
        supports_editions=True,
        edition_structure=EditionStructure.COHORT,
        edition_noun_es="cohorte",
        edition_noun_plural_es="cohortes",
        requires_start_date_on_publish=True,
        requires_end_date_on_publish=True,
        requires_location_on_publish=False,
        supports_capacity=True,
        supports_waitlist=True,
        default_delivery=OfferDeliveryModel.DWY,
        default_fulfillment=FulfillmentType.LMS_ACCESS,
        label_es="Programa / Cohorte",
        icon_name="GraduationCap",
        editions_wizard_title_es="¿Se dictará en cohortes?",
        editions_wizard_description_es=(
            "Las cohortes son grupos de alumnos que empiezan y terminan juntos en fechas fijas."
        ),
        editions_wizard_yes_label_es="Sí, en cohortes con fechas fijas",
        editions_wizard_no_label_es="No, es evergreen (cada alumno entra cuando quiere)",
    ),
    OfferArchetype.SERVICIO: ArchetypeCapabilities(
        archetype=OfferArchetype.SERVICIO,
        supports_editions=True,
        edition_structure=EditionStructure.RECURRING,
        edition_noun_es="convocatoria",
        edition_noun_plural_es="convocatorias",
        requires_start_date_on_publish=False,
        requires_end_date_on_publish=False,
        requires_location_on_publish=False,
        supports_capacity=True,
        supports_waitlist=False,
        default_delivery=OfferDeliveryModel.DFY,
        default_fulfillment=FulfillmentType.MANUAL_PROVISIONING,
        label_es="Servicio",
        icon_name="Briefcase",
        editions_wizard_title_es="¿Se ofrecerá en convocatorias?",
        editions_wizard_description_es=(
            "Las convocatorias agrupan clientes que empiezan al mismo tiempo en fechas fijas."
        ),
        editions_wizard_yes_label_es="Sí, con convocatorias agrupadas",
        editions_wizard_no_label_es="No, cada cliente agenda su propia fecha",
    ),
    OfferArchetype.PRODUCTO: ArchetypeCapabilities(
        archetype=OfferArchetype.PRODUCTO,
        supports_editions=False,
        edition_structure=EditionStructure.NONE,
        edition_noun_es="",
        edition_noun_plural_es="",
        requires_start_date_on_publish=False,
        requires_end_date_on_publish=False,
        requires_location_on_publish=False,
        supports_capacity=False,
        supports_waitlist=False,
        default_delivery=OfferDeliveryModel.DIY,
        default_fulfillment=FulfillmentType.DIGITAL_DOWNLOAD,
        label_es="Producto Digital",
        icon_name="Package",
    ),
    OfferArchetype.MEMBRESIA: ArchetypeCapabilities(
        archetype=OfferArchetype.MEMBRESIA,
        supports_editions=False,
        edition_structure=EditionStructure.NONE,
        edition_noun_es="",
        edition_noun_plural_es="",
        requires_start_date_on_publish=False,
        requires_end_date_on_publish=False,
        requires_location_on_publish=False,
        supports_capacity=False,
        supports_waitlist=False,
        default_delivery=OfferDeliveryModel.DIY,
        default_fulfillment=FulfillmentType.LMS_ACCESS,
        label_es="Membresía / Suscripción",
        icon_name="Repeat",
    ),
}


def get_capabilities(archetype: OfferArchetype) -> ArchetypeCapabilities:
    """Return the capabilities record for ``archetype``.

    Raises :class:`KeyError` at import time through the architecture test if
    the catalog is ever missing an entry, so in practice this lookup cannot
    fail in running code.
    """
    return ARCHETYPE_CATALOG[archetype]
