"""Unit tests for ``src.shared.domain.field_contract`` platform core.

Covers: derivation walker, type inference, override merge, polymorphic
unions, composable nested, lifecycle, module registry.

F11.3: ``teardown_module`` clears the synthetic test modules from the
global ``_MODULE_CONTRACTS`` registry so they do not leak into the
``test_editable_fields_ssot::test_no_cross_domain_duplicates`` arch test
when it runs later under ``pytest-randomly``. Without this teardown the
modules ``test_module_fixture`` and ``test_find`` both register a path
``"x"`` → cross-domain duplicate → flaky failure documented in F0-F10
learnings.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from luana_core_platform.domain.field_contract import (
    FieldContract,
    FieldStatus,
    FieldType,
    PolymorphicVariantSpec,
    derive_contracts_from_pydantic,
    fields_by_path_prefix,
    fields_by_section,
    find_contract,
    get_module_contracts,
    register_module_contracts,
)
from luana_core_platform.domain.field_contract import (
    FieldContractOverride as Override,
)

_SYNTHETIC_MODULES: tuple[str, ...] = (
    "test_module_fixture",
    "test_find",
    "t",
    "t2",
    "t3",
)


def teardown_module(module: object) -> None:
    """Drop synthetic registries so editable_fields_ssot stays cross-test clean.

    Both registries must be wiped: ``_MODULE_CONTRACTS`` is the source of
    truth, but ``editable_fields._CATALOGS`` caches derived projections
    once any test (in any order) calls ``get_catalog``. Clearing one
    without the other re-introduces the duplicate.
    """
    from luana_core_platform.domain.field_contract import _MODULE_CONTRACTS
    from luana_core_platform.links.ports import editable_fields as _ef

    for name in _SYNTHETIC_MODULES:
        _MODULE_CONTRACTS.pop(name, None)
        _ef._CATALOGS.pop(name, None)


# ---------------------------------------------------------------------------
# Fixtures — toy Pydantic models
# ---------------------------------------------------------------------------


class _Color(StrEnum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class _NestedBlock(BaseModel):
    foo: str | None = None
    bar: int = 0


class _VariantA(BaseModel):
    alpha: str | None = None
    shared_key: str | None = None


class _VariantB(BaseModel):
    beta: int | None = None
    shared_key: str | None = None


class _Root(BaseModel):
    id: UUID | None = None
    tenant_id: UUID | None = None
    required_text: str
    optional_text: str | None = None
    count: int | None = None
    ratio: float | None = None
    active: bool | None = None
    color: _Color | None = None
    tags: list[str] = []
    ids: list[UUID] = []
    when: datetime | None = None
    docs_url: HttpUrl | None = None
    metadata: dict[str, str] = {}
    nested: _NestedBlock | None = None
    polymorphic: _VariantA | _VariantB | None = None
    with_description: str | None = Field(None, description="Description from Field(...)")


# ---------------------------------------------------------------------------
# derive_contracts_from_pydantic
# ---------------------------------------------------------------------------


def test_derive_skips_ignore_paths() -> None:
    contracts = derive_contracts_from_pydantic(
        model=_Root,
        owner_module="test",
        section_map={"required_text": "main"},
        ignore_paths=frozenset({"id", "tenant_id"}),
    )
    paths = {c.path for c in contracts}
    assert "id" not in paths
    assert "tenant_id" not in paths


def test_derive_requires_section_map_entry() -> None:
    """Fields without section_map entry are dropped silently — arch test catches later."""
    contracts = derive_contracts_from_pydantic(
        model=_Root,
        owner_module="test",
        section_map={"required_text": "main"},  # only one entry
        ignore_paths=frozenset({"id", "tenant_id"}),
    )
    # Only fields with section in the map emerge
    paths = {c.path for c in contracts}
    assert paths == {"required_text"}


def test_derive_infers_types() -> None:
    full_map = {
        "required_text": "s",
        "optional_text": "s",
        "count": "s",
        "ratio": "s",
        "active": "s",
        "color": "s",
        "tags": "s",
        "ids": "s",
        "when": "s",
        "docs_url": "s",
        "metadata": "s",
        "with_description": "s",
    }
    contracts = derive_contracts_from_pydantic(
        model=_Root,
        owner_module="test",
        section_map=full_map,
        ignore_paths=frozenset({"id", "tenant_id", "nested", "polymorphic"}),
    )
    by_path = {c.path: c for c in contracts}
    assert by_path["required_text"].type == FieldType.TEXT
    assert by_path["required_text"].is_required_structural is True
    assert by_path["optional_text"].type == FieldType.TEXT
    assert by_path["optional_text"].is_required_structural is False
    assert by_path["count"].type == FieldType.NUMBER
    assert by_path["ratio"].type == FieldType.NUMBER
    assert by_path["active"].type == FieldType.BOOL
    assert by_path["color"].type == FieldType.ENUM
    assert by_path["color"].enum_values == ("red", "green", "blue")
    assert by_path["tags"].type == FieldType.LIST
    assert by_path["tags"].list_item_type == "text"
    assert by_path["ids"].type == FieldType.LIST
    assert by_path["when"].type == FieldType.DATE
    assert by_path["docs_url"].type == FieldType.URL
    assert by_path["metadata"].type == FieldType.DICT


def test_derive_uses_field_info_description_as_notes() -> None:
    contracts = derive_contracts_from_pydantic(
        model=_Root,
        owner_module="test",
        section_map={"with_description": "s"},
        ignore_paths=frozenset({"id", "tenant_id"}),
    )
    [c] = [c for c in contracts if c.path == "with_description"]
    assert c.notes == "Description from Field(...)"


def test_derive_composable_nested() -> None:
    """Composable nested model is walked with prefix."""
    contracts = derive_contracts_from_pydantic(
        model=_Root,
        owner_module="test",
        section_map={
            "nested.foo": "nested_section",
            "nested.bar": "nested_section",
        },
        ignore_paths=frozenset({"id", "tenant_id"}),
        composable_fields=("nested",),
    )
    paths = {c.path for c in contracts}
    assert paths == {"nested.foo", "nested.bar"}


def test_derive_polymorphic_union_same_section_merges_filter() -> None:
    """Shared key across variants WITH SAME section → 1 contract, merged filter."""
    contracts = derive_contracts_from_pydantic(
        model=_Root,
        owner_module="test",
        section_map={},
        ignore_paths=frozenset({"id", "tenant_id"}),
        polymorphic_prefix_map={
            _VariantA: PolymorphicVariantSpec(archetype_filter=("ARCH_A",), section="shared"),
            _VariantB: PolymorphicVariantSpec(archetype_filter=("ARCH_B",), section="shared"),
        },
    )
    by_path: dict[str, list[FieldContract]] = {}
    for c in contracts:
        by_path.setdefault(c.path, []).append(c)
    [alpha] = by_path["polymorphic.alpha"]
    assert alpha.archetype_filter == ("ARCH_A",)
    assert alpha.section == "shared"
    [beta] = by_path["polymorphic.beta"]
    assert beta.archetype_filter == ("ARCH_B",)
    [shared] = by_path["polymorphic.shared_key"]
    assert shared.archetype_filter == ("ARCH_A", "ARCH_B")


def test_derive_polymorphic_union_different_sections_emits_two_contracts() -> None:
    """Shared key across variants WITH DIFFERENT sections → 2 contracts."""
    contracts = derive_contracts_from_pydantic(
        model=_Root,
        owner_module="test",
        section_map={},
        ignore_paths=frozenset({"id", "tenant_id"}),
        polymorphic_prefix_map={
            _VariantA: PolymorphicVariantSpec(archetype_filter=("ARCH_A",), section="sec_a"),
            _VariantB: PolymorphicVariantSpec(archetype_filter=("ARCH_B",), section="sec_b"),
        },
    )
    shared_contracts = [c for c in contracts if c.path == "polymorphic.shared_key"]
    assert len(shared_contracts) == 2
    assert {c.section for c in shared_contracts} == {"sec_a", "sec_b"}
    assert {c.archetype_filter for c in shared_contracts} == {("ARCH_A",), ("ARCH_B",)}


# ---------------------------------------------------------------------------
# Override merge semantics
# ---------------------------------------------------------------------------


def test_override_pisa_derived_requiredness() -> None:
    contracts = derive_contracts_from_pydantic(
        model=_Root,
        owner_module="test",
        section_map={"optional_text": "s"},
        overrides={"optional_text": Override(is_required_semantic=True, priority=10)},
        ignore_paths=frozenset({"id", "tenant_id"}),
    )
    [c] = [c for c in contracts if c.path == "optional_text"]
    # is_required_structural stays False (Pydantic-derived, no override)
    assert c.is_required_structural is False
    # is_required_semantic comes from override
    assert c.is_required_semantic is True
    assert c.priority == 10


def test_override_can_propose_false_blocks_copilot() -> None:
    contracts = derive_contracts_from_pydantic(
        model=_Root,
        owner_module="test",
        section_map={"required_text": "s"},
        overrides={"required_text": Override(can_propose=False)},
        ignore_paths=frozenset({"id", "tenant_id"}),
    )
    [c] = [c for c in contracts if c.path == "required_text"]
    assert c.can_propose is False


def test_override_copilot_meta_passes_through() -> None:
    contracts = derive_contracts_from_pydantic(
        model=_Root,
        owner_module="test",
        section_map={"required_text": "s"},
        overrides={
            "required_text": Override(
                human_question_es="¿Cuál es el texto requerido?",
                expects="una frase",
                gate="some_gate_path",
                redo_if_changes=("other_path",),
            )
        },
        ignore_paths=frozenset({"id", "tenant_id"}),
    )
    [c] = [c for c in contracts if c.path == "required_text"]
    assert c.human_question_es == "¿Cuál es el texto requerido?"
    assert c.expects == "una frase"
    assert c.gate == "some_gate_path"
    assert c.redo_if_changes == ("other_path",)


def test_override_lifecycle_deprecated() -> None:
    contracts = derive_contracts_from_pydantic(
        model=_Root,
        owner_module="test",
        section_map={"required_text": "s"},
        overrides={
            "required_text": Override(
                status=FieldStatus.DEPRECATED,
                deprecated_in="2026-04-24",
                replaced_by="new_text",
            )
        },
        ignore_paths=frozenset({"id", "tenant_id"}),
    )
    [c] = [c for c in contracts if c.path == "required_text"]
    assert c.status == FieldStatus.DEPRECATED
    assert c.deprecated_in == "2026-04-24"
    assert c.replaced_by == "new_text"


# ---------------------------------------------------------------------------
# Module registry
# ---------------------------------------------------------------------------


def test_register_and_retrieve_contracts() -> None:
    dummy = FieldContract(
        path="x",
        owner_module="test_module_fixture",
        type=FieldType.TEXT,
        is_required_structural=False,
        section="s",
    )
    register_module_contracts("test_module_fixture", (dummy,))
    retrieved = get_module_contracts("test_module_fixture")
    assert retrieved == (dummy,)


def test_find_contract_by_path() -> None:
    dummy = FieldContract(
        path="x",
        owner_module="test_find",
        type=FieldType.TEXT,
        is_required_structural=False,
        section="s",
    )
    register_module_contracts("test_find", (dummy,))
    assert find_contract("test_find", "x") == dummy
    assert find_contract("test_find", "missing") is None


def test_fields_by_section_filters_by_archetype() -> None:
    a = FieldContract(
        path="p1",
        owner_module="t",
        type=FieldType.TEXT,
        is_required_structural=False,
        section="sec1",
        archetype_filter=("PROG",),
    )
    b = FieldContract(
        path="p2",
        owner_module="t",
        type=FieldType.TEXT,
        is_required_structural=False,
        section="sec1",
        archetype_filter=("SERV",),
    )
    c = FieldContract(
        path="p3",
        owner_module="t",
        type=FieldType.TEXT,
        is_required_structural=False,
        section="sec1",  # no filter
    )
    register_module_contracts("t", (a, b, c))
    prog_contracts = fields_by_section("t", "sec1", archetype="PROG")
    assert {fc.path for fc in prog_contracts} == {"p1", "p3"}


def test_fields_by_section_filters_deprecated() -> None:
    active = FieldContract(
        path="active_p",
        owner_module="t2",
        type=FieldType.TEXT,
        is_required_structural=False,
        section="s",
    )
    deprecated = FieldContract(
        path="deprecated_p",
        owner_module="t2",
        type=FieldType.TEXT,
        is_required_structural=False,
        section="s",
        status=FieldStatus.DEPRECATED,
    )
    register_module_contracts("t2", (active, deprecated))
    active_only = fields_by_section("t2", "s")
    assert {fc.path for fc in active_only} == {"active_p"}


def test_fields_by_path_prefix() -> None:
    a = FieldContract(
        path="nested.a",
        owner_module="t3",
        type=FieldType.TEXT,
        is_required_structural=False,
        section="s",
    )
    b = FieldContract(
        path="nested.b",
        owner_module="t3",
        type=FieldType.TEXT,
        is_required_structural=False,
        section="s",
    )
    c = FieldContract(
        path="top_level",
        owner_module="t3",
        type=FieldType.TEXT,
        is_required_structural=False,
        section="s",
    )
    register_module_contracts("t3", (a, b, c))
    nested_only = fields_by_path_prefix("t3", "nested")
    assert {fc.path for fc in nested_only} == {"nested.a", "nested.b"}


def test_get_module_contracts_empty_for_unknown_module() -> None:
    assert get_module_contracts("nonexistent_module_xyz") == ()


# ---------------------------------------------------------------------------
# dict_subkeys arg — JSONB sub-keys (Fase 07 buyer-persona)
# ---------------------------------------------------------------------------


class _DictRoot(BaseModel):
    """Toy model with a JSONB-like ``dict`` field whose sub-keys are declared."""

    name: str | None = None
    demographics: dict = Field(default_factory=dict)
    psychographics: dict = Field(default_factory=dict)


def test_dict_subkeys_emits_one_contract_per_subkey() -> None:
    """``dict_subkeys`` declares the JSONB sub-keys to expose as contracts."""
    contracts = derive_contracts_from_pydantic(
        model=_DictRoot,
        owner_module="test_dict",
        section_map={
            "name": "identity",
            "demographics.age_range": "demographics",
            "demographics.location": "demographics",
            "psychographics.values": "psychographics",
        },
        ignore_paths=frozenset(),
        dict_subkeys={
            "demographics": ("age_range", "location"),
            "psychographics": ("values",),
        },
    )
    paths = {c.path for c in contracts}
    assert paths == {
        "name",
        "demographics.age_range",
        "demographics.location",
        "psychographics.values",
    }


def test_dict_subkeys_skips_parent_field_emission() -> None:
    """Parent ``dict`` field is treated as a composable handle — not emitted bare."""
    contracts = derive_contracts_from_pydantic(
        model=_DictRoot,
        owner_module="test_dict",
        section_map={
            "demographics.age_range": "demographics",
        },
        ignore_paths=frozenset(),
        dict_subkeys={"demographics": ("age_range",)},
    )
    paths = {c.path for c in contracts}
    # bare 'demographics' MUST NOT appear — it's a JSONB container, sub-keys are the surface
    assert "demographics" not in paths
    assert "demographics.age_range" in paths


def test_dict_subkeys_default_type_is_text() -> None:
    """Sub-key contracts default to TEXT (JSONB has no Pydantic type info)."""
    contracts = derive_contracts_from_pydantic(
        model=_DictRoot,
        owner_module="test_dict",
        section_map={"demographics.age_range": "demographics"},
        ignore_paths=frozenset(),
        dict_subkeys={"demographics": ("age_range",)},
    )
    [c] = [c for c in contracts if c.path == "demographics.age_range"]
    assert c.type == FieldType.TEXT
    # JSONB sub-keys are never structurally required — the parent dict has a default factory
    assert c.is_required_structural is False


def test_dict_subkeys_respects_section_map_and_overrides() -> None:
    """Sub-key contracts honour section_map + override metadata (label_es, can_propose)."""
    contracts = derive_contracts_from_pydantic(
        model=_DictRoot,
        owner_module="test_dict",
        section_map={
            "demographics.age_range": "demographics",
            "demographics.location": "demographics",
        },
        overrides={
            "demographics.age_range": Override(
                label_es="Rango etario",
                notes="Edad del cliente.",
                can_propose=True,
            ),
            "demographics.location": Override(
                label_es="Ubicación",
                can_propose=False,
            ),
        },
        ignore_paths=frozenset(),
        dict_subkeys={"demographics": ("age_range", "location")},
    )
    by_path = {c.path: c for c in contracts}
    assert by_path["demographics.age_range"].label_es == "Rango etario"
    assert by_path["demographics.age_range"].notes == "Edad del cliente."
    assert by_path["demographics.age_range"].can_propose is True
    assert by_path["demographics.location"].label_es == "Ubicación"
    assert by_path["demographics.location"].can_propose is False


def test_dict_subkeys_drops_subkey_without_section_map_entry() -> None:
    """Sub-key without section_map entry is dropped (consistent with top-level)."""
    contracts = derive_contracts_from_pydantic(
        model=_DictRoot,
        owner_module="test_dict",
        section_map={"demographics.age_range": "demographics"},
        ignore_paths=frozenset(),
        dict_subkeys={"demographics": ("age_range", "location")},  # 'location' missing in map
    )
    paths = {c.path for c in contracts}
    assert "demographics.age_range" in paths
    assert "demographics.location" not in paths


def test_dict_subkeys_default_none_preserves_dict_emission() -> None:
    """Without ``dict_subkeys``, a ``dict`` field emits a bare DICT contract."""
    contracts = derive_contracts_from_pydantic(
        model=_DictRoot,
        owner_module="test_dict",
        section_map={"demographics": "demographics"},
        ignore_paths=frozenset(),
        # dict_subkeys not passed
    )
    [c] = [c for c in contracts if c.path == "demographics"]
    assert c.type == FieldType.DICT
