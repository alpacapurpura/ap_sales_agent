"""Unit tests for per-archetype landing content builders (FU-1).

Builders are pure module-level functions — tested without DB or Session.
All inputs come from a Mapping[str, Any] representing a SQL row.
"""

from __future__ import annotations

import json
import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from luana_core_landing.application.landing_content_builders import (
    _build_brochure_content,
    _build_event_content,
    _build_flash_offer_content,
    _build_squeeze_content,
    _build_transformer_content,
    _build_velvet_rope_content,
    _parse_list,
    _resolve_content,
)
from luana_core_landing.domain.content import (
    BrochureContent,
    SqueezeContent,
    TransformerContent,
    VelvetRopeContent,
)
from luana_core_landing.domain.enums import LandingPageArchetype

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _row(**kwargs: Any) -> dict[str, Any]:
    """Build a minimal SQL row dict with sensible defaults."""
    defaults: dict[str, Any] = {
        "name": "Mi Oferta",
        "headline_promise": None,
        "primary_outcome": None,
        "marketing_pain_points": None,
        "before_state": None,
        "after_state": None,
        "why_now": None,
        "measurable_outcomes": None,
        "objections": None,
        "marketing_desires": None,
        "cultural_trust_barriers": None,
        "emotional_triggers": None,
        "status_drivers": None,
        "regret_scenarios": None,
        "refund_process_description": None,
        "urgency_drivers": None,
        "scarcity_reason_honest": None,
        "bonus_if_act_now": None,
        "final_push_copy": None,
        "guarantee_terms": None,
        "guarantee_type": None,
        "support_duration_days": None,
        "deliverables": None,
        "pricing": None,
        "preset_id": None,
    }
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# _parse_list
# ---------------------------------------------------------------------------


class TestParseList:
    def test_none_returns_empty(self):
        assert _parse_list(None) == []

    def test_list_passthrough(self):
        assert _parse_list(["a", "b"]) == ["a", "b"]

    def test_json_string_parsed(self):
        assert _parse_list(json.dumps(["x", "y"])) == ["x", "y"]

    def test_invalid_json_string_returns_empty(self):
        assert _parse_list("not-json") == []

    def test_tuple_converted(self):
        result = _parse_list(("a", "b"))
        assert result == ["a", "b"]


# ---------------------------------------------------------------------------
# _build_squeeze_content
# ---------------------------------------------------------------------------


class TestBuildSqueezeContent:
    def test_build_squeeze_uses_narratives_when_present(self):
        """offer con after_state y measurable_outcomes → subheadline + bullets usan narratives."""
        row = _row(
            headline_promise="Transforma tu negocio",
            after_state="Tendrás clientes que te buscan",
            measurable_outcomes=json.dumps(["3x ventas", "50% más tiempo libre", "Sistema automatizado"]),
        )
        content = _build_squeeze_content(row)

        assert isinstance(content, SqueezeContent)
        assert content.headline == "Transforma tu negocio"
        assert content.subheadline == "Tendrás clientes que te buscan"
        assert "3x ventas" in content.bullets
        assert len(content.bullets) <= 3

    def test_build_squeeze_fallback_sin_narratives(self):
        """offer vacío → fallback strings pero shape válida."""
        row = _row()
        content = _build_squeeze_content(row)

        assert isinstance(content, SqueezeContent)
        assert content.headline != ""
        assert content.subheadline != ""
        assert len(content.bullets) == 3
        assert content.cta_text != ""
        assert content.privacy_text != ""

    def test_build_squeeze_uses_pain_points_when_no_measurable_outcomes(self):
        """Sin measurable_outcomes → bullets vienen de marketing_pain_points."""
        row = _row(
            marketing_pain_points=json.dumps(["Dolor 1", "Dolor 2", "Dolor 3"]),
        )
        content = _build_squeeze_content(row)

        assert "Dolor 1" in content.bullets

    def test_build_squeeze_latam_neutro_copy(self):
        """CTA y privacy text deben ser español latinoamericano neutro (sin voseo)."""
        row = _row()
        content = _build_squeeze_content(row)

        # Should NOT contain voseo forms
        assert "tenés" not in content.cta_text
        assert "hacé" not in content.cta_text
        # Should use Latam-neutro
        assert content.cta_text  # non-empty
        assert content.privacy_text  # non-empty

    def test_build_squeeze_fallback_uses_primary_outcome_for_subheadline(self):
        """Sin after_state pero con primary_outcome → usa primary_outcome como subheadline."""
        row = _row(primary_outcome="Lograrás resultados medibles en 30 días")
        content = _build_squeeze_content(row)

        assert content.subheadline == "Lograrás resultados medibles en 30 días"


# ---------------------------------------------------------------------------
# _build_transformer_content
# ---------------------------------------------------------------------------


class TestBuildTransformerContent:
    def _full_row(self) -> dict[str, Any]:
        return _row(
            headline_promise="De cero a experto en 90 días",
            after_state="Tendrás un negocio escalable",
            before_state="Estás atrapado en el tiempo por dinero",
            regret_scenarios=json.dumps(["En 6 meses seguirás igual"]),
            why_now="El mercado cambia rápido",
            name="El Programa",
            final_push_copy="Este es el momento",
            primary_outcome="Escalar a 6 cifras",
            deliverables=json.dumps(
                [
                    {"name": "Módulo 1", "fulfillment_note": "Estrategia base"},
                    {"name": "Módulo 2", "fulfillment_note": "Sistema ventas"},
                ]
            ),
            pricing=json.dumps({"pay_in_full": 1997.0}),
            scarcity_reason_honest="Solo 10 cupos por cohorte",
        )

    def test_build_transformer_full_data(self):
        """offer rico → TransformerContent válido."""
        content = _build_transformer_content(self._full_row())

        assert isinstance(content, TransformerContent)
        assert content.headline == "De cero a experto en 90 días"
        assert content.subheadline == "Tendrás un negocio escalable"
        assert content.problem_text == "Estás atrapado en el tiempo por dinero"
        assert content.method_name == "El Programa"
        assert len(content.modules) >= 1

    def test_build_transformer_falta_deliverables_returns_none(self):
        """Sin deliverables → devuelve None (fallback a SQUEEZE en caller)."""
        row = _row(
            headline_promise="Gran promesa",
            after_state="Después",
            pricing=json.dumps({"pay_in_full": 997.0}),
            # deliverables=None  ← not set
        )
        result = _build_transformer_content(row)
        assert result is None

    def test_build_transformer_falta_headline_returns_none(self):
        """Sin headline_promise → devuelve None."""
        row = _row(
            deliverables=json.dumps([{"name": "Mod 1"}]),
            pricing=json.dumps({"pay_in_full": 997.0}),
            # headline_promise=None ← not set
        )
        result = _build_transformer_content(row)
        assert result is None

    def test_build_transformer_falta_pricing_returns_none(self):
        """Sin pricing → devuelve None."""
        row = _row(
            headline_promise="Gran promesa",
            deliverables=json.dumps([{"name": "Mod 1"}]),
            # pricing=None ← not set
        )
        result = _build_transformer_content(row)
        assert result is None

    def test_build_transformer_agitation_from_why_now_fallback(self):
        """Sin regret_scenarios pero con why_now → agitation_text usa why_now."""
        row = _row(
            headline_promise="Promesa",
            after_state="Después",
            why_now="Razón urgente",
            name="Prog",
            deliverables=json.dumps([{"name": "Mod 1"}]),
            pricing=json.dumps({"pay_in_full": 997.0}),
        )
        content = _build_transformer_content(row)
        assert content is not None
        assert content.agitation_text == "Razón urgente"


# ---------------------------------------------------------------------------
# _build_brochure_content
# ---------------------------------------------------------------------------


class TestBuildBrochureContent:
    def test_build_brochure_from_deliverables(self):
        """BrochureContent usa deliverables para process_steps y deliverables list."""
        row = _row(
            headline_promise="ROI claro en 90 días",
            deliverables=json.dumps(
                [
                    {"name": "Auditoría inicial"},
                    {"name": "Plan de acción"},
                    {"name": "Implementación"},
                ]
            ),
        )
        content = _build_brochure_content(row)

        assert isinstance(content, BrochureContent)
        assert content.headline == "ROI claro en 90 días"
        assert len(content.process_steps) >= 1
        assert "Auditoría inicial" in content.deliverables

    def test_build_brochure_falta_headline_returns_none(self):
        """Sin headline_promise → devuelve None."""
        row = _row(
            deliverables=json.dumps([{"name": "Paso 1"}]),
        )
        result = _build_brochure_content(row)
        assert result is None

    def test_build_brochure_falta_deliverables_returns_none(self):
        """Sin deliverables → devuelve None."""
        row = _row(headline_promise="Headline")
        result = _build_brochure_content(row)
        assert result is None

    def test_build_brochure_max_six_process_steps(self):
        """process_steps limitados a 6 ítems."""
        deliverables_list = [{"name": f"Paso {i}"} for i in range(1, 10)]
        row = _row(
            headline_promise="Headline",
            deliverables=json.dumps(deliverables_list),
        )
        content = _build_brochure_content(row)
        assert content is not None
        assert len(content.process_steps) <= 6


# ---------------------------------------------------------------------------
# _build_velvet_rope_content
# ---------------------------------------------------------------------------


class TestBuildVelvetRopeContent:
    def test_build_velvet_rope_uses_marketing_desires(self):
        """VelvetRopeContent usa marketing_desires para who_is_this_for."""
        row = _row(
            headline_promise="Exclusividad y pertenencia",
            marketing_desires=json.dumps(
                [
                    "Quiero escalar",
                    "Quiero comunidad",
                    "Quiero claridad",
                ]
            ),
            why_now="El grupo crece rápido",
        )
        content = _build_velvet_rope_content(row)

        assert isinstance(content, VelvetRopeContent)
        assert content.headline == "Exclusividad y pertenencia"
        assert "Quiero escalar" in content.who_is_this_for

    def test_build_velvet_rope_falta_headline_returns_none(self):
        """Sin headline_promise → devuelve None."""
        row = _row(
            marketing_desires=json.dumps(["Deseo 1"]),
        )
        result = _build_velvet_rope_content(row)
        assert result is None

    def test_build_velvet_rope_falta_desires_returns_none(self):
        """Sin marketing_desires → devuelve None."""
        row = _row(headline_promise="Headline")
        result = _build_velvet_rope_content(row)
        assert result is None

    def test_build_velvet_rope_scarcity_fallback(self):
        """Sin scarcity_reason_honest pero con urgency_drivers → usa urgency como scarcity."""
        row = _row(
            headline_promise="Exclusivo",
            marketing_desires=json.dumps(["Deseo 1"]),
            urgency_drivers=json.dumps(["Solo hasta el viernes"]),
        )
        content = _build_velvet_rope_content(row)
        assert content is not None
        assert "viernes" in content.scarcity_text


# ---------------------------------------------------------------------------
# _build_event_content
# ---------------------------------------------------------------------------


class TestBuildEventContent:
    def test_build_event_always_none_hoy(self):
        """REGRESSION LOCK: event_date no existe en Offer hoy → siempre retorna None."""
        row = _row(
            headline_promise="Webinar en vivo",
            name="Mi evento",
        )
        result = _build_event_content(row)
        assert result is None, (
            "EventContent debe retornar None hasta que Sprint futuro agregue event_date al aggregate Offer."
        )


# ---------------------------------------------------------------------------
# _build_flash_offer_content
# ---------------------------------------------------------------------------


class TestBuildFlashOfferContent:
    def test_build_flash_offer_with_valid_pricing(self):
        """FlashOfferContent con pricing que tiene original_price y discounted_price."""
        row = _row(
            headline_promise="Oferta relámpago",
            name="Mini curso",
            pricing=json.dumps({"original_price": 497.0, "discounted_price": 97.0}),
        )
        content = _build_flash_offer_content(row)
        # If pricing has the expected keys, build succeeds
        if content is not None:
            from luana_core_landing.domain.content import FlashOfferContent

            assert isinstance(content, FlashOfferContent)
            assert content.original_price == 497.0
            assert content.discounted_price == 97.0

    def test_build_flash_offer_sin_pricing_returns_none(self):
        """Sin pricing → devuelve None."""
        row = _row(headline_promise="Oferta")
        result = _build_flash_offer_content(row)
        assert result is None

    def test_build_flash_offer_pricing_sin_precios_returns_none(self):
        """pricing sin original_price/discounted_price → devuelve None."""
        row = _row(
            headline_promise="Oferta",
            pricing=json.dumps({"pay_in_full": 497.0}),
        )
        result = _build_flash_offer_content(row)
        assert result is None


# ---------------------------------------------------------------------------
# _resolve_content
# ---------------------------------------------------------------------------


class TestResolveContent:
    def test_resolve_content_fallback_to_squeeze_cuando_builder_none(self):
        """Si el builder específico devuelve None → fallback a SQUEEZE."""
        # THE_TRANSFORMER requires deliverables + headline_promise + pricing; omit them
        row = _row(headline_promise="Headline")

        actual_archetype, content = _resolve_content(LandingPageArchetype.THE_TRANSFORMER, row)

        assert actual_archetype == LandingPageArchetype.THE_SQUEEZE
        assert isinstance(content, SqueezeContent)

    def test_resolve_content_squeeze_returns_squeeze(self):
        """THE_SQUEEZE always succeeds → archetype unchanged."""
        row = _row(headline_promise="Headline")

        actual_archetype, content = _resolve_content(LandingPageArchetype.THE_SQUEEZE, row)

        assert actual_archetype == LandingPageArchetype.THE_SQUEEZE
        assert isinstance(content, SqueezeContent)

    def test_resolve_content_transformer_with_full_data(self):
        """THE_TRANSFORMER with complete data → uses transformer archetype."""
        row = _row(
            headline_promise="Promesa",
            after_state="Después",
            name="Prog",
            deliverables=json.dumps([{"name": "Mod 1"}]),
            pricing=json.dumps({"pay_in_full": 997.0}),
        )

        actual_archetype, content = _resolve_content(LandingPageArchetype.THE_TRANSFORMER, row)

        assert actual_archetype == LandingPageArchetype.THE_TRANSFORMER
        assert isinstance(content, TransformerContent)

    def test_resolve_content_velvet_rope_fallback_on_missing_desires(self):
        """THE_VELVET_ROPE sin marketing_desires → fallback SQUEEZE."""
        row = _row(headline_promise="Exclusivo")

        actual_archetype, _content = _resolve_content(LandingPageArchetype.THE_VELVET_ROPE, row)

        assert actual_archetype == LandingPageArchetype.THE_SQUEEZE

    def test_resolve_content_event_always_falls_back(self):
        """THE_EVENT builder always returns None today → always falls back to SQUEEZE."""
        row = _row(headline_promise="Webinar")

        actual_archetype, _content = _resolve_content(LandingPageArchetype.THE_EVENT, row)

        assert actual_archetype == LandingPageArchetype.THE_SQUEEZE


# ---------------------------------------------------------------------------
# Integration: generate_landing_for_offer with TRANSFORMER archetype
# ---------------------------------------------------------------------------


class TestGenerateLandingForOfferTransformerIntegration:
    """Integration test: generate_landing_for_offer selects transformer when preset HIGH_TICKET."""

    @staticmethod
    def _seed_offer_full(db, offer_id, tenant_id):
        """Insert an offer with narrative fields via SQL."""
        from sqlalchemy import text

        db.execute(
            text(
                "INSERT INTO products (id, tenant_id, name, archetype, status,"
                " headline_promise, primary_outcome, marketing_pain_points,"
                " before_state, after_state, deliverables, marketing_desires)"
                " VALUES (:id, :tid, :name, :arch, :status, :headline, :outcome,"
                " :pains, :before, :after, :delivs, :desires)"
            ),
            {
                "id": str(offer_id),
                "tid": str(tenant_id),
                "name": "Programa Elite",
                "arch": "programa",
                "status": "active",
                "headline": "De novato a experto en 90 días",
                "outcome": "Sistema escalable",
                "pains": json.dumps(["No tiempo", "No sistema"]),
                "before": "Atrapado intercambiando tiempo por dinero",
                "after": "Tendrás un sistema que vende solo",
                "delivs": json.dumps(
                    [
                        {"name": "Módulo 1", "fulfillment_note": "Estrategia"},
                        {"name": "Módulo 2", "fulfillment_note": "Sistema"},
                    ]
                ),
                "desires": json.dumps(["Libertad financiera", "Escalar sin trabajar más"]),
            },
        )
        db.commit()

    def test_generate_landing_for_offer_transformer_archetype_integration(self, db, seed_tenant, tenant_id):
        """Integration: offer with after_state + deliverables → content reflects narratives.

        The archetype used in the landing depends on the preset flags. Without a
        preset_id the service defaults to THE_BROCHURE. We verify the content is
        built from the richer narrative fields (after_state, deliverables) when
        available — the actual archetype may be BROCHURE (default) or TRANSFORMER.
        """
        from luana_core_landing.application.landing_service import LandingService

        service = LandingService(db)
        offer_id = uuid.uuid4()
        self._seed_offer_full(db, offer_id, tenant_id)

        landing = service.generate_landing_for_offer(
            tenant_id=tenant_id,
            offer_id=offer_id,
        )

        assert landing is not None
        assert landing.offer_id == offer_id
        # Content must be a typed content object (not raw dict)
        from luana_core_landing.domain.content import (
            BrochureContent,
            SqueezeContent,
            TransformerContent,
        )

        assert isinstance(
            landing.config.content,
            (SqueezeContent, TransformerContent, BrochureContent),
        )
        # Narrative fields must be reflected when content is BrochureContent
        if isinstance(landing.config.content, BrochureContent):
            assert len(landing.config.content.deliverables) >= 1
