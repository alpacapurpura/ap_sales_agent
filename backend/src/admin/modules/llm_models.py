"""Admin module — LLM Model Registry runtime hot-swap.

PI-2 S4 PR-1. CRUD admin Streamlit para `llm_role_binding` table.
Hot-swap modelo runtime <60s sin deploy via pub/sub Redis invalidation.

Sigue rule `admin-panel.md`:
- 1 PageSpec (slug="llm-models") + 1 wrapper (`pages/llm-models.py`)
- Lógica solo aquí (`render_llm_models()`).
- NO cross-module imports (excepto `_shared.py` si necesario).
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import streamlit as st

from src.core.enums import AIProvider, ModelRole

if TYPE_CHECKING:
    from collections.abc import Coroutine


def _run_async(coro: Coroutine[Any, Any, Any]) -> Any:  # noqa: ANN401 — Streamlit boundary
    """Run async coroutine from Streamlit sync context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def _list_bindings() -> list[Any]:
    """Fetch all bindings via repo. Returns [] on error (graceful)."""
    try:
        from src.core.database import async_session_maker
        from src.shared.infrastructure.llm.infrastructure.role_binding_repository import (
            SqlAlchemyLLMRoleBindingRepository,
        )

        async def _fetch() -> list[Any]:
            async with async_session_maker() as session:
                repo = SqlAlchemyLLMRoleBindingRepository(session)
                return await repo.list_all()

        return _run_async(_fetch())
    except Exception as exc:  # noqa: BLE001 — graceful degradation
        st.error(f"Error consultando llm_role_binding: {exc}")
        return []


def _list_audit(limit: int = 25) -> list[dict[str, Any]]:
    try:
        from src.core.database import async_session_maker
        from src.shared.infrastructure.llm.infrastructure.role_binding_repository import (
            SqlAlchemyLLMRoleBindingRepository,
        )

        async def _fetch() -> list[dict[str, Any]]:
            async with async_session_maker() as session:
                repo = SqlAlchemyLLMRoleBindingRepository(session)
                return await repo.list_audit(limit=limit)

        return _run_async(_fetch())
    except Exception:  # noqa: BLE001
        return []


def _create_binding(
    role: ModelRole,
    provider: AIProvider,
    model: str,
    actor: str,
    notes: str | None,
) -> bool:
    try:
        from src.core.database import async_session_maker
        from src.shared.infrastructure.llm.application.config_service import (
            get_llm_config_service,
        )
        from src.shared.infrastructure.llm.infrastructure.role_binding_repository import (
            SqlAlchemyLLMRoleBindingRepository,
        )

        async def _do() -> None:
            async with async_session_maker() as session:
                repo = SqlAlchemyLLMRoleBindingRepository(session)
                await repo.create(
                    role=role,
                    provider=provider,
                    model=model,
                    notes=notes,
                    actor=actor,
                )
            svc = get_llm_config_service()
            if svc is not None:
                await svc.publish_invalidation()

        _run_async(_do())
    except Exception as exc:  # noqa: BLE001
        st.error(f"Error creando binding: {exc}")
        return False
    return True


def _activate_binding(binding_id: str, actor: str, reason: str | None) -> bool:
    try:
        from uuid import UUID

        from src.core.database import async_session_maker
        from src.shared.infrastructure.llm.application.config_service import (
            get_llm_config_service,
        )
        from src.shared.infrastructure.llm.infrastructure.role_binding_repository import (
            SqlAlchemyLLMRoleBindingRepository,
        )

        async def _do() -> None:
            async with async_session_maker() as session:
                repo = SqlAlchemyLLMRoleBindingRepository(session)
                await repo.activate(UUID(binding_id), actor=actor, reason=reason)
            svc = get_llm_config_service()
            if svc is not None:
                svc.invalidate_cache()
                await svc.publish_invalidation()

        _run_async(_do())
    except Exception as exc:  # noqa: BLE001
        st.error(f"Error activando binding: {exc}")
        return False
    return True


def render_llm_models() -> None:
    """Render LLM model registry runtime hot-swap admin page."""
    st.title("LLM Model Registry")
    st.caption(
        "SSoT runtime model selection per role. Cambios se propagan a backend "
        "pods en <60s via pub/sub Redis invalidation. Audit trail inmutable."
    )

    actor = st.text_input("Actor (admin user)", value="admin@nicolify")

    bindings = _list_bindings()

    st.subheader("Bindings activos por role")
    if bindings:
        rows = [
            {
                "Role": b.role.value,
                "Provider": b.provider.value,
                "Model": b.model,
                "Activo": "✅" if b.is_active else "—",
                "Tenant": "global" if b.tenant_id is None else str(b.tenant_id)[:8],
                "Created": b.created_at.strftime("%Y-%m-%d %H:%M"),
                "Activated": b.activated_at.strftime("%Y-%m-%d %H:%M") if b.activated_at else "—",
                "ID": str(b.id)[:8],
            }
            for b in bindings
        ]
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No hay bindings registrados (correr migration 118 seed).")

    st.divider()

    with st.expander("Crear nuevo binding (INACTIVE)"):
        col1, col2, col3 = st.columns(3)
        with col1:
            new_role = st.selectbox("Role", [r.value for r in ModelRole], key="new_role")
        with col2:
            new_provider = st.selectbox("Provider", [p.value for p in AIProvider], key="new_provider")
        with col3:
            new_model = st.text_input("Model wire-name", placeholder="deepseek-v4-flash", key="new_model")
        new_notes = st.text_area("Notes (opcional)", key="new_notes")

        if st.button("Crear binding"):
            if not new_model.strip():
                st.error("Model wire-name es obligatorio")
            elif _create_binding(
                ModelRole(new_role),
                AIProvider(new_provider),
                new_model.strip(),
                actor=actor,
                notes=new_notes or None,
            ):
                st.success(f"Binding creado: {new_role}/{new_provider}/{new_model} (INACTIVE)")
                st.rerun()

    with st.expander("Activar binding (ACTIVATE = atomic deactivate prior + activate target)"):
        binding_id = st.text_input("Binding ID (full UUID)", key="activate_id")
        reason = st.text_input("Reason (opcional)", key="activate_reason")
        if st.button("Activate"):
            if not binding_id.strip():
                st.error("Binding ID requerido")
            elif _activate_binding(binding_id.strip(), actor=actor, reason=reason or None):
                st.success("Binding activado + cache invalidation publicada")
                st.rerun()

    st.divider()
    st.subheader("Audit trail (últimas 25 acciones)")
    audit = _list_audit(limit=25)
    if audit:
        st.dataframe(audit, use_container_width=True)
    else:
        st.info("Sin entries en audit log.")
