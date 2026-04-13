"""Registry for interview context loaders.

Each context loader knows how to fetch domain-specific context
(e.g., existing offers, brand data) to inject into interview prompts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.copilot.infrastructure.context.offer_context_loader import (
    OfferContextLoader,
)

CONTEXT_LOADERS: dict[str, type] = {
    "offer_context": OfferContextLoader,
}


def get_context_loader(key: str, db: AsyncSession) -> OfferContextLoader:
    """Get context loader by key.

    Args:
        key: Registry key (e.g., 'offer_context').
        db: AsyncSession for database queries.

    Returns:
        Instantiated context loader.

    Raises:
        ValueError: If no loader is registered for the given key.

    """
    loader_cls = CONTEXT_LOADERS.get(key)
    if not loader_cls:
        msg = f"No context loader registered for key: {key}"
        raise ValueError(msg)
    return loader_cls(db)
