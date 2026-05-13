"""Admin module: Brand Summary lighthouse inspector + manual regen.

Lists the per-tenant ``brand_summary`` rows (version, model, chars, last
section that drove the regen) and exposes a one-click "regenerate now"
button that calls ``regen_brand_summary_sync`` directly — useful when
the LLM was rate-limited or a tenant's lighthouse was stuck.

[COPILOT-BRAND-SUMMARY-F3] -> docs/domains/copilot/redesign-2026-04/phases/F3-brand-summary-lighthouse.md
"""

from __future__ import annotations

import streamlit as st
from luana_core_brand_studio.infrastructure.repositories.brand_summary_repository import (
    BrandSummaryRepository,
)
from luana_core_platform.core.database import SessionLocal
from luana_core_platform.workers.brand_summary_regen import regen_brand_summary_sync


def _render_table() -> None:
    db = SessionLocal()
    try:
        rows = BrandSummaryRepository(db).list_all()
    finally:
        db.close()

    if not rows:
        st.info("Sin brand_summary persistidos todavía.")
        return

    st.dataframe(
        [
            {
                "Tenant": str(r.tenant_id),
                "Versión": r.version,
                "Modelo": r.model_used,
                "Chars": r.chars_count,
                "Última sección": r.last_section_changed or "—",
                "Actualizado": r.updated_at.isoformat() if r.updated_at else "—",
            }
            for r in rows
        ],
        use_container_width=True,
        hide_index=True,
    )

    for r in rows:
        with st.expander(f"{r.tenant_id} · v{r.version} · {r.chars_count} chars"):
            st.code(r.summary, language=None)


def _render_manual_regen() -> None:
    st.subheader("Regenerar manualmente")
    st.caption(
        "Útil cuando el LLM falló o el tenant publicó cambios de marca y quieres "
        "el faro fresco antes del debounce de 30 segundos.",
    )
    tenant_str = st.text_input("Tenant ID (UUID)", key="brand_summary_regen_tenant")
    section = st.text_input(
        "Sección que motivó el cambio (opcional)",
        key="brand_summary_regen_section",
    )
    if st.button("Regenerar ahora", type="primary"):
        if not tenant_str:
            st.error("Falta el tenant_id.")
            return
        from uuid import UUID

        try:
            tenant_id = UUID(tenant_str)
        except ValueError:
            st.error("Tenant ID inválido.")
            return

        db = SessionLocal()
        try:
            with st.spinner("Regenerando lighthouse…"):
                summary = regen_brand_summary_sync(
                    db=db,
                    tenant_id=tenant_id,
                    last_section_changed=section or None,
                )
                db.commit()
        except Exception as exc:  # noqa: BLE001 — admin tool; surface error to user
            db.rollback()
            st.error(f"Falló: {exc}")
            return
        finally:
            db.close()

        if summary is None:
            st.warning(
                "No se persistió. La marca está vacía o el judge rechazó el output. "
                "Revisá structlog del worker para detalle.",
            )
        else:
            st.success(f"Persistido — {len(summary)} chars.")
            st.code(summary, language=None)


def render_brand_summaries() -> None:
    """Streamlit page entrypoint."""
    st.title("Brand Summary Lighthouse")
    st.caption(
        "Resúmenes vivos de marca (≤800 chars, español neutro) que el Copilot "
        "inyecta en su system prompt para offer / landing / campaign / sales. "
        "Se regeneran automáticamente cuando cambia la marca.",
    )

    tab_list, tab_regen = st.tabs(["Listado", "Regenerar"])
    with tab_list:
        _render_table()
    with tab_regen:
        _render_manual_regen()
