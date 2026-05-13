"""BrandFieldApplyAdapter — concrete write-side adapter (B22-FP1).

Implements ``BrandFieldApplyPort`` so the copilot ``MutationApplyService``
can persist ProposalCard field updates without taking a direct dependency
on ``BrandRepository`` (preserves the F1 ratchet on new ``copilot -> module``
imports).

Walks ``field_path`` (dot-notation, e.g. ``identity.brand_name``) on the
current ``BrandSettings`` payload, sets the leaf, and re-saves through
the brand repository which validates via Pydantic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from luana_core_brand_studio.domain import BrandSettings
from luana_core_brand_studio.infrastructure.repositories.brand_repository import (
    BrandRepository,
)
from luana_core_platform.links.ports.brand import BrandFieldApplyPort

if TYPE_CHECKING:
    from uuid import UUID

logger = structlog.get_logger()


def _set_path(payload: dict[str, Any], path: str, value: Any) -> None:  # noqa: ANN401
    """Walk ``path`` on ``payload`` and set the leaf to ``value``.

    Intermediate dicts are created on demand so partial settings (e.g. a
    tenant who never saved ``identity``) accept their first write.
    """
    parts = path.split(".")
    cursor: dict[str, Any] = payload
    for key in parts[:-1]:
        nxt = cursor.get(key)
        if not isinstance(nxt, dict):
            nxt = {}
            cursor[key] = nxt
        cursor = nxt
    cursor[parts[-1]] = value


class BrandFieldApplyAdapter(BrandFieldApplyPort):
    """Concrete adapter writing one brand field per call."""

    def __init__(self, db: Any) -> None:  # noqa: ANN401
        """Initialize with a database session."""
        self._db = db

    def apply_field(
        self,
        tenant_id: UUID,
        field_path: str,
        new_value: Any,  # noqa: ANN401
    ) -> None:
        """Persist ``new_value`` at ``field_path`` for ``tenant_id``.

        Round-trips through ``BrandSettings`` Pydantic validation so any
        invalid value raises before the repository write.
        """
        repo = BrandRepository(self._db)
        current = repo.get_settings(tenant_id)
        payload = current.model_dump(mode="json")
        _set_path(payload, field_path, new_value)
        settings = BrandSettings.model_validate(payload)
        repo.save_settings(tenant_id, settings)
        logger.info(
            "brand_field_applied",
            tenant_id=str(tenant_id),
            field_path=field_path,
        )
