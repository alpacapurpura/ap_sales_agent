"""Architecture fitness: ``variant_structure_catalog`` stays a pure base axis.

The sixth SSoT axis is deliberately at the bottom of the catalog DAG —
nothing it declares may reference other catalogs (``SectionCatalog``,
``ArchetypeCatalog``, ``OfferFormat``, ``ExpertBusinessType``). Keeping
this module free of outbound references means the upcoming catalog
rework (where ``SectionCatalog``, ``OfferFormat``, and Expert catalogs
will be reshaped) cannot churn the ``VariantStructure`` metadata.

This gate parses the catalog module as Python AST and rejects any
``import``/``from ... import`` statement that pulls another offer-studio
catalog. It also rejects imports from the shared expert-business-type
module. Imports from ``offer.domain.enums`` (the pure enum module) and
standard library are explicitly allowed.

If you need to add a cross-catalog reference, that is a sign the rule is
wrong and a design discussion is needed — do not whitelist it here. See
``docs/domains/offer/variant-structure-catalog.md`` §"Extension rules".
"""

from __future__ import annotations

import ast
from pathlib import Path

CATALOG_PATH = (
    Path(__file__).resolve().parents[2] / "src" / "modules" / "offer" / "domain" / "variant_structure_catalog.py"
)

# Any import whose dotted path STARTS with one of these prefixes is an
# illegal outbound reference. The check is prefix-based so
# ``archetype_catalog_v2`` or a sibling module at the same depth can't
# sneak in a rename escape hatch.
FORBIDDEN_IMPORT_PREFIXES: tuple[str, ...] = (
    "src.modules.offer.domain.archetype_catalog",
    "src.modules.offer.domain.section_catalog",
    "src.modules.offer.domain.format_catalog",
    "src.modules.offer.domain.value_level_catalog",
    "src.shared.domain.expert_business_type",
)

# These prefixes are explicitly allowed. The catalog legitimately needs
# the ``VariantStructure`` enum (and nothing else from ``enums.py``) plus
# standard library modules.
ALLOWED_OFFER_IMPORT_PREFIXES: tuple[str, ...] = (
    "src.modules.offer.domain.enums",
    "src.modules.offer.domain.variant_structure_catalog",  # self-reference, unlikely
)


def _collect_dotted_imports(tree: ast.Module) -> list[tuple[str, int]]:
    """Return every ``(module_path, lineno)`` referenced by import statements."""
    dotted: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            dotted.extend((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            dotted.append((node.module, node.lineno))
    return dotted


def test_catalog_file_exists() -> None:
    """Sanity check — the catalog file must exist for the other tests to run."""
    assert CATALOG_PATH.is_file(), f"Expected catalog at {CATALOG_PATH} but it was not found."


def test_no_outbound_catalog_imports() -> None:
    """No ``import`` or ``from ... import`` may reference a sibling catalog.

    Triggering conditions (all illegal):

    - ``from src.modules.offer.domain.archetype_catalog import ...``
    - ``import src.modules.offer.domain.section_catalog``
    - ``from src.modules.offer.domain.format_catalog import ...``
    - ``from src.shared.domain.expert_business_type import ...``

    Allowed neighbours:

    - ``from src.modules.offer.domain.enums import VariantStructure``
    - anything from the standard library.
    """
    source = CATALOG_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    violations = [
        f"{CATALOG_PATH.name}:{lineno} imports {module!r} — forbidden outbound reference."
        for module, lineno in _collect_dotted_imports(tree)
        if module.startswith(FORBIDDEN_IMPORT_PREFIXES)
    ]
    assert not violations, (
        "``variant_structure_catalog`` must remain a pure base axis — no "
        "imports from other catalogs. Violations:\n  " + "\n  ".join(violations)
    )


def test_only_expected_offer_module_imports() -> None:
    """Inbound-dependency surface of the catalog is tiny and exhaustively listed.

    Any import whose path starts with ``src.modules.offer`` MUST match an
    allowed prefix in ``ALLOWED_OFFER_IMPORT_PREFIXES``. New offer-module
    imports require updating this allowlist consciously — which is the
    point of the gate.
    """
    source = CATALOG_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    unexpected = [
        f"{CATALOG_PATH.name}:{lineno} imports {module!r}"
        for module, lineno in _collect_dotted_imports(tree)
        if module.startswith("src.modules.offer") and not module.startswith(ALLOWED_OFFER_IMPORT_PREFIXES)
    ]
    assert not unexpected, (
        "``variant_structure_catalog`` imports an offer-module not in the "
        "allowed list. Update ALLOWED_OFFER_IMPORT_PREFIXES only after "
        "confirming the new dependency does not couple the catalog to "
        "another axis. Unexpected:\n  " + "\n  ".join(unexpected)
    )
