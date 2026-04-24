"""FieldContract platform — cross-module SSoT for field metadata.

Successor of ``src.modules.offer.domain.field_contract`` (which was
offer-specific). Promoted to ``shared/`` per ADR-011 to serve as the
single contract for every module (offer, brand, buyer_persona, ...).

Layered model:

* L0 Pydantic models — estructural (what is persisted).
* L1 FieldContract (this module) — semantic SSoT cross-module.
* L2 Consumers (FE schemas, copilot prompts, sales-agent, landing) — projections.

Pydantic answers "what is persisted". ``FieldContract`` answers "how
do I treat it semantically (section, lifecycle, copilot meta)". FE
schemas answer "how does it look". Each consumer is a projection —
never duplicates.

Per-module usage lives in ``{module}/domain/field_contract.py`` which
declares ``{MODULE}_SECTION_MAP`` + ``{MODULE}_FIELD_OVERRIDES`` and
calls ``derive_contracts_from_pydantic`` + ``register_module_contracts``.

See ``docs/refactors/field-contract-platform/DESIGN.md`` and
``DECISIONS.md`` ADR-011..017 for rationale.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime
from enum import Enum, StrEnum
from types import UnionType
from typing import TYPE_CHECKING, Any, Union, get_args, get_origin
from uuid import UUID

from pydantic import AnyUrl, BaseModel

if TYPE_CHECKING:
    from pydantic.fields import FieldInfo


_AnnotationT = Any
"""Alias for Pydantic annotation types. Pydantic annotations are
dynamic — a field can be ``str``, ``list[X]``, ``X | None``, an Enum
subclass, or a custom type. Any is appropriate here."""


# ---------------------------------------------------------------------------
# Enums + override dataclass
# ---------------------------------------------------------------------------


class FieldType(StrEnum):
    """Semantic type of a field.

    Derived from Pydantic annotation. Coarser than Python types —
    groups compatible shapes (int + float -> NUMBER) for downstream
    uniformity.
    """

    TEXT = "text"
    NUMBER = "number"
    BOOL = "bool"
    ENUM = "enum"
    LIST = "list"
    OBJECT = "object"
    DATE = "date"
    URL = "url"
    UUID = "uuid"
    DICT = "dict"
    UNKNOWN = "unknown"


class FieldStatus(StrEnum):
    """Lifecycle of a field (ADR-013)."""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    REMOVED = "removed"


@dataclass(frozen=True, slots=True)
class FieldContractOverride:
    """Per-field semantic metadata que Pydantic no puede expresar.

    Every attribute is optional — only override what differs from
    defaults derived from Pydantic introspection + ``section_map``.

    Merge semantics: non-None attributes in the override replace the
    derived value. ``None`` leaves the derived value intact.
    """

    section: str | None = None
    group: str | None = None
    priority: int | None = None

    archetype_filter: tuple[str, ...] | None = None
    value_level_filter: tuple[str, ...] | None = None
    business_type_filter: tuple[str, ...] | None = None
    preset_filter: tuple[str, ...] | None = None

    is_required_semantic: bool | None = None

    status: FieldStatus | None = None
    deprecated_in: str | None = None
    replaced_by: str | None = None
    introduced_in: str | None = None

    can_propose: bool | None = None
    human_question_es: str | None = None
    expects: str | None = None
    gate: str | None = None
    redo_if_changes: tuple[str, ...] | None = None

    label_es: str | None = None

    notes: str | None = None


# ---------------------------------------------------------------------------
# FieldContract dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FieldContract:
    """Cross-module SSoT metadata for one field.

    Immutable. Registered by each module via
    :func:`register_module_contracts`. Consumers project from the
    registry — never duplicate.
    """

    path: str
    owner_module: str

    type: FieldType
    is_required_structural: bool
    enum_values: tuple[str, ...] | None = None
    list_item_type: str | None = None

    section: str = ""
    group: str | None = None
    priority: int = 0

    archetype_filter: tuple[str, ...] | None = None
    value_level_filter: tuple[str, ...] | None = None
    business_type_filter: tuple[str, ...] | None = None
    preset_filter: tuple[str, ...] | None = None

    is_required_semantic: bool = False

    status: FieldStatus = FieldStatus.ACTIVE
    deprecated_in: str | None = None
    replaced_by: str | None = None
    introduced_in: str | None = None

    can_propose: bool = True
    human_question_es: str | None = None
    expects: str | None = None
    gate: str | None = None
    redo_if_changes: tuple[str, ...] | None = None

    label_es: str | None = None
    notes: str | None = None


# ---------------------------------------------------------------------------
# Pydantic introspection helpers
# ---------------------------------------------------------------------------


def _unwrap_optional(annotation: _AnnotationT) -> _AnnotationT:
    """Unwrap ``Optional[X]`` or ``X | None`` to ``X``.

    Handles both ``typing.Optional`` / ``typing.Union`` and PEP 604
    ``X | None`` (new in 3.10+). Polymorphic unions (2+ non-None
    variants) are returned unchanged — caller handles.
    """
    origin = get_origin(annotation)
    if origin in (Union, UnionType):
        args = [a for a in get_args(annotation) if a is not type(None)]
        if len(args) == 1:
            return args[0]
    return annotation


def _unwrap_union_variants(annotation: _AnnotationT) -> tuple[_AnnotationT, ...]:
    """Return the non-None variants of a Union / ``X | Y | None``.

    Returns ``(annotation,)`` when not a union.
    """
    origin = get_origin(annotation)
    if origin in (Union, UnionType):
        return tuple(a for a in get_args(annotation) if a is not type(None))
    return (annotation,)


def _is_pydantic_model(tp: _AnnotationT) -> bool:
    try:
        return isinstance(tp, type) and issubclass(tp, BaseModel)
    except TypeError:
        return False


def _is_list_type(tp: _AnnotationT) -> bool:
    return get_origin(tp) is list


def _list_item_annotation(tp: _AnnotationT) -> _AnnotationT:
    args = get_args(tp)
    return args[0] if args else Any


def _is_enum_subclass(tp: _AnnotationT) -> bool:
    try:
        return isinstance(tp, type) and issubclass(tp, Enum)
    except TypeError:
        return False


def _enum_values(enum_cls: type[Enum]) -> tuple[str, ...]:
    return tuple(str(m.value) for m in enum_cls)


_PRIMITIVE_LIST_ITEM_TYPES: dict[type, str] = {
    str: "text",
    int: "number",
    float: "number",
    bool: "bool",
    UUID: "uuid",
}


def _derive_list_item_type(item_annotation: _AnnotationT) -> str:
    """Derive ``list_item_type`` string from a list's item annotation."""
    inner = _unwrap_optional(item_annotation)
    if _is_pydantic_model(inner):
        return "object"
    if _is_enum_subclass(inner):
        return "enum"
    if get_origin(inner) in (Union, UnionType):
        variants = tuple(a for a in get_args(inner) if a is not type(None))
        return "enum" if any(_is_enum_subclass(v) for v in variants) else "text"
    return _PRIMITIVE_LIST_ITEM_TYPES.get(inner, "unknown")


def _derive_type(
    annotation: _AnnotationT,
) -> tuple[FieldType, tuple[str, ...] | None, str | None]:
    """Derive ``(FieldType, enum_values, list_item_type)`` from annotation."""
    inner = _unwrap_optional(annotation)

    if _is_list_type(inner):
        return FieldType.LIST, None, _derive_list_item_type(_list_item_annotation(inner))

    if _is_enum_subclass(inner):
        return FieldType.ENUM, _enum_values(inner), None

    if _is_pydantic_model(inner):
        return FieldType.OBJECT, None, None

    if get_origin(inner) in (Union, UnionType):
        variants = _unwrap_union_variants(inner)
        if all(_is_pydantic_model(v) for v in variants):
            return FieldType.OBJECT, None, None

    return _derive_primitive_type(inner), None, None


_PRIMITIVE_FIELD_TYPES: dict[type, FieldType] = {
    str: FieldType.TEXT,
    bool: FieldType.BOOL,
    int: FieldType.NUMBER,
    float: FieldType.NUMBER,
    datetime: FieldType.DATE,
    date: FieldType.DATE,
    UUID: FieldType.UUID,
}


def _derive_primitive_type(inner: _AnnotationT) -> FieldType:
    """Map a non-list, non-enum, non-model annotation to a FieldType."""
    if inner in _PRIMITIVE_FIELD_TYPES:
        return _PRIMITIVE_FIELD_TYPES[inner]
    try:
        if isinstance(inner, type) and issubclass(inner, AnyUrl):
            return FieldType.URL
    except TypeError:
        pass
    if get_origin(inner) is dict or inner is dict:
        return FieldType.DICT
    return FieldType.UNKNOWN


def _is_field_required(finfo: FieldInfo) -> bool:
    """Pydantic v2 structural-required check.

    A field is structurally required when it has no default and no
    default_factory.
    """
    return finfo.is_required()


# ---------------------------------------------------------------------------
# Walker — Pydantic -> FieldContract tuple
# ---------------------------------------------------------------------------


def derive_contracts_from_pydantic(
    *,
    model: type[BaseModel],
    owner_module: str,
    section_map: dict[str, str],
    overrides: dict[str, FieldContractOverride] | None = None,
    ignore_paths: frozenset[str] = frozenset(),
    polymorphic_prefix_map: dict[type[BaseModel], tuple[str, ...]] | None = None,
    composable_fields: tuple[str, ...] = (),
) -> tuple[FieldContract, ...]:
    """Derive a tuple of FieldContract from a Pydantic root model.

    Walks top-level fields. For composable nested Pydantic fields
    (declared in ``composable_fields``) recurses with prefix
    ``{composable_field_name}.``. For polymorphic unions (e.g.
    ``specific_details: Variant1 | Variant2 | ... | None``) recurses
    into each variant with prefix and attaches ``archetype_filter``
    from ``polymorphic_prefix_map``.

    Args:
        model: Pydantic root (e.g. ``Offer``).
        owner_module: Canonical module name for the platform registry.
        section_map: ``path -> section_slug`` mapping. Every derived
            path must have an entry (arch test enforces).
        overrides: Optional ``path -> FieldContractOverride``.
        ignore_paths: System fields to skip.
        polymorphic_prefix_map: Maps variant class to archetype values
            that select this variant.
        composable_fields: Top-level fields whose nested Pydantic
            models should be walked with prefix.

    Returns:
        Immutable tuple ordered by ``(section, -priority, path)``.
    """
    overrides = overrides or {}
    polymorphic_prefix_map = polymorphic_prefix_map or {}

    contracts: list[FieldContract] = []

    for fname, finfo in model.model_fields.items():
        if fname in ignore_paths:
            continue

        annotation = finfo.annotation

        if fname in composable_fields or _is_polymorphic_pydantic_union(annotation):
            _walk_union_or_composable(
                fname=fname,
                annotation=annotation,
                composable=fname in composable_fields,
                owner_module=owner_module,
                section_map=section_map,
                overrides=overrides,
                ignore_paths=ignore_paths,
                polymorphic_prefix_map=polymorphic_prefix_map,
                contracts=contracts,
            )
            continue

        contract = _build_contract(
            path=fname,
            finfo=finfo,
            owner_module=owner_module,
            section_map=section_map,
            overrides=overrides,
            archetype_filter=None,
        )
        if contract is not None:
            contracts.append(contract)

    contracts.sort(key=lambda c: (c.section, -c.priority, c.path))
    return tuple(contracts)


def _walk_union_or_composable(
    *,
    fname: str,
    annotation: _AnnotationT,
    composable: bool,
    owner_module: str,
    section_map: dict[str, str],
    overrides: dict[str, FieldContractOverride],
    ignore_paths: frozenset[str],
    polymorphic_prefix_map: dict[type[BaseModel], tuple[str, ...]],
    contracts: list[FieldContract],
) -> None:
    """Dispatch composable vs polymorphic handling."""
    inner = _unwrap_optional(annotation)
    variants = _unwrap_union_variants(inner)
    pydantic_variants = [v for v in variants if _is_pydantic_model(v)]

    if composable and len(pydantic_variants) == 1:
        _walk_nested(
            nested_model=pydantic_variants[0],
            path_prefix=fname,
            owner_module=owner_module,
            section_map=section_map,
            overrides=overrides,
            ignore_paths=ignore_paths,
            archetype_filter=None,
            contracts=contracts,
            dedupe_existing=False,
        )
        return

    if pydantic_variants:
        for variant in pydantic_variants:
            variant_filter = polymorphic_prefix_map.get(variant)
            _walk_nested(
                nested_model=variant,
                path_prefix=fname,
                owner_module=owner_module,
                section_map=section_map,
                overrides=overrides,
                ignore_paths=ignore_paths,
                archetype_filter=variant_filter,
                contracts=contracts,
                dedupe_existing=True,
            )


def _is_polymorphic_pydantic_union(annotation: _AnnotationT) -> bool:
    """True when annotation is ``A | B | ... | None`` and all non-None are Pydantic."""
    origin = get_origin(annotation)
    if origin not in (Union, UnionType):
        return False
    variants = [v for v in get_args(annotation) if v is not type(None)]
    return len(variants) >= 2 and all(_is_pydantic_model(v) for v in variants)


def _walk_nested(
    *,
    nested_model: type[BaseModel],
    path_prefix: str,
    owner_module: str,
    section_map: dict[str, str],
    overrides: dict[str, FieldContractOverride],
    ignore_paths: frozenset[str],
    archetype_filter: tuple[str, ...] | None,
    contracts: list[FieldContract],
    dedupe_existing: bool,
) -> None:
    """Walk a nested Pydantic model, emitting contracts with prefix.

    When ``dedupe_existing`` is True and an identical path already
    exists, merge the archetype_filter (union) instead of duplicating.
    """
    existing_paths = {c.path: c for c in contracts} if dedupe_existing else {}

    for fname, finfo in nested_model.model_fields.items():
        nested_path = f"{path_prefix}.{fname}"
        if nested_path in ignore_paths:
            continue

        contract = _build_contract(
            path=nested_path,
            finfo=finfo,
            owner_module=owner_module,
            section_map=section_map,
            overrides=overrides,
            archetype_filter=archetype_filter,
        )
        if contract is None:
            continue

        if dedupe_existing and nested_path in existing_paths:
            existing = existing_paths[nested_path]
            merged_filter = _merge_archetype_filters(existing.archetype_filter, contract.archetype_filter)
            merged = replace(existing, archetype_filter=merged_filter)
            idx = contracts.index(existing)
            contracts[idx] = merged
            existing_paths[nested_path] = merged
        else:
            contracts.append(contract)
            if dedupe_existing:
                existing_paths[nested_path] = contract


def _merge_archetype_filters(a: tuple[str, ...] | None, b: tuple[str, ...] | None) -> tuple[str, ...] | None:
    """Union of two archetype filters. ``None`` means 'all' and wins."""
    if a is None or b is None:
        return None
    return tuple(sorted(set(a) | set(b)))


def _build_contract(
    *,
    path: str,
    finfo: FieldInfo,
    owner_module: str,
    section_map: dict[str, str],
    overrides: dict[str, FieldContractOverride],
    archetype_filter: tuple[str, ...] | None,
) -> FieldContract | None:
    """Build a single FieldContract from a Pydantic field + override."""
    ftype, enum_values, list_item_type = _derive_type(finfo.annotation)

    override = overrides.get(path, FieldContractOverride())

    section = override.section or section_map.get(path)
    if section is None:
        return None

    derived_required = _is_field_required(finfo)

    return FieldContract(
        path=path,
        owner_module=owner_module,
        type=ftype,
        is_required_structural=derived_required,
        enum_values=enum_values,
        list_item_type=list_item_type,
        section=section,
        group=override.group,
        priority=override.priority if override.priority is not None else 0,
        archetype_filter=(override.archetype_filter if override.archetype_filter is not None else archetype_filter),
        value_level_filter=override.value_level_filter,
        business_type_filter=override.business_type_filter,
        preset_filter=override.preset_filter,
        is_required_semantic=(
            override.is_required_semantic if override.is_required_semantic is not None else derived_required
        ),
        status=override.status or FieldStatus.ACTIVE,
        deprecated_in=override.deprecated_in,
        replaced_by=override.replaced_by,
        introduced_in=override.introduced_in,
        can_propose=override.can_propose if override.can_propose is not None else True,
        human_question_es=override.human_question_es,
        expects=override.expects,
        gate=override.gate,
        redo_if_changes=override.redo_if_changes,
        label_es=override.label_es,
        notes=override.notes or finfo.description,
    )


# ---------------------------------------------------------------------------
# Module registry — cross-module accessors
# ---------------------------------------------------------------------------


_MODULE_CONTRACTS: dict[str, tuple[FieldContract, ...]] = {}

_LAZY_REGISTRARS: dict[str, str] = {
    "offer": "src.modules.offer.domain.field_contract",
}


def register_module_contracts(module: str, contracts: tuple[FieldContract, ...]) -> None:
    """Register (or replace) the FieldContract registry for ``module``.

    Idempotent: calling twice with the same payload is a no-op. Calling
    with different payload replaces — useful for tests.
    """
    _MODULE_CONTRACTS[module] = tuple(contracts)


def get_module_contracts(module: str) -> tuple[FieldContract, ...]:
    """Return the frozen tuple of contracts for ``module``.

    Triggers lazy registration by importing the module's registry file
    on first access, so callers don't have to manage import ordering.
    """
    if module not in _MODULE_CONTRACTS:
        _lazy_register(module)
    return _MODULE_CONTRACTS.get(module, ())


def _lazy_register(module: str) -> None:
    """Import the owner module's registry file, which registers itself."""
    registrar = _LAZY_REGISTRARS.get(module)
    if registrar is None:
        return
    try:
        __import__(registrar)
    except ImportError:
        # Owner module without a registry file yet — consumers see an
        # empty tuple. Safe default.
        return


def get_all_modules() -> tuple[str, ...]:
    """Return every registered module name sorted."""
    for module in _LAZY_REGISTRARS:
        if module not in _MODULE_CONTRACTS:
            _lazy_register(module)
    return tuple(sorted(_MODULE_CONTRACTS.keys()))


def find_contract(module: str, path: str) -> FieldContract | None:
    """Return the contract for ``(module, path)``, ``None`` if absent."""
    for c in get_module_contracts(module):
        if c.path == path:
            return c
    return None


def fields_by_section(
    module: str,
    section: str,
    *,
    archetype: str | None = None,
    status: FieldStatus = FieldStatus.ACTIVE,
) -> tuple[FieldContract, ...]:
    """Return contracts of ``module`` filtered by section.

    When ``archetype`` is given, applies ``archetype_filter`` — a
    contract with ``archetype_filter`` set but not containing
    ``archetype`` is excluded.

    When ``status`` is given (default ACTIVE), only contracts with that
    status are included.
    """
    result: list[FieldContract] = []
    for c in get_module_contracts(module):
        if c.section != section:
            continue
        if status is not None and c.status != status:
            continue
        if archetype is not None and c.archetype_filter is not None and archetype not in c.archetype_filter:
            continue
        result.append(c)
    return tuple(result)


def fields_by_path_prefix(
    module: str, prefix: str, *, status: FieldStatus = FieldStatus.ACTIVE
) -> tuple[FieldContract, ...]:
    """Return contracts whose path equals or starts with ``prefix.``.

    Useful for walking ``specific_details.*`` or ``platform_details.*``.
    """
    result: list[FieldContract] = []
    for c in get_module_contracts(module):
        if c.path == prefix or c.path.startswith(f"{prefix}."):
            if status is not None and c.status != status:
                continue
            result.append(c)
    return tuple(result)


# ---------------------------------------------------------------------------
# Versioned snapshot for HTTP endpoint consumers
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FieldContractRegistrySnapshot:
    """Versioned snapshot for HTTP endpoints.

    The ``version`` string is bumped every time a module's overrides
    change materially — clients cache by it, so a deploy invalidates
    their local cache.
    """

    version: str
    module: str
    contracts: tuple[FieldContract, ...] = field(default_factory=tuple)


__all__ = [
    "FieldContract",
    "FieldContractOverride",
    "FieldContractRegistrySnapshot",
    "FieldStatus",
    "FieldType",
    "derive_contracts_from_pydantic",
    "fields_by_path_prefix",
    "fields_by_section",
    "find_contract",
    "get_all_modules",
    "get_module_contracts",
    "register_module_contracts",
]
