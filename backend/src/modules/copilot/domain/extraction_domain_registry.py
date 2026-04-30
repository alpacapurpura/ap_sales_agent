"""Single source of truth for the document-extraction domain registry.

Each entry maps a copilot domain (``brand``, ``offer``, ``buyer_persona``) to
the assets the document-extraction pipeline needs:

* ``template_name``: Jinja2 template under
  ``infrastructure/prompts/templates/interview/`` (loaded via the shared
  ``prompt_loader``).
* ``persister_key``: key into ``persister_registry`` so the extracted delta
  can be written back to the right entity.
* ``response_value_kind``: hint about what shape the LLM is allowed to
  return per field — strings only (offer/brand) or strings + lists +
  dicts (buyer_persona, where ``pain_points``/``desires`` are arrays of
  objects).

Centralising this dict removes the duplication that previously lived in
``tools/guided/extract.py`` and ``tools/extract_from_doc.py``: both files
imported their own copy of ``_DOCUMENT_EXTRACTION_TEMPLATES`` and could
drift silently.

# [COPILOT-DOC-EXTRACTION-SSOT]
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ResponseValueKind = Literal["scalar", "mixed"]


@dataclass(frozen=True, slots=True)
class ExtractionDomainConfig:
    """Per-domain wiring for the document-extraction pipeline."""

    domain: str
    template_name: str
    persister_key: str
    response_value_kind: ResponseValueKind = "scalar"


_REGISTRY: dict[str, ExtractionDomainConfig] = {
    "brand": ExtractionDomainConfig(
        domain="brand",
        template_name="interview/brand_doc_extraction",
        persister_key="brand",
        response_value_kind="scalar",
    ),
    "offer": ExtractionDomainConfig(
        domain="offer",
        template_name="interview/offer_doc_extraction",
        persister_key="offer",
        response_value_kind="scalar",
    ),
    "buyer_persona": ExtractionDomainConfig(
        domain="buyer_persona",
        template_name="interview/buyer_persona_doc_extraction",
        persister_key="buyer_persona",
        # BuyerPersona stores pain_points/desires/purchase_triggers/anti_patterns
        # as arrays (objects or strings), so the LLM may return list[dict] or
        # list[str] values alongside scalars. The DocumentExtractionResponse
        # model is widened in document_processor to accept those shapes.
        response_value_kind="mixed",
    ),
}


def get_extraction_config(domain: str) -> ExtractionDomainConfig | None:
    """Return the config for ``domain`` or ``None`` if not registered.

    Callers should treat ``None`` as "domain not supported" — the tool
    surface returns a structured ``unsupported_domain`` error instead of
    raising.
    """
    return _REGISTRY.get(domain)


def supported_domains() -> tuple[str, ...]:
    """Return the tuple of domains that have a registered extraction config."""
    return tuple(sorted(_REGISTRY.keys()))


__all__ = [
    "ExtractionDomainConfig",
    "ResponseValueKind",
    "get_extraction_config",
    "supported_domains",
]
