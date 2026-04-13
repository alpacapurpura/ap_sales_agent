from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.offer.infrastructure.models.product_model import (
    ProductModel as Product,
)


class BusinessRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_current_launch_product(self):
        # Find active product and return it with its stage name
        product = (
            self.db.execute(select(Product).where(Product.status == "active"))
            .scalars()
            .first()
        )
        if product:
            return product, "evergreen"
        return None, None

    def get_enrollment(self, user_id, product_id):
        # Placeholder: Return None until Enrollment model is restored/found
        return None

    def close(self):
        self.db.close()
