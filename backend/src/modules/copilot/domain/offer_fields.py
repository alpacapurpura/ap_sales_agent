"""Domain-layer declaration of which Offer fields the copilot may write.

Post field-contract-platform refactor (Fase 04), :data:`PERSISTABLE_FIELDS`
is **derived** from the platform :data:`OFFER_FIELD_CONTRACTS` registry
(filtered by ``can_propose=True`` + ``status=ACTIVE``). No more manual
``set[str]`` to maintain in parallel — adding/removing a writable field
happens in ``offer/domain/field_contract.py``.

Kept here as ``set[str]`` for backward-compat with existing callers
(``offer_persister.py`` validates path membership; ``schema_introspection.py``
exposes it via ``validate_field_path``).
"""

from __future__ import annotations

from luana_core_offer_studio.domain.field_contract import OFFER_FIELD_CONTRACTS
from luana_core_platform.domain.field_contract import FieldStatus


def _build_persistable_fields() -> set[str]:
    """Project the FieldContract registry to writable paths.

    Filters:
      - ``can_propose=True`` (copilot may write the field).
      - ``status=ACTIVE`` (deprecated/removed paths excluded).

    Returns a flat ``set[str]``; polymorphic paths shared across
    archetypes (e.g. ``specific_details.start_date``) appear once.
    """
    return {c.path for c in OFFER_FIELD_CONTRACTS if c.can_propose and c.status == FieldStatus.ACTIVE}


# All Offer fields the interview / copilot can write to.
# Derived — NOT manually maintained.
PERSISTABLE_FIELDS: set[str] = _build_persistable_fields()


__all__ = ["PERSISTABLE_FIELDS"]
