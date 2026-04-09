"""Shared constants for stage services.

Single source of truth for group mappings, display names, error messages,
and stage group definitions used across multiple stage services.
"""

# ─── Channel type → group mappings (per stage) ──────────────────────────────

ATTRACTION_GROUP_MAP: dict[str, str] = {
    "social": "organic_social",
    "search": "ga4_search",
    "direct": "ga4_search",
    "paid": "paid",
    "outbound": "outbound",
    "website": "organic_social",
}

CAPTURE_GROUP_MAP: dict[str, str] = {
    "form": "web_infrastructure",
    "email": "web_infrastructure",
    "messaging": "ai_agent",
}

NURTURE_GROUP_MAP: dict[str, str] = {
    "retargeting": "retargeting",
    "email": "automation",
    "automation": "automation",
}

OPPORTUNITY_GROUP_MAP: dict[str, str] = {
    "checkout": "checkout",
    "payment_link": "payment_links",
    "qualification": "qualification",
}

# ─── Extraction error → user-facing message ─────────────────────────────────

ERROR_MESSAGES: dict[str, str] = {
    "token_expired": "Token expirado",
    "token_refresh_failed": "Token expirado",
    "connection_revoked": "Token expirado",
    "rate_limited": "Reintentando...",
    "rate_limit": "Reintentando...",
    "provider_error": "Servicio no disponible",
    "timeout": "Servicio no disponible",
    "http_5xx": "Servicio no disponible",
}

# ─── Provider → connection config key for display name ───────────────────────

DISPLAY_NAME_MAP: dict[str, str] = {
    "google_analytics": "property_display_name",
    "youtube": "channel_title",
    "meta": "tracked_ig_username",
    "google_ads": "property_display_name",
}

# ─── Stage → group definitions (group_key, label, dto_field_name) ────────────

STAGE_GROUPS: dict[str, list[tuple[str, str, str]]] = {
    "attraction": [
        ("organic_social", "Social Orgánico", "organic_social"),
        ("ga4_search", "Búsqueda Orgánica", "ga4_search"),
        ("paid", "Pagado", "paid"),
        ("outbound", "Outbound", "outbound"),
    ],
    "capture": [
        ("web_infrastructure", "Web / Infraestructura", "web_infrastructure"),
        ("ai_agent", "AI Agent / Mensajería", "ai_agent"),
    ],
    "nurture": [
        ("retargeting", "Retargeting", "retargeting"),
        ("automation", "Automatización", "automation"),
    ],
    "opportunity": [
        ("checkout", "Checkout", "checkout"),
        ("payment_links", "Links de Pago", "payment_links"),
        ("qualification", "Calificación", "qualification"),
    ],
    "sales": [
        ("adquisicion", "Adquisición", "adquisicion"),
        ("expansion", "Expansión", "expansion"),
    ],
    "adoption": [],  # No channel groups — uses offers list
    "expansion": [
        ("retencion", "Retención", "retencion"),
        ("crecimiento", "Crecimiento", "crecimiento"),
        ("cancelaciones", "Cancelaciones", "cancelaciones"),
    ],
    "evangelization": [],  # No channel groups — uses referidos, candidatos
}
