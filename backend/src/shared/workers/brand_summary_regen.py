"""ARQ worker — regenerate the brand-summary lighthouse.

# [COPILOT-BRAND-SUMMARY-F3] -> docs/domains/copilot/redesign-2026-04/phases/F3-brand-summary-lighthouse.md

Triggered (debounced) by ``BrandSectionUpdatedEvent``. Distills the full
``BrandSettings`` document into ≤800 chars of Spanish neutro copy that
the copilot pre-pends as a stable system-prompt prefix for offer/landing/
campaign/sales routes.

Pipeline:

    1. Load BrandSettings from DB.
    2. Render ``brand_summary_lighthouse.j2`` with the full JSON dump
       and call ``ModelRole.FAST`` (gpt-4o-mini) for distillation.
    3. ``judge_summary`` enforces ≤800 chars + bans voseo. On failure
       the task retries once with a stricter instruction; if it still
       fails we abort (the table keeps the previous version).
    4. UPSERT via ``BrandSummaryRepository`` (version auto-increments).

Why an ARQ job rather than a sync handler:
- Keeps the API request latency bounded — saves return immediately and
  the regen completes in the background (LLM call is the slow path).
- Lets us debounce/dedupe per tenant via ``_job_id`` so flurry-saves in
  Brand Studio collapse to one regen per tenant.
"""

from __future__ import annotations

import re
from uuid import UUID

import structlog

logger = structlog.get_logger(__name__)


# ── Constants ───────────────────────────────────────────────────────────────

_MAX_CHARS = 800
_HARD_CAP = 1000  # stored if judge passes; matches CHECK constraint in migration
_MODEL_ROLE_TIER = "fast"  # ModelRole.FAST — gpt-4o-mini equivalent

# Voseo detector — flags second-person singular argentino/rioplatense
# imperatives and pronouns. Matches the curated list in
# ``.claude/rules/spanish-text.md`` glosario. Word-boundary anchored so
# legitimate words (``vosotros``, ``tener``, ``vosotros podéis``) don't
# trigger.
_VOSEO_RE = re.compile(
    r"\b("
    # Pronouns + clearly second-person voseo conjugations
    r"vos|sos|tenés|querés|podés|sabés|hacés|venís|decís|"
    r"ofrecés|cobrás|ejecutás|acompañás|activás|desactivás|atendés|integrás|"
    # Imperative -á (1st conjugation)
    r"mirá|dejá|poné|usá|hacé|seleccioná|empezá|arrancá|agregá|configurá|revisá|"
    r"guardá|cambiá|linkeá|reactivá|validá|considerá|marcá|"
    r"listá|probá|mostrá|contá|explicá|tomá|esperá|cerrá|llamá|volá|pensá|"
    r"preguntá|intentá|cuidá|recordá|mandá|escuchá|ayudá|pegá|sumá|restá|"
    r"calculá|saltá|andá|tirá|empujá|llevá|traé|terminá|pará|aceptá|notá|"
    # Imperative -é (2nd conjugation)
    r"crecé|corré|leé|aprendé|comé|bebé|metelo|meté|prendé|encendé|vendé|"
    r"hacelo|dejalo|ponelo|sacalo|"
    # Imperative -í (3rd conjugation)
    r"escribí|subí|bajá|abrí|volvé|elegí|seguí|sentí|salí|oí|mové|vení|"
    r"compartí|decime|contame|fijate|acordate|despublicala|cancelala|formulala|"
    r"linkealo|usalo|hacelo|elegilo|cambialo|"
    # Casual markers
    r"chau|che|dale"
    r")\b",
    re.IGNORECASE,
)


# ── Validation helpers (pure, easy to unit-test) ────────────────────────────


class _SummaryRejectionError(Exception):
    """Raised when the LLM output fails ``judge_summary`` validation."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def judge_summary(text: str) -> None:
    """Validate that ``text`` is a usable brand summary.

    Raises ``_SummaryRejectionError`` with a structured ``reason`` so the
    caller can either retry with a stricter instruction or abort. Kept
    intentionally synchronous + dependency-free so the unit tests run
    without DB or LLM fixtures.
    """
    stripped = text.strip()
    if not stripped:
        msg = "empty"
        raise _SummaryRejectionError(msg)
    if len(stripped) > _HARD_CAP:
        msg = f"hard_cap_exceeded:{len(stripped)}"
        raise _SummaryRejectionError(msg)
    if len(stripped) > _MAX_CHARS:
        msg = f"soft_cap_exceeded:{len(stripped)}"
        raise _SummaryRejectionError(msg)
    voseo = _VOSEO_RE.search(stripped)
    if voseo is not None:
        msg = f"voseo:{voseo.group(0)}"
        raise _SummaryRejectionError(msg)


def _normalise_summary(raw: str) -> str:
    """Trim whitespace + collapse blank lines to keep the prefix compact."""
    lines = [line.rstrip() for line in raw.strip().splitlines()]
    return "\n".join(line for line in lines if line)


# ── Core regen primitive (sync — used by ARQ task + admin Streamlit) ────────


def regen_brand_summary_sync(
    *,
    db: object,
    tenant_id: UUID,
    last_section_changed: str | None = None,
) -> str | None:
    """Synchronous regen path. Returns the persisted summary or ``None``.

    Imports are lazy so the worker module can be imported without
    pulling in optional deps (LLM SDK) at module-load time. Unit tests
    monkeypatch ``_invoke_llm`` to avoid network calls.
    """
    import json

    from src.core.enums import ModelRole
    from src.modules.brand.infrastructure.repositories.brand_repository import (
        BrandRepository,
    )
    from src.modules.brand.infrastructure.repositories.brand_summary_repository import (
        BrandSummaryRepository,
    )
    from src.modules.copilot.infrastructure.prompts.base import prompt_loader
    from src.shared.infrastructure.llm.factory import LLMFactory

    settings = BrandRepository(db).get_settings(tenant_id)  # type: ignore[arg-type]
    brand_dump = settings.model_dump(mode="json", exclude_none=True)
    if not brand_dump or _is_empty_brand(brand_dump):
        logger.info(
            "brand_summary_skip_empty",
            tenant_id=str(tenant_id),
        )
        return None

    brand_json = json.dumps(brand_dump, ensure_ascii=False, indent=2)
    rendered = prompt_loader.render(
        "brand_summary_lighthouse",
        brand_json=brand_json,
    )

    llm = LLMFactory.get_service().get_client(ModelRole.FAST)
    llm = llm.bind(temperature=0.4)

    text, model_name = _invoke_llm(llm, rendered)
    summary = _normalise_summary(text)

    try:
        judge_summary(summary)
    except _SummaryRejectionError as exc:
        logger.warning(
            "brand_summary_judge_first_pass_failed",
            tenant_id=str(tenant_id),
            reason=exc.reason,
        )
        # Retry once with an explicit reminder. We re-render the prompt
        # with a stricter suffix; the LLM tends to obey the second time.
        retry_prompt = (
            rendered + "\n\nIMPORTANTE: la respuesta anterior fue rechazada por exceder 800 caracteres "
            "o usar voseo. Acortá y re-escribí en español neutro tuteo (`tú`)."
        )
        text2, model_name = _invoke_llm(llm, retry_prompt)
        summary = _normalise_summary(text2)
        try:
            judge_summary(summary)
        except _SummaryRejectionError as exc2:
            logger.exception(
                "brand_summary_judge_retry_failed",
                tenant_id=str(tenant_id),
                reason=exc2.reason,
            )
            return None

    repo = BrandSummaryRepository(db)  # type: ignore[arg-type]
    row = repo.upsert(
        tenant_id=tenant_id,
        summary=summary,
        model_used=model_name,
        last_section_changed=last_section_changed,
    )
    logger.info(
        "brand_summary_persisted",
        tenant_id=str(tenant_id),
        version=row.version,
        chars=row.chars_count,
    )
    return summary


def _invoke_llm(llm: object, prompt: str) -> tuple[str, str]:
    """Call ``llm.invoke([HumanMessage(prompt)])`` and return (text, model).

    Isolated so unit tests can monkeypatch with a stub returning a
    canned (text, model_name) tuple.
    """
    from langchain_core.messages import HumanMessage

    response = llm.invoke([HumanMessage(content=prompt)])  # type: ignore[attr-defined]
    text = getattr(response, "content", None) or str(response)
    if isinstance(text, list):  # multimodal payload safety
        text = "\n".join(str(part) for part in text)
    model_name = getattr(llm, "model_name", None) or getattr(llm, "model", None) or "fast"
    return str(text), str(model_name)


_BRAND_SUMMARY_REQUIRED_KEYS: frozenset[str] = frozenset(
    {
        "identity",
        "positioning",
        "narrative",
        "brand_personality",
        "story",
        "communication_assets",
    }
)


def _is_empty_brand(dump: dict[str, object]) -> bool:
    """Return True if no field that drives the summary has any data."""
    for key in _BRAND_SUMMARY_REQUIRED_KEYS:
        value = dump.get(key)
        if value:
            return False
    return True


# ── ARQ entry point ─────────────────────────────────────────────────────────


async def regen_brand_summary(
    ctx: dict,
    tenant_id: str,
    last_section_changed: str | None = None,
) -> dict[str, str]:
    """ARQ task: regen the lighthouse for ``tenant_id``.

    Dedupe is enforced upstream by the enqueuer (``_job_id`` parameter
    on ``arq_redis.enqueue_job``). This task is intentionally idempotent:
    running twice for the same tenant is harmless beyond LLM cost.

    The task owns the session lifecycle: ``regen_brand_summary_sync``
    only flushes — without the explicit commit here the worker would
    log ``brand_summary_persisted`` while the row never lands (TP2 S2.4
    regression).
    """
    db_factory = ctx["db_factory"]
    db = db_factory()
    try:
        summary = regen_brand_summary_sync(
            db=db,
            tenant_id=UUID(tenant_id),
            last_section_changed=last_section_changed,
        )
        if summary is not None:
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return {
        "tenant_id": tenant_id,
        "status": "persisted" if summary else "skipped",
    }


__all__ = [
    "judge_summary",
    "regen_brand_summary",
    "regen_brand_summary_sync",
]
