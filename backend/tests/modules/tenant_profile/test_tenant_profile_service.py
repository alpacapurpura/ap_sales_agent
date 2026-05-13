"""Service-layer tests for TenantProfileService.

Uses a mock repository so no DB is required. Covers orchestration logic:
get_or_init delegation, event dispatch, no-op path, and error propagation.
"""

from __future__ import annotations

import uuid
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

from luana_core_tenant_profile.application.services.tenant_profile_service import (
    TenantProfileService,
)
from luana_core_tenant_profile.domain.exceptions import BusinessTypesChangeRateLimitedError
from luana_core_tenant_profile.domain.tenant_profile import (
    RATE_LIMIT_WINDOW,
    TenantProfile,
)
from luana_core_platform.domain.datetime_utils import utc_now
from luana_core_platform.domain.expert_business_type import ExpertBusinessType

TYPE_A = ExpertBusinessType.ACADEMIA_INFOPRODUCTOR
TYPE_B = ExpertBusinessType.AGENCIA_FREELANCE
TENANT = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")


def _new_profile() -> TenantProfile:
    return TenantProfile(
        tenant_id=TENANT,
        business_types=(),
        declared_at=None,
        updated_at=utc_now(),
        last_business_types_change_at=None,
    )


def _declared_profile() -> TenantProfile:
    anchor = utc_now() - RATE_LIMIT_WINDOW - timedelta(days=1)
    return TenantProfile(
        tenant_id=TENANT,
        business_types=(TYPE_A,),
        declared_at=anchor,
        updated_at=anchor,
        last_business_types_change_at=anchor,
    )


@pytest.fixture
def mock_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(mock_repo: MagicMock) -> TenantProfileService:
    return TenantProfileService(mock_repo)


class TestGetProfile:
    def test_delegates_to_get_or_init(self, service: TenantProfileService, mock_repo: MagicMock) -> None:
        mock_repo.get_or_init.return_value = _new_profile()
        result = service.get_profile(TENANT)
        mock_repo.get_or_init.assert_called_once_with(TENANT)
        assert result is not None

    def test_returns_profile_from_repo(self, service: TenantProfileService, mock_repo: MagicMock) -> None:
        profile = _new_profile()
        mock_repo.get_or_init.return_value = profile
        assert service.get_profile(TENANT) is profile


class TestUpdateBusinessTypes:
    def test_first_declaration_calls_save(self, service: TenantProfileService, mock_repo: MagicMock) -> None:
        profile = _new_profile()
        mock_repo.get_or_init.return_value = profile
        service.update_business_types(TENANT, (TYPE_A,))
        mock_repo.save.assert_called_once_with(profile)

    def test_returns_updated_profile(self, service: TenantProfileService, mock_repo: MagicMock) -> None:
        profile = _new_profile()
        mock_repo.get_or_init.return_value = profile
        result = service.update_business_types(TENANT, (TYPE_A,))
        assert result.business_types == (TYPE_A,)
        assert result.is_complete

    def test_noop_does_not_call_save(self, service: TenantProfileService, mock_repo: MagicMock) -> None:
        profile = _declared_profile()
        mock_repo.get_or_init.return_value = profile
        # Same set → no-op
        service.update_business_types(TENANT, (TYPE_A,))
        mock_repo.save.assert_not_called()

    def test_rate_limited_propagates_to_caller(self, service: TenantProfileService, mock_repo: MagicMock) -> None:
        anchor = utc_now() - timedelta(days=5)
        rate_limited = TenantProfile(
            tenant_id=TENANT,
            business_types=(TYPE_A,),
            declared_at=anchor,
            updated_at=anchor,
            last_business_types_change_at=anchor,
        )
        mock_repo.get_or_init.return_value = rate_limited
        with pytest.raises(BusinessTypesChangeRateLimitedError):
            service.update_business_types(TENANT, (TYPE_B,))

    def test_value_error_propagates_to_caller(self, service: TenantProfileService, mock_repo: MagicMock) -> None:
        mock_repo.get_or_init.return_value = _new_profile()
        with pytest.raises(ValueError, match="between"):
            service.update_business_types(TENANT, ())

    def test_dispatch_event_is_called_on_change(self, service: TenantProfileService, mock_repo: MagicMock) -> None:
        mock_repo.get_or_init.return_value = _new_profile()
        with patch.object(service, "_dispatch_event") as dispatch:
            service.update_business_types(TENANT, (TYPE_A,))
            dispatch.assert_called_once()

    def test_dispatch_event_not_called_on_noop(self, service: TenantProfileService, mock_repo: MagicMock) -> None:
        mock_repo.get_or_init.return_value = _declared_profile()
        with patch.object(service, "_dispatch_event") as dispatch:
            service.update_business_types(TENANT, (TYPE_A,))
            dispatch.assert_not_called()
