"""Extended repository tests covering uncovered methods.

Complements test_channel_connection_isolation.py and test_channel_connection_soft_delete.py.
Covers: get_by_asset_id, get_all_by_tenant_and_types, get_all_active_by_type,
get_active_shopify_by_shop, create_asset, update_config, update_credentials,
activate, revoke, delete.
"""

import uuid

import pytest
from sqlalchemy.orm import Session

from luana_core_connections.domain.enums import ChannelType
from luana_core_connections.infrastructure.models.channel_connection_model import (
    ChannelConnectionModel,
)
from luana_core_connections.infrastructure.repositories.channel_connection_repository import (
    ChannelConnectionRepository,
)

TENANT_A = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")


def _insert(
    db: Session,
    *,
    tenant_id: uuid.UUID = TENANT_A,
    channel_type: ChannelType = ChannelType.META,
    credentials: dict | None = None,
    config: dict | None = None,
    is_active: bool = True,
) -> ChannelConnectionModel:
    conn = ChannelConnectionModel(
        tenant_id=tenant_id,
        channel_type=channel_type.value,
        credentials=credentials or {},
        config=config or {},
        is_active=is_active,
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


# ---------------------------------------------------------------------------
# get_by_asset_id
# NOTE: uses JSONB .astext (Postgres-only) — expression fails at build time
# on SQLite. Covered by integration tests running against real Postgres.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# get_all_by_tenant_and_types
# ---------------------------------------------------------------------------


class TestGetAllByTenantAndTypes:
    def test_filters_by_channel_types(self, db: Session):
        _insert(db, channel_type=ChannelType.META)
        _insert(db, channel_type=ChannelType.SHOPIFY)
        _insert(db, channel_type=ChannelType.TELEGRAM)
        repo = ChannelConnectionRepository(db)

        results = repo.get_all_by_tenant_and_types(TENANT_A, [ChannelType.META, ChannelType.SHOPIFY])
        types = {r.channel_type for r in results}
        assert types == {ChannelType.META.value, ChannelType.SHOPIFY.value}

    def test_excludes_soft_deleted(self, db: Session):
        conn = _insert(db, channel_type=ChannelType.META)
        from sqlalchemy.sql import func

        conn.deleted_at = func.now()
        db.commit()

        repo = ChannelConnectionRepository(db)
        results = repo.get_all_by_tenant_and_types(TENANT_A, [ChannelType.META])
        assert results == []

    def test_empty_types_list_returns_empty(self, db: Session):
        _insert(db, channel_type=ChannelType.META)
        repo = ChannelConnectionRepository(db)
        results = repo.get_all_by_tenant_and_types(TENANT_A, [])
        assert results == []


# ---------------------------------------------------------------------------
# get_all_active_by_type (cross-tenant, admin use)
# ---------------------------------------------------------------------------


class TestGetAllActiveByType:
    def test_returns_active_connections_across_tenants(self, db: Session):
        _insert(db, tenant_id=TENANT_A, channel_type=ChannelType.SHOPIFY, is_active=True)
        _insert(db, tenant_id=TENANT_B, channel_type=ChannelType.SHOPIFY, is_active=True)
        _insert(db, tenant_id=TENANT_A, channel_type=ChannelType.SHOPIFY, is_active=False)
        repo = ChannelConnectionRepository(db)

        results = repo.get_all_active_by_type([ChannelType.SHOPIFY.value])
        assert len(results) == 2

    def test_excludes_inactive(self, db: Session):
        _insert(db, channel_type=ChannelType.SHOPIFY, is_active=False)
        repo = ChannelConnectionRepository(db)
        results = repo.get_all_active_by_type([ChannelType.SHOPIFY.value])
        assert results == []


# ---------------------------------------------------------------------------
# get_active_shopify_by_shop
# ---------------------------------------------------------------------------


class TestGetActiveShopifyByShop:
    def test_finds_by_exact_shop_url(self, db: Session):
        _insert(
            db,
            channel_type=ChannelType.SHOPIFY,
            config={"shop_url": "mystore.myshopify.com"},
            is_active=True,
        )
        repo = ChannelConnectionRepository(db)
        result = repo.get_active_shopify_by_shop("mystore.myshopify.com")
        assert result is not None

    def test_normalizes_https_prefix(self, db: Session):
        _insert(
            db,
            channel_type=ChannelType.SHOPIFY,
            config={"shop_url": "https://mystore.myshopify.com"},
            is_active=True,
        )
        repo = ChannelConnectionRepository(db)
        result = repo.get_active_shopify_by_shop("mystore.myshopify.com")
        assert result is not None

    def test_normalizes_short_name_without_domain(self, db: Session):
        _insert(
            db,
            channel_type=ChannelType.SHOPIFY,
            config={"shop_url": "mystore.myshopify.com"},
            is_active=True,
        )
        repo = ChannelConnectionRepository(db)
        result = repo.get_active_shopify_by_shop("mystore")
        assert result is not None

    def test_finds_by_shop_info_domain(self, db: Session):
        _insert(
            db,
            channel_type=ChannelType.SHOPIFY,
            config={"shop_info": {"domain": "otherstore.myshopify.com"}},
            is_active=True,
        )
        repo = ChannelConnectionRepository(db)
        result = repo.get_active_shopify_by_shop("otherstore.myshopify.com")
        assert result is not None

    def test_returns_none_when_not_found(self, db: Session):
        repo = ChannelConnectionRepository(db)
        result = repo.get_active_shopify_by_shop("notexist.myshopify.com")
        assert result is None

    def test_returns_none_for_inactive(self, db: Session):
        _insert(
            db,
            channel_type=ChannelType.SHOPIFY,
            config={"shop_url": "inactive.myshopify.com"},
            is_active=False,
        )
        repo = ChannelConnectionRepository(db)
        result = repo.get_active_shopify_by_shop("inactive.myshopify.com")
        assert result is None


# ---------------------------------------------------------------------------
# create_asset
# ---------------------------------------------------------------------------


class TestCreateAsset:
    def test_creates_new_row_always(self, db: Session):
        repo = ChannelConnectionRepository(db)
        conn1 = repo.create_asset(
            TENANT_A,
            ChannelType.FACEBOOK_PAGE,
            {"access_token": "tok"},
            {"asset_id": "page_1"},
        )
        conn2 = repo.create_asset(
            TENANT_A,
            ChannelType.FACEBOOK_PAGE,
            {"access_token": "tok"},
            {"asset_id": "page_2"},
        )
        assert conn1.id != conn2.id

    def test_created_asset_is_active(self, db: Session):
        repo = ChannelConnectionRepository(db)
        conn = repo.create_asset(TENANT_A, ChannelType.FACEBOOK_PAGE, {}, {"asset_id": "px"})
        assert conn.is_active is True

    def test_created_asset_has_correct_tenant(self, db: Session):
        repo = ChannelConnectionRepository(db)
        conn = repo.create_asset(TENANT_A, ChannelType.INSTAGRAM_ACCOUNT, {}, {})
        assert conn.tenant_id == TENANT_A


# ---------------------------------------------------------------------------
# update_config
# ---------------------------------------------------------------------------


class TestUpdateConfig:
    def test_merges_new_keys_into_config(self, db: Session):
        conn = _insert(db, config={"existing": "val"})
        repo = ChannelConnectionRepository(db)
        updated = repo.update_config(conn, {"new_key": "new_val"})
        assert updated.config["existing"] == "val"
        assert updated.config["new_key"] == "new_val"

    def test_overwrites_existing_key(self, db: Session):
        conn = _insert(db, config={"key": "old"})
        repo = ChannelConnectionRepository(db)
        updated = repo.update_config(conn, {"key": "new"})
        assert updated.config["key"] == "new"


# ---------------------------------------------------------------------------
# update_credentials
# ---------------------------------------------------------------------------


class TestUpdateCredentials:
    def test_replaces_credentials(self, db: Session):
        conn = _insert(db, credentials={"access_token": "old"})
        repo = ChannelConnectionRepository(db)
        updated = repo.update_credentials(conn, {"access_token": "fresh"})
        assert updated.credentials["access_token"] == "fresh"

    def test_old_keys_not_preserved(self, db: Session):
        conn = _insert(db, credentials={"access_token": "old", "stale": "data"})
        repo = ChannelConnectionRepository(db)
        updated = repo.update_credentials(conn, {"access_token": "new"})
        assert "stale" not in updated.credentials


# ---------------------------------------------------------------------------
# activate / revoke
# ---------------------------------------------------------------------------


class TestActivateRevoke:
    def test_activate_sets_is_active_true(self, db: Session):
        conn = _insert(db, is_active=False)
        repo = ChannelConnectionRepository(db)
        result = repo.activate(conn)
        assert result.is_active is True

    def test_revoke_clears_credentials_and_deactivates(self, db: Session):
        conn = _insert(db, credentials={"access_token": "tok"}, is_active=True)
        repo = ChannelConnectionRepository(db)
        result = repo.revoke(conn)
        assert result.is_active is False
        assert result.credentials == {}

    def test_deactivate_sets_is_active_false(self, db: Session):
        conn = _insert(db, is_active=True)
        repo = ChannelConnectionRepository(db)
        result = repo.deactivate(conn)
        assert result.is_active is False


# ---------------------------------------------------------------------------
# delete (soft-delete via deleted_at)
# ---------------------------------------------------------------------------


class TestDelete:
    def test_delete_sets_deleted_at(self, db: Session):
        conn = _insert(db, is_active=True)
        repo = ChannelConnectionRepository(db)
        repo.delete(conn)
        db.refresh(conn)
        assert conn.deleted_at is not None

    def test_delete_sets_is_active_false(self, db: Session):
        conn = _insert(db, is_active=True)
        repo = ChannelConnectionRepository(db)
        repo.delete(conn)
        db.refresh(conn)
        assert conn.is_active is False

    def test_deleted_connection_excluded_from_get_all_by_tenant(self, db: Session):
        conn = _insert(db, channel_type=ChannelType.SHOPIFY)
        repo = ChannelConnectionRepository(db)
        repo.delete(conn)
        db.refresh(conn)
        all_conns = repo.get_all_by_tenant(TENANT_A)
        ids = [c.id for c in all_conns]
        assert conn.id not in ids
