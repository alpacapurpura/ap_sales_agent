"""Metric Catalog — fuente de verdad semántica para todas las métricas del sistema.

Define qué es cada métrica, cómo agregarla correctamente en períodos multi-día,
y cómo interpretarla para el usuario final.

Clasificación de agregación:
- ADDITIVE: SUM() seguro (clicks, spend, sessions, order_count)
- WEIGHTED_AVERAGE: Requiere denominador (bounceRate ponderado por sessions)
- DERIVED: Recalcular siempre de componentes (CPC = spend/clicks)
- NON_AGGREGABLE: Solo diario; personas únicas no se pueden sumar cross-day
- SNAPSHOT: Último valor del período (active_subscribers es un estado, no flujo)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.modules.analytics.domain.enums import AggregationType, MetricUnit


@dataclass(frozen=True)
class MetricDefinition:
    """Defines the semantic contract of a single metric."""

    name: str
    display_name: str
    description: str
    interpretation: str
    unit: MetricUnit  # count, currency, percentage, ratio, seconds, json
    aggregation: AggregationType
    weight_metric: str | None = None        # Para WEIGHTED_AVERAGE: denominador
    formula: str | None = None              # Para DERIVED: expresión legible
    formula_components: tuple[str, ...] = field(default_factory=tuple)  # Para DERIVED: nombres de métricas componentes
    is_unique_metric: bool = False          # True = personas únicas (no summable cross-day)
    real_api_name: str | None = None        # Si metric_name difiere del nombre real en la API
    higher_is_better: bool = True
    providers: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# ADDITIVE — SUM() seguro
# ---------------------------------------------------------------------------

_ADDITIVE: list[MetricDefinition] = [
    MetricDefinition(
        name="impressions",
        display_name="Impresiones",
        description="Veces que se mostró tu contenido o anuncio",
        interpretation="Más = mayor visibilidad. No implica personas únicas. impressions ≥ reach siempre.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("meta",),
    ),
    MetricDefinition(
        name="clicks",
        display_name="Clics",
        description="Clics en tu contenido o anuncio",
        interpretation="Más = mayor interés. clicks/impressions = CTR.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("meta", "google_ads", "tiktok"),
    ),
    MetricDefinition(
        name="spend",
        display_name="Inversión",
        description="Gasto publicitario",
        interpretation="Controlar vs presupuesto. spend/conversions = CPA.",
        unit=MetricUnit.CURRENCY,
        aggregation=AggregationType.ADDITIVE,
        providers=("meta", "google_ads", "tiktok"),
    ),
    MetricDefinition(
        name="conversions",
        display_name="Conversiones",
        description="Acciones de conversión completadas. Meta: solo compras. GA4/GAds: configurado por usuario.",
        interpretation="Meta: compras atribuidas a ads. Si es 0, revisar pixel/tracking.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("meta", "google_ads", "tiktok", "google_analytics"),
    ),
    MetricDefinition(
        name="conversion_value",
        display_name="Valor de Conversiones",
        description="Ingreso monetario atribuido a conversiones",
        interpretation="conversion_value / spend = ROAS (Return On Ad Spend).",
        unit=MetricUnit.CURRENCY,
        aggregation=AggregationType.ADDITIVE,
        providers=("google_ads",),
    ),
    MetricDefinition(
        name="sessions",
        display_name="Sesiones",
        description="Visitas al sitio. Un usuario puede tener múltiples sesiones.",
        interpretation="Más = más tráfico. sessions creciendo + users estable = usuarios vuelven (bueno para retención).",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("google_analytics",),
    ),
    MetricDefinition(
        name="engagedSessions",
        display_name="Sesiones Comprometidas",
        description="Sesiones con >10s de duración, 2+ pageviews, o una conversión",
        interpretation="engagedSessions / sessions = engagement rate del sitio.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("google_analytics",),
    ),
    MetricDefinition(
        name="newUsers",
        display_name="Usuarios Nuevos",
        description="Usuarios que visitan el sitio por primera vez",
        interpretation="newUsers / sessions = tasa de adquisición.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("google_analytics",),
    ),
    MetricDefinition(
        name="screenPageViews",
        display_name="Vistas de Página",
        description="Total de páginas vistas (un usuario puede ver múltiples páginas)",
        interpretation="screenPageViews / sessions = profundidad de navegación.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("google_analytics",),
    ),
    MetricDefinition(
        name="engagement",
        display_name="Interacciones",
        description="Likes + comments (+ shares en TikTok/FB). Mide resonancia del contenido.",
        interpretation="engagement / reach = engagement rate. Alto = contenido que genera conversación.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("meta", "tiktok", "youtube"),
    ),
    MetricDefinition(
        name="video_views",
        display_name="Reproducciones de Video",
        description="Reproducciones totales de video en TikTok organic. Una persona puede ver múltiples veces.",
        interpretation="Más = mayor alcance de contenido. No es comparable con Meta reach (personas únicas).",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("tiktok",),
    ),
    MetricDefinition(
        name="views",
        display_name="Vistas",
        description="Vistas de video en YouTube (reproducciones >30s). No es personas únicas.",
        interpretation="Más = mayor alcance. No es comparable con Meta reach (personas únicas).",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("youtube",),
    ),
    MetricDefinition(
        name="contacts",
        display_name="Contactos",
        description="Intentos de contacto outbound (email, llamada, mensaje directo)",
        interpretation="Mide volumen de prospección. responses / contacts = tasa de respuesta.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("crm_internal",),
    ),
    MetricDefinition(
        name="responses",
        display_name="Respuestas",
        description="Respuestas recibidas a contacto outbound",
        interpretation="responses / contacts = tasa de respuesta.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("crm_internal",),
    ),
    MetricDefinition(
        name="emails_sent",
        display_name="Emails Enviados",
        description="Total de emails enviados en el período",
        interpretation="Línea base para calcular tasas. Alta variabilidad = campañas puntuales.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("mailerlite",),
    ),
    MetricDefinition(
        name="unique_opens",
        display_name="Aperturas Únicas",
        description="Emails abiertos (contado por persona única, no por total de aperturas)",
        interpretation="unique_opens / emails_sent = open_rate.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("mailerlite",),
    ),
    MetricDefinition(
        name="unique_clicks",
        display_name="Clics Únicos",
        description="Clics en email por persona única",
        interpretation="unique_clicks / emails_sent = click_rate.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("mailerlite",),
    ),
    MetricDefinition(
        name="hard_bounces",
        display_name="Rebotes Duros",
        description="Emails no entregados permanentemente (dirección inválida, dominio inexistente)",
        interpretation="Alto = lista de emails sucia. Limpiar lista inmediatamente.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        higher_is_better=False,
        providers=("mailerlite",),
    ),
    MetricDefinition(
        name="soft_bounces",
        display_name="Rebotes Suaves",
        description="Emails no entregados temporalmente (buzón lleno, servidor caído)",
        interpretation="Normal si es bajo ocasional. Preocupante si sube sostenidamente.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        higher_is_better=False,
        providers=("mailerlite",),
    ),
    MetricDefinition(
        name="unsubscribes",
        display_name="Desuscripciones",
        description="Personas que se dieron de baja de la lista",
        interpretation="Alto = contenido no relevante o frecuencia excesiva. >0.5% es señal de alarma.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        higher_is_better=False,
        providers=("mailerlite",),
    ),
    MetricDefinition(
        name="spam_reports",
        display_name="Reportes de Spam",
        description="Emails marcados como spam por los destinatarios",
        interpretation="CRÍTICO si >0.1% de sent. Puede afectar deliverability permanentemente.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        higher_is_better=False,
        providers=("mailerlite",),
    ),
    MetricDefinition(
        name="forwards",
        display_name="Reenvíos",
        description="Emails reenviados por los destinatarios",
        interpretation="Señal de contenido valioso. Un forward = amplificación orgánica.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("mailerlite",),
    ),
    MetricDefinition(
        name="form_conversions",
        display_name="Conversiones de Formulario",
        description="Formularios de captación completados",
        interpretation="Mide captación directa. form_conversions / form_views = tasa de conversión del form.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("mailerlite",),
    ),
    MetricDefinition(
        name="new_subscribers",
        display_name="Suscriptores Nuevos",
        description="Nuevos suscriptores de email en el período",
        interpretation="Crecimiento de lista. new_subscribers / emails_sent = tasa de crecimiento.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("mailerlite",),
    ),
    MetricDefinition(
        name="automation_completed",
        display_name="Automatizaciones Completadas",
        description="Flujos de automatización email completados",
        interpretation="Mide engagement con secuencias. automation_completed / emails_sent = tasa de completado.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("mailerlite",),
    ),
    MetricDefinition(
        name="revenue",
        display_name="Ingresos Brutos",
        description="total_price de órdenes Shopify (excluye voided y fully refunded)",
        interpretation="Métrica principal de ventas. revenue - discounts - refunds = net_sales.",
        unit=MetricUnit.CURRENCY,
        aggregation=AggregationType.ADDITIVE,
        providers=("shopify",),
    ),
    MetricDefinition(
        name="order_count",
        display_name="Órdenes",
        description="Cantidad de órdenes Shopify en el período",
        interpretation="revenue / order_count = AOV. order_count creciendo + revenue estable = AOV bajando.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("shopify",),
    ),
    MetricDefinition(
        name="units_sold",
        display_name="Unidades Vendidas",
        description="Items vendidos (suma de line_items quantity)",
        interpretation="Volumen de producto. units_sold / order_count = items por orden.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("shopify",),
    ),
    MetricDefinition(
        name="total_discounts",
        display_name="Descuentos",
        description="Total de descuentos aplicados en órdenes",
        interpretation="total_discounts / revenue = % descontado. Alto = dependencia de descuentos.",
        unit=MetricUnit.CURRENCY,
        aggregation=AggregationType.ADDITIVE,
        higher_is_better=False,
        providers=("shopify",),
    ),
    MetricDefinition(
        name="total_tax",
        display_name="Impuestos",
        description="Total de impuestos cobrados",
        interpretation="Informativo y contable.",
        unit=MetricUnit.CURRENCY,
        aggregation=AggregationType.ADDITIVE,
        providers=("shopify",),
    ),
    MetricDefinition(
        name="net_sales",
        display_name="Ventas Netas",
        description="revenue - discounts - refunds. Ingreso real después de descuentos y reembolsos.",
        interpretation="Más preciso que revenue para P&L. net_sales / order_count = AOV neto.",
        unit=MetricUnit.CURRENCY,
        aggregation=AggregationType.ADDITIVE,
        providers=("shopify",),
    ),
    MetricDefinition(
        name="refund_amount",
        display_name="Monto de Reembolsos",
        description="Valor monetario de reembolsos procesados",
        interpretation="refund_amount / revenue = tasa de reembolso monetaria.",
        unit=MetricUnit.CURRENCY,
        aggregation=AggregationType.ADDITIVE,
        higher_is_better=False,
        providers=("shopify",),
    ),
    MetricDefinition(
        name="refund_count",
        display_name="Reembolsos",
        description="Cantidad de reembolsos procesados",
        interpretation="refund_count / order_count = tasa de reembolso. >5% = problema de calidad.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        higher_is_better=False,
        providers=("shopify",),
    ),
    MetricDefinition(
        name="shipping_revenue",
        display_name="Ingresos por Envío",
        description="Cobros por envío incluidos en las órdenes",
        interpretation="Contribución al margen. shipping_revenue / revenue = % de ingresos de envío.",
        unit=MetricUnit.CURRENCY,
        aggregation=AggregationType.ADDITIVE,
        providers=("shopify",),
    ),
    MetricDefinition(
        name="discount_usage_count",
        display_name="Usos de Código de Descuento",
        description="Cantidad de órdenes que usaron un código de descuento",
        interpretation="discount_usage_count / order_count = penetración de descuentos.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("shopify",),
    ),
    MetricDefinition(
        name="count",
        display_name="Cantidad",
        description="Conteo genérico (checkouts iniciados, carritos abandonados). Contexto depende del channel_slug.",
        interpretation="Ver channel_slug para contexto específico.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("shopify",),
    ),
    MetricDefinition(
        name="value",
        display_name="Valor",
        description="Valor monetario genérico (valor de checkout, carrito). Contexto depende del channel_slug.",
        interpretation="Ver channel_slug para contexto específico.",
        unit=MetricUnit.CURRENCY,
        aggregation=AggregationType.ADDITIVE,
        providers=("shopify",),
    ),
    MetricDefinition(
        name="pixel_pageviews",
        display_name="Vistas de Página (Pixel)",
        description="Eventos PageView registrados por el Meta Pixel",
        interpretation="Tráfico medido por Pixel. Complementa GA4. Diferencias = bloqueo de adblockers.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("meta_pixel",),
    ),
    MetricDefinition(
        name="pixel_view_content",
        display_name="ViewContent (Pixel)",
        description="Eventos ViewContent del Meta Pixel (usuario ve producto o contenido específico)",
        interpretation="Usuarios que ven producto/contenido. pixel_view_content / pixel_pageviews = tasa de engagement.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("meta_pixel",),
    ),
    MetricDefinition(
        name="pixel_leads",
        display_name="Leads (Pixel)",
        description="Eventos Lead registrados por el Meta Pixel",
        interpretation="Captación medida por Pixel. Comparar con form_conversions para validar tracking.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("meta_pixel",),
    ),
    MetricDefinition(
        name="pixel_add_to_cart",
        display_name="AddToCart (Pixel)",
        description="Eventos AddToCart del Meta Pixel",
        interpretation="Intención de compra. pixel_add_to_cart / pixel_view_content = tasa de carrito.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("meta_pixel",),
    ),
    MetricDefinition(
        name="pixel_purchases",
        display_name="Compras (Pixel)",
        description="Eventos Purchase del Meta Pixel",
        interpretation="Ventas atribuidas via Pixel. pixel_purchases / pixel_add_to_cart = tasa de completado.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.ADDITIVE,
        providers=("meta_pixel",),
    ),
]

# ---------------------------------------------------------------------------
# WEIGHTED_AVERAGE — Requiere denominador para agregar correctamente
# ---------------------------------------------------------------------------

_WEIGHTED_AVERAGE: list[MetricDefinition] = [
    MetricDefinition(
        name="bounceRate",
        display_name="Tasa de Rebote",
        description="Porcentaje de sesiones de una sola página sin engagement",
        interpretation=">70% = landing page no retiene. Revisar contenido/diseño.",
        unit=MetricUnit.PERCENTAGE,
        aggregation=AggregationType.WEIGHTED_AVERAGE,
        weight_metric="sessions",
        formula="bounced_sessions / sessions × 100",
        higher_is_better=False,
        providers=("google_analytics",),
    ),
    MetricDefinition(
        name="ctr",
        display_name="CTR",
        description="Click-through rate = clicks / impressions × 100",
        interpretation="<1% en ads = creative/copy no genera interés. >3% = muy bueno.",
        unit=MetricUnit.PERCENTAGE,
        aggregation=AggregationType.WEIGHTED_AVERAGE,
        weight_metric="impressions",
        formula="clicks / impressions × 100",
        providers=("meta", "google_ads", "tiktok"),
    ),
    MetricDefinition(
        name="cpm",
        display_name="CPM",
        description="Costo por 1000 impresiones = (spend / impressions) × 1000",
        interpretation="Alto = audiencia competida o cara. Comparar por industria.",
        unit=MetricUnit.CURRENCY,
        aggregation=AggregationType.WEIGHTED_AVERAGE,
        weight_metric="impressions",
        formula="spend / impressions × 1000",
        higher_is_better=False,
        providers=("meta",),
    ),
    MetricDefinition(
        name="open_rate",
        display_name="Tasa de Apertura",
        description="Porcentaje de emails abiertos sobre el total enviado",
        interpretation="<20% = subject lines débiles o lista fría. >40% = excelente.",
        unit=MetricUnit.PERCENTAGE,
        aggregation=AggregationType.WEIGHTED_AVERAGE,
        weight_metric="emails_sent",
        formula="unique_opens / emails_sent × 100",
        providers=("mailerlite",),
    ),
    MetricDefinition(
        name="click_rate",
        display_name="Tasa de Clics Email",
        description="Porcentaje de clics sobre emails enviados",
        interpretation="<2% = CTAs no claros o contenido no relevante.",
        unit=MetricUnit.PERCENTAGE,
        aggregation=AggregationType.WEIGHTED_AVERAGE,
        weight_metric="emails_sent",
        formula="unique_clicks / emails_sent × 100",
        providers=("mailerlite",),
    ),
    MetricDefinition(
        name="click_to_open_rate",
        display_name="CTOR",
        description="Click-to-open rate = unique_clicks / unique_opens × 100",
        interpretation="Mide calidad del contenido post-apertura. >10% = bueno.",
        unit=MetricUnit.PERCENTAGE,
        aggregation=AggregationType.WEIGHTED_AVERAGE,
        weight_metric="unique_opens",
        formula="unique_clicks / unique_opens × 100",
        providers=("mailerlite",),
    ),
    MetricDefinition(
        name="averageSessionDuration",
        display_name="Duración Promedio de Sesión",
        description="Duración promedio de sesión en segundos",
        interpretation="<30s = usuarios no encuentran valor. >180s = alto engagement.",
        unit=MetricUnit.SECONDS,
        aggregation=AggregationType.WEIGHTED_AVERAGE,
        weight_metric="sessions",
        formula="total_duration / sessions",
        providers=("google_analytics",),
    ),
    MetricDefinition(
        name="abandonment_rate",
        display_name="Tasa de Abandono de Carrito",
        description="Porcentaje de checkouts iniciados que no completaron la compra",
        interpretation="Alto = fricción en el proceso de checkout. Revisar UX y pricing.",
        unit=MetricUnit.PERCENTAGE,
        aggregation=AggregationType.WEIGHTED_AVERAGE,
        weight_metric="count",
        formula="abandoned_count / total_checkout_count × 100",
        higher_is_better=False,
        providers=("shopify",),
    ),
]

# ---------------------------------------------------------------------------
# DERIVED — Recalcular SIEMPRE de componentes (NUNCA sumar)
# ---------------------------------------------------------------------------

_DERIVED: list[MetricDefinition] = [
    MetricDefinition(
        name="cpc",
        display_name="CPC",
        description="Costo por clic = spend / clicks",
        interpretation="Más bajo = más eficiente. cpc subiendo = audiencia más cara o menos relevante.",
        unit=MetricUnit.CURRENCY,
        aggregation=AggregationType.DERIVED,
        formula="spend / clicks",
        formula_components=("spend", "clicks"),
        higher_is_better=False,
        providers=("google_ads",),
    ),
    MetricDefinition(
        name="avg_order_value",
        display_name="Valor Promedio de Orden",
        description="Valor promedio por orden = revenue / order_count",
        interpretation="AOV subiendo = upsell/cross-sell funcionando. Bajando = descuentos excesivos.",
        unit=MetricUnit.CURRENCY,
        aggregation=AggregationType.DERIVED,
        formula="revenue / order_count",
        formula_components=("revenue", "order_count"),
        providers=("shopify",),
    ),
    MetricDefinition(
        name="bounce_rate",
        display_name="Tasa de Rebote Email",
        description="Porcentaje de emails rebotados (hard + soft) sobre enviados",
        interpretation=">5% = lista sucia. Limpiar suscriptores inactivos y direcciones inválidas.",
        unit=MetricUnit.PERCENTAGE,
        aggregation=AggregationType.DERIVED,
        formula="(hard_bounces + soft_bounces) / emails_sent × 100",
        formula_components=("hard_bounces", "soft_bounces", "emails_sent"),
        higher_is_better=False,
        providers=("mailerlite",),
    ),
    MetricDefinition(
        name="unsubscribe_rate",
        display_name="Tasa de Desuscripción",
        description="Porcentaje de desuscripciones sobre emails enviados",
        interpretation=">0.5% = contenido no alineado con expectativas de la audiencia.",
        unit=MetricUnit.PERCENTAGE,
        aggregation=AggregationType.DERIVED,
        formula="unsubscribes / emails_sent × 100",
        formula_components=("unsubscribes", "emails_sent"),
        higher_is_better=False,
        providers=("mailerlite",),
    ),
    MetricDefinition(
        name="reactivation_rate",
        display_name="Tasa de Reactivación",
        description="Porcentaje de aperturas únicas sobre emails enviados (usado en secuencias de retención)",
        interpretation="Mide recuperación de suscriptores inactivos.",
        unit=MetricUnit.PERCENTAGE,
        aggregation=AggregationType.DERIVED,
        formula="unique_opens / emails_sent × 100",
        formula_components=("unique_opens", "emails_sent"),
        providers=("mailerlite",),
    ),
    MetricDefinition(
        name="response_rate",
        display_name="Tasa de Respuesta Outbound",
        description="Porcentaje de respuestas recibidas sobre contactos enviados",
        interpretation="Mide efectividad del outreach. <5% = mensaje o segmentación mejorable.",
        unit=MetricUnit.PERCENTAGE,
        aggregation=AggregationType.DERIVED,
        formula="responses / contacts × 100",
        formula_components=("responses", "contacts"),
        providers=("crm_internal",),
    ),
    MetricDefinition(
        name="form_conversion_rate",
        display_name="Tasa de Conversión de Formulario",
        description="Porcentaje de vistas de formulario que resultaron en conversión",
        interpretation="Mide efectividad de formularios de captación.",
        unit=MetricUnit.PERCENTAGE,
        aggregation=AggregationType.DERIVED,
        formula="form_conversions / form_views × 100",
        formula_components=("form_conversions",),
        providers=("mailerlite",),
    ),
    MetricDefinition(
        name="completion_rate",
        display_name="Tasa de Completado de Automatización",
        description="Porcentaje de flujos de automatización completados sobre los disparados",
        interpretation="Mide engagement con secuencias de email. <50% = deserción alta.",
        unit=MetricUnit.PERCENTAGE,
        aggregation=AggregationType.DERIVED,
        formula="completed / triggered × 100",
        formula_components=("automation_completed",),
        providers=("mailerlite",),
    ),
]

# ---------------------------------------------------------------------------
# NON_AGGREGABLE — Solo diario; para rangos → API call o no agregar
# ---------------------------------------------------------------------------

_NON_AGGREGABLE: list[MetricDefinition] = [
    MetricDefinition(
        name="reach",
        display_name="Alcance",
        description="Personas únicas que vieron tu contenido ese día. NO es summable cross-day (misma persona en lunes y martes = 2 al sumar, pero debería ser 1).",
        interpretation="Mide amplitud de audiencia. Para períodos >1 día, pedir a la API con el rango completo.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.NON_AGGREGABLE,
        is_unique_metric=True,
        providers=("meta",),
    ),
    MetricDefinition(
        name="users",
        display_name="Usuarios",
        description="Usuarios únicos del sitio ese día. NO summable cross-day.",
        interpretation="Mide audiencia real. Para períodos >1 día, pedir a GA4 con el rango completo.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.NON_AGGREGABLE,
        is_unique_metric=True,
        providers=("google_analytics",),
    ),
    MetricDefinition(
        name="frequency",
        display_name="Frecuencia",
        description="Promedio de veces que cada persona vio el anuncio = impressions / reach. NO aggregable: depende de reach que tampoco es summable.",
        interpretation=">3 = fatiga de audiencia, rotar creatives. Para períodos: IMPOSIBLE calcular localmente, requiere API call.",
        unit=MetricUnit.RATIO,
        aggregation=AggregationType.NON_AGGREGABLE,
        is_unique_metric=False,
        higher_is_better=False,
        providers=("meta",),
    ),
    MetricDefinition(
        name="repeat_customers",
        display_name="Clientes Recurrentes",
        description="Clientes con más de una orden histórica. Mismo cliente en múltiples días duplica al sumar.",
        interpretation="Para rangos: requiere dedup de customer_ids a nivel DB o query especial.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.NON_AGGREGABLE,
        is_unique_metric=True,
        providers=("shopify",),
    ),
]

# ---------------------------------------------------------------------------
# SNAPSHOT — Último valor del período (no sumar ni promediar)
# ---------------------------------------------------------------------------

_SNAPSHOT: list[MetricDefinition] = [
    MetricDefinition(
        name="active_subscribers",
        display_name="Suscriptores Activos",
        description="Total de suscriptores activos en el momento (snapshot del estado actual)",
        interpretation="Creciente = lista saludable. Decreciente = desuscripciones > nuevos suscriptores.",
        unit=MetricUnit.COUNT,
        aggregation=AggregationType.SNAPSHOT,
        providers=("mailerlite",),
    ),
    MetricDefinition(
        name="top_pages",
        display_name="Páginas Top",
        description="JSON con las top 10 páginas por vistas en el período",
        interpretation="Muestra qué contenido genera más tráfico.",
        unit=MetricUnit.JSON,
        aggregation=AggregationType.SNAPSHOT,
        providers=("google_analytics",),
    ),
    MetricDefinition(
        name="traffic_sources",
        display_name="Fuentes de Tráfico",
        description="JSON con distribución de tráfico por canal (organic, direct, paid, etc.)",
        interpretation="Diversificación de fuentes = menor riesgo. Dependencia de 1 fuente = vulnerabilidad.",
        unit=MetricUnit.JSON,
        aggregation=AggregationType.SNAPSHOT,
        providers=("google_analytics",),
    ),
    MetricDefinition(
        name="device_split",
        display_name="Dispositivos",
        description="JSON con % de tráfico por dispositivo (mobile, desktop, tablet)",
        interpretation=">70% mobile = asegurarse que el sitio es mobile-first.",
        unit=MetricUnit.JSON,
        aggregation=AggregationType.SNAPSHOT,
        providers=("google_analytics",),
    ),
]

# ---------------------------------------------------------------------------
# Catálogo unificado
# ---------------------------------------------------------------------------

METRIC_CATALOG: dict[str, MetricDefinition] = {
    m.name: m
    for m in [*_ADDITIVE, *_WEIGHTED_AVERAGE, *_DERIVED, *_NON_AGGREGABLE, *_SNAPSHOT]
}


def get_metric_def(name: str) -> MetricDefinition | None:
    """Return the MetricDefinition for a given metric name, or None if not catalogued."""
    return METRIC_CATALOG.get(name)


def is_additive(name: str) -> bool:
    """Return True if the metric can be safely summed across time periods."""
    defn = get_metric_def(name)
    return defn is not None and defn.aggregation == AggregationType.ADDITIVE
