"""Unit tests for ``src.shared.domain.field_contract`` platform core.

Covers: derivation walker, type inference, override merge, polymorphic
unions, composable nested, lifecycle, module registry.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from src.shared.domain.field_contract import (
    FieldContract,
    FieldStatus,
    FieldType,
    derive_contracts_from_pydantic,
    fields_by_path_prefix,
    fields_by_section,
    find_contract,
    get_module_contracts,
    register_module_contracts,
)
from src.shared.domain.field_contract import (
    FieldContractOverride as Override,
)

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


def test_derive_polymorphic_union_dedupes_shared_key_with_merged_filter() -> None:
    """Shared key across variants → single contract with merged archetype_filter."""
    contracts = derive_contracts_from_pydantic(
        model=_Root,
        owner_module="test",
        section_map={
            "polymorphic.alpha": "s",
            "polymorphic.beta": "s",
            "polymorphic.shared_key": "s",
        },
        ignore_paths=frozenset({"id", "tenant_id"}),
        polymorphic_prefix_map={
            _VariantA: ("ARCH_A",),
            _VariantB: ("ARCH_B",),
        },
    )
    by_path = {c.path: c for c in contracts}
    assert by_path["polymorphic.alpha"].archetype_filter == ("ARCH_A",)
    assert by_path["polymorphic.beta"].archetype_filter == ("ARCH_B",)
    # Shared key → merged filter
    assert by_path["polymorphic.shared_key"].archetype_filter == ("ARCH_A", "ARCH_B")


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
