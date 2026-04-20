"""Architecture fitness: OfferTypePreset catalog invariants.

This gate enforces the 7th SSoT axis of the offer-studio catalog system
(see ``.claude/rules/offer-catalogs.md``). Drift between the preset
catalog and its upstream axes (ExpertBusinessType, OfferArchetype,
SectionCatalog) is blocked at CI.

Invariants enforced (one test per):

1. ``preset_id`` is snake_case, globally unique, prefixed by business_type.
2. Every ``ExpertBusinessType`` has at least 3 presets (diverse choice).
3. Every preset's ``archetype`` exists in ``ARCHETYPE_CATALOG``.
4. Every section in ``base_sections`` exists in ``SECTION_CATALOG``.
5. Every ``conditional_question_id`` exists in ``QUESTION_REGISTRY``.
6. ``base_sections`` includes IDENTITY + PROMISE + CLOSING (universal
   minimum to be recognisable) AND PRICING unless it's a lead magnet.
7. Lead magnets (``IS_LEAD_MAGNET`` flag) must NOT include PRICING.
8. ``examples_es`` is non-empty and has >= 2 entries.
9. Every catalog entry self-references its dict key.
10. Conditional questions self-reference their id and point to real sections.
11. Every ``OfferArchetype`` has at least one preset that uses it (so the
    archetype is reachable via a preset somewhere).
"""

from __future__ import annotations

import re

import pytest

from src.modules.offer.domain.archetype_catalog import ARCHETYPE_CATALOG
from src.modules.offer.domain.enums import OfferArchetype, OfferValueLevel
from src.modules.offer.domain.offer_type_preset_catalog import (
    OFFER_TYPE_PRESET_CATALOG,
    QUESTION_REGISTRY,
    PresetFlag,
    resolve_preset_flags,
    resolve_preset_sections,
)
from src.modules.offer.domain.section_catalog import SECTION_CATALOG, SectionKey
from src.shared.domain.expert_business_type import ExpertBusinessType

_BUSINESS_TYPE_SLUG: dict[ExpertBusinessType, str] = {
    ExpertBusinessType.PROFESIONAL_SALUD: "salud",
    ExpertBusinessType.CONSULTOR_PROFESIONAL: "consultor",
    ExpertBusinessType.COACH_MENTOR: "coach",
    ExpertBusinessType.ACADEMIA_INFOPRODUCTOR: "academia",
    ExpertBusinessType.ANFITRION_PRODUCTOR: "anfitrion",
    ExpertBusinessType.AGENCIA_FREELANCE: "agencia",
    ExpertBusinessType.MARCA_ECOMMERCE: "ecom",
    ExpertBusinessType.NEGOCIO_LOCAL: "local",
    ExpertBusinessType.SOFTWARE_SAAS: "saas",
}

_SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]*[a-z0-9]$")

_UNIVERSAL_MIN_SECTIONS: frozenset[SectionKey] = frozenset(
    {SectionKey.IDENTITY, SectionKey.PROMISE, SectionKey.CLOSING}
)


def test_preset_id_is_snake_case_and_prefixed_by_business_type() -> None:
    violations: list[str] = []
    for preset_id, preset in OFFER_TYPE_PRESET_CATALOG.items():
        if not _SNAKE_CASE.match(preset_id):
            violations.append(f"{preset_id!r} is not snake_case")
            continue
        expected_prefix = _BUSINESS_TYPE_SLUG[preset.business_type]
        if not preset_id.startswith(f"{expected_prefix}_"):
            violations.append(
                f"{preset_id!r} does not start with expected prefix "
                f"{expected_prefix!r} (business_type={preset.business_type.value})"
            )
    assert violations == [], "Preset IDs must be snake_case + prefixed:\n" + "\n".join(violations)


def test_every_business_type_has_at_least_three_presets() -> None:
    counts: dict[ExpertBusinessType, int] = dict.fromkeys(ExpertBusinessType, 0)
    for preset in OFFER_TYPE_PRESET_CATALOG.values():
        counts[preset.business_type] += 1
    under_three = {bt: n for bt, n in counts.items() if n < 3}
    assert under_three == {}, (
        f"Every ExpertBusinessType needs >= 3 presets (got: {under_three}). "
        "Add more presets so users have diverse offer-type choices."
    )


def test_preset_archetype_exists_in_archetype_catalog() -> None:
    orphans = [
        preset_id
        for preset_id, preset in OFFER_TYPE_PRESET_CATALOG.items()
        if preset.archetype not in ARCHETYPE_CATALOG
    ]
    assert orphans == [], (
        f"Presets reference archetypes not in ARCHETYPE_CATALOG: {orphans}. "
        "Every preset archetype must have a capabilities record."
    )


def test_base_sections_exist_in_section_catalog() -> None:
    violations: list[str] = []
    for preset_id, preset in OFFER_TYPE_PRESET_CATALOG.items():
        violations.extend(
            f"{preset_id!r} references missing section {section.value!r}"
            for section in preset.base_sections
            if section not in SECTION_CATALOG
        )
    assert violations == [], "Preset base_sections must all exist in SECTION_CATALOG:\n" + "\n".join(violations)


def test_conditional_question_ids_exist_in_registry() -> None:
    violations: list[str] = []
    for preset_id, preset in OFFER_TYPE_PRESET_CATALOG.items():
        violations.extend(
            f"{preset_id!r} references missing question_id {qid!r}"
            for qid in preset.conditional_question_ids
            if qid not in QUESTION_REGISTRY
        )
    assert violations == [], "Every conditional_question_id must exist in QUESTION_REGISTRY:\n" + "\n".join(violations)


def test_base_sections_cover_universal_minimum() -> None:
    violations: list[str] = []
    for preset_id, preset in OFFER_TYPE_PRESET_CATALOG.items():
        missing = _UNIVERSAL_MIN_SECTIONS - set(preset.base_sections)
        if missing:
            violations.append(f"{preset_id!r} missing {[s.value for s in missing]}")
    assert violations == [], (
        "Every preset must include IDENTITY, PROMISE and CLOSING in base_sections "
        "(the minimum to be a recognisable offer):\n" + "\n".join(violations)
    )


def test_paid_presets_include_pricing() -> None:
    violations: list[str] = []
    for preset_id, preset in OFFER_TYPE_PRESET_CATALOG.items():
        is_lead_magnet = PresetFlag.IS_LEAD_MAGNET in preset.default_flags
        has_pricing = SectionKey.PRICING in preset.base_sections
        if not is_lead_magnet and not has_pricing:
            violations.append(f"{preset_id!r} is paid but omits PRICING")
    assert violations == [], "Paid presets must include PRICING:\n" + "\n".join(violations)


def test_lead_magnets_exclude_pricing() -> None:
    violations: list[str] = []
    for preset_id, preset in OFFER_TYPE_PRESET_CATALOG.items():
        is_lead_magnet = PresetFlag.IS_LEAD_MAGNET in preset.default_flags
        has_pricing = SectionKey.PRICING in preset.base_sections
        if is_lead_magnet and has_pricing:
            violations.append(f"{preset_id!r} is a lead magnet but includes PRICING")
    assert violations == [], "Lead-magnet presets must NOT include PRICING:\n" + "\n".join(violations)


def test_examples_es_non_empty_and_varied() -> None:
    violations: list[str] = []
    for preset_id, preset in OFFER_TYPE_PRESET_CATALOG.items():
        if len(preset.examples_es) < 2:
            violations.append(f"{preset_id!r} has {len(preset.examples_es)} examples (min 2 required)")
    assert violations == [], "Every preset must have >= 2 examples_es so users recognise the offer type:\n" + "\n".join(
        violations
    )


def test_catalog_entries_self_reference_their_key() -> None:
    violations: list[str] = []
    for preset_id, preset in OFFER_TYPE_PRESET_CATALOG.items():
        if preset.preset_id != preset_id:
            violations.append(f"catalog key {preset_id!r} != preset.preset_id {preset.preset_id!r}")
    assert violations == [], "Catalog keys must match preset.preset_id:\n" + "\n".join(violations)


def test_question_registry_self_references_and_points_to_real_sections() -> None:
    violations: list[str] = []
    for qid, question in QUESTION_REGISTRY.items():
        if question.question_id != qid:
            violations.append(f"registry key {qid!r} != question.question_id {question.question_id!r}")
        violations.extend(
            f"question {qid!r} points to missing section {section.value!r}"
            for section in question.on_yes_sections
            if section not in SECTION_CATALOG
        )
    assert violations == [], "QUESTION_REGISTRY integrity:\n" + "\n".join(violations)


def test_lead_magnet_presets_carry_lead_magnet_value_level() -> None:
    """Sprint 15 invariant: preset and flag MUST agree on lead-magnet status.

    If the preset declares ``IS_LEAD_MAGNET`` in ``default_flags`` then its
    ``typical_value_level`` MUST be ``LEAD_MAGNET``. Otherwise the wizard
    derives a paid ladder rung from a free preset (or vice versa) and the
    dashboard ladder grouping silently lies.
    """
    violations: list[str] = []
    for preset_id, preset in OFFER_TYPE_PRESET_CATALOG.items():
        is_flagged = PresetFlag.IS_LEAD_MAGNET in preset.default_flags
        is_leveled = preset.typical_value_level is OfferValueLevel.LEAD_MAGNET
        if is_flagged and not is_leveled:
            violations.append(
                f"{preset_id!r} has IS_LEAD_MAGNET flag but typical_value_level={preset.typical_value_level.value!r}"
            )
        if is_leveled and not is_flagged:
            violations.append(
                f"{preset_id!r} declares typical_value_level=LEAD_MAGNET but lacks the IS_LEAD_MAGNET flag"
            )
    assert violations == [], "Preset lead-magnet flag ↔ value_level alignment:\n" + "\n".join(violations)


def test_paid_presets_carry_non_lead_magnet_value_level() -> None:
    """Paid presets must sit on a paid rung (ACTIVACION / TRANSFORMACION /
    MAXIMIZACION / CORPORATIVO). Never LEAD_MAGNET.
    """
    paid_rungs = {
        OfferValueLevel.ACTIVACION,
        OfferValueLevel.TRANSFORMACION,
        OfferValueLevel.MAXIMIZACION,
        OfferValueLevel.CORPORATIVO,
    }
    violations = [
        f"{preset_id!r} on rung {preset.typical_value_level.value!r}"
        for preset_id, preset in OFFER_TYPE_PRESET_CATALOG.items()
        if PresetFlag.IS_LEAD_MAGNET not in preset.default_flags and preset.typical_value_level not in paid_rungs
    ]
    assert violations == [], "Paid presets must sit on a paid ladder rung:\n" + "\n".join(violations)


def test_high_ticket_presets_are_max_or_corporate_rung() -> None:
    """Sprint 15 sanity: ``HIGH_TICKET`` flag implies MAXIMIZACION or
    CORPORATIVO. Everything cheaper is a modelling error — HIGH_TICKET
    means a signature / premium offer, not a first-purchase entry.
    """
    premium_rungs = {OfferValueLevel.MAXIMIZACION, OfferValueLevel.CORPORATIVO}
    violations = [
        f"{preset_id!r} is HIGH_TICKET but rung={preset.typical_value_level.value!r}"
        for preset_id, preset in OFFER_TYPE_PRESET_CATALOG.items()
        if PresetFlag.HIGH_TICKET in preset.default_flags and preset.typical_value_level not in premium_rungs
    ]
    assert violations == [], "HIGH_TICKET presets must sit on MAXIMIZACION or CORPORATIVO:\n" + "\n".join(violations)


def test_every_archetype_has_at_least_one_preset() -> None:
    used = {preset.archetype for preset in OFFER_TYPE_PRESET_CATALOG.values()}
    unused = set(OfferArchetype) - used
    assert unused == set(), (
        f"Every OfferArchetype must be reachable via at least one preset. "
        f"Orphaned archetypes: {sorted(a.value for a in unused)}. "
        "Add a preset that uses this archetype or retire the archetype."
    )


def test_descriptions_and_labels_are_non_empty() -> None:
    violations: list[str] = []
    for preset_id, preset in OFFER_TYPE_PRESET_CATALOG.items():
        if not preset.label_es.strip():
            violations.append(f"{preset_id!r} has empty label_es")
        if not preset.description_es.strip():
            violations.append(f"{preset_id!r} has empty description_es")
        if not preset.icon_name.strip():
            violations.append(f"{preset_id!r} has empty icon_name")
    assert violations == [], "Preset metadata completeness:\n" + "\n".join(violations)


# ── Behavior: resolver functions ───────────────────────────────────────────


def test_resolve_preset_sections_base_only_when_no_answers() -> None:
    preset = next(iter(OFFER_TYPE_PRESET_CATALOG.values()))
    resolved = resolve_preset_sections(preset.preset_id, answers={})
    assert resolved == preset.base_sections


def test_resolve_preset_sections_dedupes_duplicates() -> None:
    # Any preset with conditional question that adds a section already in base
    # would still be deduped — pick 'salud_plan_seguimiento' which has LOCATION
    # in base and requires_physical_location as conditional.
    answers = {"requires_physical_location": True}
    resolved = resolve_preset_sections("salud_plan_seguimiento", answers=answers)
    assert resolved.count(SectionKey.LOCATION) == 1


def test_resolve_preset_flags_combines_defaults_and_yes_answers() -> None:
    # coach_bootcamp has REQUIRES_START_DATE + SUPPORTS_CAPACITY in defaults
    # + has_limited_capacity question which also adds SUPPORTS_CAPACITY.
    flags = resolve_preset_flags(
        "coach_bootcamp",
        answers={"has_limited_capacity": True},
    )
    assert PresetFlag.SUPPORTS_CAPACITY in flags
    assert PresetFlag.REQUIRES_START_DATE in flags
    # dedup
    assert list(flags).count(PresetFlag.SUPPORTS_CAPACITY) == 1


@pytest.mark.parametrize("preset_id", list(OFFER_TYPE_PRESET_CATALOG.keys()))
def test_every_preset_resolves_cleanly_with_no_answers(preset_id: str) -> None:
    """Smoke test: resolve_preset_sections never raises and returns a tuple."""
    result = resolve_preset_sections(preset_id, answers={})
    assert isinstance(result, tuple)
    assert len(result) > 0


@pytest.mark.parametrize("preset_id", list(OFFER_TYPE_PRESET_CATALOG.keys()))
def test_every_preset_resolves_cleanly_with_all_yes_answers(preset_id: str) -> None:
    """Smoke test: all-yes answers never raise and never shrink the section list."""
    preset = OFFER_TYPE_PRESET_CATALOG[preset_id]
    answers = dict.fromkeys(preset.conditional_question_ids, True)
    result = resolve_preset_sections(preset_id, answers=answers)
    assert set(preset.base_sections).issubset(set(result))
