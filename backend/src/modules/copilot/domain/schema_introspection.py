"""Schema Introspection Utility — Discover sections and fields dynamically from Pydantic models.

Complementary to the editable-fields SSoT exposed via
``src.shared.links.ports.editable_fields``:

* ``get_model_sections`` and ``validate_field_path`` introspect the live
  Pydantic models for READ-side features (awareness, nudges, module_data).
* The editable-fields port defines the CANONICAL WRITE surface — what the
  copilot may propose via ``propose_field_updates``. The two are aligned
  by convention (legacy fields removed from the port but still present in
  the model for back-compat).
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import get_args, get_origin

from luana_core_platform.links.ports.editable_fields import (
    FieldSpec,
    get_catalog,
    get_registered_domains,
)
from pydantic import BaseModel


@dataclass
class SectionInfo:
    """Metadata about a section (nested Pydantic model) within a root model."""

    name: str  # Field name in the parent model (e.g. "identity")
    label: str  # Human-readable label (e.g. "Identidad")
    description: str  # From field_info.description or auto-generated
    fields: list[str] = field(default_factory=list)  # Sub-field names
    field_descriptions: dict[str, str] = field(default_factory=dict)  # fname -> label
    is_list: bool = False  # True if this is a List[Model] section
    inner_type_name: str = ""  # Name of the inner Pydantic model


@dataclass
class CompletionStatus:
    """Completion status for a single section."""

    filled: int = 0
    total: int = 0
    is_configured: bool = False
    details: dict[str, bool] = field(default_factory=dict)  # field_name -> has_value


def unwrap_optional(annotation: type) -> type:
    """Unwrap Optional[X] -> X, handling Union[X, None]."""
    origin = get_origin(annotation)
    if origin is type(None):
        return annotation

    # Handle Optional[X] which is Union[X, None]
    args = get_args(annotation)
    if args:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return non_none[0]
    return annotation


def is_pydantic_model(tp: type) -> bool:
    """Check if a type is a Pydantic BaseModel subclass."""
    try:
        return isinstance(tp, type) and issubclass(tp, BaseModel)
    except TypeError:
        return False


def is_list_of_pydantic(tp: type) -> bool:
    """Check if type is List[SomePydanticModel]."""
    origin = get_origin(tp)
    if origin is list:
        args = get_args(tp)
        if args and is_pydantic_model(args[0]):
            return True
    return False


def is_list_type(tp: type) -> bool:
    """Check if type is any List[...]."""
    return get_origin(tp) is list


def get_model_sections(model_class: type[BaseModel]) -> dict[str, SectionInfo]:
    """Discover sections and fields of any Pydantic model dynamically.

    A "section" is a field whose type is:
    - Another Pydantic BaseModel (nested object with sub-fields)
    - A List[BaseModel] (list of structured items)
    - A List[simple_type] (list of primitives)

    Returns a dict mapping field_name -> SectionInfo.
    """
    sections: dict[str, SectionInfo] = {}

    for name, field_info in model_class.model_fields.items():
        annotation = field_info.annotation
        inner_type = unwrap_optional(annotation)

        label = field_info.description or _humanize(name)

        if is_pydantic_model(inner_type):
            # Nested model = section with sub-fields
            sub_fields = list(inner_type.model_fields.keys())
            field_descs = {
                fname: finfo.description or _humanize(fname) for fname, finfo in inner_type.model_fields.items()
            }
            sections[name] = SectionInfo(
                name=name,
                label=label,
                description=f"Sección con {len(sub_fields)} campos",
                fields=sub_fields,
                field_descriptions=field_descs,
                is_list=False,
                inner_type_name=inner_type.__name__,
            )
        elif is_list_of_pydantic(inner_type):
            # Handle list of Pydantic models
            item_type = get_args(inner_type)[0]
            sub_fields = list(item_type.model_fields.keys())
            field_descs = {
                fname: finfo.description or _humanize(fname) for fname, finfo in item_type.model_fields.items()
            }
            sections[name] = SectionInfo(
                name=name,
                label=label,
                description=f"Lista de {item_type.__name__}",
                fields=sub_fields,
                field_descriptions=field_descs,
                is_list=True,
                inner_type_name=item_type.__name__,
            )
        elif is_list_type(inner_type):
            # List of primitives
            sections[name] = SectionInfo(
                name=name,
                label=label,
                description="Lista de elementos",
                is_list=True,
            )

    return sections


def check_section_completion(
    data: dict,
    sections: dict[str, SectionInfo],
) -> dict[str, CompletionStatus]:
    """Check completion status dynamically — NEVER hardcodes field names.

    Args:
        data: model_dump() output (dict)
        sections: Output of get_model_sections()

    Returns:
        Dict mapping section_name -> CompletionStatus

    """
    results: dict[str, CompletionStatus] = {}

    for name, section in sections.items():
        section_data = data.get(name)

        if section.is_list:
            # List sections: configured if at least one item exists
            items = section_data or []
            count = len(items) if isinstance(items, list) else 0
            results[name] = CompletionStatus(
                filled=count,
                total=1,  # "at least one" threshold
                is_configured=count > 0,
            )
        elif isinstance(section_data, dict):
            # Nested object: count non-empty values
            total_fields = len(section.fields) if section.fields else len(section_data)
            details = {}
            filled = 0
            for key in section.fields or section_data.keys():
                val = section_data.get(key)
                has_value = val not in (None, "", [], {})
                details[key] = has_value
                if has_value:
                    filled += 1
            results[name] = CompletionStatus(
                filled=filled,
                total=total_fields,
                is_configured=filled > 0,
                details=details,
            )
        else:
            # Scalar or None — not configured if None/empty
            has_value = section_data not in (None, "", [], {})
            results[name] = CompletionStatus(
                filled=1 if has_value else 0,
                total=1,
                is_configured=has_value,
            )

    return results


def format_completion_markdown(
    module_label: str,
    completion: dict[str, CompletionStatus],
    sections: dict[str, SectionInfo],
) -> str:
    """Render completion status as markdown for LLM consumption."""
    configured_count = sum(1 for s in completion.values() if s.is_configured)
    total = len(completion)

    lines = [
        f"### {'✅' if configured_count == total else '⚠️'} {module_label} ({configured_count}/{total} secciones)",
    ]

    for name, status in completion.items():
        section_info = sections.get(name)
        label = section_info.label if section_info else _humanize(name)
        icon = "✓" if status.is_configured else "✗"

        if status.is_configured and status.total > 1:
            lines.append(f"  {icon} {label}: {status.filled}/{status.total} campos")
        elif status.is_configured:
            lines.append(f"  {icon} {label}: configurado")
        else:
            lines.append(f"  {icon} {label}: pendiente")

    return "\n".join(lines)


def _humanize(name: str) -> str:
    """Convert snake_case to Title Case."""
    return name.replace("_", " ").title()


# Module-level cache: domain -> set of valid field paths.
# Populated lazily on first call per domain. The FieldContract registry
# is immutable post-bootstrap, so the cached projection is also immutable.
_DOMAIN_FIELD_CACHE: dict[str, set[str]] = {}


def _build_brand_paths() -> set[str]:
    """Discover all valid field paths for the 'brand' domain.

    Post-Fase-08 deriva del FieldContract registry. La unión incluye
    los paths de los contracts (``identity.brand_name``, etc.) **y**
    los nombres de section bare (``identity``, ``story``, ``positioning``,
    ``narrative``, ``visuals``…) — preservando la validación legacy
    que ``get_model_sections(BrandSettings)`` permitía.
    """
    from luana_core_platform.domain.field_contract import get_module_contracts

    contracts = get_module_contracts("brand")
    paths: set[str] = {c.path for c in contracts}
    paths |= {c.section for c in contracts}
    return paths


def _build_offer_paths() -> set[str]:
    """Discover all valid field paths for the 'offer' domain.

    Post-Fase-08 deriva directo del FieldContract registry. Equivalente
    matemáticamente a ``PERSISTABLE_FIELDS`` (que también deriva del
    mismo registry) pero sin la indirección — un único origen de verdad.
    """
    from luana_core_platform.domain.field_contract import (
        FieldStatus,
        get_module_contracts,
    )

    return {c.path for c in get_module_contracts("offer") if c.can_propose and c.status == FieldStatus.ACTIVE}


def _build_buyer_persona_paths() -> set[str]:
    """Discover all valid field paths for the 'buyer_persona' domain.

    Post-Fase-08 deriva del FieldContract registry. Los 3 dict parents
    (``demographics``, ``psychographics``, ``buyer_journey``) NO se incluyen
    en el set — la validación del bare name acepta dot-notation con
    prefix match (ver :data:`_DOMAIN_DICT_PARENTS`).
    """
    from luana_core_platform.domain.field_contract import get_module_contracts

    return {c.path for c in get_module_contracts("buyer_persona")}


def _build_buyer_persona_dict_parents() -> set[str]:
    """Derive the set of dict_parent names from BUYER_PERSONA_DICT_SUBKEYS.

    Lazy import (avoid circular: copilot -> brand) and runtime call so the
    set stays in sync if a sub-key parent is added in the registry.
    """
    from luana_core_brand_studio.domain.buyer_persona_field_contract import (
        BUYER_PERSONA_DICT_SUBKEYS,
    )

    return set(BUYER_PERSONA_DICT_SUBKEYS.keys())


# Dict-field parents per domain: any dot-notation path whose prefix is in this
# set is accepted even if the exact path was not pre-registered.  This allows
# the LLM to use new sub-keys (e.g. demographics.marital_status) without
# requiring a code change.
#
# Post-Fase-08 the value for ``buyer_persona`` is derived from
# ``BUYER_PERSONA_DICT_SUBKEYS.keys()`` via :func:`_build_buyer_persona_dict_parents`.
# A cached frozen set keeps the lookup constant-time.
_DOMAIN_DICT_PARENTS: dict[str, set[str]] = {}


def _get_dict_parents(domain: str) -> set[str]:
    """Return the dict_parent set for ``domain`` (lazy + cached)."""
    if domain in _DOMAIN_DICT_PARENTS:
        return _DOMAIN_DICT_PARENTS[domain]
    if domain == "buyer_persona":
        _DOMAIN_DICT_PARENTS[domain] = _build_buyer_persona_dict_parents()
        return _DOMAIN_DICT_PARENTS[domain]
    return set()


_DOMAIN_BUILDERS: dict[str, Callable[[], set[str]]] = {
    "brand": _build_brand_paths,
    "offer": _build_offer_paths,
    "buyer_persona": _build_buyer_persona_paths,
}


def validate_field_path(domain: str, field_path: str) -> bool:
    """Validate that field_path exists in the domain's schema.

    Uses lazy-loaded domain model mapping. For 'brand', checks against
    BrandSettings sections (section names and section.field dot-notation).
    For 'offer', checks against PERSISTABLE_FIELDS (flat field names).
    For 'buyer_persona', checks against known interview fields; additionally
    accepts any dot-notation path whose parent is a known dict field
    (e.g. ``demographics.<anything>``).
    Returns False for unknown domains or empty field_path.

    Args:
        domain: The interview domain (e.g. 'brand', 'offer', 'buyer_persona').
        field_path: Dot-notation or flat field path to validate.

    Returns:
        True if the path is valid for the domain, False otherwise.

    """
    if not field_path:
        return False

    if domain not in _DOMAIN_BUILDERS:
        return False

    if domain not in _DOMAIN_FIELD_CACHE:
        builder = _DOMAIN_BUILDERS[domain]
        _DOMAIN_FIELD_CACHE[domain] = builder()

    valid_paths = _DOMAIN_FIELD_CACHE[domain]

    # Exact match covers both section names ("identity") and dot-notation
    # paths ("identity.brand_name"). _build_brand_paths emits both forms.
    if field_path in valid_paths:
        return True

    # Prefix fallback: for domains with dict fields, accept any dot-notation
    # path whose parent is a registered dict field (e.g. demographics.*)
    dict_parents = _get_dict_parents(domain)
    if dict_parents and "." in field_path:
        parent = field_path.split(".", 1)[0]
        return parent in dict_parents

    return False


# ── Editable-fields SSoT helpers ─────────────────────────────────────────
# These helpers consume the editable-fields port
# (``src.shared.links.ports.editable_fields``) so the copilot stays
# decoupled from the owner modules. They power the system prompt catalog
# and the ``propose_field_updates`` validator.


def is_editable_path(domain: str, field_path: str) -> bool:
    """Return True iff ``field_path`` is in the editable-fields catalog of ``domain``.

    Distinct from :func:`validate_field_path`: the latter accepts *any*
    schema path (including legacy fields still living in the model),
    whereas this one honors the curated editable surface.
    """
    if not field_path or not domain:
        return False
    paths = {f.path for f in get_catalog(domain)}
    return field_path in paths


def _group_by_section(fields: tuple[FieldSpec, ...]) -> dict[str, list[FieldSpec]]:
    groups: dict[str, list[FieldSpec]] = {}
    for f in fields:
        groups.setdefault(f.section, []).append(f)
    return groups


def format_editable_field_catalog_markdown(domain: str) -> str:
    """Render the editable-field catalog of ``domain`` as compact markdown.

    Injected into the copilot's system prompt so the LLM can only propose
    ``field_id``s that actually exist in the UI. Empty string when the
    domain has no catalog registered — callers should treat that as
    "no editable surface to advertise".
    """
    catalog = get_catalog(domain)
    if not catalog:
        return ""
    grouped = _group_by_section(catalog)
    lines = [f"### {domain}"]
    for section_name in sorted(grouped.keys()):
        lines.append(f"- **{section_name}**")
        for spec in grouped[section_name]:
            suffix = f" — {spec.description}" if spec.description else ""
            lines.append(f"  - `{spec.path}` · {spec.label}{suffix}")
    return "\n".join(lines)


def format_all_editable_catalogs_markdown() -> str:
    """Render every registered domain's catalog as one markdown block.

    Used by the system-prompt builder so the LLM sees the whole editable
    surface in one place. Blocks are separated by a blank line.
    """
    blocks = [format_editable_field_catalog_markdown(d) for d in get_registered_domains()]
    return "\n\n".join(b for b in blocks if b)
