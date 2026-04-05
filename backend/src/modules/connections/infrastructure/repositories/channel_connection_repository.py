from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.connections.domain.channel import ChannelConnection
from src.modules.connections.domain.enums import ChannelType
from src.modules.connections.infrastructure.models.channel_connection_model import (
    ChannelConnectionModel,
)


class ChannelConnectionRepository:
    """
    Repository for ChannelConnection entities.
    Encapsulates all DB access for channel_connections using SQLAlchemy 2.0 syntax.
    Credentials are encrypted/decrypted transparently by the EncryptedJSON column type.
    """

    def __init__(self, db: Session):
        self.db = db

    # --- Mapping ---

    def _to_domain(self, model: ChannelConnectionModel) -> ChannelConnection:
        return ChannelConnection(
            id=model.id,
            tenant_id=model.tenant_id,
            channel_type=ChannelType(model.channel_type),
            credentials=model.credentials or {},
            config=model.config or {},
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    # --- Queries ---

    def get_active(
        self, tenant_id: UUID, channel_type: ChannelType
    ) -> ChannelConnectionModel | None:
        """Get the active connection for a tenant + channel type."""
        stmt = select(ChannelConnectionModel).where(
            ChannelConnectionModel.tenant_id == tenant_id,
            ChannelConnectionModel.channel_type == channel_type.value,
            ChannelConnectionModel.is_active.is_(True),
        )
        return self.db.execute(stmt).scalars().first()

    def get_by_tenant_and_type(
        self, tenant_id: UUID, channel_type: ChannelType
    ) -> ChannelConnectionModel | None:
        """Get connection (active or not) for a tenant + channel type."""
        stmt = select(ChannelConnectionModel).where(
            ChannelConnectionModel.tenant_id == tenant_id,
            ChannelConnectionModel.channel_type == channel_type.value,
        )
        return self.db.execute(stmt).scalars().first()

    def get_all_by_tenant_and_types(
        self, tenant_id: UUID, channel_types: list[ChannelType]
    ) -> list[ChannelConnectionModel]:
        """Get all connections (active or not) for a tenant filtered by a list of channel types."""
        type_values = [ct.value for ct in channel_types]
        stmt = select(ChannelConnectionModel).where(
            ChannelConnectionModel.tenant_id == tenant_id,
            ChannelConnectionModel.channel_type.in_(type_values),
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_by_asset_id(
        self, tenant_id: UUID, channel_type: ChannelType, asset_id: str
    ) -> ChannelConnectionModel | None:
        """Get a specific asset connection by its stored asset_id in config."""
        stmt = select(ChannelConnectionModel).where(
            ChannelConnectionModel.tenant_id == tenant_id,
            ChannelConnectionModel.channel_type == channel_type.value,
            ChannelConnectionModel.config["asset_id"].astext == asset_id,
        )
        return self.db.execute(stmt).scalars().first()

    def get_all_active_by_type(
        self, channel_types: list[str]
    ) -> list[ChannelConnectionModel]:
        """Get all active connections across tenants for given channel types."""
        stmt = select(ChannelConnectionModel).where(
            ChannelConnectionModel.channel_type.in_(channel_types),
            ChannelConnectionModel.is_active.is_(True),
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_all_by_tenant(self, tenant_id: UUID) -> list[ChannelConnectionModel]:
        """Get all connections for a tenant."""
        stmt = select(ChannelConnectionModel).where(
            ChannelConnectionModel.tenant_id == tenant_id
        )
        return list(self.db.execute(stmt).scalars().all())

    @staticmethod
    def _normalize_shop_domain(shop: str) -> str:
        normalized = (
            shop.replace("https://", "")
            .replace("http://", "")
            .strip()
            .strip("/")
            .lower()
        )
        if not normalized.endswith("myshopify.com") and "." not in normalized:
            normalized = f"{normalized}.myshopify.com"
        return normalized

    def get_active_shopify_by_shop(self, shop: str) -> ChannelConnectionModel | None:
        normalized_shop = self._normalize_shop_domain(shop)
        stmt = select(ChannelConnectionModel).where(
            ChannelConnectionModel.channel_type == ChannelType.SHOPIFY.value,
            ChannelConnectionModel.is_active.is_(True),
        )
        connections = self.db.execute(stmt).scalars().all()

        for connection in connections:
            config = connection.config or {}
            shop_url = config.get("shop_url")
            shop_info = config.get("shop_info") or {}
            shop_info_domain = shop_info.get("domain")

            candidates = [shop_url, shop_info_domain]
            for candidate in candidates:
                if not candidate:
                    continue
                if self._normalize_shop_domain(candidate) == normalized_shop:
                    return connection

        return None

    # --- Mutations ---

    def create_asset(
        self,
        tenant_id: UUID,
        channel_type: ChannelType,
        credentials: dict,
        config: dict,
    ) -> ChannelConnectionModel:
        """Create a new asset connection row. Unlike upsert(), this always inserts.

        Use for asset channel types (FACEBOOK_PAGE, INSTAGRAM_ACCOUNT, META_ADS_ACCOUNT)
        where multiple rows per tenant per type are expected.
        """
        connection = ChannelConnectionModel(
            tenant_id=tenant_id,
            channel_type=channel_type.value,
            credentials=credentials,
            config=config,
            is_active=True,
        )
        self.db.add(connection)
        self.db.commit()
        self.db.refresh(connection)
        return connection

    def upsert(
        self,
        tenant_id: UUID,
        channel_type: ChannelType,
        credentials: dict,
        config: dict,
    ) -> ChannelConnectionModel:
        """Create or update a connection. The most common operation across all routers."""
        connection = self.get_by_tenant_and_type(tenant_id, channel_type)

        if connection:
            connection.credentials = credentials
            connection.config = config
            connection.is_active = True
        else:
            connection = ChannelConnectionModel(
                tenant_id=tenant_id,
                channel_type=channel_type.value,
                credentials=credentials,
                config=config,
                is_active=True,
            )
            self.db.add(connection)

        self.db.commit()
        self.db.refresh(connection)
        return connection

    def update_config(
        self, connection: ChannelConnectionModel, config_updates: dict
    ) -> ChannelConnectionModel:
        """Merge updates into config JSONB."""
        from sqlalchemy.orm.attributes import flag_modified

        current = dict(connection.config) if connection.config else {}
        current.update(config_updates)
        connection.config = current
        flag_modified(connection, "config")
        self.db.commit()
        self.db.refresh(connection)
        return connection

    def update_credentials(
        self, connection: ChannelConnectionModel, credentials: dict
    ) -> ChannelConnectionModel:
        """Replace credentials."""
        connection.credentials = credentials
        self.db.commit()
        self.db.refresh(connection)
        return connection

    def deactivate(self, connection: ChannelConnectionModel) -> ChannelConnectionModel:
        """Soft-delete: set is_active = False."""
        connection.is_active = False
        self.db.commit()
        self.db.refresh(connection)
        return connection

    def activate(self, connection: ChannelConnectionModel) -> ChannelConnectionModel:
        """Re-activate a deactivated connection."""
        connection.is_active = True
        self.db.commit()
        self.db.refresh(connection)
        return connection

    def revoke(self, connection: ChannelConnectionModel) -> ChannelConnectionModel:
        """Full OAuth revocation: clear credentials and set is_active=False.
        Use this for user-initiated disconnect (not individual service toggles)."""
        connection.credentials = {}
        connection.is_active = False
        self.db.commit()
        self.db.refresh(connection)
        return connection

    def delete(self, connection: ChannelConnectionModel) -> None:
        """Hard-delete an asset connection that no longer exists in the external platform."""
        self.db.delete(connection)
        self.db.commit()
