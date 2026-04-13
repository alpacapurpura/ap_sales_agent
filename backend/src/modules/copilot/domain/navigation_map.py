"""Declarative navigation map of the Nicolify app.

Used by copilot tools to:
- Navigate users to specific pages/sections
- Understand what modules/sections exist
- Map user intents to routes
"""

from dataclasses import dataclass, field


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
    fields: list[AppField] = field(default_factory=list)


@dataclass(frozen=True)
class AppPage:
    """A navigable page in the app."""

    route_template: str  # e.g. "/{tenantId}/brand-settings"
    label: str
    module: str  # brand, offer, growth, sales, connections, settings
    description: str
    sections: list[AppSection] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)


# ── Navigation Map ───────────────────────────────────────────────────

NAVIGATION_MAP: list[AppPage] = [
    # ── Brand Studio ─────────────────────────────────────────────
    # ── Brand Studio — Esencia ────────────────────────────────────
    AppPage(
        route_template="/{tenantId}/brand-studio/esencia",
        label="Esencia",
        module="brand",
        description="ADN de la marca: identidad, historia, personalidad, equipo, credibilidad, contacto",
        keywords=[
            "marca",
            "brand",
            "identidad",
            "esencia",
            "historia",
            "equipo",
            "contacto",
        ],
        sections=[
            AppSection(
                "identity",
                "Identidad",
                "Nombre de marca, industria, tagline, descripción, datos legales",
            ),
            AppSection(
                "story",
                "Historia",
                "Historia de origen, misión, visión, hitos importantes",
            ),
            AppSection(
                "values-essence",
                "Personalidad",
                "Valores, personalidad, arquetipo, esencia de marca, RTBs",
            ),
            AppSection("team", "Equipo", "Personas clave y liderazgo"),
            AppSection(
                "authority",
                "Autoridad",
                "Prensa, certificaciones, premios, partnerships",
            ),
            AppSection("testimonials", "Testimonios", "Prueba social y casos de éxito"),
            AppSection(
                "contact",
                "Contacto",
                "Información pública de contacto y redes sociales",
            ),
        ],
    ),
    # ── Brand Studio — Estrategia ──────────────────────────────────
    AppPage(
        route_template="/{tenantId}/brand-studio/estrategia",
        label="Estrategia",
        module="brand",
        description="Plan de juego: posicionamiento, mercado, StoryBrand, metodología",
        keywords=[
            "estrategia",
            "posicionamiento",
            "mercado",
            "storybrand",
            "metodología",
            "UVP",
        ],
        sections=[
            AppSection(
                "positioning",
                "Posicionamiento (Brand Love Key)",
                "Entorno competitivo, insight, beneficios, discriminador, UVP",
            ),
            AppSection(
                "market",
                "Mercado",
                "Competidores directos/indirectos, consumer insights",
            ),
            AppSection(
                "storybrand",
                "Narrativa (StoryBrand)",
                "Héroe, problema, guía, plan, CTAs, resultado, one-liner",
            ),
            AppSection(
                "methodology",
                "Metodología",
                "Framework o método propio de la marca",
            ),
        ],
    ),
    # ── Brand Studio — Público ─────────────────────────────────────
    AppPage(
        route_template="/{tenantId}/brand-studio/publico",
        label="Público",
        module="brand",
        description="Clientes ideales: buyer personas y perfiles de avatar",
        keywords=["público", "avatar", "buyer persona", "cliente ideal", "audiencia"],
        sections=[
            AppSection("avatars", "Avatares", "Perfiles de cliente ideal"),
        ],
    ),
    # ── Brand Studio — Identidad Creativa ────────────────────────────
    AppPage(
        route_template="/{tenantId}/brand-studio/identidad-creativa",
        label="Identidad Creativa",
        module="brand",
        description=(
            "Imagen, voz y mensajes: galería, colores, tipografía, logos, tono, conceptos creativos, assets por funnel"
        ),
        keywords=[
            "assets",
            "visual",
            "logo",
            "colores",
            "tipografía",
            "diseño",
            "galería",
            "voz",
            "tono",
            "comunicación",
            "idioma",
            "voice",
            "creativos",
            "conceptos",
            "funnel",
            "TOFU",
            "MOFU",
            "BOFU",
            "messaging",
        ],
        sections=[
            AppSection("gallery", "Galería de Marca", "Media assets de la marca"),
            AppSection(
                "visuals",
                "Sistema de Diseño",
                "Colores, tipografía, personalidad visual",
            ),
            AppSection("logos", "Logo Kit", "Variantes de logo"),
            AppSection(
                "voice",
                "Voz AI",
                "Estilo de comunicación y configuración de voz",
            ),
            AppSection(
                "creative-concepts",
                "Conceptos Creativos",
                "Plantillas de messaging reutilizables",
            ),
            AppSection(
                "funnel-assets",
                "Assets por Funnel",
                "Piezas por etapa (TOFU/MOFU/BOFU/Retención)",
            ),
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
            AppSection(
                "offer-list",
                "Lista de Ofertas",
                "Todas las ofertas del negocio",
            ),
        ],
    ),
    AppPage(
        route_template="/{tenantId}/offer-studio/offer/{offerId}",
        label="Detalle de Oferta",
        module="offer",
        description=(
            "Configuración individual de una oferta: nombre, descripción, precio,"
            " psicología, avatar, objeciones, knowledge base"
        ),
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
        route_template="/{tenantId}/growth-studio/ventas",
        label="Growth Studio",
        module="growth",
        description="Funnel Bowtie completo — redirige a la etapa Ventas",
        keywords=["funnel", "bowtie", "métricas", "analytics", "growth", "marketing"],
        sections=[],
    ),
    AppPage(
        route_template="/{tenantId}/growth-studio/atraccion-captura",
        label="Atracción & Captura",
        module="growth",
        description="Etapa 1-2: tráfico, visitantes, leads, canales orgánicos, paid, captura",
        keywords=[
            "atracción",
            "captura",
            "visitantes",
            "tráfico",
            "leads",
            "orgánico",
            "paid",
            "SEO",
            "redes sociales",
        ],
        sections=[
            AppSection(
                "attraction",
                "Atracción",
                "Visitantes por canal: orgánico, paid, search, outbound",
            ),
            AppSection(
                "capture",
                "Captura",
                "Conversión de visitantes a leads, landing pages, chatbots",
            ),
        ],
    ),
    AppPage(
        route_template="/{tenantId}/growth-studio/nutricion-oportunidad",
        label="Nutrición & Oportunidad",
        module="growth",
        description="Etapa 3-4: nurture, MQLs, SQLs, retargeting, automatización, calificación",
        keywords=[
            "nutrición",
            "oportunidad",
            "MQL",
            "SQL",
            "retargeting",
            "automatización",
            "nurture",
            "calificación",
        ],
        sections=[
            AppSection(
                "nurture",
                "Nutrición",
                "Retargeting, email automation, engagement",
            ),
            AppSection(
                "opportunity",
                "Oportunidad",
                "Checkout, payment links, calificación de leads",
            ),
        ],
    ),
    AppPage(
        route_template="/{tenantId}/growth-studio/ventas",
        label="Ventas",
        module="growth",
        description="Etapa 5: revenue, clientes nuevos, ofertas vendidas, Shopify, suscripciones",
        keywords=[
            "ventas",
            "revenue",
            "ingresos",
            "clientes",
            "shopify",
            "suscripciones",
            "CAC",
            "ticket",
        ],
        sections=[
            AppSection(
                "sales-metrics",
                "Métricas de Ventas",
                "Revenue total, nuevos clientes, CAC",
            ),
            AppSection(
                "offer-ladder",
                "Escalera de Ofertas",
                "Revenue por oferta y tipo",
            ),
        ],
    ),
    AppPage(
        route_template="/{tenantId}/growth-studio/adopcion",
        label="Adopción",
        module="growth",
        description="Etapa 6: salud del cliente, activación, retención temprana, refunds",
        keywords=[
            "adopción",
            "salud",
            "activación",
            "retención",
            "refund",
            "churn temprano",
            "onboarding",
        ],
        sections=[
            AppSection(
                "health",
                "Salud de Clientes",
                "Porcentaje de salud, activos vs inactivos",
            ),
        ],
    ),
    AppPage(
        route_template="/{tenantId}/growth-studio/expansion-evangelizacion",
        label="Expansión & Evangelización",
        module="growth",
        description="Etapa 7-8: MRR, LTV, churn, referidos, NPS, k-factor, upsell",
        keywords=[
            "expansión",
            "evangelización",
            "MRR",
            "LTV",
            "churn",
            "referidos",
            "NPS",
            "k-factor",
            "upsell",
        ],
        sections=[
            AppSection(
                "expansion",
                "Expansión",
                "Net MRR, LTV, retención, crecimiento, cancelaciones",
            ),
            AppSection(
                "evangelization",
                "Evangelización",
                "Referidos, NPS, k-factor, UGC",
            ),
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
            AppSection(
                "conversations",
                "Conversaciones",
                "Historial de chats del agente de ventas",
            ),
        ],
    ),
    # ── Closer Studio ─────────────────────────────────────────────
    AppPage(
        route_template="/{tenantId}/sales/studio/inbox",
        label="Closer Studio - Inbox",
        module="sales",
        description=(
            "Supervisión en tiempo real de conversaciones del AI Sales Agent."
            " Ver mensajes, pausar/reanudar AI, enviar mensajes directos."
        ),
        keywords=[
            "closer",
            "inbox",
            "conversación",
            "stop",
            "pause",
            "mensaje directo",
            "supervisión",
        ],
        sections=[
            AppSection(
                "conversations",
                "Conversaciones",
                "Lista de conversaciones activas con filtros",
            ),
            AppSection("thread", "Thread", "Historial de mensajes de una conversación"),
            AppSection(
                "actions",
                "Acciones",
                "STOP/RESUME AI, mensajes, instrucciones",
            ),
        ],
    ),
    AppPage(
        route_template="/{tenantId}/sales/studio/pipeline",
        label="Closer Studio - Pipeline",
        module="sales",
        description="Vista Kanban del pipeline de ventas. Arrastra leads entre etapas del funnel.",
        keywords=["pipeline", "kanban", "funnel", "etapa", "drag"],
        sections=[
            AppSection("board", "Kanban", "Tablero de pipeline con columnas por etapa"),
        ],
    ),
    AppPage(
        route_template="/{tenantId}/sales/studio/frozen",
        label="Closer Studio - Congeladas",
        module="sales",
        description="Conversaciones sin actividad >72h. Diagnóstico AI y reactivación rápida.",
        keywords=["congelada", "frozen", "inactiva", "reactivar", "diagnóstico"],
        sections=[
            AppSection(
                "frozen-list",
                "Lista",
                "Conversaciones congeladas con diagnóstico",
            ),
            AppSection(
                "diagnosis",
                "Diagnóstico AI",
                "Análisis automático y recomendaciones",
            ),
        ],
    ),
    # ── Connections ───────────────────────────────────────────────
    AppPage(
        route_template="/connections",
        label="Conexiones",
        module="connections",
        description=(
            "Integraciones externas: Meta, Instagram, WhatsApp, Shopify,"
            " Google Calendar, Gmail, Mailerlite, YouTube, Google Analytics, Google Ads"
        ),
        keywords=[
            "conexión",
            "integración",
            "meta",
            "instagram",
            "whatsapp",
            "shopify",
            "google",
            "calendar",
            "gmail",
            "youtube",
        ],
        sections=[
            AppSection("meta", "Meta / Instagram", "Conexión con Facebook e Instagram"),
            AppSection("whatsapp", "WhatsApp", "Conexión con WhatsApp Business"),
            AppSection("shopify", "Shopify", "Conexión con tienda Shopify"),
            AppSection(
                "google-calendar",
                "Google Calendar",
                "Sincronización de agenda",
            ),
            AppSection("gmail", "Gmail", "Conexión de email"),
            AppSection("mailerlite", "MailerLite", "Email marketing"),
            AppSection("youtube", "YouTube", "Canal de YouTube"),
            AppSection(
                "google-analytics",
                "Google Analytics",
                "Analytics del sitio web",
            ),
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


def get_all_pages() -> list[AppPage]:
    """Return all pages."""
    return NAVIGATION_MAP


def get_page_by_module(module: str) -> list[AppPage]:
    """Return page by module."""
    return [p for p in NAVIGATION_MAP if p.module == module]


def find_pages_by_keyword(keyword: str) -> list[AppPage]:
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
