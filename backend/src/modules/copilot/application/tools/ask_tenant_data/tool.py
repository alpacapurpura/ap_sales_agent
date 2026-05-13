"""F5 — ``ask_tenant_data`` tool entry point.

Pipeline orchestrator + langchain ``BaseTool`` wrapper. Tests inject
collaborators (``db``, ``llm_intent``, ``llm_synth``, ``accessors``) via
:func:`_ask_tenant_data_impl` to keep the unit suites away from
``discover_providers()`` (which loads every module's provider eagerly and
opens a Postgres connection — too heavy for SQLite-backed unit tests).

# [COPILOT-ASK-TENANT-DATA-F5] -> docs/domains/copilot/redesign-2026-04/phases/F5-ask-tenant-data.md
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import structlog
from langchain_core.tools import tool
from luana_core_copilot.application.data_access import (
    ConversationDataAccessProvider,
)
from luana_core_copilot.application.tools.ask_tenant_data.executor import (
    NoAccessorError,
    execute_plan,
)
from luana_core_copilot.application.tools.ask_tenant_data.intent_classifier import (
    classify_intent,
)
from luana_core_copilot.application.tools.ask_tenant_data.query_builder import (
    build_plan,
)
from luana_core_copilot.application.tools.ask_tenant_data.state_check import (
    annotate_state,
)
from luana_core_copilot.application.tools.ask_tenant_data.synthesizer import (
    synthesize_answer,
)
from luana_core_copilot.infrastructure.cache.data_query_cache import (
    DataQueryCache,
    make_cache_key,
)
from luana_core_platform.core.context import get_tenant_id

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from luana_core_copilot.domain.ports import DataAccessProvider
    from sqlalchemy.orm import Session

logger = structlog.get_logger()


def _err_payload(message: str, **extra: Any) -> str:  # noqa: ANN401 — passthrough payload
    return json.dumps(
        {
            "status": "error",
            "message": message,
            "llm_content": message,
            **extra,
        },
        ensure_ascii=False,
    )


def _success_payload(*, answer: str, kind: str, metadata: dict[str, Any]) -> str:
    return json.dumps(
        {
            "status": "ok",
            "kind": kind,
            "answer": answer,
            "metadata": metadata,
            "llm_content": answer,
        },
        ensure_ascii=False,
        default=str,
    )


def _open_session() -> Session:
    from luana_core_platform.core.database import SessionLocal

    return SessionLocal()


def _default_accessors(db_factory: Callable[[], Session]) -> tuple:
    """Resolve the accessor list at request time.

    Order matters: copilot-own accessors come first so a future cross-module
    accessor cannot accidentally shadow the canonical conversation count.
    """
    accessors: list = [ConversationDataAccessProvider(db_factory=db_factory)]

    try:
        from luana_core_copilot.application.discovery import discover_providers

        for provider in discover_providers().values():
            da = provider.data_access()
            if da is not None:
                accessors.append(da)
    except Exception:
        logger.exception("ask_tenant_data_provider_discovery_failed")

    return tuple(accessors)


def _default_cache() -> DataQueryCache:
    try:
        from luana_core_platform.core.database import redis_client
    except Exception:  # noqa: BLE001 — Redis is optional; cache fails open
        return DataQueryCache(redis=None)
    return DataQueryCache(redis=redis_client)


async def _ask_tenant_data_impl(
    *,
    question: str,
    output_channel: str = "chat",
    db: Session | None = None,
    llm_intent: object | None = None,
    llm_synth: object | None = None,
    accessors: Sequence[DataAccessProvider] | None = None,
    cache: DataQueryCache | None = None,
) -> str:
    """Core implementation — split out so unit tests inject collaborators."""
    tenant_id = get_tenant_id()
    if tenant_id is None:
        return _err_payload("No hay contexto de tenant. Vuelve a iniciar sesión.")

    if not question or not question.strip():
        return _err_payload("La pregunta está vacía.")

    cache_layer = cache if cache is not None else _default_cache()
    cache_key = make_cache_key(tenant_id, question, output_channel)
    cached = cache_layer.get(cache_key)
    if cached is not None:
        logger.info("ask_tenant_data_cache_hit", key=cache_key)
        return cached

    intent = await classify_intent(question, llm=llm_intent)
    plan = build_plan(intent)

    if plan is None:
        answer = await synthesize_answer(
            question=question,
            plan=type("UnknownPlan", (), {"kind": "unknown", "filters": {}})(),  # type: ignore[arg-type]
            result=type("EmptyResult", (), {"rows": [], "metadata": {}})(),  # type: ignore[arg-type]
            flags={},
            output_channel=output_channel,
            llm=llm_synth,
        )
        return _success_payload(
            answer=answer,
            kind="unknown",
            metadata={"intent_confidence": intent.confidence},
        )

    owns_db = db is None
    if owns_db:
        db = _open_session()
    try:
        if accessors is None:
            accessors = _default_accessors(lambda: db)

        try:
            result = await execute_plan(
                plan=plan,
                tenant_id=tenant_id,
                accessors=accessors,
                db=db,
            )
        except NoAccessorError as exc:
            logger.warning("ask_tenant_data_no_accessor", kind=plan.kind)
            return _err_payload(str(exc), kind=plan.kind)

        flags = annotate_state(plan=plan, result=result)
        answer = await synthesize_answer(
            question=question,
            plan=plan,
            result=result,
            flags=flags,
            output_channel=output_channel,
            llm=llm_synth,
        )
    finally:
        if owns_db and db is not None:
            db.close()

    metadata: dict[str, Any] = {
        "intent_kind": plan.kind,
        "intent_confidence": intent.confidence,
        "result_count": result.metadata.get("count", 0),
        "flags": flags,
    }
    payload = _success_payload(answer=answer, kind=plan.kind, metadata=metadata)
    cache_layer.set(cache_key, payload)
    return payload


@tool
async def ask_tenant_data(question: str, output_channel: str = "chat") -> str:
    """Responde preguntas sobre los datos del tenant en lenguaje natural.

    Cuándo usarla:
    - El usuario pregunta "cuántas personas escribieron esta semana", "dame
      resumen del programa <X>", "cuántas conversaciones tuve el mes pasado".
    - Cualquier pregunta cuya respuesta sea un dato del propio tenant
      (ofertas, leads inbound, conversaciones del copilot).

    NO la uses cuando:
    - El usuario quiere modificar datos (usá las tools de mutación).
    - El usuario pega una URL externa (usá ``fetch_url``).
    - La pregunta es sobre el método o doctrina (usá ``knowledge_search``).

    Args:
        question: Pregunta en español neutro tal como la escribió el usuario.
            El motor extrae intención, entidad y período.
        output_channel: ``"chat"`` (default), ``"whatsapp"`` o ``"email"``.
            El sintetizador adapta longitud y estilo al canal.

    Returns:
        JSON con ``status="ok"``, ``answer`` (string en español neutro listo
        para mostrar), ``kind`` (categoría intent) y ``metadata``. En error,
        ``status="error"`` con ``message`` user-friendly.
    """
    return await _ask_tenant_data_impl(
        question=question,
        output_channel=output_channel,
    )


__all__ = ("_ask_tenant_data_impl", "ask_tenant_data")
