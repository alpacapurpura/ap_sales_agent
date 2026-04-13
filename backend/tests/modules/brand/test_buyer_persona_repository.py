"""Tests for BuyerPersonaRepository — CRUD + tenant isolation."""

import uuid

from src.modules.brand.domain.buyer_persona import BuyerPersona
from src.modules.brand.infrastructure.repositories.buyer_persona_repository import (
    BuyerPersonaRepository,
)
from tests.modules.conftest import TENANT_A, TENANT_B, USER_A


def _make_persona(
    tenant_id: uuid.UUID = TENANT_A,
    user_id: uuid.UUID = USER_A,
    name: str = "Test Persona",
    scope: str = "GLOBAL",
    **kwargs,
) -> BuyerPersona:
    return BuyerPersona(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        name=name,
        scope=scope,
        **kwargs,
    )


class TestBuyerPersonaRepository:
    def test_create_and_get_by_id(self, db):
        repo = BuyerPersonaRepository(db)
        persona = _make_persona(name="Maria Creadora")
        created = repo.create(persona)

        assert created.name == "Maria Creadora"
        assert created.id == persona.id

        retrieved = repo.get_by_id(tenant_id=TENANT_A, persona_id=persona.id)
        assert retrieved is not None
        assert retrieved.name == "Maria Creadora"

    def test_get_by_id_filters_by_tenant(self, db):
        repo = BuyerPersonaRepository(db)
        persona = _make_persona(tenant_id=TENANT_A)
        repo.create(persona)

        # Wrong tenant should return None
        retrieved = repo.get_by_id(tenant_id=TENANT_B, persona_id=persona.id)
        assert retrieved is None

    def test_get_by_id_excludes_soft_deleted(self, db):
        repo = BuyerPersonaRepository(db)
        persona = _make_persona()
        repo.create(persona)
        repo.soft_delete(tenant_id=TENANT_A, persona_id=persona.id)

        retrieved = repo.get_by_id(tenant_id=TENANT_A, persona_id=persona.id)
        assert retrieved is None

    def test_list_by_tenant(self, db):
        repo = BuyerPersonaRepository(db)
        repo.create(_make_persona(name="P1", tenant_id=TENANT_A))
        repo.create(_make_persona(name="P2", tenant_id=TENANT_A))
        repo.create(_make_persona(name="P3", tenant_id=TENANT_B))

        results_a = repo.list_by_tenant(tenant_id=TENANT_A)
        assert len(results_a) == 2
        assert all(str(p.tenant_id) == str(TENANT_A) for p in results_a)

        results_b = repo.list_by_tenant(tenant_id=TENANT_B)
        assert len(results_b) == 1

    def test_list_by_tenant_with_scope_filter(self, db):
        repo = BuyerPersonaRepository(db)
        repo.create(_make_persona(name="Global", scope="GLOBAL"))
        repo.create(_make_persona(name="Offer", scope="OFFER"))

        global_only = repo.list_by_tenant(tenant_id=TENANT_A, scope="GLOBAL")
        assert all(p.scope == "GLOBAL" for p in global_only)
        assert len(global_only) == 1

    def test_list_by_tenant_excludes_soft_deleted(self, db):
        repo = BuyerPersonaRepository(db)
        persona = _make_persona()
        repo.create(persona)
        repo.soft_delete(tenant_id=TENANT_A, persona_id=persona.id)

        results = repo.list_by_tenant(tenant_id=TENANT_A)
        assert len(results) == 0

    def test_update(self, db):
        repo = BuyerPersonaRepository(db)
        persona = _make_persona(name="Original")
        repo.create(persona)

        updated = repo.update(
            tenant_id=TENANT_A,
            persona_id=persona.id,
            updates={
                "name": "Updated Name",
                "tagline": "New tagline",
                "demographics": {"age_range": "25-35"},
            },
        )
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.tagline == "New tagline"
        assert updated.demographics == {"age_range": "25-35"}

    def test_update_nonexistent(self, db):
        repo = BuyerPersonaRepository(db)
        result = repo.update(
            tenant_id=TENANT_A,
            persona_id=uuid.uuid4(),
            updates={"name": "X"},
        )
        assert result is None

    def test_update_wrong_tenant(self, db):
        repo = BuyerPersonaRepository(db)
        persona = _make_persona(tenant_id=TENANT_A)
        repo.create(persona)

        result = repo.update(
            tenant_id=TENANT_B,
            persona_id=persona.id,
            updates={"name": "Hacked"},
        )
        assert result is None

    def test_soft_delete(self, db):
        repo = BuyerPersonaRepository(db)
        persona = _make_persona()
        repo.create(persona)

        result = repo.soft_delete(tenant_id=TENANT_A, persona_id=persona.id)
        assert result is True

        # Should not be retrievable
        assert repo.get_by_id(tenant_id=TENANT_A, persona_id=persona.id) is None

    def test_soft_delete_nonexistent(self, db):
        repo = BuyerPersonaRepository(db)
        result = repo.soft_delete(tenant_id=TENANT_A, persona_id=uuid.uuid4())
        assert result is False

    def test_soft_delete_wrong_tenant(self, db):
        repo = BuyerPersonaRepository(db)
        persona = _make_persona(tenant_id=TENANT_A)
        repo.create(persona)

        result = repo.soft_delete(tenant_id=TENANT_B, persona_id=persona.id)
        assert result is False

    def test_create_with_full_profile(self, db):
        repo = BuyerPersonaRepository(db)
        persona = _make_persona(
            demographics={"age_range": "30-40", "location": "LATAM"},
            psychographics={"values": ["family", "growth"]},
            pain_points=[{"description": "No puede escalar", "intensity": "high"}],
            desires=[{"description": "Automatizar ventas", "priority": "high"}],
            objections=[{"objection": "Es caro", "root_cause": "No ve el ROI"}],
            preferred_channels=[{"channel": "Instagram", "usage_pattern": "daily"}],
            buyer_journey={"awareness": "social media", "decision": "webinar"},
            purchase_triggers=["deadline", "discount"],
            anti_patterns=["no invierte en formacion"],
            completeness_score=65.0,
        )
        created = repo.create(persona)

        retrieved = repo.get_by_id(tenant_id=TENANT_A, persona_id=created.id)
        assert retrieved is not None
        assert retrieved.demographics["age_range"] == "30-40"
        assert len(retrieved.pain_points) == 1
        assert retrieved.purchase_triggers == ["deadline", "discount"]
        assert retrieved.completeness_score == 65.0
