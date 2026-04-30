"""Admin module — Copilot per-tenant limits CRUD.

Allows Nicolify admin (Chris) to view and override per-tenant voice/media limits.
PI-2 S1 PR-1: voice/media hardening.

Surfaces:
- List active overrides (all tenants)
- Upsert override for a specific tenant (voice RPM, media max bytes)
- Clear (soft-delete) override — tenant reverts to env defaults
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import streamlit as st

from src.admin.modules._shared import render_tenant_selector

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
from src.core.config import settings
from src.core.database import SessionLocal
from src.modules.copilot.infrastructure.repositories.tenant_limits_repository import (
    SyncCopilotTenantLimitsRepository,
)

_ONE_MIB = 1 * 1024 * 1024
_HUNDRED_MIB = 100 * 1024 * 1024


def _get_repo() -> tuple[Session, SyncCopilotTenantLimitsRepository]:
    """Return (session, repo). Caller must close session."""
    db = SessionLocal()
    return db, SyncCopilotTenantLimitsRepository(db)


def _mb(n_bytes: int | None) -> str:
    """Format bytes as MB string for display."""
    if n_bytes is None:
        return "—"
    return f"{n_bytes / _ONE_MIB:.1f} MB"


def render_copilot_limits_view() -> None:
    """Render the copilot per-tenant limits management page."""
    st.title("Límites de Copilot por Tenant")
    st.caption(
        "Configura overrides de rate limit (voice) y tamaño máximo de archivo (media/voice) "
        "por tenant. Sin override = se usa el valor de entorno."
    )

    st.info(
        f"Env defaults — Voice RPM: **{settings.COPILOT_VOICE_RATE_LIMIT_PER_MIN}** rpm/tenant | "
        f"Media max: **{_mb(settings.COPILOT_MEDIA_MAX_BYTES)}** | "
        f"Media upload RPM: **{settings.COPILOT_MEDIA_UPLOAD_RATE_LIMIT_PER_MIN}** rpm/tenant"
    )

    # ── Active overrides listing ──────────────────────────────────────────────
    st.subheader("Overrides activos")
    try:
        db, repo = _get_repo()
        try:
            overrides = repo.list_overrides(limit=100)
        finally:
            db.close()

        if overrides:
            import pandas as pd

            rows = [
                {
                    "Tenant ID": str(o.tenant_id),
                    "Voice RPM override": o.voice_rpm_override or "—",
                    "Media max bytes override": _mb(o.media_max_bytes_override),
                    "Actualizado": o.updated_at.strftime("%Y-%m-%d %H:%M UTC") if o.updated_at else "—",
                }
                for o in overrides
            ]

            st.dataframe(pd.DataFrame(rows), use_container_width=True)
        else:
            st.info("Sin overrides activos. Todos los tenants usan env defaults.")
    except Exception as exc:  # noqa: BLE001 — Streamlit admin: surface all DB errors to operator
        st.error(f"Error al cargar overrides: {exc}")

    st.divider()

    # ── Upsert / clear override ───────────────────────────────────────────────
    st.subheader("Configurar override por tenant")

    tenant_id_input = render_tenant_selector(key="copilot_limits_tenant_selector", allow_all=False)

    if not tenant_id_input:
        st.info("Selecciona un tenant para configurar sus límites.")
        return

    # Show current override for selected tenant
    try:
        db, repo = _get_repo()
        try:
            current = repo.get_by_tenant(tenant_id_input)
        finally:
            db.close()
    except Exception as exc:  # noqa: BLE001 — Streamlit admin: surface all DB errors to operator
        st.error(f"Error al leer override actual: {exc}")
        return

    if current:
        st.success(
            f"Override actual — Voice RPM: {current.voice_rpm_override or 'env default'} | "
            f"Media max: {_mb(current.media_max_bytes_override) if current.media_max_bytes_override else 'env default'}"
        )
    else:
        st.info("Sin override — usa env defaults.")

    with st.form(f"copilot_limits_form_{tenant_id_input}"):
        st.markdown("**Voice rate limit override**")
        voice_rpm_enabled = st.checkbox(
            "Activar override de Voice RPM",
            value=bool(current and current.voice_rpm_override),
        )
        _voice_rpm_default = (
            current.voice_rpm_override
            if (current and current.voice_rpm_override)
            else settings.COPILOT_VOICE_RATE_LIMIT_PER_MIN
        )
        voice_rpm_value = st.number_input(
            "Voice RPM (override)",
            min_value=1,
            max_value=1000,
            value=_voice_rpm_default,
            help="Requests por minuto para /voice/upload-and-transcribe. Rango: 1–1000.",
        )

        st.markdown("**Media max bytes override**")
        media_enabled = st.checkbox(
            "Activar override de Media Max Bytes",
            value=bool(current and current.media_max_bytes_override),
        )
        if current and current.media_max_bytes_override:
            _media_default_bytes = current.media_max_bytes_override
        else:
            _media_default_bytes = settings.COPILOT_MEDIA_MAX_BYTES
        media_mb_value = st.number_input(
            "Media max (MB)",
            min_value=1,
            max_value=100,
            value=int(_media_default_bytes / _ONE_MIB),
            help="Tamaño máximo en MB para uploads. Rango: 1–100 MB.",
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Guardar")
        with col2:
            clear_submitted = st.form_submit_button("Limpiar override")

    if submitted:
        voice_rpm_override = int(voice_rpm_value) if voice_rpm_enabled else None
        media_max_bytes_override = int(media_mb_value * _ONE_MIB) if media_enabled else None

        try:
            db, repo = _get_repo()
            try:
                repo.upsert(
                    tenant_id=tenant_id_input,
                    voice_rpm_override=voice_rpm_override,
                    media_max_bytes_override=media_max_bytes_override,
                    updated_by_user_id=None,  # admin Streamlit — no user auth context
                )
                db.commit()
            finally:
                db.close()
            st.success("Override guardado correctamente.")
            st.rerun()
        except Exception as exc:  # noqa: BLE001 — Streamlit admin: surface all DB errors to operator
            st.error(f"Error al guardar override: {exc}")

    if clear_submitted:
        try:
            db, repo = _get_repo()
            try:
                repo.soft_delete(tenant_id=tenant_id_input, deleted_by_user_id=None)
                db.commit()
            finally:
                db.close()
            st.success("Override limpiado. El tenant usará env defaults.")
            st.rerun()
        except Exception as exc:  # noqa: BLE001 — Streamlit admin: surface all DB errors to operator
            st.error(f"Error al limpiar override: {exc}")
