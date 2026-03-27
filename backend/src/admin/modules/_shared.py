"""Shared utilities for admin modules — tenant selector, tooltips, cross-tenant queries."""

import streamlit as st
from typing import List, Optional
from uuid import UUID

from src.core.database import SessionLocal
from src.modules.iam.application.services.tenant_service import TenantService


# ── Tooltips centralizados ─────────────────────────────────────────────
TOOLTIPS = {
    "active_tenant": "Tenant con al menos 1 evento de copilot en los ultimos 7 dias",
    "total_events": "Cantidad total de interacciones registradas con el copilot",
    "friction_score": "Frecuencia con que los usuarios abren el copilot en esa ruta — indica dificultad",
    "adoption_rate": "Porcentaje de tenants que han configurado este modulo",
    "proposal_acceptance": "Propuestas del copilot aceptadas vs rechazadas. Mayor = copilot mas util",
    "procedure_completion": "Porcentaje de procedimientos guiados que se completaron exitosamente",
    "msgs_per_user": "Promedio de mensajes enviados por usuario activo en el periodo",
    "suggested_vs_typed": "Mensajes iniciados por sugerencia vs escritos manualmente por el usuario",
    "nudge_ctr": "Porcentaje de nudges (sugerencias proactivas) que el usuario acepta vs descarta",
    "module_completion": "Porcentaje de campos completados en este modulo (auto-detectado via schema)",
    "knowledge_docs": "Documentos indexados en la base de conocimiento del copilot (Qdrant)",
    "conversation_tools": "Herramientas que el copilot invoco durante la conversacion",
}


# ── Tenant helpers ─────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def _get_all_tenants_cached() -> List[dict]:
    """Fetch all tenants, cached 5 min. Returns list of dicts."""
    db = SessionLocal()
    try:
        service = TenantService(db)
        tenants = service.get_all_tenants()
        return [
            {"id": str(t.id), "name": t.name, "slug": t.slug, "is_active": t.is_active}
            for t in tenants
        ]
    finally:
        db.close()


def get_tenant_options() -> List[dict]:
    """Get tenants list (cached). Each dict has id, name, slug, is_active."""
    return _get_all_tenants_cached()


def render_tenant_selector(key: str, allow_all: bool = True) -> Optional[UUID]:
    """Selectbox with tenant names, returns UUID or None for 'Todos'."""
    tenants = get_tenant_options()

    options = []
    if allow_all:
        options.append("Todos (cross-tenant)")
    options.extend([f"{t['name']} ({t['id'][:8]}...)" for t in tenants])

    selected = st.selectbox("Tenant", options, key=key)

    if selected == "Todos (cross-tenant)":
        return None

    # Extract index from options list
    idx = options.index(selected)
    if allow_all:
        idx -= 1
    return UUID(tenants[idx]["id"])


def get_tenant_name(tenant_id) -> str:
    """Lookup tenant name by UUID. Returns str(uuid)[:8] as fallback."""
    tenant_id_str = str(tenant_id)
    for t in get_tenant_options():
        if t["id"] == tenant_id_str:
            return t["name"]
    return tenant_id_str[:8]


# ── Color/Flag helpers ────────────────────────────────────────────────

def completion_flag(ratio: float) -> str:
    """🟢 >70%, 🟡 30-70%, 🔴 <30%"""
    if ratio > 0.7:
        return "🟢"
    elif ratio >= 0.3:
        return "🟡"
    return "🔴"


def health_flag(days_inactive: int) -> str:
    """🟢 <7d, 🟡 7-14d, 🔴 >14d"""
    if days_inactive < 7:
        return "🟢"
    elif days_inactive <= 14:
        return "🟡"
    return "🔴"


def pct_flag(pct: float) -> str:
    """🟢 <10%, 🟡 10-20%, 🔴 >20%"""
    if pct > 20:
        return "🔴"
    elif pct > 10:
        return "🟡"
    return "🟢"


# ── Cross-tenant SQL queries ──────────────────────────────────────────

def get_all_tenants_summary() -> List[dict]:
    """Tenants with user count and last event date. One SQL query."""
    from sqlalchemy import text
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT
                t.id,
                t.name,
                t.is_active,
                COUNT(DISTINCT ut.user_id) AS user_count,
                MAX(ce.created_at) AS last_event
            FROM tenants t
            LEFT JOIN user_tenants ut ON ut.tenant_id = t.id AND ut.is_active = true
            LEFT JOIN copilot_events ce ON ce.tenant_id = t.id AND ce.deleted_at IS NULL
            WHERE t.is_active = true
            GROUP BY t.id, t.name, t.is_active
            ORDER BY last_event DESC NULLS LAST
        """))
        return [dict(row._mapping) for row in result]
    finally:
        db.close()


def get_adoption_funnel() -> dict:
    """Batch SQL: count tenants with brand, offer, connection, copilot usage."""
    from sqlalchemy import text
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM tenants WHERE is_active = true) AS total_tenants,
                (SELECT COUNT(DISTINCT tenant_id) FROM avatars) AS has_brand,
                (SELECT COUNT(DISTINCT tenant_id) FROM products) AS has_offer,
                (SELECT COUNT(DISTINCT tenant_id) FROM channel_connections WHERE is_active = true) AS has_connection,
                (SELECT COUNT(DISTINCT tenant_id) FROM copilot_events WHERE event_type = 'message_sent' AND deleted_at IS NULL) AS has_copilot,
                (SELECT COUNT(DISTINCT tenant_id) FROM copilot_events WHERE event_type = 'procedure_completed' AND deleted_at IS NULL) AS has_procedure_completed
        """))
        row = result.fetchone()
        return dict(row._mapping) if row else {}
    finally:
        db.close()
