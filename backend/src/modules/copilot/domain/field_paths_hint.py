"""Generate the "valid paths" hint that the document-extraction LLM receives.

The LLM that runs ``extract_document_to_fields`` needs to know exactly
which dot-notation paths it may emit. Without this hint it hallucinates
paths from the source document's own framework (e.g. ``buyer_persona.symptoms``
when StoryBrand-flavoured docs are uploaded), the response fails Pydantic
validation, and the tool returns ``extraction_failed``.

This module derives the hint from two existing sources of truth:

1. ``editable_fields`` catalog — the curated surface that
   ``propose_field_updates`` validates against.
2. ``schema_introspection._DOMAIN_DICT_PARENTS`` — dict-typed parents (e.g.
   ``demographics``) that accept arbitrary sub-keys via prefix matching.

Plus a lightweight, locally-declared map of which catalog paths are list
fields (so the LLM knows ``pain_points`` expects ``list[dict]``, not a
single string). Persisters validate the actual shape on persist, so this
hint is best-effort guidance, not a binding contract.
"""

from __future__ import annotations

from src.modules.copilot.domain.schema_introspection import _get_dict_parents
from src.shared.links.ports.editable_fields import FieldSpec, get_catalog

# Paths that store arrays of objects (form-runtime split-mode lists). The
# LLM is hinted to emit ``list[dict]`` for these. Keep aligned with
# BuyerPersona / Offer entity definitions; missing entries just mean the
# LLM gets the default scalar hint.
_LIST_PATHS: dict[str, set[str]] = {
    "buyer_persona": {
        "pain_points",
        "desires",
        "objections",
        "preferred_channels",
        "purchase_triggers",
        "anti_patterns",
    },
    "offer": {
        "marketing_pain_points",
        "marketing_desires",
        "deliverables",
        "pricing_options",
        "objections",
        "target_avatar_match",
    },
}


def _kind_label(domain: str, path: str) -> str:
    """Human label for the value kind (string vs list) the LLM should emit."""
    return "list" if path in _LIST_PATHS.get(domain, set()) else "string"


def _group_by_section(specs: tuple[FieldSpec, ...]) -> dict[str, list[FieldSpec]]:
    grouped: dict[str, list[FieldSpec]] = {}
    for spec in specs:
        grouped.setdefault(spec.section, []).append(spec)
    return grouped


def build_field_paths_hint(domain: str) -> str:
    """Return a Markdown hint enumerating valid paths for ``domain``.

    The hint is consumed by the document-extraction template so the LLM
    constrains its output to the editable surface. Returns empty string
    when the domain has no catalog registered (callers should skip the
    section header in that case).

    Format::

        ## Campos válidos para `<domain>`

        Solo emite estos paths. Cualquier otro será descartado.

        ### identity
        - `name` (string) — Nombre interno del avatar.
        - `tagline` (string) — Una línea que describe quién es.

        ### dynamic
        Bajo `demographics.*`, `psychographics.*`, `buyer_journey.*`
        puedes emitir nuevas sub-claves si el documento las justifica.
    """
    catalog = get_catalog(domain)
    if not catalog:
        return ""

    grouped = _group_by_section(catalog)
    lines = [
        f"## Campos válidos para `{domain}`",
        "",
        "Solo emite estos paths como claves de `extracted_fields`. Cualquier otro será descartado por validación.",
        "",
    ]

    for section_name in sorted(grouped.keys()):
        lines.append(f"### {section_name}")
        for spec in grouped[section_name]:
            kind = _kind_label(domain, spec.path)
            description = f" — {spec.description}" if spec.description else ""
            lines.append(f"- `{spec.path}` ({kind}){description}")
        lines.append("")

    dict_parents = _get_dict_parents(domain)
    if dict_parents:
        parents_md = ", ".join(f"`{p}.*`" for p in sorted(dict_parents))
        lines.extend(
            [
                "### dynamic",
                (
                    f"Bajo {parents_md} puedes emitir nuevas sub-claves "
                    "si el documento las justifica con evidencia clara."
                ),
                "",
            ],
        )

    return "\n".join(lines).rstrip() + "\n"


__all__ = ["build_field_paths_hint"]
