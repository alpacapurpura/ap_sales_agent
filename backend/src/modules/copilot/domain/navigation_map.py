"""
Declarative navigation map of the Nicolify app.

Used by copilot tools to:
- Navigate users to specific pages/sections
- Understand what modules/sections exist
- Map user intents to routes
"""

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class AppField:
    """A specific field within a section."""
    field_id: str
    label: str
    description: str


@dataclass(frozen=True)
class AppSection:
    """A section within a page (e.g. a tab, accordion, or form group)."""
    section_id: str
    label: str
    description: str
    fields: List[AppField] = field(default_factory=list)


@dataclass(frozen=True)
class AppPage:
    """A navigable page in the app."""
    route_template: str  # e.g. "/{tenantId}/brand-settings"
    label: str
    module: str  # brand, offer, growth, sales, connections, settings
    description: str
    sections: List[AppSection] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


# ── Navigation Map ───────────────────────────────────────────────────

NAVIGATION_MAP: List[AppPage] = [
    # ── Brand Studio ─────────────────────────────────────────────
    AppPage(
        route_template="/{tenantId}/brand-settings",
        label="Brand Studio",
        module="brand",
        description="Identidad de marca: nombre, historia, posicionamiento, narrativa, identidad visual, voz, equipo, testimonios, autoridad",
        keywords=["marca", "brand", "identidad", "logo", "colores", "tipografía", "voz", "tono"],
        sections=[
            AppSection(
                section_id="identity",
                label="Identidad",
                description="Nombre de marca, industria, tagline, descripción, datos legales",
                fields=[
                    AppField("brand_name", "Nombre de marca", "El nombre comercial de la marca"),
                    AppField("industry", "Industria", "Sector o industria principal"),
                    AppField("tagline", "Tagline", "Frase corta que define la marca"),
                    AppField("description", "Descripción", "Descripción general de la marca"),
                ],
            ),
            AppSection(
                section_id="story",
                label="Historia",
                description="Historia de origen, misión, visión, hitos importantes",
                fields=[
                    AppField("origin_story", "Historia de origen", "Cómo nació la marca"),
                    AppField("mission", "Misión", "Propósito fundamental"),
                    AppField("vision", "Visión", "Hacia dónde se dirige"),
                ],
            ),
            AppSection(
                section_id="positioning",
                label="Posicionamiento (Brand Love Key)",
                description="Entorno competitivo, insight, beneficios, valores, razones para creer, discriminador, esencia, UVP",
                fields=[
                    AppField("competitive_environment", "Entorno competitivo", "Categoría y competencia"),
                    AppField("insight", "Insight", "Verdad profunda del consumidor"),
                    AppField("functional_benefits", "Beneficios funcionales", "Qué resuelve el producto"),
                    AppField("emotional_benefits", "Beneficios emocionales", "Cómo hace sentir al usuario"),
                    AppField("brand_values", "Valores de marca", "Principios fundamentales"),
                    AppField("discriminator", "Discriminador", "Lo que hace única a la marca"),
                    AppField("brand_essence", "Esencia de marca", "La verdad central de la marca"),
                    AppField("uvp", "UVP", "Propuesta de Valor Única"),
                ],
            ),
            AppSection(
                section_id="narrative",
                label="Narrativa (StoryBrand)",
                description="Estructura narrativa: héroe, problema, guía, plan, CTAs, resultado",
                fields=[
                    AppField("hero", "Héroe", "El cliente como protagonista"),
                    AppField("problem", "Problema", "Villano, externo, interno, filosófico"),
                    AppField("guide", "Guía", "La marca como mentor"),
                    AppField("plan", "Plan", "Pasos claros para el cliente"),
                    AppField("cta", "CTAs", "Llamadas a la acción"),
                ],
            ),
            AppSection("methodology", "Metodología", "Framework o método propio de la marca"),
            AppSection("visuals", "Identidad Visual", "Colores, tipografía, sistema de diseño"),
            AppSection("voice", "Voz y Tono", "Estilo de comunicación de la marca"),
            AppSection("team", "Equipo", "Personas clave y liderazgo"),
            AppSection("testimonials", "Testimonios", "Prueba social y casos de éxito"),
            AppSection("authority", "Autoridad", "Prensa, certificaciones, premios, partnerships"),
            AppSection("avatars", "Avatares", "Perfiles de cliente ideal"),
            AppSection("communication-assets", "Assets de Comunicación", "Conceptos creativos y piezas por etapa de funnel"),
        ],
    ),

    # ── Offer Studio ─────────────────────────────────────────────
    AppPage(
        route_template="/{tenantId}/offer-studio",
        label="Offer Studio",
        module="offer",
        description="Escalera de ofertas: lista de productos/servicios con sus configuraciones",
        keywords=["oferta", "producto", "servicio", "precio", "offer", "escalera"],
        sections=[
            AppSection("offer-list", "Lista de Ofertas", "Todas las ofertas del negocio"),
        ],
    ),
    AppPage(
        route_template="/{tenantId}/offer-studio/offer/{offerId}",
        label="Detalle de Oferta",
        module="offer",
        description="Configuración individual de una oferta: nombre, descripción, precio, psicología, avatar, objeciones, knowledge base",
        keywords=["oferta", "detalle", "psicología", "dolor", "deseo", "objeción"],
        sections=[
            AppSection("offer-general", "General", "Nombre, descripción, precio, tipo"),
            AppSection(
                "offer-avatar",
                "Avatar",
                "Cliente ideal asociado a esta oferta",
            ),
            AppSection(
                "offer-objections",
                "Objeciones",
                "Objeciones comunes y respuestas",
            ),
            AppSection(
                "offer-knowledge",
                "Knowledge Base",
                "Documentos y contexto para el agente de ventas",
            ),
        ],
    ),

    # ── Growth Studio (Marketing Studio) ─────────────────────────
    AppPage(
        route_template="/{tenantId}/marketing-studio",
        label="Growth Studio",
        module="growth",
        description="Funnel Bowtie, métricas de marketing y ventas, analytics por canal",
        keywords=["funnel", "bowtie", "métricas", "analytics", "growth", "marketing", "ventas", "conversión"],
        sections=[
            AppSection("funnel", "Funnel Bowtie", "Visualización del funnel completo"),
            AppSection("metrics", "Métricas", "Dashboard de métricas por etapa"),
        ],
    ),

    # ── Sales Studio ─────────────────────────────────────────────
    AppPage(
        route_template="/{tenantId}/sales",
        label="Sales Studio",
        module="sales",
        description="Centro de operaciones de ventas: conversaciones del agente IA, pipeline, métricas",
        keywords=["ventas", "sales", "agente", "conversación", "pipeline", "CRM"],
        sections=[
            AppSection("conversations", "Conversaciones", "Historial de chats del agente de ventas"),
        ],
    ),

    # ── Connections ───────────────────────────────────────────────
    AppPage(
        route_template="/connections",
        label="Conexiones",
        module="connections",
        description="Integraciones externas: Meta, Instagram, WhatsApp, Shopify, Google Calendar, Gmail, Mailerlite, YouTube, Google Analytics, Google Ads",
        keywords=["conexión", "integración", "meta", "instagram", "whatsapp", "shopify", "google", "calendar", "gmail", "youtube"],
        sections=[
            AppSection("meta", "Meta / Instagram", "Conexión con Facebook e Instagram"),
            AppSection("whatsapp", "WhatsApp", "Conexión con WhatsApp Business"),
            AppSection("shopify", "Shopify", "Conexión con tienda Shopify"),
            AppSection("google-calendar", "Google Calendar", "Sincronización de agenda"),
            AppSection("gmail", "Gmail", "Conexión de email"),
            AppSection("mailerlite", "MailerLite", "Email marketing"),
            AppSection("youtube", "YouTube", "Canal de YouTube"),
            AppSection("google-analytics", "Google Analytics", "Analytics del sitio web"),
        ],
    ),

    # ── Settings ─────────────────────────────────────────────────
    AppPage(
        route_template="/{tenantId}/settings",
        label="Configuración",
        module="settings",
        description="Configuración general del tenant: moneda, webhooks, llaves API, zona horaria",
        keywords=["configuración", "settings", "api key", "moneda", "webhook"],
        sections=[
            AppSection("general", "General", "Moneda, zona horaria"),
            AppSection("api-keys", "API Keys", "Llaves de IA (OpenAI/Gemini)"),
            AppSection("webhooks", "Webhooks", "URLs de webhook configuradas"),
        ],
    ),
]


# ── Lookup helpers ───────────────────────────────────────────────────

def get_all_pages() -> List[AppPage]:
    return NAVIGATION_MAP


def get_page_by_module(module: str) -> List[AppPage]:
    return [p for p in NAVIGATION_MAP if p.module == module]


def find_pages_by_keyword(keyword: str) -> List[AppPage]:
    """Fuzzy search across labels, descriptions, and keywords."""
    kw = keyword.lower()
    results = []
    for page in NAVIGATION_MAP:
        score = 0
        if kw in page.label.lower():
            score += 3
        if kw in page.description.lower():
            score += 2
        if any(kw in k.lower() for k in page.keywords):
            score += 3
        for section in page.sections:
            if kw in section.label.lower() or kw in section.description.lower():
                score += 1
        if score > 0:
            results.append((score, page))
    results.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in results]


def get_navigation_summary() -> str:
    """Generate a concise summary for the LLM system prompt."""
    lines = []
    for page in NAVIGATION_MAP:
        sections = ", ".join(s.label for s in page.sections)
        lines.append(f"- {page.label} ({page.route_template}): {sections}")
    return "\n".join(lines)
