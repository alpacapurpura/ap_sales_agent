"""Schema Introspection Utility — Discover sections and fields dynamically from Pydantic models.

This replaces all hardcoded field name lists in copilot tools.
When you add/remove fields from any Pydantic model, the copilot detects
the change automatically via model_fields introspection.
"""

from dataclasses import dataclass, field
from typing import get_args, get_origin

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
# Populated lazily on first call per domain.
_DOMAIN_FIELD_CACHE: dict[str, set[str]] = {}


def _build_brand_paths() -> set[str]:
    """Discover all valid field paths for the 'brand' domain from BrandSettings.

    Imports lazily to avoid circular imports (copilot -> brand).
    Returns a set of valid paths: section names and section.field dot-notation.
    """
    from src.modules.brand.domain.aggregates import BrandSettings

    paths: set[str] = set()
    sections = get_model_sections(BrandSettings)
    for section_name, section_info in sections.items():
        paths.add(section_name)
        for field_name in section_info.fields:
            paths.add(f"{section_name}.{field_name}")
    return paths


def _build_offer_paths() -> set[str]:
    """Discover all valid field paths for the 'offer' domain from PERSISTABLE_FIELDS.

    Offer fields are flat (no dot-notation) — top-level entity attributes.
    PERSISTABLE_FIELDS lives in the domain layer (offer_fields.py) so this
    function stays within the domain boundary.
    """
    from src.modules.copilot.domain.offer_fields import PERSISTABLE_FIELDS

    return set(PERSISTABLE_FIELDS)


_DOMAIN_BUILDERS: dict[str, type] = {
    "brand": _build_brand_paths,  # type: ignore[assignment]
    "offer": _build_offer_paths,  # type: ignore[assignment]
}


def validate_field_path(domain: str, field_path: str) -> bool:
    """Validate that field_path exists in the domain's schema.

    Uses lazy-loaded domain model mapping. For 'brand', checks against
    BrandSettings sections (section names and section.field dot-notation).
    For 'offer', checks against PERSISTABLE_FIELDS (flat field names).
    Returns False for unknown domains or empty field_path.

    Args:
        domain: The interview domain (e.g. 'brand', 'offer').
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
        _DOMAIN_FIELD_CACHE[domain] = builder()  # type: ignore[operator]

    valid_paths = _DOMAIN_FIELD_CACHE[domain]

    # Exact match covers both section names ("identity") and dot-notation
    # paths ("identity.brand_name"). _build_brand_paths emits both forms.
    return field_path in valid_paths
