"""Eval tenant seed loader.

Provides ``load_eval_tenant(archetype_slug)`` which reads the 6 YAML seed
files for a given archetype and returns an immutable ``TenantContext``.

Design decisions (per 03-arch.md):
  AD3  — TenantContext is test infrastructure, NOT a domain entity. Pure
          functional dataclass, lives only in tests/fixtures/.
  AD4  — dialect_code is a first-class BCP-47 field loaded from the seed
          YAML and validated against dialect_catalog.yaml. It is NOT added
          to any runtime Pydantic model (that is story sales-agent-dialect-
          configuration's job).
  AD6  — Missing L0 lead magnet in offer_ladder → structlog warning +
          has_lead_magnet=False. Load proceeds normally.
  AD9  — Zero production-code impact. No src/ imports from sales_agent.

Currency + dialect note (for downstream consumers):
  All 5 seed tenants use currency=PEN for test isolation (Q3 ratified).
  Dialects differ per archetype (es-PE, es-MX, es-CO, es-AR, es-419).
  Do NOT assume coupling between currency and dialect — they are
  independently parameterised in the seed data.

REPO_ROOT resolution pattern from backend/tests/scripts/test_pre_commit_hook.py:
  ``Path(__file__).resolve().parents[3]`` resolves to the repo root.
  From loader.py: tests/fixtures/eval/tenants/ → parents[3] = repo root.
  The seed YAML directory: REPO_ROOT / "backend" / "tests" / "fixtures" /
  "eval" / "tenants" / {archetype_slug} / {filename}.yaml
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog
import yaml

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Ordered list of the 5 ratified archetype slugs (Q1+Q2 ratified).
ARCHETYPE_SLUGS: tuple[str, ...] = (
    "tenant_coach_lat",
    "tenant_medicina_estetica",
    "tenant_clinica_dental",
    "tenant_agencia_growth_video",
    "tenant_agencia_automatizacion_ia",
)

#: The 6 YAML files present in each archetype sub-folder.
YAML_FILENAMES: tuple[str, ...] = (
    "brand",
    "personality_profile",
    "offer_ladder",
    "pricing",
    "buyer_personas",
    "communication_assets",
)

#: Map archetype_slug → BCP-47 dialect_code (Q7 ratified).
ARCHETYPE_DIALECT_MAP: dict[str, str] = {
    "tenant_coach_lat": "es-PE",
    "tenant_medicina_estetica": "es-MX",
    "tenant_clinica_dental": "es-CO",
    "tenant_agencia_growth_video": "es-AR",
    "tenant_agencia_automatizacion_ia": "es-419",
}

# Resolve paths relative to this file.
# parents[0] = tenants/
# parents[1] = eval/
# parents[2] = fixtures/
# parents[3] = tests/
# parents[4] = backend/
# parents[5] = repo root
_THIS_DIR: Path = Path(__file__).resolve().parent
_DIALECT_CATALOG_PATH: Path = _THIS_DIR / "dialect_catalog.yaml"


# ---------------------------------------------------------------------------
# OfferLadderContext — thin wrapper around offer_ladder.yaml
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OfferLadderContext:
    """Thin wrapper around the offer_ladder YAML content.

    Provides the ``has_lead_magnet`` computed property (per AD6).
    """

    raw: dict[str, Any]  # full parsed YAML content

    @property
    def has_lead_magnet(self) -> bool:
        """True iff the offer ladder includes an L0 (LEAD_MAGNET) entry.

        A1/A2/A3 have L0; A4/A5 intentionally do not (edge case per spec).
        """
        offers = self.raw.get("offers", [])
        if not isinstance(offers, list):
            return False
        return any((isinstance(o, dict) and o.get("level") in {"L0", "lead_magnet", "LEAD_MAGNET"}) for o in offers)


# ---------------------------------------------------------------------------
# TenantContext — immutable test-infrastructure dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TenantContext:
    """Immutable container for a fully-loaded eval seed tenant.

    Fields align with the 6 YAML files per archetype folder plus
    ``archetype_slug`` and ``dialect_code`` metadata.

    This is test infrastructure only (AD3).  It is NOT a domain entity
    and must NOT be imported from backend/src/.
    """

    archetype_slug: str
    dialect_code: str

    # Raw YAML content for schema-alignment tests and downstream consumers.
    brand: dict[str, Any]
    personality_profile: dict[str, Any]
    offer_ladder: OfferLadderContext
    pricing: dict[str, Any]
    buyer_personas: dict[str, Any]
    communication_assets: dict[str, Any]


# ---------------------------------------------------------------------------
# Dialect catalog helpers
# ---------------------------------------------------------------------------


def _load_dialect_catalog() -> dict[str, dict[str, Any]]:
    """Load dialect_catalog.yaml → code-keyed dict.

    Returns mapping {code: entry_dict} for O(1) lookup.
    Raises ``FileNotFoundError`` if catalog missing.
    """
    raw = yaml.safe_load(_DIALECT_CATALOG_PATH.read_text(encoding="utf-8"))
    return {entry["code"]: entry for entry in raw.get("dialects", [])}


def _validate_dialect_code(code: str) -> None:
    """Validate that ``code`` is listed in dialect_catalog.yaml.

    Raises ``ValueError`` if not found.
    """
    catalog = _load_dialect_catalog()
    if code not in catalog:
        valid = sorted(catalog.keys())
        msg = f"dialect_code '{code}' not found in dialect_catalog.yaml. Valid codes: {valid}"
        raise ValueError(msg)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_eval_tenant(archetype_slug: str) -> TenantContext:
    """Load a seed tenant by archetype slug.

    Reads the 6 YAML files from
    ``backend/tests/fixtures/eval/tenants/{archetype_slug}/``
    and returns an immutable ``TenantContext``.

    Parameters
    ----------
    archetype_slug:
        One of the 5 ratified slugs (see ``ARCHETYPE_SLUGS``).

    Returns
    -------
    TenantContext
        Immutable dataclass with all YAML content + computed properties.

    Raises
    ------
    ValueError
        If ``archetype_slug`` is not in ``ARCHETYPE_SLUGS``.
    FileNotFoundError
        If the archetype folder or any of the 6 YAML files is missing.
    ValueError
        If the ``dialect_code`` in personality_profile.yaml is not listed
        in dialect_catalog.yaml.
    """
    if archetype_slug not in ARCHETYPE_SLUGS:
        msg = f"Unknown archetype_slug '{archetype_slug}'. Valid slugs: {list(ARCHETYPE_SLUGS)}"
        raise ValueError(msg)

    tenant_dir = _THIS_DIR / archetype_slug

    if not tenant_dir.is_dir():
        msg = f"Tenant directory not found: {tenant_dir}. Run T-3 to create the seed YAML files."
        raise FileNotFoundError(msg)

    # ---- Load all 6 YAML files ----------------------------------------
    def _load(filename: str) -> dict[str, Any]:
        path = tenant_dir / f"{filename}.yaml"
        if not path.is_file():
            msg = f"Seed YAML missing: {path}. Run T-3 to create the seed YAML files."
            raise FileNotFoundError(msg)
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}

    brand = _load("brand")
    personality_profile = _load("personality_profile")
    offer_ladder_raw = _load("offer_ladder")
    pricing = _load("pricing")
    buyer_personas = _load("buyer_personas")
    communication_assets = _load("communication_assets")

    # ---- Resolve + validate dialect_code (AD4) -------------------------
    # The dialect_code is stored in personality_profile.yaml as a top-level
    # field (NOT a runtime Pydantic model field — that is for the
    # sales-agent-dialect-configuration story).
    dialect_code = personality_profile.get("dialect_code") or ARCHETYPE_DIALECT_MAP[archetype_slug]
    _validate_dialect_code(dialect_code)

    # ---- Compute offer_ladder wrapped context (AD6) --------------------
    offer_ladder = OfferLadderContext(raw=offer_ladder_raw)

    if not offer_ladder.has_lead_magnet:
        logger.warning(
            "offer_ladder_missing_lead_magnet",
            tenant_slug=archetype_slug,
            missing_levels=["L0"],
            note="A4+A5 intentionally skip lead magnet (entry via discovery call / portfolio).",
        )

    # ---- Build immutable TenantContext ---------------------------------
    return TenantContext(
        archetype_slug=archetype_slug,
        dialect_code=dialect_code,
        brand=brand,
        personality_profile=personality_profile,
        offer_ladder=offer_ladder,
        pricing=pricing,
        buyer_personas=buyer_personas,
        communication_assets=communication_assets,
    )
