import datetime
import secrets
import string
import uuid
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.iam.domain.tenant import Tenant
from src.shared.domain.datetime_utils import utc_now
from src.shared.links.models import ShareableLink

logger = structlog.get_logger()


class LinkService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def generate_token(self, length: int = 12) -> str:
        """
        Generates a URL-safe unique token.
        Combines random chars with a timestamp component to ensure low collision probability.
        """
        # 1. Random Component
        alphabet = string.ascii_letters + string.digits
        random_part = "".join(secrets.choice(alphabet) for _ in range(length))

        # 2. Timestamp Component (hex) - ensures temporal uniqueness
        timestamp_hex = f"{int(utc_now().timestamp()):x}"

        return f"{random_part}{timestamp_hex}"

    def create_link(
        self,
        tenant_id: uuid.UUID,
        target_type: str,
        params: dict[str, Any] | None = None,
        expires_days: int | None = None,
        created_by: uuid.UUID | None = None,
    ) -> ShareableLink:
        """
        Creates a new secure shareable link.
        """
        if params is None:
            params = {}
        token = self.generate_token()

        expires_at = None
        if expires_days:
            expires_at = utc_now() + datetime.timedelta(days=expires_days)

        link = ShareableLink(
            tenant_id=tenant_id,
            token=token,
            target_type=target_type,
            params=params,
            expires_at=expires_at,
            created_by=created_by,
            is_active=True,
        )

        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)

        logger.info(
            "link_created",
            token=token,
            tenant_id=str(tenant_id),
            type=target_type,
        )
        return link

    def resolve_link(self, token: str) -> ShareableLink | None:
        """
        Validates and retrieves a link.
        Checks: Exists, Is Active, Not Expired.
        Increments visit count.
        """
        stmt = select(ShareableLink).where(ShareableLink.token == token)
        link = self.db.execute(stmt).scalar_one_or_none()

        if not link:
            logger.warning("link_resolution_failed", reason="not_found", token=token)
            return None

        if not link.is_active:
            logger.warning("link_resolution_failed", reason="inactive", token=token)
            return None

        if link.expires_at and link.expires_at.replace(tzinfo=None) < utc_now().replace(
            tzinfo=None,
        ):
            logger.warning("link_resolution_failed", reason="expired", token=token)
            return None

        # Update Audit
        link.visit_count += 1
        link.last_visited_at = utc_now()
        self.db.commit()

        return link

    def revoke_link(self, token: str) -> bool:
        stmt = select(ShareableLink).where(ShareableLink.token == token)
        link = self.db.execute(stmt).scalar_one_or_none()

        if link:
            link.is_active = False
            self.db.commit()
            logger.info("link_revoked", token=token)
            return True
        return False

    def get_tenant_for_link(self, link: ShareableLink) -> Tenant | None:
        return self.db.get(Tenant, link.tenant_id)
