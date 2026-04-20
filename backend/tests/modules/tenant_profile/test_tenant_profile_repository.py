"""Repository round-trip + tenant isolation tests for SqlTenantProfileRepository.

Uses the in-memory SQLite session from the global conftest. Every assertion is
phrased to fail loudly if the repository ever leaks cross-tenant data.
"""

from __future__ import annotations

from datetime import timedelta

from src.modules.tenant_profile.domain.tenant_profile import RATE_LIMIT_WINDOW, TenantProfile
from src.shared.domain.datetime_utils import utc_now
from tests.modules.tenant_profile.conftest import OTHER_TENANT_ID, TENANT_ID, TYPE_A, TYPE_B


def _same_instant(a, b) -> bool:
    """Compare two datetimes as absolute instants regardless of tzinfo.

    SQLite strips tzinfo on round-trip; PostgreSQL preserves it. The domain
    always writes UTC, so we can compare by substituting tzinfo when missing.
    """
    if a is None or b is None:
        return a is b
    from datetime import UTC

    na = a.replace(tzinfo=UTC) if a.tzinfo is None else a
    nb = b.replace(tzinfo=UTC) if b.tzinfo is None else b
    return na == nb


class TestGetOrNone:
    """get_or_none: read-only lookup."""

    def test_returns_none_for_unknown_tenant(self, repo) -> None:
        assert repo.get_or_none(TENANT_ID) is None

    def test_does_not_create_row(self, repo, db) -> None:
        repo.get_or_none(TENANT_ID)
        from src.modules.tenant_profile.infrastructure.models.tenant_profile_model import (
            TenantProfileModel,
        )

        count = db.query(TenantProfileModel).count()
        assert count == 0


class TestGetOrInit:
    """get_or_init: returns in-memory aggregate without persisting."""

    def test_returns_empty_profile_for_new_tenant(self, repo) -> None:
        profile = repo.get_or_init(TENANT_ID)
        assert profile.tenant_id == TENANT_ID
        assert profile.business_types == ()
        assert profile.declared_at is None
        assert not profile.is_complete

    def test_does_not_persist_until_save(self, repo, db) -> None:
        repo.get_or_init(TENANT_ID)
        from src.modules.tenant_profile.infrastructure.models.tenant_profile_model import (
            TenantProfileModel,
        )

        count = db.query(TenantProfileModel).count()
        assert count == 0

    def test_returns_existing_profile_when_row_exists(self, repo) -> None:
        # Seed
        now = utc_now()
        seed = TenantProfile(
            tenant_id=TENANT_ID,
            business_types=(TYPE_A,),
            declared_at=now,
            updated_at=now,
            last_business_types_change_at=now,
        )
        repo.save(seed)

        # Act
        fetched = repo.get_or_init(TENANT_ID)

        # Assert
        assert fetched.business_types == (TYPE_A,)
        assert _same_instant(fetched.declared_at, now)


class TestSaveRoundTrip:
    """save + read-back preserves all fields."""

    def test_insert_persists_full_state(self, repo) -> None:
        now = utc_now()
        profile = TenantProfile(
            tenant_id=TENANT_ID,
            business_types=(TYPE_A, TYPE_B),
            declared_at=now,
            updated_at=now,
            last_business_types_change_at=now,
        )

        repo.save(profile)
        fetched = repo.get_or_none(TENANT_ID)

        assert fetched is not None
        assert fetched.business_types == (TYPE_A, TYPE_B)
        assert _same_instant(fetched.declared_at, now)
        assert _same_instant(fetched.last_business_types_change_at, now)

    def test_update_overwrites_existing_row(self, repo) -> None:
        initial = utc_now() - RATE_LIMIT_WINDOW - timedelta(days=1)
        profile = TenantProfile(
            tenant_id=TENANT_ID,
            business_types=(TYPE_A,),
            declared_at=initial,
            updated_at=initial,
            last_business_types_change_at=initial,
        )
        repo.save(profile)

        # Update
        profile.update_business_types((TYPE_A, TYPE_B))
        repo.save(profile)

        fetched = repo.get_or_none(TENANT_ID)
        assert fetched is not None
        assert fetched.business_types == (TYPE_A, TYPE_B)
        assert fetched.last_business_types_change_at is not None
        # Normalise tzinfo for cross-dialect comparison
        from datetime import UTC

        lc = fetched.last_business_types_change_at
        lc = lc.replace(tzinfo=UTC) if lc.tzinfo is None else lc
        assert lc > initial


class TestTenantIsolation:
    """No cross-tenant leakage under any circumstance."""

    def test_read_scoped_to_tenant_id(self, repo) -> None:
        now = utc_now()
        profile_a = TenantProfile(
            tenant_id=TENANT_ID,
            business_types=(TYPE_A,),
            declared_at=now,
            updated_at=now,
            last_business_types_change_at=now,
        )
        repo.save(profile_a)

        # Other tenant sees nothing.
        assert repo.get_or_none(OTHER_TENANT_ID) is None

    def test_two_tenants_coexist_without_interference(self, repo) -> None:
        now = utc_now()
        repo.save(
            TenantProfile(
                tenant_id=TENANT_ID,
                business_types=(TYPE_A,),
                declared_at=now,
                updated_at=now,
                last_business_types_change_at=now,
            )
        )
        repo.save(
            TenantProfile(
                tenant_id=OTHER_TENANT_ID,
                business_types=(TYPE_B,),
                declared_at=now,
                updated_at=now,
                last_business_types_change_at=now,
            )
        )

        a = repo.get_or_none(TENANT_ID)
        b = repo.get_or_none(OTHER_TENANT_ID)
        assert a is not None and b is not None
        assert a.business_types == (TYPE_A,)
        assert b.business_types == (TYPE_B,)


class TestLegacyDataHandling:
    """Repository gracefully ignores unknown enum values in the DB.

    Why: a future enum value could be removed while rows still reference it.
    The mapper must not explode — it drops unknown slugs silently (logged at
    INFO by the model-to-domain mapping).
    """

    def test_unknown_slug_in_db_is_dropped(self, repo, db) -> None:
        from src.modules.tenant_profile.infrastructure.models.tenant_profile_model import (
            TenantProfileModel,
        )

        now = utc_now()
        row = TenantProfileModel(
            tenant_id=TENANT_ID,
            business_types=[TYPE_A.value, "unknown_legacy_slug"],
            declared_at=now,
            updated_at=now,
            last_business_types_change_at=now,
        )
        db.add(row)
        db.commit()

        fetched = repo.get_or_none(TENANT_ID)
        assert fetched is not None
        assert fetched.business_types == (TYPE_A,)
