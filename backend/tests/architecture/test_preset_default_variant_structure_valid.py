"""Architecture fitness: preset ``default_variant_structure`` alignment.

Sprint 15.1 adds ``OfferTypePreset.default_variant_structure`` so a preset
can override the archetype's default (e.g. ``consultor_retainer`` forces
``TIER`` even though SERVICIO defaults to ``RECURRING_INTAKE``).

Invariants:

1. If a preset declares ``default_variant_structure`` (non-None), that
   value MUST appear in the parent archetype's
   ``supported_variant_structures`` tuple. Otherwise the wizard would hand
   the backend a structure the archetype rejects.

2. If the parent archetype does NOT ``supports_editions`` the preset
   MUST keep ``default_variant_structure=None``. Surfacing a structure
   for an editions-less archetype would contradict the archetype
   capabilities.
"""

from __future__ import annotations

from luana_core_offer_studio.domain.archetype_catalog import ARCHETYPE_CATALOG
from luana_core_offer_studio.domain.offer_type_preset_catalog import OFFER_TYPE_PRESET_CATALOG


def test_preset_default_structure_within_archetype_supported_tuple() -> None:
    offenders: list[tuple[str, str, str, list[str]]] = []
    for preset_id, preset in OFFER_TYPE_PRESET_CATALOG.items():
        if preset.default_variant_structure is None:
            continue
        caps = ARCHETYPE_CATALOG[preset.archetype]
        if preset.default_variant_structure not in caps.supported_variant_structures:
            offenders.append(
                (
                    preset_id,
                    preset.archetype.value,
                    preset.default_variant_structure.value,
                    [s.value for s in caps.supported_variant_structures],
                )
            )
    assert offenders == [], (
        "Preset.default_variant_structure must be a member of the parent "
        "archetype's supported_variant_structures. Offenders: "
        f"{offenders}. Add the structure to the archetype's supported tuple "
        "or drop the preset override."
    )


def test_preset_on_non_edition_archetype_keeps_default_none() -> None:
    leaks: list[tuple[str, str, str]] = []
    for preset_id, preset in OFFER_TYPE_PRESET_CATALOG.items():
        if preset.default_variant_structure is None:
            continue
        caps = ARCHETYPE_CATALOG[preset.archetype]
        if not caps.supports_editions:
            leaks.append((preset_id, preset.archetype.value, preset.default_variant_structure.value))
    assert leaks == [], (
        "Presets on non-edition archetypes must keep default_variant_structure=None. "
        f"Leaks: {leaks}. "
        "Promote the archetype to supports_editions=True or clear the preset override."
    )
