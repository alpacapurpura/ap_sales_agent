"""Tests for legal / compliance guardrail integration in TenantKnowledgeBuilder.

The brand-studio Legal section (``brand.legal``) persists 23 fields on the
``BrandIdentity`` aggregate. The sales-agent surfaces three subsets of those
fields into the agent identity prompt:

1. **Guardrails** (``sales_agent_disclaimer``, ``sales_agent_out_of_scope``,
   ``escalation_contact``) — internal, **never** disclosed to leads.
2. **Credenciales Regulatorias** (``regulated_profession_body``,
   ``professional_license_*``, ``operating_authorization``,
   ``liability_insurance_carrier``) — disclosable only when the lead asks.
3. **Documentos Legales** (``terms_url``, ``privacy_url``, ``cookies_url``,
   ``refund_policy_url``, ``acceptable_use_url``) — shared on request.

These tests verify:
    (a) ``TenantKnowledgeBuilder`` derives the three ``has_*`` flags correctly.
    (b) ``agent_identity.j2`` renders each section conditionally and does not
        leak guardrails into lead-visible copy.
    (c) Backward compatibility — templates still render when the new legal
        keys are absent entirely (existing tenants migrate gradually).
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = str(
    Path(__file__).parent
    / ".."
    / ".."
    / ".."
    / "src"
    / "modules"
    / "sales_agent"
    / "infrastructure"
    / "prompts"
    / "templates",
)


@pytest.fixture
def jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(Path(TEMPLATES_DIR).resolve())),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )


TENANT_ID = uuid.UUID("cccc0000-0000-0000-0000-000000000001")


def _base_identity_context(**identity_overrides: Any) -> dict[str, Any]:
    """Minimal context for rendering agent_identity.j2 with overrides."""
    return {
        "has_brand": True,
        "identity": {"brand_name": "ConsultorioDemo", **identity_overrides},
        "strategy": {},
        "story": {},
        "team": [],
        "contact": {},
        "positioning": {},
        "testimonials": [],
        "authority_items": [],
        "default_avatar": {},
        "avatars": [],
        "offers": [],
        "has_team": False,
        "has_avatars": False,
        "has_offers": False,
        "has_testimonials": False,
        "has_authority": False,
        "personality_instruction": None,
        "channel_type": "whatsapp",
    }


def _make_brand_knowledge(brand_data: dict) -> MagicMock:
    from src.shared.links.ports.brand import BrandKnowledgeDTO

    return BrandKnowledgeDTO(brand_data=brand_data, avatars=[], personality_profile=None)


# ─── Knowledge builder flag derivation ────────────────────────────────────────


class TestKnowledgeBuilderLegalFlags:
    """Flag derivation for the three legal sections."""

    def _run_builder(self, identity: dict[str, Any]) -> str:
        brand_data = {
            "identity": identity,
            "strategy": {},
            "story": {},
            "team": [],
            "contact": {},
            "positioning": {},
            "testimonials": [],
        }
        mock_brand_port = MagicMock()
        mock_brand_port.get_brand_knowledge.return_value = _make_brand_knowledge(brand_data)
        mock_db = MagicMock()

        with (
            patch(
                "src.modules.sales_agent.application.services.knowledge_builder.create_brand_data_port",
                return_value=mock_brand_port,
            ),
            patch(
                "src.modules.sales_agent.application.services.knowledge_builder.get_offer_repository",
            ) as mock_offer_repo,
            patch(
                "src.modules.sales_agent.application.services.knowledge_builder.SemanticRouter",
            ),
        ):
            mock_offer_repo.return_value.get_all_by_tenant.return_value = []
            from src.modules.sales_agent.application.services.knowledge_builder import (
                TenantKnowledgeBuilder,
            )

            return TenantKnowledgeBuilder(mock_db).build_identity(TENANT_ID)

    def test_guardrails_section_renders_when_disclaimer_set(self) -> None:
        """Disclaimer alone is enough to surface the Guardrails block."""
        result = self._run_builder(
            {
                "brand_name": "Clínica Demo",
                "sales_agent_disclaimer": (
                    "Información orientativa. Toda atención clínica requiere consulta presencial."
                ),
            }
        )
        assert "Guardrails" in result
        assert "consulta presencial" in result

    def test_guardrails_section_renders_out_of_scope_topics(self) -> None:
        """Each non-empty line in sales_agent_out_of_scope becomes a bullet."""
        result = self._run_builder(
            {
                "brand_name": "Clínica Demo",
                "sales_agent_out_of_scope": "diagnóstico\nreceta\nemergencia",
            }
        )
        assert "diagnóstico" in result
        assert "receta" in result
        assert "emergencia" in result

    def test_guardrails_section_absent_when_all_empty(self) -> None:
        """Tenants without legal guardrails don't see the block."""
        result = self._run_builder({"brand_name": "Clínica Demo"})
        assert "Guardrails" not in result

    def test_regulated_profession_section_renders_when_license_set(self) -> None:
        """Credenciales block appears when any of the 4 license fields is set."""
        result = self._run_builder(
            {
                "brand_name": "Clínica Demo",
                "regulated_profession_body": "Colegio Médico del Perú",
                "professional_license_number": "CMP 45678",
            }
        )
        assert "Credenciales Regulatorias" in result
        assert "Colegio Médico del Perú" in result
        assert "CMP 45678" in result

    def test_regulated_profession_never_discloses_insurance_details(self) -> None:
        """liability_insurance_carrier is acknowledged but policy number is never present."""
        result = self._run_builder(
            {
                "brand_name": "Clínica Demo",
                "liability_insurance_carrier": "Pacífico Seguros",
            }
        )
        assert "Pacífico Seguros" in result
        # Guardrail copy must instruct not to disclose policy details
        assert "NUNCA divulgues número de póliza" in result

    def test_legal_documents_block_lists_provided_urls(self) -> None:
        """terms_url / privacy_url / refund_policy_url render when set."""
        result = self._run_builder(
            {
                "brand_name": "Clínica Demo",
                "terms_url": "https://example.com/terminos",
                "privacy_url": "https://example.com/privacidad",
                "refund_policy_url": "https://example.com/reembolsos",
            }
        )
        assert "https://example.com/terminos" in result
        assert "https://example.com/privacidad" in result
        assert "https://example.com/reembolsos" in result

    def test_all_legal_sections_absent_when_fields_empty(self) -> None:
        """Template remains clean for tenants that never filled Legal section."""
        result = self._run_builder({"brand_name": "Clínica Demo"})
        assert "Guardrails" not in result
        assert "Credenciales Regulatorias" not in result
        # "Documentos Legales" block must not appear without URLs
        assert "Documentos Legales" not in result


# ─── Template rendering directly (fast — no builder mocks) ────────────────────


class TestAgentIdentityTemplateLegal:
    """Jinja template renders correctly given each combination of flags."""

    def test_disclaimer_instructs_agent_to_include_at_start_or_close(
        self,
        jinja_env: Environment,
    ) -> None:
        ctx = _base_identity_context(
            sales_agent_disclaimer="Información orientativa.",
        )
        ctx["has_legal_guardrails"] = True
        ctx["has_regulated_profession"] = False
        ctx["has_legal_documents"] = False
        result = jinja_env.get_template("agent_identity.j2").render(**ctx)
        # The template must both print the disclaimer AND instruct the agent
        # to include it at the start or close of every conversation.
        assert "Información orientativa." in result
        assert "DEBES incluir" in result

    def test_out_of_scope_guardrail_tells_agent_never_to_reveal_the_list(
        self,
        jinja_env: Environment,
    ) -> None:
        ctx = _base_identity_context(
            sales_agent_out_of_scope="diagnóstico\nreceta",
            escalation_contact="+51 999 888 777",
        )
        ctx["has_legal_guardrails"] = True
        ctx["has_regulated_profession"] = False
        ctx["has_legal_documents"] = False
        result = jinja_env.get_template("agent_identity.j2").render(**ctx)
        # Must mention escalation contact and prohibit revealing the list
        assert "+51 999 888 777" in result
        assert "NUNCA menciones la lista" in result

    def test_regulated_profession_section_tagged_as_on_ask_only(
        self,
        jinja_env: Environment,
    ) -> None:
        ctx = _base_identity_context(
            regulated_profession_body="COFEPRIS",
            professional_license_number="CED-123",
        )
        ctx["has_legal_guardrails"] = False
        ctx["has_regulated_profession"] = True
        ctx["has_legal_documents"] = False
        result = jinja_env.get_template("agent_identity.j2").render(**ctx)
        # Section header must make the on-ask-only rule explicit
        assert "solo si el lead pregunta" in result
        assert "COFEPRIS" in result

    def test_template_backward_compatible_when_legal_flags_absent(
        self,
        jinja_env: Environment,
    ) -> None:
        """No has_legal_* flags at all — template still renders for existing tenants."""
        ctx = _base_identity_context()
        # Intentionally do NOT set any has_legal_* key
        rendered = jinja_env.get_template("agent_identity.j2").render(**ctx)
        assert "ConsultorioDemo" in rendered
        assert "Guardrails" not in rendered
        assert "Credenciales Regulatorias" not in rendered
