import uuid

import pytest


TENANT_A = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return TENANT_A


@pytest.fixture
def tenant_id_b() -> uuid.UUID:
    return TENANT_B


@pytest.fixture
def lead_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def customer_profile_id() -> uuid.UUID:
    return uuid.uuid4()
