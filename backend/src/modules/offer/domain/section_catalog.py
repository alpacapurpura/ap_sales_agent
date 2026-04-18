"""Section Catalog — single source of truth for Offer Studio editor sections.

This module is the 5th SSoT axis of the offer-studio catalog system (see
``.claude/rules/offer-catalogs.md``), sitting alongside OfferArchetype,
OfferValueLevel, OfferFormat, ExpertBusinessType and VariantStructure.

Architecture
~~~~~~~~~~~~

Each ``SectionKey`` is a stable id for an editor bloc. The catalog declares
Spanish copy (label + subtitle + help_text) tuned for Latam microempresarios
— dueños de gimnasios, odontólogos, abogados, coaches — sin jerga de
marketer. The ``help_text_es`` is deliberately rich (2-4 sentences) so the
copilot can ground its suggestions; sub-UX surfaces (tooltips) truncate it
to the needed length.

Per-archetype filtering is declared in ``archetype_catalog.py`` via
``ArchetypeCapabilities.sections``. The union of all archetypes' sections
is a subset of ``SectionKey``.

Invariants (arch-test-enforced)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Every ``SectionKey`` enum member has a matching ``SECTION_CATALOG``
   entry.
2. Icons are unique per section (cross-section collisions would show the
   same glyph twice in a single surface).
3. Every entry declares non-empty label/subtitle/help_text/icon.
4. ``help_text_es`` is at least 1.5x the length of ``subtitle_es`` (the
   help should add context, not duplicate the subtitle).
5. ``completion_weight`` is in [0.1, 1.0]; required sections weigh >= 0.8.
6. See ``test_section_catalog_completeness.py`` for the full gate list.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SectionKey(StrEnum):
    """Stable identifier for an Offer Studio editor section.

    Values match the frontend ``SECTION_REGISTRY`` keys verbatim so URL
    segments, schema filenames, and copilot route-tool maps align without
    per-layer translation tables.
    """

    # Universal bloques
    IDENTITY = "identity"
    STRATEGY = "strategy"
    PSYCHOLOGY = "psychology"
    PROMISE = "promise"
    VALUE_STACK = "value_stack"
    INSTRUCTORS = "instructors"
    KNOWLEDGE = "knowledge"
    CLOSING = "closing"
    GALLERY = "gallery"

    # Archetype-specific
    PRODUCT_DETAILS = "product_details"
    SUBSCRIPTION_DETAILS = "subscription_details"
    EVENT_DETAILS = "event_details"
    PRICING = "pricing"
    PROGRAM_DETAILS = "program_details"
    SERVICE_DETAILS = "service_details"
    RESOURCES = "resources"

    # Nuevas secciones (Latam mass-market rollout)
    FAQ = "faq"
    TESTIMONIALS = "testimonials"
    PORTFOLIO = "portfolio"
    LOCATION = "location"
    PLATFORM_DETAILS = "platform_details"


class SectionScope(StrEnum):
    """Which aggregate a section's fields persist to.

    - ``OFFER_LEVEL``: fields live on the ``Offer`` row. Content is shared
      across all launches of the offer. Visible on both the virtual
      ``/edition/evergreen/`` URL and every specific-edition URL.
    - ``EDITION_LEVEL``: fields live on a ``LaunchEdition`` row. Visible
      only on specific-edition URLs; hidden under ``evergreen``.
    - ``MIXED``: per-field ``owner`` split (some fields on ``Offer``, others
      on ``LaunchEdition``). The form-runtime dispatcher routes saves based
      on the field's declared ``owner``.
    """

    OFFER_LEVEL = "offer_level"
    EDITION_LEVEL = "edition_level"
    MIXED = "mixed"


@dataclass(frozen=True, slots=True)
class SectionMetadata:
    """Frozen record describing a single offer-studio editor section.

    ``help_text_es`` is copilot-grade: 2-4 sentences that explain **why**
    the section matters, **how** it connects to other Nicolify surfaces
    (sales agent, landing, analytics), and **what good looks like** so the
    copilot can suggest or auto-fill intelligently.
    """

    key: SectionKey
    label_es: str
    subtitle_es: str
    help_text_es: str
    icon_name: str
    scope: SectionScope
    completion_weight: float
    required_to_publish: bool


SECTION_CATALOG: dict[SectionKey, SectionMetadata] = {
    # ── Universal bloques ──────────────────────────────────────────────────
    SectionKey.IDENTITY: SectionMetadata(
        key=SectionKey.IDENTITY,
        label_es="Identidad de la oferta",
        subtitle_es="Cómo se llama y cómo se presenta",
        help_text_es=(
            "El nombre público de la oferta, una frase titular memorable y el tiempo "
            "hasta el primer resultado. Es lo que verá tu cliente en anuncios, landings "
            "y checkout. Un nombre claro + una promesa breve facilitan que entiendan qué "
            "vendés en 3 segundos. Si tu oferta se llama 'Programa Libertad Financiera', "
            "la frase titular podría ser 'Aprendé a invertir tus primeros USD 500 sin miedo'."
        ),
        icon_name="Fingerprint",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=1.0,
        required_to_publish=True,
    ),
    SectionKey.STRATEGY: SectionMetadata(
        key=SectionKey.STRATEGY,
        label_es="Para quién es",
        subtitle_es="Tu cliente ideal y sus dolores",
        help_text_es=(
            "Describí a tu cliente ideal: qué problema concreto tiene, qué quiere lograr "
            "y para quién esta oferta NO es. El agente de ventas usa esto para calificar "
            "leads y descartar consultas que no van a cerrar. Cuanto más específico "
            "mejor: 'Dueñas de salones de belleza en Perú que quieren pasar de agenda "
            "manual a online' convierte mejor que 'Emprendedoras'."
        ),
        icon_name="Target",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=0.9,
        required_to_publish=True,
    ),
    SectionKey.PSYCHOLOGY: SectionMetadata(
        key=SectionKey.PSYCHOLOGY,
        label_es="Motivaciones y objeciones",
        subtitle_es="Qué frena y qué empuja a tu cliente",
        help_text_es=(
            "Las objeciones típicas ('es caro', 'no tengo tiempo', 'no va a funcionar conmigo'), "
            "los disparadores emocionales (frustración actual, aspiración futura) y las "
            "barreras de confianza propias de Latam (miedo a estafas online, prefieren "
            "WhatsApp a formularios, desconfían de pagos con tarjeta). El agente de ventas "
            "responde cada objeción en tiempo real con los argumentos que cargues acá."
        ),
        icon_name="HeartPulse",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=0.7,
        required_to_publish=False,
    ),
    SectionKey.PROMISE: SectionMetadata(
        key=SectionKey.PROMISE,
        label_es="Promesa y resultado",
        subtitle_es="La transformación que le garantizás",
        help_text_es=(
            "El antes/después que comprometés: dónde está tu cliente hoy y dónde va a "
            "estar al terminar. Tiene que ser concreto y medible ('bajar 6 kg en 12 "
            "semanas' mejor que 'sentirte mejor'). Es la promesa central de tu marketing "
            "y del contrato implícito con quien compra — si no se cumple, aplica la "
            "garantía. El 'por qué ahora' explica la urgencia."
        ),
        icon_name="Star",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=1.0,
        required_to_publish=True,
    ),
    SectionKey.VALUE_STACK: SectionMetadata(
        key=SectionKey.VALUE_STACK,
        label_es="Entregables y valor",
        subtitle_es="Qué recibe el cliente al comprar",
        help_text_es=(
            "La lista enumerada de todo lo que incluye la compra: sesiones, módulos, "
            "materiales, accesos, bonos. Asignale a cada ítem su valor percibido en USD "
            "(lo que costaría comprado por separado) para que la suma justifique el "
            "precio final. Es el clásico 'stack' de marketing que ancla precio: "
            "'Valor total USD 4.344 · Tu inversión hoy USD 1.497'. Incluí el acceso a "
            "comunidad (WhatsApp/Telegram/Discord) si forma parte."
        ),
        icon_name="Gift",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=0.8,
        required_to_publish=False,
    ),
    SectionKey.INSTRUCTORS: SectionMetadata(
        key=SectionKey.INSTRUCTORS,
        label_es="Equipo y autoridad",
        subtitle_es="Quién respalda la oferta",
        help_text_es=(
            "Las personas que dictan, facilitan o respaldan la oferta — con sus "
            "credenciales blandas (experiencia, logros, casos). La autoridad de quien "
            "enseña se transfiere a la oferta: un abogado con 15 años de trayectoria "
            "vende más caro que un recién egresado. Para eventos, este bloque aloja el "
            "lineup de speakers. Las credenciales duras (matrícula, título) van en la "
            "sección Credenciales."
        ),
        icon_name="BadgeCheck",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=0.5,
        required_to_publish=False,
    ),
    SectionKey.KNOWLEDGE: SectionMetadata(
        key=SectionKey.KNOWLEDGE,
        label_es="Base de conocimiento",
        subtitle_es="Documentos que alimentan al agente",
        help_text_es=(
            "Documentos, PDFs, guiones y URLs que el agente de ventas consulta para "
            "responder preguntas técnicas sobre tu oferta en tiempo real. A mayor "
            "cobertura documental menos escalamientos humanos necesitás. Este material "
            "es INTERNO del agente — no se muestra público. Las preguntas frecuentes "
            "públicas tienen su propia sección."
        ),
        icon_name="Database",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=0.6,
        required_to_publish=False,
    ),
    SectionKey.CLOSING: SectionMetadata(
        key=SectionKey.CLOSING,
        label_es="Cierre y garantía",
        subtitle_es="Garantía, urgencia y cancelación",
        help_text_es=(
            "Los elementos que disparan la decisión final: garantía de devolución "
            "(30 días por ejemplo), cupos reales o fecha límite, política de cancelación "
            "y el 'último empujón' de copy. En Latam la desconfianza online es alta — "
            "explicitá siempre cómo devolvés el dinero (transferencia bancaria, reverso "
            "de tarjeta) y qué garantiza la devolución. No uses escasez falsa."
        ),
        icon_name="CheckCircle",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=0.7,
        required_to_publish=False,
    ),
    SectionKey.GALLERY: SectionMetadata(
        key=SectionKey.GALLERY,
        label_es="Galería",
        subtitle_es="Imágenes y video para la landing",
        help_text_es=(
            "Imagen principal (hero), galería complementaria y video demo opcional. "
            "El generador de landings y assets las usa automáticamente. Para ofertas "
            "de transformación (fitness, salud estética, coaching), subí pares "
            "antes/después — convierten 3x mejor que fotos sueltas."
        ),
        icon_name="Image",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=0.4,
        required_to_publish=False,
    ),
    # ── Archetype-specific ────────────────────────────────────────────────
    SectionKey.PRODUCT_DETAILS: SectionMetadata(
        key=SectionKey.PRODUCT_DETAILS,
        label_es="Detalles del producto",
        subtitle_es="Formato, entrega y envío",
        help_text_es=(
            "Especificaciones técnicas del producto: formato (PDF, video, físico), "
            "forma de entrega y — para físicos en Latam — qué carriers usás "
            "(OCA, Andreani, Servientrega, Estafeta, Mercado Envíos), tiempos de "
            "entrega por región y política de devoluciones. Para digitales: URL de "
            "acceso, instrucciones, duración del acceso."
        ),
        icon_name="PackageOpen",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=0.9,
        required_to_publish=True,
    ),
    SectionKey.SUBSCRIPTION_DETAILS: SectionMetadata(
        key=SectionKey.SUBSCRIPTION_DETAILS,
        label_es="Detalles de suscripción",
        subtitle_es="Ciclo, duración y cancelación",
        help_text_es=(
            "Reglas de la suscripción: frecuencia (mensual/anual), renovación automática "
            "con aviso previo, política de cancelación, trial gratuito si aplica. "
            "Transparencia acá previene cancelaciones tempranas y disputas con pasarelas. "
            "En Latam conviene explicitar cómo se cobra en moneda local y equivalente USD."
        ),
        icon_name="CreditCard",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=0.9,
        required_to_publish=True,
    ),
    SectionKey.EVENT_DETAILS: SectionMetadata(
        key=SectionKey.EVENT_DETAILS,
        label_es="Detalles del evento",
        subtitle_es="Fecha, lugar y agenda",
        help_text_es=(
            "Datos logísticos específicos de esta salida: fecha y hora con zona horaria, "
            "venue físico o link virtual, capacidad, agenda día-a-día, qué traer, "
            "comidas incluidas, alojamiento sugerido. Cambia por edición — un mismo "
            "retiro puede repetirse en distintas ciudades/fechas con datos diferentes."
        ),
        icon_name="CalendarCheck",
        scope=SectionScope.EDITION_LEVEL,
        completion_weight=1.0,
        required_to_publish=True,
    ),
    SectionKey.PRICING: SectionMetadata(
        key=SectionKey.PRICING,
        label_es="Precios y pagos",
        subtitle_es="Cuánto cuesta y cómo se paga",
        help_text_es=(
            "Precio en moneda local (PEN/MXN/COP/ARS/CLP/BRL) + equivalente USD, "
            "IVA/IGV/ICMS incluido o no, cuotas sin interés (3/6/12 — decisivas en Latam), "
            "métodos de pago aceptados (Mercado Pago, Yape, Plin, Nequi, MODO, PIX, "
            "Oxxo Pay, transferencia, tarjeta, PayPal). Para salud: obras sociales y "
            "planes aceptados. Para B2B: quote-only si aplica."
        ),
        icon_name="DollarSign",
        scope=SectionScope.MIXED,
        completion_weight=1.0,
        required_to_publish=True,
    ),
    SectionKey.PROGRAM_DETAILS: SectionMetadata(
        key=SectionKey.PROGRAM_DETAILS,
        label_es="Detalles del programa",
        subtitle_es="Estructura, módulos y certificación",
        help_text_es=(
            "Cómo se desarrolla el programa: duración total (semanas/meses), carga "
            "horaria semanal esperada, módulos o temas cubiertos, tipo de interacción "
            "(autodirigido/grupal/1:1/híbrido), certificación al completar si aplica. "
            "Por cohorte específica (edition) se definen fechas de inicio/fin, cupos y "
            "el cronograma de sesiones en vivo."
        ),
        icon_name="Route",
        scope=SectionScope.MIXED,
        completion_weight=0.9,
        required_to_publish=True,
    ),
    SectionKey.SERVICE_DETAILS: SectionMetadata(
        key=SectionKey.SERVICE_DETAILS,
        label_es="Detalles del servicio",
        subtitle_es="Modalidad, alcance y entrega",
        help_text_es=(
            "Cómo trabajás con el cliente: modalidad (1:1, grupal, híbrido, asíncrono), "
            "frecuencia (semanal/quincenal/mensual), qué incluye el servicio (scope in) "
            "y qué NO incluye (scope out — crítico para evitar discusiones post-venta), "
            "tiempos de respuesta, canal principal (WhatsApp Business es estándar Latam B2B), "
            "si requiere firma de contrato."
        ),
        icon_name="Briefcase",
        scope=SectionScope.MIXED,
        completion_weight=0.9,
        required_to_publish=True,
    ),
    SectionKey.RESOURCES: SectionMetadata(
        key=SectionKey.RESOURCES,
        label_es="Materiales y recursos",
        subtitle_es="Plantillas, PDFs y accesos",
        help_text_es=(
            "Material descargable o accesos que el cliente recibe: plantillas, guías, "
            "grabaciones, accesos a herramientas. Separá los recursos base (incluidos "
            "siempre, offer-level) de los bonus específicos de una edición "
            "(edition-level: 'grabación exclusiva de la cohorte Q2')."
        ),
        icon_name="FileStack",
        scope=SectionScope.MIXED,
        completion_weight=0.6,
        required_to_publish=False,
    ),
    # ── Nuevas (Latam mass-market rollout) ────────────────────────────────
    SectionKey.FAQ: SectionMetadata(
        key=SectionKey.FAQ,
        label_es="Preguntas frecuentes",
        subtitle_es="Dudas comunes y sus respuestas",
        help_text_es=(
            "Preguntas frecuentes PÚBLICAS que se muestran en la landing y que el "
            "agente de ventas usa como primera línea de respuesta. Cubrí las categorías "
            "típicas Latam: Pagos (cuotas, métodos), Envíos (tiempos, cobertura), "
            "Devoluciones, Horarios de atención, Soporte post-compra. Diferente de la "
            "Base de conocimiento, que es interna del agente."
        ),
        icon_name="HelpCircle",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=0.6,
        required_to_publish=False,
    ),
    SectionKey.TESTIMONIALS: SectionMetadata(
        key=SectionKey.TESTIMONIALS,
        label_es="Testimonios y reseñas",
        subtitle_es="Clientes que ya compraron",
        help_text_es=(
            "Testimonios en texto, video o audio de clientes reales. Sumá país de cada "
            "testimonio — mezclar PE/MX/CO/AR da credibilidad regional. Para ofertas de "
            "transformación (fitness, salud estética, coaching), los pares antes/después "
            "convierten más que el texto. Si tenés Google My Business o Trustpilot, "
            "linkeá el perfil público para mostrar calificación agregada verificable."
        ),
        icon_name="Quote",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=0.7,
        required_to_publish=False,
    ),
    SectionKey.PORTFOLIO: SectionMetadata(
        key=SectionKey.PORTFOLIO,
        label_es="Casos de éxito",
        subtitle_es="Proyectos y resultados reales",
        help_text_es=(
            "Casos concretos trabajados: quién era el cliente, qué problema tenía, qué "
            "hiciste, qué resultado obtuvo. Los números duros mueven la aguja: 'Aumentamos "
            "ventas de X marca 320% en 6 meses'. Si tenés NDAs, usá 'Cliente en industria Y' "
            "en vez de nombre. Los logos de clientes atendidos suman trust por asociación."
        ),
        icon_name="Trophy",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=0.7,
        required_to_publish=False,
    ),
    SectionKey.LOCATION: SectionMetadata(
        key=SectionKey.LOCATION,
        label_es="Ubicación y reserva",
        subtitle_es="Dónde atendés y cómo agendar",
        help_text_es=(
            "Dirección(es) física(s), barrio/colonia (más importante que el código postal "
            "en Latam), horarios de atención, cómo llegar, estacionamiento, "
            "accesibilidad y — crítico — canales de reserva (WhatsApp es el "
            "dominante en Latam, seguido por teléfono y app propia). Para consultorios "
            "y negocios locales, esta sección es decisiva: si no se entiende cómo "
            "agendar, no hay venta."
        ),
        icon_name="MapPin",
        scope=SectionScope.MIXED,
        completion_weight=0.8,
        required_to_publish=True,
    ),
    SectionKey.PLATFORM_DETAILS: SectionMetadata(
        key=SectionKey.PLATFORM_DETAILS,
        label_es="Detalles de plataforma",
        subtitle_es="Features, integraciones y seguridad",
        help_text_es=(
            "Funcionalidades core del software por plan, integraciones con herramientas "
            "populares (Mercado Pago, WhatsApp Business API, Manychat, Stripe, Google "
            "Workspace), certificaciones de seguridad (SOC2, ISO 27001, LGPD Brasil, "
            "Habeas Data Colombia, LOPD Perú), residencia de datos, uptime SLA y "
            "canales de soporte. Específico de ofertas SaaS — para otros archetypes "
            "esta sección no aplica."
        ),
        icon_name="Cpu",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=0.9,
        required_to_publish=True,
    ),
}


def get_section(key: SectionKey) -> SectionMetadata:
    """Return the metadata record for ``key``.

    Raises ``KeyError`` when the catalog is missing an entry. Under the
    architecture test ``test_every_section_key_has_a_catalog_entry`` this
    branch cannot be reached at runtime — enum values and catalog keys are
    kept aligned by CI.
    """
    return SECTION_CATALOG[key]
