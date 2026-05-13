"""Regression tests — PR-1 PI-4 S1: objections + preferred_channels dropped.

These tests are RED before the cleanup and GREEN after. They guard against
any future re-introduction of the two fields we intentionally removed.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Domain layer
# ---------------------------------------------------------------------------


def test_buyer_persona_entity_has_no_objections_field() -> None:
    """BuyerPersona Pydantic entity must not declare objections."""
    from luana_core_brand_studio.domain.buyer_persona import BuyerPersona

    fields = BuyerPersona.model_fields
    assert "objections" not in fields


def test_buyer_persona_entity_has_no_preferred_channels_field() -> None:
    """BuyerPersona Pydantic entity must not declare preferred_channels."""
    from luana_core_brand_studio.domain.buyer_persona import BuyerPersona

    fields = BuyerPersona.model_fields
    assert "preferred_channels" not in fields


# ---------------------------------------------------------------------------
# Infrastructure layer — SQLAlchemy model
# ---------------------------------------------------------------------------


def test_buyer_persona_model_has_no_objections_column() -> None:
    """The buyer_personas table must not have an objections column."""
    from luana_core_brand_studio.infrastructure.models.buyer_persona_model import (
        BuyerPersonaModel,
    )

    columns = {c.name for c in BuyerPersonaModel.__table__.columns}
    assert "objections" not in columns


def test_buyer_persona_model_has_no_preferred_channels_column() -> None:
    """The buyer_personas table must not have a preferred_channels column."""
    from luana_core_brand_studio.infrastructure.models.buyer_persona_model import (
        BuyerPersonaModel,
    )

    columns = {c.name for c in BuyerPersonaModel.__table__.columns}
    assert "preferred_channels" not in columns


# ---------------------------------------------------------------------------
# API layer — DTOs
# ---------------------------------------------------------------------------


def test_response_dto_excludes_objections() -> None:
    """BuyerPersonaResponseDTO must not expose objections."""
    from luana_core_brand_studio.api.dto.buyer_personas import BuyerPersonaResponseDTO

    fields = BuyerPersonaResponseDTO.model_fields
    assert "objections" not in fields


def test_response_dto_excludes_preferred_channels() -> None:
    """BuyerPersonaResponseDTO must not expose preferred_channels."""
    from luana_core_brand_studio.api.dto.buyer_personas import BuyerPersonaResponseDTO

    fields = BuyerPersonaResponseDTO.model_fields
    assert "preferred_channels" not in fields


def test_update_dto_excludes_objections() -> None:
    """BuyerPersonaSectionUpdateDTO must not accept objections."""
    from luana_core_brand_studio.api.dto.buyer_personas import BuyerPersonaSectionUpdateDTO

    fields = BuyerPersonaSectionUpdateDTO.model_fields
    assert "objections" not in fields


def test_update_dto_excludes_preferred_channels() -> None:
    """BuyerPersonaSectionUpdateDTO must not accept preferred_channels."""
    from luana_core_brand_studio.api.dto.buyer_personas import BuyerPersonaSectionUpdateDTO

    fields = BuyerPersonaSectionUpdateDTO.model_fields
    assert "preferred_channels" not in fields


# ---------------------------------------------------------------------------
# API layer — completeness denominator
# ---------------------------------------------------------------------------


def test_profile_fields_excludes_dropped_fields() -> None:
    """_PROFILE_FIELDS in buyer_personas route must not include dropped fields."""
    import src.modules.brand.api.buyer_personas as bp_api

    assert "objections" not in bp_api._PROFILE_FIELDS
    assert "preferred_channels" not in bp_api._PROFILE_FIELDS


def test_completeness_denominator_is_seven() -> None:
    """After dropping 2 fields from 9, the denominator must be 7."""
    import src.modules.brand.api.buyer_personas as bp_api

    assert len(bp_api._PROFILE_FIELDS) == 7


# ---------------------------------------------------------------------------
# Domain — FieldContract registry
# ---------------------------------------------------------------------------


def test_field_contract_section_map_excludes_objections() -> None:
    """BUYER_PERSONA_SECTION_MAP must not map objections to any section."""
    from luana_core_brand_studio.domain.buyer_persona_field_contract import (
        BUYER_PERSONA_SECTION_MAP,
    )

    assert "objections" not in BUYER_PERSONA_SECTION_MAP


def test_field_contract_section_map_excludes_preferred_channels() -> None:
    """BUYER_PERSONA_SECTION_MAP must not map preferred_channels to any section."""
    from luana_core_brand_studio.domain.buyer_persona_field_contract import (
        BUYER_PERSONA_SECTION_MAP,
    )

    assert "preferred_channels" not in BUYER_PERSONA_SECTION_MAP


def test_field_contract_overrides_excludes_objections() -> None:
    """BUYER_PERSONA_FIELD_OVERRIDES must not carry an objections entry."""
    from luana_core_brand_studio.domain.buyer_persona_field_contract import (
        BUYER_PERSONA_FIELD_OVERRIDES,
    )

    assert "objections" not in BUYER_PERSONA_FIELD_OVERRIDES


def test_field_contract_overrides_excludes_preferred_channels() -> None:
    """BUYER_PERSONA_FIELD_OVERRIDES must not carry a preferred_channels entry."""
    from luana_core_brand_studio.domain.buyer_persona_field_contract import (
        BUYER_PERSONA_FIELD_OVERRIDES,
    )

    assert "preferred_channels" not in BUYER_PERSONA_FIELD_OVERRIDES


# ---------------------------------------------------------------------------
# Copilot — persister
# ---------------------------------------------------------------------------


def test_copilot_persister_list_fields_excludes_objections() -> None:
    """BuyerPersonaPersister._LIST_FIELDS must not contain objections."""
    from luana_core_copilot.infrastructure.persisters.buyer_persona_persister import (
        _LIST_FIELDS,
    )

    assert "objections" not in _LIST_FIELDS


def test_copilot_persister_list_fields_excludes_preferred_channels() -> None:
    """BuyerPersonaPersister._LIST_FIELDS must not contain preferred_channels."""
    from luana_core_copilot.infrastructure.persisters.buyer_persona_persister import (
        _LIST_FIELDS,
    )

    assert "preferred_channels" not in _LIST_FIELDS


# ---------------------------------------------------------------------------
# Copilot — field paths hint
# ---------------------------------------------------------------------------


def test_field_paths_hint_buyer_persona_excludes_objections() -> None:
    """_LIST_PATHS['buyer_persona'] must not include objections after cleanup."""
    from luana_core_copilot.domain.field_paths_hint import _LIST_PATHS

    assert "objections" not in _LIST_PATHS.get("buyer_persona", set())


def test_field_paths_hint_buyer_persona_excludes_preferred_channels() -> None:
    """_LIST_PATHS['buyer_persona'] must not include preferred_channels after cleanup."""
    from luana_core_copilot.domain.field_paths_hint import _LIST_PATHS

    assert "preferred_channels" not in _LIST_PATHS.get("buyer_persona", set())


def test_offer_list_paths_objections_still_present() -> None:
    """offer.objections must remain in _LIST_PATHS (distinct field, NOT dropped)."""
    from luana_core_copilot.domain.field_paths_hint import _LIST_PATHS

    assert "objections" in _LIST_PATHS.get("offer", set())


# ---------------------------------------------------------------------------
# Copilot — extraction template content
# ---------------------------------------------------------------------------


def test_extraction_template_does_not_mention_objections_as_list_field() -> None:
    """After cleanup, the template rule-4 block must not describe objections."""
    from luana_core_copilot.domain.field_paths_hint import build_field_paths_hint
    from luana_core_platform.infrastructure.prompts.base import prompt_loader

    rendered = prompt_loader.render(
        "interview/buyer_persona_doc_extraction",
        document_text="Documento de prueba.",
        existing_data="",
        field_paths_hint=build_field_paths_hint("buyer_persona"),
    )
    # The cue line "objections → lista de objetos {text, response}" must be gone.
    assert "`objections` → lista" not in rendered
    assert "preferred_channels" not in rendered.lower() or (
        # 'preferred_channels' may appear in field_paths_hint if it's still in
        # catalog — but after cleanup it must NOT appear in rule-4 cues block.
        "preferred_channels` → lista" not in rendered
    )


def test_extraction_template_does_not_mention_preferred_channels_as_list_field() -> None:
    """After cleanup, the template rule-4 block must not describe preferred_channels."""
    from luana_core_copilot.domain.field_paths_hint import build_field_paths_hint
    from luana_core_platform.infrastructure.prompts.base import prompt_loader

    rendered = prompt_loader.render(
        "interview/buyer_persona_doc_extraction",
        document_text="Documento de prueba.",
        existing_data="",
        field_paths_hint=build_field_paths_hint("buyer_persona"),
    )
    assert "`preferred_channels` → lista" not in rendered
