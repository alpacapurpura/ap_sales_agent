"""F3 — unit + integration tests for the brand-summary regen pipeline.

Covers ``judge_summary`` validation rules and ``regen_brand_summary_sync``
end-to-end with a stubbed LLM (no network).
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.modules.brand.domain import BrandSettings
from src.modules.brand.domain.identity import BrandIdentity
from src.modules.brand.domain.positioning import BrandPositioning
from src.modules.brand.infrastructure.repositories.brand_repository import (
    BrandRepository,
)
from src.modules.brand.infrastructure.repositories.brand_summary_repository import (
    BrandSummaryRepository,
)
from src.modules.iam.infrastructure.models.tenant_model import TenantModel
from src.shared.domain.events import EventBus
from src.shared.workers import brand_summary_regen


@pytest.fixture(autouse=True)
def _clear_bus():
    EventBus.clear()
    yield
    EventBus.clear()


# ── judge_summary ───────────────────────────────────────────────────────────


class TestJudgeSummary:
    def test_accepts_neutro_under_800(self) -> None:
        text = "Marca de educación financiera para mujeres LatAm. Promete claridad y libertad. Tu voz es directa, cálida, sin jerga."
        # raises -> bubble up; here we just expect no raise
        brand_summary_regen.judge_summary(text)

    def test_rejects_empty(self) -> None:
        with pytest.raises(brand_summary_regen._SummaryRejectionError) as exc:
            brand_summary_regen.judge_summary("")
        assert exc.value.reason == "empty"

    def test_rejects_over_800(self) -> None:
        with pytest.raises(brand_summary_regen._SummaryRejectionError) as exc:
            brand_summary_regen.judge_summary("x" * 801)
        assert exc.value.reason.startswith("soft_cap_exceeded")

    def test_rejects_voseo_imperative(self) -> None:
        text = "Marca con propósito. Tomá decisiones rápidas y crecé tu negocio."
        with pytest.raises(brand_summary_regen._SummaryRejectionError) as exc:
            brand_summary_regen.judge_summary(text)
        assert exc.value.reason.startswith("voseo:")

    def test_rejects_voseo_pronoun(self) -> None:
        text = "Vos sos la marca. La gente te quiere por eso."
        with pytest.raises(brand_summary_regen._SummaryRejectionError) as exc:
            brand_summary_regen.judge_summary(text)
        assert exc.value.reason.startswith("voseo:")

    def test_does_not_flag_vosotros(self) -> None:
        # vosotros is español castellano — outside the LatAm rule
        # boundary BUT not voseo. Our regex is anchored with \b and the
        # `vos` token is matched but only as a standalone word, not the
        # prefix of `vosotros`. Verify the carve-out works.
        text = "Vosotros podéis usar este faro."
        # vosotros itself is plural -> not in our blocklist; but `podéis`
        # is castellano not voseo. Should NOT raise.
        brand_summary_regen.judge_summary(text)


# ── regen_brand_summary_sync (integration with stubbed LLM) ─────────────────


def _seed_tenant_with_brand(db) -> tuple:
    tenant_id = uuid4()
    tenant = TenantModel(
        id=tenant_id,
        name="Tenant Lighthouse",
        slug=f"lighthouse-{tenant_id.hex[:8]}",
        config_json={},
    )
    db.add(tenant)
    db.commit()
    repo = BrandRepository(db)
    settings = BrandSettings(
        identity=BrandIdentity(brand_name="Visionarias"),
        positioning=BrandPositioning(unique_value_proposition="Llevamos a empresarias a su próximo nivel."),
    )
    repo.save_settings(tenant_id, settings)
    return tenant_id


class _StubLLM:
    def __init__(self, output: str, model_name: str = "gpt-4o-mini") -> None:
        self.output = output
        self.model_name = model_name
        self.calls: list[str] = []

    def invoke(self, messages):
        prompt = "\n".join(getattr(m, "content", str(m)) for m in messages)
        self.calls.append(prompt)

        class _Resp:
            def __init__(self, content: str) -> None:
                self.content = content

        return _Resp(self.output)

    def bind(self, **_kwargs):
        return self


class _StubLLMService:
    def __init__(self, llm: _StubLLM) -> None:
        self._llm = llm

    def get_client(self, _role):
        return self._llm


def test_regen_persists_summary_when_judge_passes(db, monkeypatch) -> None:
    tenant_id = _seed_tenant_with_brand(db)

    output = (
        "Marca formación para empresarias LatAm. Promete escalar negocios sin perder humanidad. "
        "Habla a líderes en transición. Diferencia: comunidad + acompañamiento real. Tono cálido, "
        "directo, sin jerga."
    )
    stub = _StubLLM(output)
    monkeypatch.setattr(
        brand_summary_regen,
        "_invoke_llm",
        lambda _llm, _prompt: (output, "gpt-4o-mini"),
    )

    # Wire the LLMFactory to return our stub service.
    from src.shared.infrastructure.llm import factory as factory_module

    monkeypatch.setattr(
        factory_module.LLMFactory,
        "get_service",
        classmethod(lambda _cls: _StubLLMService(stub)),
    )

    summary = brand_summary_regen.regen_brand_summary_sync(
        db=db,
        tenant_id=tenant_id,
        last_section_changed="identity",
    )

    db.commit()
    assert summary == output

    repo = BrandSummaryRepository(db)
    row = repo.get(tenant_id=tenant_id)
    assert row is not None
    assert row.summary == output
    assert row.version == 1
    assert row.chars_count == len(output)
    assert row.last_section_changed == "identity"


def test_regen_skips_persist_when_brand_is_empty(db, monkeypatch) -> None:
    tenant_id = uuid4()
    db.add(
        TenantModel(
            id=tenant_id,
            name="Empty",
            slug=f"empty-{tenant_id.hex[:8]}",
            config_json={"brand_settings": {}},
        )
    )
    db.commit()

    # Should not even call the LLM — assert by raising if invoked.
    def _explode(_llm, _prompt):
        msg = "LLM should not be called for empty brand"
        raise AssertionError(msg)

    monkeypatch.setattr(brand_summary_regen, "_invoke_llm", _explode)

    summary = brand_summary_regen.regen_brand_summary_sync(
        db=db,
        tenant_id=tenant_id,
    )
    assert summary is None
    repo = BrandSummaryRepository(db)
    assert repo.get(tenant_id=tenant_id) is None


def test_regen_retries_when_first_pass_has_voseo(db, monkeypatch) -> None:
    tenant_id = _seed_tenant_with_brand(db)

    # First call: voseo (rejected). Second call: clean.
    bad = "Vos sos la marca. Cambialo cuando quieras."
    good = "Marca formación empresarias. Promesa clara. Diferencia comunidad. Voz directa, cálida."
    calls = {"n": 0}

    def _stub(_llm, _prompt):
        calls["n"] += 1
        return (bad, "gpt-4o-mini") if calls["n"] == 1 else (good, "gpt-4o-mini")

    monkeypatch.setattr(brand_summary_regen, "_invoke_llm", _stub)

    from src.shared.infrastructure.llm import factory as factory_module

    monkeypatch.setattr(
        factory_module.LLMFactory,
        "get_service",
        classmethod(lambda _cls: _StubLLMService(_StubLLM(good))),
    )

    summary = brand_summary_regen.regen_brand_summary_sync(
        db=db,
        tenant_id=tenant_id,
    )
    db.commit()
    assert summary == good
    assert calls["n"] == 2


def test_regen_aborts_when_retry_also_fails(db, monkeypatch) -> None:
    tenant_id = _seed_tenant_with_brand(db)

    bad_long = "x" * 1500  # hard cap blown — both calls
    monkeypatch.setattr(
        brand_summary_regen,
        "_invoke_llm",
        lambda _llm, _prompt: (bad_long, "gpt-4o-mini"),
    )

    from src.shared.infrastructure.llm import factory as factory_module

    monkeypatch.setattr(
        factory_module.LLMFactory,
        "get_service",
        classmethod(lambda _cls: _StubLLMService(_StubLLM(bad_long))),
    )

    summary = brand_summary_regen.regen_brand_summary_sync(
        db=db,
        tenant_id=tenant_id,
    )
    assert summary is None
    repo = BrandSummaryRepository(db)
    assert repo.get(tenant_id=tenant_id) is None
