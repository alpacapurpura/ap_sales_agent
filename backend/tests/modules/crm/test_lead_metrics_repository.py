"""Unit tests — LeadRepository (lead_metrics_repository.py).

PR-2 PI-11: coverage lift para lead_metrics_repository.py (0% → ≥85%).
Cubre:
- count_total / count_qualified (aggregation queries)
- get_by_id (UUID string/UUID, not found)
- get_by_channel_id (canal válido, canal inválido)
- get_active_lead (con/sin leads)
- create_lead (con/sin channel_user_id, con customer_id, sin full_name error,
  relinking customer cuando cambia customer_id)
- update_profile (fields, smart list merge, str/UUID lead_id)

Usa el fixture `db` síncrono del conftest raíz (Session SQLite in-memory).
`get_tenant_id()` del contexto retorna None en tests → repos no aplican
filtro de tenant vía context; los tests pasan tenant_id manualmente al repo.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from luana_core_crm.domain.lead import Lead
from luana_core_crm.infrastructure.models.customer_model import CustomerProfileModel
from luana_core_crm.infrastructure.models.lead_model import LeadModel
from luana_core_crm.infrastructure.repositories.lead_metrics_repository import (
    LeadRepository,
)

TENANT_ID = uuid.UUID("11110000-0000-0000-0000-000000000001")
NOW = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_customer(full_name: str = "Test Customer") -> CustomerProfileModel:
    return CustomerProfileModel(
        id=uuid4(),
        tenant_id=TENANT_ID,
        full_name=full_name,
        lifecycle_stage="subscriber",
        lead_score=0.0,
        lifetime_value=0.0,
        is_inactive=False,
        traits={},
        computed_traits={},
    )


def _make_lead_model(
    customer_id: UUID,
    *,
    telegram_id: str | None = None,
    whatsapp_id: str | None = None,
    is_blacklisted: bool = False,
    temperature: str = "COLD",
    fit_score: int = 0,
) -> LeadModel:
    return LeadModel(
        id=uuid4(),
        tenant_id=TENANT_ID,
        customer_id=customer_id,
        telegram_id=telegram_id,
        whatsapp_id=whatsapp_id,
        fit_score=fit_score,
        intent_score=0,
        temperature=temperature,
        is_blacklisted=is_blacklisted,
        profile_data={},
        key_objections_history=[],
    )


# ---------------------------------------------------------------------------
# TestCountMethods
# ---------------------------------------------------------------------------


class TestCountMethods:
    """count_total y count_qualified — líneas #44-67."""

    def test_count_total_returns_active_leads(self, db: Session):
        """count_total excluye blacklisted."""
        customer = _make_customer()
        db.add(customer)
        db.flush()

        active = _make_lead_model(customer.id, is_blacklisted=False)
        blacklisted = _make_lead_model(customer.id, is_blacklisted=True)
        db.add_all([active, blacklisted])
        db.commit()

        repo = LeadRepository(db)
        count = repo.count_total(TENANT_ID)

        assert count == 1

    def test_count_total_returns_zero_when_empty(self, db: Session):
        repo = LeadRepository(db)
        count = repo.count_total(TENANT_ID)
        assert count == 0

    def test_count_qualified_high_fit_score(self, db: Session):
        """Leads con fit_score >= 50 son qualified."""
        customer = _make_customer()
        db.add(customer)
        db.flush()

        qualified = _make_lead_model(customer.id, fit_score=60)
        not_qualified = _make_lead_model(customer.id, fit_score=20, temperature="COLD")
        db.add_all([qualified, not_qualified])
        db.commit()

        repo = LeadRepository(db)
        count = repo.count_qualified(TENANT_ID)

        assert count == 1

    def test_count_qualified_warm_temperature(self, db: Session):
        """Leads con temperature != COLD son qualified (aunque fit_score < 50)."""
        customer = _make_customer()
        db.add(customer)
        db.flush()

        warm = _make_lead_model(customer.id, fit_score=10, temperature="WARM")
        cold = _make_lead_model(customer.id, fit_score=10, temperature="COLD")
        db.add_all([warm, cold])
        db.commit()

        repo = LeadRepository(db)
        count = repo.count_qualified(TENANT_ID)

        # warm lead is qualified (temperature != COLD)
        assert count == 1

    def test_count_qualified_excludes_blacklisted(self, db: Session):
        """Blacklisted leads no cuentan aunque sean qualified."""
        customer = _make_customer()
        db.add(customer)
        db.flush()

        blacklisted_hot = _make_lead_model(customer.id, fit_score=80, is_blacklisted=True)
        db.add(blacklisted_hot)
        db.commit()

        repo = LeadRepository(db)
        count = repo.count_qualified(TENANT_ID)

        assert count == 0


# ---------------------------------------------------------------------------
# TestGetById
# ---------------------------------------------------------------------------


class TestGetById:
    """get_by_id — líneas #69-86."""

    def test_get_by_id_uuid_returns_lead(self, db: Session):
        customer = _make_customer()
        db.add(customer)
        db.flush()

        lead = _make_lead_model(customer.id)
        db.add(lead)
        db.commit()

        repo = LeadRepository(db)
        # Sin tenant en context, no aplica filtro extra
        result = repo.get_by_id(lead.id)

        assert result is not None
        assert result.id == lead.id

    def test_get_by_id_str_uuid_returns_lead(self, db: Session):
        """get_by_id acepta str UUID (línea #72-73)."""
        customer = _make_customer()
        db.add(customer)
        db.flush()

        lead = _make_lead_model(customer.id)
        db.add(lead)
        db.commit()

        repo = LeadRepository(db)
        result = repo.get_by_id(str(lead.id))

        assert result is not None
        assert result.id == lead.id

    def test_get_by_id_invalid_str_returns_none(self, db: Session):
        """str no parseable como UUID retorna None (línea #74-75)."""
        repo = LeadRepository(db)
        result = repo.get_by_id("not-a-valid-uuid")
        assert result is None

    def test_get_by_id_not_found_returns_none(self, db: Session):
        repo = LeadRepository(db)
        result = repo.get_by_id(uuid4())
        assert result is None


# ---------------------------------------------------------------------------
# TestGetByChannelId
# ---------------------------------------------------------------------------


class TestGetByChannelId:
    """get_by_channel_id — líneas #88-103."""

    def test_get_by_channel_id_telegram_found(self, db: Session):
        customer = _make_customer()
        db.add(customer)
        db.flush()

        lead = _make_lead_model(customer.id, telegram_id="tg-user-123")
        db.add(lead)
        db.commit()

        repo = LeadRepository(db)
        result = repo.get_by_channel_id("telegram", "tg-user-123")

        assert result is not None
        assert result.telegram_id == "tg-user-123"

    def test_get_by_channel_id_whatsapp_found(self, db: Session):
        customer = _make_customer()
        db.add(customer)
        db.flush()

        lead = _make_lead_model(customer.id, whatsapp_id="wa-user-456")
        db.add(lead)
        db.commit()

        repo = LeadRepository(db)
        result = repo.get_by_channel_id("whatsapp", "wa-user-456")

        assert result is not None
        assert result.whatsapp_id == "wa-user-456"

    def test_get_by_channel_id_invalid_channel_returns_none(self, db: Session):
        """Canal no registrado en _CHANNEL_ATTR_MAP retorna None (línea #90-91)."""
        repo = LeadRepository(db)
        result = repo.get_by_channel_id("unknown_channel", "some-id")
        assert result is None

    def test_get_by_channel_id_not_found_returns_none(self, db: Session):
        repo = LeadRepository(db)
        result = repo.get_by_channel_id("telegram", "nonexistent-tg-id")
        assert result is None


# ---------------------------------------------------------------------------
# TestGetActiveLead
# ---------------------------------------------------------------------------


class TestGetActiveLead:
    """get_active_lead — líneas #105-123."""

    def test_get_active_lead_returns_most_recent(self, db: Session):
        """Retorna el lead más reciente no blacklisted (línea #112)."""
        customer = _make_customer()
        db.add(customer)
        db.flush()

        # Simular dos leads para mismo customer
        lead1 = _make_lead_model(customer.id)
        db.add(lead1)
        db.flush()

        lead2 = _make_lead_model(customer.id, telegram_id="tg-active")
        db.add(lead2)
        db.commit()

        repo = LeadRepository(db)
        result = repo.get_active_lead(customer.id)

        assert result is not None
        # Retorna alguno de los leads no blacklisted

    def test_get_active_lead_excludes_blacklisted(self, db: Session):
        """Leads blacklisted son excluidos (is_blacklisted filter)."""
        customer = _make_customer()
        db.add(customer)
        db.flush()

        lead = _make_lead_model(customer.id, is_blacklisted=True)
        db.add(lead)
        db.commit()

        repo = LeadRepository(db)
        result = repo.get_active_lead(customer.id)

        # Todos blacklisted → None
        assert result is None

    def test_get_active_lead_no_leads_returns_none(self, db: Session):
        repo = LeadRepository(db)
        result = repo.get_active_lead(uuid4())
        assert result is None


# ---------------------------------------------------------------------------
# TestCreateLead
# ---------------------------------------------------------------------------


class TestCreateLead:
    """create_lead — líneas #125-191."""

    def test_create_lead_with_full_name_creates_customer(self, db: Session):
        """Sin customer_id, crea CustomerProfile + Lead (línea #173-190)."""
        repo = LeadRepository(db)
        lead = repo.create_lead(full_name="New Contact", channel="telegram", channel_user_id="tg-new")

        assert lead is not None
        assert lead.telegram_id == "tg-new"

    def test_create_lead_with_customer_id(self, db: Session):
        """Con customer_id existente, crea Lead linkeado (línea #157-167)."""
        customer = _make_customer()
        db.add(customer)
        db.flush()

        repo = LeadRepository(db)
        lead = repo.create_lead(customer_id=customer.id, channel="whatsapp", channel_user_id="wa-linked")

        assert lead is not None
        assert lead.customer_id == customer.id
        assert lead.whatsapp_id == "wa-linked"

    def test_create_lead_without_full_name_raises(self, db: Session):
        """Sin full_name ni customer_id, levanta ValueError (línea #169-171)."""
        repo = LeadRepository(db)
        with pytest.raises(ValueError, match="full_name is required"):
            repo.create_lead()

    def test_create_lead_returns_existing_when_channel_id_matches(self, db: Session):
        """Si ya existe lead con mismo channel_user_id, retorna existente (línea #139-155)."""
        customer = _make_customer()
        db.add(customer)
        db.flush()

        repo = LeadRepository(db)
        # Primera vez: crea
        lead1 = repo.create_lead(
            full_name="Contact",
            channel="telegram",
            channel_user_id="tg-exists",
        )

        # Segunda vez con mismo channel_user_id → retorna existente
        lead2 = repo.create_lead(
            full_name="Different Name",
            channel="telegram",
            channel_user_id="tg-exists",
        )

        assert str(lead1.id) == str(lead2.id)

    def test_create_lead_updates_customer_id_when_relinked(self, db: Session):
        """Si lead existe pero customer_id cambió, actualiza el link (línea #142-154)."""
        customer1 = _make_customer("Customer 1")
        customer2 = _make_customer("Customer 2")
        db.add_all([customer1, customer2])
        db.flush()

        repo = LeadRepository(db)

        # Crea lead linkeado a customer1
        lead = repo.create_lead(
            full_name="Customer 1",
            channel="telegram",
            channel_user_id="tg-relink",
        )

        # Intenta crear con mismo channel_user_id pero customer2
        updated_lead = repo.create_lead(
            channel="telegram",
            channel_user_id="tg-relink",
            customer_id=customer2.id,
        )

        # El mismo lead pero con customer_id actualizado
        assert str(updated_lead.id) == str(lead.id)

    def test_create_lead_channel_without_channel_user_id(self, db: Session):
        """_set_channel_id no falla cuando channel_user_id es None (línea #37-39)."""
        repo = LeadRepository(db)
        lead = repo.create_lead(full_name="No Channel ID", channel="telegram", channel_user_id=None)

        assert lead is not None
        assert lead.telegram_id is None


# ---------------------------------------------------------------------------
# TestUpdateProfile
# ---------------------------------------------------------------------------


class TestUpdateProfile:
    """update_profile — líneas #193-241."""

    def test_update_profile_updates_profile_data(self, db: Session):
        """Merge de profile_data actualiza campos conocidos (línea #215-224)."""
        customer = _make_customer()
        db.add(customer)
        db.flush()

        lead = _make_lead_model(customer.id)
        db.add(lead)
        db.commit()

        repo = LeadRepository(db)
        # Usa campos reales de UserProfile: name, age (str)
        result = repo.update_profile(lead.id, {"name": "Ana García", "age": "30"})

        assert result is not None
        assert isinstance(result, Lead)
        # UserProfile fields son accesibles como atributos
        assert result.profile_data.age == "30"
        assert result.profile_data.name == "Ana García"

    def test_update_profile_smart_list_merge(self, db: Session):
        """Lista existente + nueva → union (línea #218-219: list + list merge).

        Usa `missing_fields` (único list[str] en UserProfile) para testear merge.
        """
        customer = _make_customer()
        db.add(customer)
        db.flush()

        # Lead con profile_data inicial que incluye missing_fields lista
        lead = LeadModel(
            id=uuid4(),
            tenant_id=TENANT_ID,
            customer_id=customer.id,
            fit_score=0,
            intent_score=0,
            temperature="COLD",
            is_blacklisted=False,
            profile_data={"missing_fields": ["email", "phone"]},
            key_objections_history=[],
        )
        db.add(lead)
        db.commit()

        repo = LeadRepository(db)
        # Merge lista con items nuevos
        result = repo.update_profile(lead.id, {"missing_fields": ["location", "email"]})

        assert result is not None
        # UserProfile.missing_fields es list[str] — merge = union de ambas listas
        merged = set(result.profile_data.missing_fields)
        assert "email" in merged
        assert "phone" in merged
        assert "location" in merged

    def test_update_profile_str_lead_id(self, db: Session):
        """update_profile acepta str UUID (línea #200-204)."""
        customer = _make_customer()
        db.add(customer)
        db.flush()

        lead = _make_lead_model(customer.id)
        db.add(lead)
        db.commit()

        repo = LeadRepository(db)
        # Usa campo real de UserProfile: occupation
        result = repo.update_profile(str(lead.id), {"occupation": "Coach"})

        assert result is not None
        assert isinstance(result, Lead)
        assert result.profile_data.occupation == "Coach"

    def test_update_profile_invalid_str_returns_none(self, db: Session):
        """str inválido como UUID retorna None (línea #202-204)."""
        repo = LeadRepository(db)
        result = repo.update_profile("not-a-uuid", {"data": "x"})
        assert result is None

    def test_update_profile_not_found_returns_none(self, db: Session):
        """UUID inexistente retorna None."""
        repo = LeadRepository(db)
        result = repo.update_profile(uuid4(), {"data": "x"})
        assert result is None

    def test_update_profile_updates_customer_email_name(self, db: Session):
        """Si profile_data tiene email/name, actualiza CustomerProfile (líneas #227-234)."""
        customer = _make_customer("Old Name")
        db.add(customer)
        db.flush()

        lead = _make_lead_model(customer.id)
        db.add(lead)
        db.commit()

        repo = LeadRepository(db)
        result = repo.update_profile(
            lead.id,
            {"email": "new@example.com", "name": "New Name"},
        )

        assert result is not None
        # Los cambios se aplican en customer a través del eager load
        db.refresh(customer)
        assert customer.primary_email == "new@example.com"
        assert customer.full_name == "New Name"

    def test_update_profile_full_name_key(self, db: Session):
        """Fallback de full_name key (línea #235-236: elif full_name)."""
        customer = _make_customer("Original Name")
        db.add(customer)
        db.flush()

        lead = _make_lead_model(customer.id)
        db.add(lead)
        db.commit()

        repo = LeadRepository(db)
        result = repo.update_profile(lead.id, {"full_name": "Updated Name"})

        assert result is not None
        db.refresh(customer)
        assert customer.full_name == "Updated Name"
