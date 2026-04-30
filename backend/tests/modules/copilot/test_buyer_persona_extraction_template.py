"""Regression guards for the buyer_persona document-extraction prompt.

The prompt drives the gpt-4o-mini extractor that turns an uploaded ICP
document into ``proposal`` updates. Conv 0d64c4a9 (2026-04-27) showed the
extractor returning only 10 fields from a clearly-complete profile —
``desires``, ``purchase_triggers`` and ``anti_patterns`` were all dropped
because the prompt told the model to default to "omit" with no explicit
category cues.

These tests pin the template at three behaviours we will not regress on:

1. Default is to extract — the over-conservative "Sin evidencia clara →
   omite" line is replaced with an inverted rule that asks the model to
   capture every category the document touches, however briefly.
2. Each remaining list-shaped field has an explicit semantic cue so the
   model can route inferred evidence to the right path (desires vs.
   pain_points are easy to confuse).
3. Sub-keys under ``demographics``/``psychographics``/``buyer_journey``
   are encouraged when the document has a single concrete data point —
   the previous wording told the model to skip them silently.

NOTE: ``objections`` and ``preferred_channels`` were removed from the
buyer_persona surface in PR-1 PI-4 S1 (2026-04-29). Tests for those
cues are intentionally absent.
"""

from __future__ import annotations

from src.modules.copilot.domain.field_paths_hint import build_field_paths_hint
from src.shared.infrastructure.prompts.base import prompt_loader


def _render() -> str:
    return prompt_loader.render(
        "interview/buyer_persona_doc_extraction",
        document_text="Texto del documento de prueba.",
        existing_data="",
        field_paths_hint=build_field_paths_hint("buyer_persona"),
    )


class TestExtractionTemplateInversion:
    """Default behaviour is extract, not omit."""

    def test_does_not_default_to_omit(self) -> None:
        rendered = _render()
        # Pre-fix line that suppressed full extraction. Keep blocked.
        assert "Sin evidencia clara → omite el campo" not in rendered, (
            "Conservative default re-introduced — model will skip categories like desires/objections again."
        )

    def test_explicitly_states_extract_default(self) -> None:
        rendered = _render().lower()
        # The new rule names the inverted default in plain words so the
        # behaviour is auditable from the prompt alone.
        assert "por defecto" in rendered or "default" in rendered
        assert "extraer" in rendered or "captura" in rendered


class TestExtractionTemplateCategoryCues:
    """Every collection field surfaces a semantic cue the model can match."""

    def test_desires_have_explicit_cue(self) -> None:
        rendered = _render().lower()
        assert "desires" in rendered
        # "lograr / aspira / quiere" → the verbs the model needs to see
        # to decide an evidence belongs to desires rather than pain_points.
        assert any(cue in rendered for cue in ("lograr", "aspira", "quiere conseguir"))

    def test_purchase_triggers_have_explicit_cue(self) -> None:
        rendered = _render().lower()
        assert "purchase_triggers" in rendered
        assert any(cue in rendered for cue in ("gatillo", "trigger", "decide comprar", "decisión"))


class TestExtractionTemplateSubKeyGuidance:
    """Dynamic sub-keys under JSONB roots get an explicit nudge."""

    def test_mentions_dynamic_sub_keys_explicitly(self) -> None:
        rendered = _render()
        for root in ("demographics", "psychographics", "buyer_journey"):
            assert f"{root}." in rendered, f"Sub-key root '{root}.*' missing — model will not infer dynamic sub-keys."

    def test_encourages_partial_evidence_for_sub_keys(self) -> None:
        rendered = _render().lower()
        # The new wording asks the model to emit a sub-key whenever there
        # is ANY concrete data point, even brief — the prior version
        # suppressed sub-keys on partial evidence.
        assert any(
            cue in rendered
            for cue in (
                "aunque sea breve",
                "aunque la mención sea breve",
                "un dato concreto",
                "incluso un fragmento",
            )
        )


class TestExtractionTemplateLatamSpanish:
    """Template stays in neutral LATAM Spanish — no voseo regressions."""

    def test_no_voseo_imperatives(self) -> None:
        rendered = _render().lower()
        # Snapshot of the imperatives we explicitly migrated away from
        # under the spanish-text rule. The list is not exhaustive but
        # catches the patterns we have actually seen drift back in.
        forbidden = (
            "tenés",
            "podés",
            "querés",
            "sabés",
            "elegí ",
            "fijate",
            "dejá ",
            "agregá ",
            "andá ",
        )
        for pattern in forbidden:
            assert pattern not in rendered, f"Voseo pattern '{pattern.strip()}' leaked into prompt."
