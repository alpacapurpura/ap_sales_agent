"""Business repository."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from src.shared.links.ports.offer import get_product_model_class

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.modules.offer.infrastructure.models.product_model import ProductModel as Product


class BusinessRepository:
    """Repository for business persistence."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def get_current_launch_product(self) -> tuple[Product | None, str | None]:
        """Retrieve current launch product."""
        product_cls = get_product_model_class()
        product = self.db.execute(select(product_cls).where(product_cls.status == "active")).scalars().first()
        if product:
            return product, "evergreen"
        return None, None

    def get_enrollment(self, user_id: UUID, product_id: UUID) -> None:
        """Retrieve enrollment."""
        # Placeholder: Return None until Enrollment model is restored/found

    def close(self) -> None:
        """Close."""
        self.db.close()
