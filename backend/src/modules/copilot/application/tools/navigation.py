"""Navigation tools — allow the copilot to direct the user to specific pages/sections.

These tools emit ui_action events that the frontend interprets to perform
router.push(), scrollIntoView(), highlight, etc.
"""

from langchain_core.tools import tool
from luana_core_copilot.domain.navigation_map import (
    find_pages_by_keyword,
    get_all_pages,
)


@tool
def navigate_to_page(page_keyword: str, section_id: str | None = None) -> dict:
    """Navigate the user to a specific page in the app.

    Args:
        page_keyword: A keyword to identify the page
            (e.g. "brand", "offer", "growth", "sales", "connections", "settings").
        section_id: Optional section within the page to scroll to (e.g. "positioning", "identity", "narrative").

    Returns:
        A ui_action payload that the frontend will execute.

    """
    matches = find_pages_by_keyword(page_keyword)
    if not matches:
        return {
            "success": False,
            "message": f"No encontré una página que coincida con '{page_keyword}'. "
            f"Las páginas disponibles son: {', '.join(p.label for p in get_all_pages())}",
        }

    target = matches[0]
    action = {
        "success": True,
        "ui_action": {
            "type": "navigate",
            "route": target.route_template,
            "page_label": target.label,
            "section_id": section_id,
        },
        "message": f"Navegando a {target.label}" + (f" > {section_id}" if section_id else ""),
    }

    # Validate section if provided
    if section_id:
        valid_sections = [s.section_id for s in target.sections]
        if section_id not in valid_sections:
            action["ui_action"]["section_id"] = None
            action["message"] += (
                f" (sección '{section_id}' no encontrada, secciones válidas: {', '.join(valid_sections)})"
            )

    return action


@tool
def scroll_to_field(field_id: str) -> dict:
    """Scroll the page to highlight a specific field.

    Args:
        field_id: The ID of the field to scroll to and highlight (e.g. "uvp", "brand_name", "tagline").

    Returns:
        A ui_action payload that the frontend will execute.

    """
    return {
        "success": True,
        "ui_action": {
            "type": "scroll_to_field",
            "field_id": field_id,
        },
        "message": f"Mostrando el campo '{field_id}'",
    }


@tool
def open_form(form_id: str, prefill_data: dict | None = None) -> dict:
    """Open a specific form or dialog in the UI.

    Args:
        form_id: The identifier of the form to open (e.g. "new-offer", "new-avatar", "edit-connection").
        prefill_data: Optional data to pre-fill in the form.

    Returns:
        A ui_action payload that the frontend will execute.

    """
    return {
        "success": True,
        "ui_action": {
            "type": "open_form",
            "form_id": form_id,
            "prefill_data": prefill_data or {},
        },
        "message": f"Abriendo formulario '{form_id}'",
    }


@tool
def list_app_pages() -> str:
    """List all available pages and sections in the app.

    Returns:
        A formatted list of all navigable pages with their sections.

    """
    lines = []
    for page in get_all_pages():
        sections_str = ", ".join(s.label for s in page.sections) if page.sections else "(sin secciones)"
        lines.append(f"• {page.label} [{page.module}] — {sections_str}")
    return "\n".join(lines)


VALID_STAGES = {
    "atraccion-captura",
    "nutricion-oportunidad",
    "ventas",
    "adopcion",
    "expansion-evangelizacion",
}


@tool
def navigate_to_channel(
    stage: str,
    channel_slug: str,
    tab: str | None = None,
    expanded: bool = False,
) -> dict:
    """Navigate to a specific channel in Growth Studio.

    Args:
        stage: Funnel stage slug (atraccion-captura, nutricion-oportunidad,
               ventas, adopcion, expansion-evangelizacion).
        channel_slug: Channel identifier (meta-ads, ig-organic, yt-organic,
                      email-nurture, google-analytics, google-ads, shopify, etc.).
        tab: Optional tab within the channel sidebar/dashboard.
        expanded: If true, opens full-page dashboard instead of sidebar.

    Returns:
        A ui_action payload that the frontend will execute.

    """
    if stage not in VALID_STAGES:
        return {
            "success": False,
            "message": (f"Stage '{stage}' no es válido. Opciones: {', '.join(sorted(VALID_STAGES))}"),
        }

    # Build the route template — {tenantId} placeholder is resolved by the frontend
    if expanded:
        route = f"/{{tenantId}}/growth-studio/{stage}/{channel_slug}"
        if tab:
            route += f"?tab={tab}"
    else:
        route = f"/{{tenantId}}/growth-studio/{stage}?channel={channel_slug}"
        if tab:
            route += f"&tab={tab}"

    label = f"{channel_slug} en {stage}"
    if tab:
        label += f" > {tab}"

    return {
        "success": True,
        "ui_action": {
            "type": "navigate",
            "route": route,
            "page_label": label,
        },
        "message": f"Navegando a {label}",
    }


# Collect all navigation tools for easy import
NAVIGATION_TOOLS = [
    navigate_to_page,
    scroll_to_field,
    open_form,
    list_app_pages,
    navigate_to_channel,
]
