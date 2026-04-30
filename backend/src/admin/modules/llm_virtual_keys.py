"""Admin module — LiteLLM Proxy virtual keys read-only view.

Displays virtual keys registered in LiteLLM Proxy via GET /key/info
(master key). Read-only in S3 — CRUD UI completo en S4 PR-1.

PI-2 S3 PR-2. Ref: CONTRACT.md §D-3 + §D-16.

Surfaces:
- List virtual keys + spend por key
- Master key info + total spend summary
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st

from src.core.config import settings


def _fetch_virtual_keys() -> list[dict[str, Any]]:
    """Fetch virtual keys from LiteLLM Proxy /key/list endpoint.

    Returns list of key info dicts. Returns empty list on any error
    (best-effort — proxy may not be running in dev).
    """
    try:
        import httpx

        proxy_root = settings.LITELLM_BASE_URL.rstrip("/")
        proxy_root = proxy_root.removesuffix("/v1")

        resp = httpx.get(
            f"{proxy_root}/key/list",
            headers={"Authorization": f"Bearer {settings.LITELLM_MASTER_KEY}"},
            timeout=5.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("keys", []) if isinstance(data, dict) else []
    except Exception as e:  # noqa: BLE001 — best-effort display
        st.warning(f"No se pudo conectar con LiteLLM Proxy: {e}")
        return []


def _fmt_date(value: str | None) -> str:
    """Format ISO datetime string for display."""
    if not value:
        return "—"
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, AttributeError):
        return str(value)


def _fmt_budget(value: float | None) -> str:
    """Format budget float as currency string."""
    if value is None:
        return "Sin límite"
    return f"USD {value:.4f}"


def render_llm_virtual_keys() -> None:
    """Render the LiteLLM Proxy virtual keys read-only page."""
    st.title("LLM Virtual Keys")
    st.caption("Vista de claves virtuales registradas en LiteLLM Proxy. Solo lectura en S3 — CRUD disponible en S4.")

    st.info(
        "Proxy: `"
        + settings.LITELLM_BASE_URL
        + "` · Toggle: "
        + ("**activo**" if settings.LITELLM_PROXY_ENABLED else "**desactivado (fallback legacy)**"),
    )

    if not settings.LITELLM_PROXY_ENABLED:
        st.warning(
            "LITELLM_PROXY_ENABLED=false — el proxy está en modo rollback. "
            "Los datos mostrados pueden estar desactualizados."
        )

    col_refresh, _ = st.columns([1, 5])
    with col_refresh:
        st.button("Actualizar")  # Triggers Streamlit rerun

    keys = _fetch_virtual_keys()

    if not keys:
        st.info("No hay claves virtuales registradas o el proxy no está disponible.")
        return

    st.metric("Total de claves virtuales", len(keys))
    st.divider()

    rows = [
        {
            "Alias": k.get("key_alias") or "—",
            "Token (preview)": str(k.get("token", ""))[:12] + "...",
            "Modelos": ", ".join(k.get("models", [])) or "todos",
            "Gasto (USD)": f"{k.get('spend', 0):.4f}",
            "Presupuesto máx.": _fmt_budget(k.get("max_budget")),
            "RPM límite": str(k.get("rpm_limit") or "—"),
            "TPM límite": str(k.get("tpm_limit") or "—"),
            "Vence": _fmt_date(k.get("expires")),
            "Team ID": k.get("team_id") or "—",
            "User ID": k.get("user_id") or "—",
        }
        for k in keys
    ]

    st.dataframe(rows, use_container_width=True)

    st.caption(
        "Nota: para crear, modificar o revocar claves, usa la API admin de LiteLLM "
        "directamente (S4 expondrá CRUD en esta página)."
    )
