"""Referral code generation, management, and Shopify extraction service."""

import logging
import secrets
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.modules.crm.infrastructure.models.referral_code_model import ReferralCodeModel

logger = logging.getLogger(__name__)


class ReferralService:
    """Manage referral codes for evangelist customers."""

    def __init__(self, db: Session):
        self.db = db

    def generate_code(self, tenant_id: UUID, customer_id: UUID) -> ReferralCodeModel:
        """Generate unique referral code: REF-XXXXXX (6 alphanumeric chars).

        Uses secrets.token_urlsafe(4), strips non-alphanumeric, uppercases, takes first 6.
        Retries up to 3 times on unique constraint violation.
        """
        for attempt in range(3):
            raw = secrets.token_urlsafe(6)
            suffix = "".join(c for c in raw if c.isalnum()).upper()[:6]
            code = f"REF-{suffix}"

            record = ReferralCodeModel(
                tenant_id=tenant_id,
                customer_id=customer_id,
                code=code,
                source="internal",
                is_active=True,
            )
            self.db.add(record)
            try:
                self.db.flush()
                logger.info(
                    "Referral code generated: %s for customer %s (tenant %s)",
                    code,
                    customer_id,
                    tenant_id,
                )
                return record
            except IntegrityError:
                self.db.rollback()
                logger.warning(
                    "Referral code collision on attempt %d: %s", attempt + 1, code
                )
                if attempt == 2:
                    raise

        # Should never reach here due to raise above, but satisfy type checker
        raise RuntimeError("Failed to generate unique referral code after 3 attempts")

    def get_codes_by_tenant(
        self, tenant_id: UUID, active_only: bool = True
    ) -> list[ReferralCodeModel]:
        """List all referral codes for tenant. Filter by is_active if active_only."""
        stmt = select(ReferralCodeModel).where(ReferralCodeModel.tenant_id == tenant_id)
        if active_only:
            stmt = stmt.where(ReferralCodeModel.is_active.is_(True))
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def get_code_by_customer(
        self, tenant_id: UUID, customer_id: UUID
    ) -> ReferralCodeModel | None:
        """Get active referral code for a specific customer."""
        stmt = select(ReferralCodeModel).where(
            ReferralCodeModel.tenant_id == tenant_id,
            ReferralCodeModel.customer_id == customer_id,
            ReferralCodeModel.is_active.is_(True),
        )
        result = self.db.execute(stmt)
        return result.scalars().first()

    def deactivate_code(self, tenant_id: UUID, code_id: UUID) -> None:
        """Soft-deactivate a referral code (set is_active=False)."""
        stmt = select(ReferralCodeModel).where(
            ReferralCodeModel.id == code_id,
            ReferralCodeModel.tenant_id == tenant_id,
        )
        result = self.db.execute(stmt)
        record = result.scalars().first()
        if record:
            record.is_active = False
            self.db.flush()
            logger.info("Referral code %s deactivated", code_id)

    async def extract_shopify_codes(
        self, tenant_id: UUID, shop_domain: str, access_token: str
    ) -> list[ReferralCodeModel]:
        """Read existing discount codes from Shopify Admin GraphQL API.

        Query: codeDiscountNodes(first: 50) -> extract codes -> upsert with source='shopify'.
        Read-only: does NOT push codes to Shopify.
        """
        import httpx

        url = f"https://{shop_domain}/admin/api/2024-01/graphql.json"
        query = """
        {
            codeDiscountNodes(first: 50) {
                nodes {
                    codeDiscount {
                        ... on DiscountCodeBasic {
                            title
                            codes(first: 10) {
                                nodes {
                                    code
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        imported: list[ReferralCodeModel] = []
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    url,
                    json={"query": query},
                    headers={
                        "X-Shopify-Access-Token": access_token,
                        "Content-Type": "application/json",
                    },
                    timeout=15.0,
                )
                resp.raise_for_status()
                data = resp.json()

            nodes = data.get("data", {}).get("codeDiscountNodes", {}).get("nodes", [])

            for node in nodes:
                discount = node.get("codeDiscount", {})
                codes_data = discount.get("codes", {}).get("nodes", [])
                for code_node in codes_data:
                    code_str = code_node.get("code", "")
                    if not code_str:
                        continue

                    # Check if already exists
                    existing = (
                        self.db.execute(
                            select(ReferralCodeModel).where(
                                ReferralCodeModel.code == code_str,
                                ReferralCodeModel.tenant_id == tenant_id,
                            )
                        )
                        .scalars()
                        .first()
                    )

                    if existing:
                        continue

                    record = ReferralCodeModel(
                        tenant_id=tenant_id,
                        customer_id=None,  # Shopify codes may not map to a customer yet
                        code=code_str,
                        source="shopify",
                        is_active=True,
                    )
                    self.db.add(record)
                    imported.append(record)

            if imported:
                self.db.flush()
                logger.info(
                    "Imported %d Shopify discount codes for tenant %s",
                    len(imported),
                    tenant_id,
                )

        except Exception as e:
            logger.error(
                "Failed to extract Shopify codes for tenant %s: %s",
                tenant_id,
                str(e),
            )

        return imported
