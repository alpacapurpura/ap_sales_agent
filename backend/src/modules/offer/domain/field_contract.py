"""FieldContract — structural SSoT for Offer schema fields.

Fase 01 pilot (pricing LATAM). FieldContract separates the **structural
contract** (path, type, ownership, requiredness, archetype filter) from
the **UX presentation layer** (label, hint, placeholder, copy) that
schemas in ``frontend/src/features/offer-studio/schemas/`` describe.

Motivation: see ``docs/refactors/field-contract-ssot/DECISIONS.md`` ADR-001.

Pilot scope: only the pricing section is modeled here. Phases 02→04 port
the remaining sections and eventually derive ``OFFER_FIELDS_BY_FE_SECTION``
from this registry.

Consumers:
- ``GET /api/v1/offer/field-contract`` serialises this registry.
- Frontend typechecks schema ``path`` literals against the generated
  ``OfferFieldPath`` TS union (codegen from the registry + Offer
  introspection).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.modules.offer.domain.enums import FieldOwner, OfferArchetype


@dataclass(frozen=True, slots=True)
class FieldContract:
    """Structural contract for a single offer-studio field.

    Immutable (frozen) + slotted so the registry can be treated as a
    compile-time constant. Mirrors the ``field-contract-ssot`` refactor
    goal: every FE schema path MUST resolve to a contract here by Fase 04.

    Attributes:
        path: Dotted path into the Offer aggregate (``headline_promise``,
            ``pricing_options``, ``specific_details.cohort_limit``, etc).
            Matches ``backend/tests/architecture/fixtures/offer_field_paths.json``.
        type: Persistence type hint ("bool", "text", "number", "list",
            "object", "enum"). Used by codegen + completion rules.
        owner: Which aggregate persists the field. ``OFFER`` for most,
            ``EDITION`` for edition-scoped ones (pricing_tiers).
        section: Section slug under ``OFFER_SECTIONS`` (e.g. ``pricing``,
            ``closing``). Drives FE grouping.
        required: Whether the field must be filled before the section is
            considered complete.
        archetype_filter: Subset of archetypes for which the field is
            visible. ``None`` = universal.
    """

    path: str
    type: str
    owner: FieldOwner
    section: str
    required: bool = False
    archetype_filter: tuple[OfferArchetype, ...] | None = None
    # Optional human-readable notes for BE consumers (sales-agent, landing).
    # NOT UX copy — that lives in FE schemas. Here for structural hints.
    notes: str | None = None


# ---------------------------------------------------------------------------
# Pricing section — 6 fields (3 legacy + 3 new LATAM, Fase 01 pilot)
# ---------------------------------------------------------------------------

PRICING_SECTION = "pricing"

PRICING_FIELD_CONTRACTS: tuple[FieldContract, ...] = (
    FieldContract(
        path="pricing_options",
        type="list",
        owner=FieldOwner.OFFER,
        section=PRICING_SECTION,
        required=True,
        notes="List of PricingStructure (plan_type, total_amount, installments, ...).",
    ),
    FieldContract(
        path="currency",
        type="text",
        owner=FieldOwner.OFFER,
        section=PRICING_SECTION,
        required=False,
        notes="ISO 4217. Falls back to TenantLocale.currency when null.",
    ),
    FieldContract(
        path="price_pay_in_full",
        type="number",
        owner=FieldOwner.OFFER,
        section=PRICING_SECTION,
        required=False,
        notes="USD equivalent for cross-currency benchmarks.",
    ),
    FieldContract(
        path="tax_included",
        type="bool",
        owner=FieldOwner.OFFER,
        section=PRICING_SECTION,
        required=False,
        notes="IVA/IGV/ICMS inclusion flag. Avoids Latam checkout disputes.",
    ),
    FieldContract(
        path="installments_available",
        type="text",
        owner=FieldOwner.OFFER,
        section=PRICING_SECTION,
        required=False,
        notes="Free-text installment counts (e.g. '3, 6, 12').",
    ),
    FieldContract(
        path="accepted_payment_providers",
        type="list",
        owner=FieldOwner.OFFER,
        section=PRICING_SECTION,
        required=False,
        notes=(
            "list[str] — IDs from sales_agent.PaymentProvider. UI-configured"
            " via Conexiones; not LLM-extracted (ADR-009)."
        ),
    ),
)


# ---------------------------------------------------------------------------
# Registry (grows per phase — pricing only in Fase 01)
# ---------------------------------------------------------------------------

_PHASE_01_CONTRACTS: tuple[FieldContract, ...] = PRICING_FIELD_CONTRACTS

FIELD_CONTRACT_REGISTRY: tuple[FieldContract, ...] = _PHASE_01_CONTRACTS


def contracts_by_section(section: str) -> tuple[FieldContract, ...]:
    """Return all contracts for a given section slug."""
    return tuple(fc for fc in FIELD_CONTRACT_REGISTRY if fc.section == section)


@dataclass(frozen=True, slots=True)
class FieldContractRegistrySnapshot:
    """Versioned snapshot returned by ``/api/v1/offer/field-contract``.

    The ``version`` string is bumped every time the registry changes —
    clients cache by it, so a deploy invalidates their local cache.
    """

    version: str
    contracts: tuple[FieldContract, ...] = field(default_factory=tuple)


# Bump when the registry changes materially.
FIELD_CONTRACT_VERSION = "2026-04-24-fase-01-pricing-pilot"

FIELD_CONTRACT_SNAPSHOT = FieldContractRegistrySnapshot(
    version=FIELD_CONTRACT_VERSION,
    contracts=FIELD_CONTRACT_REGISTRY,
)
