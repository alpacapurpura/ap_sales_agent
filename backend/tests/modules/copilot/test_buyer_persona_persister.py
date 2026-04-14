"""Tests for BuyerPersonaPersister — persist, load, registry."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

from src.modules.brand.domain.buyer_persona import BuyerPersona
from src.modules.copilot.infrastructure.persisters.buyer_persona_persister import (
    BuyerPersonaPersister,
)
from src.modules.copilot.infrastructure.persisters.persister_registry import (
    get_persister,
)


def _make_persona(**overrides: object) -> BuyerPersona:
    """Build a minimal BuyerPersona for testing."""
    defaults: dict = {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "user_id": uuid4(),
        "name": "Test Persona",
    }
    defaults.update(overrides)
    return BuyerPersona(**defaults)


class TestBuyerPersonaPersist:
    """Tests for persist method."""

    def test_persist_creates_new_when_no_entity_id(self) -> None:
        """Without entity_id, persister creates a new persona."""
        db = MagicMock()
        persister = BuyerPersonaPersister(db)
        tenant_id = uuid4()

        mapa_global = {
            "name": "Mamá Rural",
            "demographics.age_range": "30-45",
            "demographics.location": "Rural LATAM",
            "pain_points": [{"description": "No time", "intensity": "high"}],
        }
        fields = list(mapa_global.keys())

        with patch.object(persister, "repo") as mock_repo:
            created = _make_persona(tenant_id=tenant_id, name="Mamá Rural")
            mock_repo.create.return_value = created

            result_id = persister.persist(tenant_id, mapa_global, fields)

            mock_repo.create.assert_called_once()
            assert result_id == created.id

    def test_persist_updates_existing_entity(self) -> None:
        """With entity_id, persister updates existing persona."""
        db = MagicMock()
        persister = BuyerPersonaPersister(db)
        tenant_id = uuid4()
        entity_id = uuid4()
        persona = _make_persona(id=entity_id, tenant_id=tenant_id)

        mapa_global = {
            "demographics.age_range": "25-35",
            "demographics.location": "Urban",
        }
        fields = list(mapa_global.keys())

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_by_id.return_value = persona
            mock_repo.update.return_value = persona

            result_id = persister.persist(
                tenant_id,
                mapa_global,
                fields,
                entity_id=entity_id,
            )

            mock_repo.get_by_id.assert_called_once_with(tenant_id, entity_id)
            mock_repo.update.assert_called_once()
            assert result_id == entity_id

    def test_persist_returns_none_if_entity_not_found(self) -> None:
        """If entity_id is given but not found, return None."""
        db = MagicMock()
        persister = BuyerPersonaPersister(db)
        tenant_id = uuid4()
        entity_id = uuid4()

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_by_id.return_value = None
            result = persister.persist(
                tenant_id,
                {"name": "X"},
                ["name"],
                entity_id=entity_id,
            )
            assert result is None
            mock_repo.update.assert_not_called()

    def test_persist_skips_missing_fields(self) -> None:
        """Fields in fields_to_persist but not in mapa_global are skipped."""
        db = MagicMock()
        persister = BuyerPersonaPersister(db)
        tenant_id = uuid4()
        entity_id = uuid4()
        persona = _make_persona(id=entity_id, tenant_id=tenant_id)

        mapa_global = {"demographics.age_range": "25-35"}
        fields = ["demographics.age_range", "demographics.location"]

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_by_id.return_value = persona
            mock_repo.update.return_value = persona

            persister.persist(tenant_id, mapa_global, fields, entity_id=entity_id)

            call_kwargs = mock_repo.update.call_args[1]
            updates = call_kwargs["updates"]
            # Only age_range present (location was missing from mapa_global)
            assert updates["demographics"]["age_range"] == "25-35"


class TestBuildUpdatesListValidation:
    """_build_updates must reject non-list values for list fields."""

    def test_rejects_string_for_list_field(self) -> None:
        """If the AI stores a list field as a plain string, it must be dropped.

        Regression: the AI sometimes stores e.g. pain_points as a sentence
        ('Su mayor dolor es...') instead of a list[dict]. Persisting that string
        directly would corrupt the DB row and crash future model_validate() calls.
        """
        mapa_global = {
            "pain_points": "Su mayor dolor es sentir que no tiene tiempo",  # string — invalid
            "name": "María Creadora",
        }
        updates = BuyerPersonaPersister._build_updates(mapa_global, ["pain_points", "name"])

        # Scalar 'name' accepted; list field 'pain_points' must be dropped
        assert "name" in updates
        assert "pain_points" not in updates

    def test_accepts_list_for_list_field(self) -> None:
        """Valid list values for list fields must be accepted."""
        mapa_global = {
            "pain_points": [{"description": "No time", "intensity": "high"}],
        }
        updates = BuyerPersonaPersister._build_updates(mapa_global, ["pain_points"])

        assert "pain_points" in updates
        assert updates["pain_points"] == [{"description": "No time", "intensity": "high"}]

    def test_rejects_non_dict_for_dict_field(self) -> None:
        """If a plain 'demographics' key gets a non-dict value, it must be dropped."""
        # demographics is in _DICT_FIELDS; only dot-notation subkeys are the normal path,
        # but if AI somehow passes the parent key directly with a string value, reject it.
        mapa_global = {
            "demographics": "some string value",  # invalid — must be a dict
        }
        updates = BuyerPersonaPersister._build_updates(mapa_global, ["demographics"])
        assert "demographics" not in updates


class TestBuyerPersonaLoadExisting:
    """Tests for load_existing method."""

    def test_load_existing_returns_flat_dict(self) -> None:
        """load_existing flattens persona data to dot-notation keys."""
        db = MagicMock()
        persister = BuyerPersonaPersister(db)
        tenant_id = uuid4()
        entity_id = uuid4()
        persona = _make_persona(
            id=entity_id,
            tenant_id=tenant_id,
            name="Mamá Rural",
            demographics={"age_range": "30-40", "location": "Rural"},
            pain_points=[{"description": "No time"}],
            purchase_triggers=["discount", "urgency"],
        )

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_by_id.return_value = persona
            result = persister.load_existing(tenant_id, entity_id)

        assert result["name"] == "Mamá Rural"
        assert result["demographics.age_range"] == "30-40"
        assert result["demographics.location"] == "Rural"
        assert result["pain_points"] == [{"description": "No time"}]
        assert result["purchase_triggers"] == ["discount", "urgency"]

    def test_load_existing_returns_empty_if_not_found(self) -> None:
        """If entity_id not found, return empty dict."""
        db = MagicMock()
        persister = BuyerPersonaPersister(db)

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_by_id.return_value = None
            result = persister.load_existing(uuid4(), uuid4())
            assert result == {}

    def test_load_existing_calls_repo_exactly_once(self) -> None:
        """Single query guarantee — no N+1."""
        db = MagicMock()
        persister = BuyerPersonaPersister(db)
        tenant_id = uuid4()
        entity_id = uuid4()
        persona = _make_persona(id=entity_id, tenant_id=tenant_id)

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_by_id.return_value = persona
            persister.load_existing(tenant_id, entity_id)

        mock_repo.get_by_id.assert_called_once_with(tenant_id, entity_id)


class TestPersisterRegistryBuyerPersona:
    """Registry recognises buyer_persona."""

    def test_get_buyer_persona_persister(self) -> None:
        """get_persister('buyer_persona') returns BuyerPersonaPersister."""
        db = MagicMock()
        persister = get_persister("buyer_persona", db)
        assert isinstance(persister, BuyerPersonaPersister)

    def test_existing_persisters_still_work(self) -> None:
        """brand and offer persisters unaffected."""
        from src.modules.copilot.infrastructure.persisters.brand_persister import (
            BrandPersister,
        )
        from src.modules.copilot.infrastructure.persisters.offer_persister import (
            OfferPersister,
        )

        db = MagicMock()
        assert isinstance(get_persister("brand", db), BrandPersister)
        assert isinstance(get_persister("offer", db), OfferPersister)
