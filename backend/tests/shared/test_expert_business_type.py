"""Unit tests for ExpertBusinessType enum + metadata catalog.

The enum + metadata live together in ``shared/domain/expert_business_type.py``
because it is consumed by multiple bounded contexts (brand declares the
tenant's types, offer filters formats by suitability).
"""

from __future__ import annotations

from luana_core_platform.domain.expert_business_type import (
    EXPERT_BUSINESS_TYPE_CATALOG,
    ExpertBusinessType,
    ExpertBusinessTypeMetadata,
    get_expert_business_type_metadata,
)


class TestExpertBusinessTypeEnum:
    def test_enum_has_nine_canonical_types(self) -> None:
        expected = {
            "profesional_salud",
            "consultor_profesional",
            "coach_mentor",
            "academia_infoproductor",
            "anfitrion_productor",
            "agencia_freelance",
            "marca_ecommerce",
            "negocio_local",
            "software_saas",
        }
        actual = {member.value for member in ExpertBusinessType}
        assert actual == expected

    def test_enum_values_are_lowercase_snake(self) -> None:
        for member in ExpertBusinessType:
            assert member.value == member.value.lower()
            assert " " not in member.value


class TestExpertBusinessTypeCatalog:
    def test_every_enum_value_has_a_catalog_entry(self) -> None:
        missing = [t for t in ExpertBusinessType if t not in EXPERT_BUSINESS_TYPE_CATALOG]
        assert missing == []

    def test_catalog_has_no_orphan_entries(self) -> None:
        enum_values = set(ExpertBusinessType)
        catalog_values = set(EXPERT_BUSINESS_TYPE_CATALOG.keys())
        orphans = catalog_values - enum_values
        assert orphans == set()

    def test_every_entry_has_required_localized_fields(self) -> None:
        for business_type, metadata in EXPERT_BUSINESS_TYPE_CATALOG.items():
            assert isinstance(metadata, ExpertBusinessTypeMetadata)
            assert metadata.business_type is business_type
            assert metadata.label_es.strip(), f"label_es empty for {business_type}"
            assert metadata.description_es.strip(), f"description_es empty for {business_type}"
            assert metadata.value_proposition_es.strip(), f"value_proposition_es empty for {business_type}"
            assert metadata.revenue_model_es.strip(), f"revenue_model_es empty for {business_type}"
            assert metadata.icon_name.strip(), f"icon_name empty for {business_type}"
            assert metadata.examples_es, f"examples_es empty for {business_type}"

    def test_get_metadata_returns_frozen_record(self) -> None:
        record = get_expert_business_type_metadata(ExpertBusinessType.COACH_MENTOR)
        assert record.business_type is ExpertBusinessType.COACH_MENTOR
        assert record.label_es

    def test_icon_names_are_pascalcase(self) -> None:
        """Icons reference Lucide React component names, which are PascalCase."""
        for metadata in EXPERT_BUSINESS_TYPE_CATALOG.values():
            first = metadata.icon_name[0]
            assert first.isupper(), f"icon_name {metadata.icon_name} must be PascalCase"

    def test_value_proposition_is_chip_length(self) -> None:
        """3-5 words for badge/chip UI — hard cap at 6 to leave slack."""
        for metadata in EXPERT_BUSINESS_TYPE_CATALOG.values():
            word_count = len(metadata.value_proposition_es.split())
            assert 1 <= word_count <= 6, (
                f"value_proposition_es for {metadata.business_type} has {word_count} "
                f"words — should be 3-5 for chip UI: {metadata.value_proposition_es!r}"
            )
