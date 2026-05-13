"""Tests for the document-extraction domain registry."""

from __future__ import annotations

from luana_core_copilot.domain.extraction_domain_registry import (
    ExtractionDomainConfig,
    get_extraction_config,
    supported_domains,
)


class TestSupportedDomains:
    def test_returns_brand_offer_buyer_persona(self) -> None:
        domains = supported_domains()
        assert set(domains) == {"brand", "offer", "buyer_persona"}
        assert domains == tuple(sorted(domains)), "domains must be sorted for stability"


class TestGetExtractionConfig:
    def test_brand_config(self) -> None:
        cfg = get_extraction_config("brand")
        assert isinstance(cfg, ExtractionDomainConfig)
        assert cfg.domain == "brand"
        assert cfg.template_name == "interview/brand_doc_extraction"
        assert cfg.persister_key == "brand"
        assert cfg.response_value_kind == "scalar"

    def test_offer_config(self) -> None:
        cfg = get_extraction_config("offer")
        assert cfg is not None
        assert cfg.template_name == "interview/offer_doc_extraction"
        assert cfg.persister_key == "offer"

    def test_buyer_persona_config_is_mixed(self) -> None:
        cfg = get_extraction_config("buyer_persona")
        assert cfg is not None
        assert cfg.template_name == "interview/buyer_persona_doc_extraction"
        assert cfg.response_value_kind == "mixed"

    def test_unknown_domain_returns_none(self) -> None:
        assert get_extraction_config("nonexistent") is None

    def test_domain_field_matches_key(self) -> None:
        for domain in supported_domains():
            cfg = get_extraction_config(domain)
            assert cfg is not None
            assert cfg.domain == domain
