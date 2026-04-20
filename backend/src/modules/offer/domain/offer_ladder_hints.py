"""OfferLadderHints — per-business-type adaptation of the value ladder.

The value ladder (``OfferValueLevel``) is universal — every expert business
has Lead Magnet → Primera Compra → Oferta Principal → Oferta Premium →
Venta Corporativa. But the **language** changes per business type: a
dentist's "primera compra" is a promotional first consultation, a gym's
is a day-pass, a SaaS founder's is a starter plan.

This module declares those adaptive hints: per ``(ExpertBusinessType,
OfferValueLevel)`` pair, we record:

- ``examples_es`` — concrete offer examples the tenant will recognise.
- ``typical_offer_type_es`` — wizard placeholder ("¿qué tipo de primera
  compra vas a crear?" → "Primera consulta promocional").
- ``typical_price_min_usd`` / ``typical_price_max_usd`` — price range
  calibrated to the typical ticket for that business type at that rung.
  ``None`` means "use the universal fallback from ``VALUE_LEVEL_CATALOG``".

Architecture
~~~~~~~~~~~~

The module depends on both ``ExpertBusinessType`` (shared/domain) and
``OfferValueLevel`` (offer/domain). It is a composite catalog in the
offer-studio DAG — same category as ``OfferFormat`` which also depends
on two axes. ``VALUE_LEVEL_CATALOG`` stays pure-base: consuming the
hints is the **tenant's choice**, not a dependency of the ladder itself.

The wizard and dashboard call ``get_ladder_hint(business_type,
value_level)`` when a tenant has declared a primary ``business_types``;
otherwise they fall back to ``VALUE_LEVEL_CATALOG`` universals. The
frontend merges both via ``useLadderHint(businessType, valueLevel)``.

Invariants (arch-test-enforced)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Every ``(ExpertBusinessType, OfferValueLevel)`` pair has an entry
   (9 x 5 = 45). Missing entries fail CI.
2. No orphan entries (both keys must be valid enum members).
3. Every entry self-references its own keys.
4. Every entry declares ``examples_es`` non-empty and
   ``typical_offer_type_es`` non-empty.
5. Paid rungs (everything except ``LEAD_MAGNET``) must declare both
   prices, with ``min < max``. ``LEAD_MAGNET`` must have both ``None``
   (it is free in the universal catalog).
6. Per-type prices must be within ±10x of the universal VL range — a
   10x deviation is a signal that the rung is mis-classified.

See ``.claude/rules/offer-catalogs.md`` for the full DAG rules.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.modules.offer.domain.enums import OfferValueLevel
from src.shared.domain.expert_business_type import ExpertBusinessType


@dataclass(frozen=True, slots=True)
class LadderHint:
    """Frozen record describing one ``(ExpertBusinessType, OfferValueLevel)`` pair.

    All fields are derivable from the two keys alone — no tenant state,
    no external references. Changes bump ``_CATALOG_VERSION`` in
    ``api/offer_ladder_hints.py`` so clients evict cached copies.
    """

    business_type: ExpertBusinessType
    value_level: OfferValueLevel

    # Contextualised examples the tenant will recognise instantly.
    examples_es: tuple[str, ...]
    # One-liner used as wizard placeholder + dashboard chip.
    typical_offer_type_es: str
    # Per-type price range. ``None`` = use the universal VL fallback.
    typical_price_min_usd: float | None = None
    typical_price_max_usd: float | None = None


def _hint(
    business_type: ExpertBusinessType,
    value_level: OfferValueLevel,
    examples: tuple[str, ...],
    typical_offer_type: str,
    price_min: float | None = None,
    price_max: float | None = None,
) -> LadderHint:
    """Internal factory that keeps the catalog literal compact."""
    return LadderHint(
        business_type=business_type,
        value_level=value_level,
        examples_es=examples,
        typical_offer_type_es=typical_offer_type,
        typical_price_min_usd=price_min,
        typical_price_max_usd=price_max,
    )


_EBT = ExpertBusinessType
_VL = OfferValueLevel


OFFER_LADDER_HINTS: dict[tuple[ExpertBusinessType, OfferValueLevel], LadderHint] = {
    # ── PROFESIONAL_SALUD ───────────────────────────────────────────────
    (_EBT.PROFESIONAL_SALUD, _VL.LEAD_MAGNET): _hint(
        _EBT.PROFESIONAL_SALUD,
        _VL.LEAD_MAGNET,
        (
            "Consulta diagnóstica gratuita",
            "Masterclass de prevención",
            "Guía descargable (cuidados, nutrición)",
            "Screening express gratis",
        ),
        "Consulta diagnóstica gratuita",
    ),
    (_EBT.PROFESIONAL_SALUD, _VL.ACTIVACION): _hint(
        _EBT.PROFESIONAL_SALUD,
        _VL.ACTIVACION,
        (
            "Primera consulta promocional",
            "Evaluación inicial accesible",
            "Chequeo básico",
            "Mini-consulta online",
        ),
        "Primera consulta promocional",
        price_min=15.0,
        price_max=80.0,
    ),
    (_EBT.PROFESIONAL_SALUD, _VL.TRANSFORMACION): _hint(
        _EBT.PROFESIONAL_SALUD,
        _VL.TRANSFORMACION,
        (
            "Plan de tratamiento completo",
            "Paquete de 5-10 sesiones",
            "Programa de rehabilitación",
            "Ortodoncia base",
        ),
        "Plan de tratamiento",
        price_min=200.0,
        price_max=3000.0,
    ),
    (_EBT.PROFESIONAL_SALUD, _VL.MAXIMIZACION): _hint(
        _EBT.PROFESIONAL_SALUD,
        _VL.MAXIMIZACION,
        (
            "Implante premium",
            "Cirugía estética integral",
            "Programa personalizado VIP",
            "Tratamiento multi-especialidad",
        ),
        "Tratamiento premium",
        price_min=1500.0,
        price_max=15000.0,
    ),
    (_EBT.PROFESIONAL_SALUD, _VL.CORPORATIVO): _hint(
        _EBT.PROFESIONAL_SALUD,
        _VL.CORPORATIVO,
        (
            "Convenio con aseguradora",
            "Plan corporativo para empleados",
            "Programa de salud ocupacional",
            "Contrato con clínica partner",
        ),
        "Convenio institucional",
        price_min=5000.0,
        price_max=50000.0,
    ),
    # ── CONSULTOR_PROFESIONAL ───────────────────────────────────────────
    (_EBT.CONSULTOR_PROFESIONAL, _VL.LEAD_MAGNET): _hint(
        _EBT.CONSULTOR_PROFESIONAL,
        _VL.LEAD_MAGNET,
        (
            "Auditoría gratuita",
            "Diagnóstico inicial sin costo",
            "Webinar de valor",
            "Checklist descargable",
        ),
        "Diagnóstico gratis",
    ),
    (_EBT.CONSULTOR_PROFESIONAL, _VL.ACTIVACION): _hint(
        _EBT.CONSULTOR_PROFESIONAL,
        _VL.ACTIVACION,
        (
            "Revisión de documento",
            "Consulta puntual",
            "Workshop pagado",
            "Segunda opinión legal o financiera",
        ),
        "Consulta puntual",
        price_min=30.0,
        price_max=250.0,
    ),
    (_EBT.CONSULTOR_PROFESIONAL, _VL.TRANSFORMACION): _hint(
        _EBT.CONSULTOR_PROFESIONAL,
        _VL.TRANSFORMACION,
        (
            "Proyecto por scope",
            "Retainer mensual básico",
            "Asesoría integral",
            "Caso legal completo",
        ),
        "Proyecto / retainer",
        price_min=500.0,
        price_max=5000.0,
    ),
    (_EBT.CONSULTOR_PROFESIONAL, _VL.MAXIMIZACION): _hint(
        _EBT.CONSULTOR_PROFESIONAL,
        _VL.MAXIMIZACION,
        (
            "Retainer senior premium",
            "Consultoría ejecutiva",
            "Representación en alto perfil",
            "Estrategia C-level a medida",
        ),
        "Retainer senior",
        price_min=3000.0,
        price_max=25000.0,
    ),
    (_EBT.CONSULTOR_PROFESIONAL, _VL.CORPORATIVO): _hint(
        _EBT.CONSULTOR_PROFESIONAL,
        _VL.CORPORATIVO,
        (
            "Contrato anual con empresa",
            "Retainer corporativo",
            "Auditoría institucional",
            "Asesoría permanente staff legal",
        ),
        "Contrato empresa",
        price_min=10000.0,
        price_max=100000.0,
    ),
    # ── COACH_MENTOR ────────────────────────────────────────────────────
    (_EBT.COACH_MENTOR, _VL.LEAD_MAGNET): _hint(
        _EBT.COACH_MENTOR,
        _VL.LEAD_MAGNET,
        (
            "Webinar gratuito",
            "Workbook descargable",
            "Diagnóstico de situación",
            "Mini-curso por email",
        ),
        "Webinar gratis",
    ),
    (_EBT.COACH_MENTOR, _VL.ACTIVACION): _hint(
        _EBT.COACH_MENTOR,
        _VL.ACTIVACION,
        (
            "Masterclass pagada",
            "Mini-programa de 1-2 semanas",
            "Challenge pagado",
            "Workshop grabado",
        ),
        "Masterclass",
        price_min=27.0,
        price_max=197.0,
    ),
    (_EBT.COACH_MENTOR, _VL.TRANSFORMACION): _hint(
        _EBT.COACH_MENTOR,
        _VL.TRANSFORMACION,
        (
            "Programa de 3-6 meses",
            "Mentoría grupal",
            "Cohorte con acompañamiento",
            "Paquete de 10 sesiones",
        ),
        "Programa insignia",
        price_min=497.0,
        price_max=2997.0,
    ),
    (_EBT.COACH_MENTOR, _VL.MAXIMIZACION): _hint(
        _EBT.COACH_MENTOR,
        _VL.MAXIMIZACION,
        (
            "Mentoría 1:1 premium",
            "Mastermind exclusivo",
            "VIP Day intensivo",
            "Acompañamiento anual",
        ),
        "1:1 premium / mastermind",
        price_min=2500.0,
        price_max=20000.0,
    ),
    (_EBT.COACH_MENTOR, _VL.CORPORATIVO): _hint(
        _EBT.COACH_MENTOR,
        _VL.CORPORATIVO,
        (
            "Coaching a equipo ejecutivo",
            "Programa leadership in-company",
            "Facilitación de equipo interno",
            "Coaching al board",
        ),
        "Coaching corporativo",
        price_min=5000.0,
        price_max=50000.0,
    ),
    # ── ACADEMIA_INFOPRODUCTOR ──────────────────────────────────────────
    (_EBT.ACADEMIA_INFOPRODUCTOR, _VL.LEAD_MAGNET): _hint(
        _EBT.ACADEMIA_INFOPRODUCTOR,
        _VL.LEAD_MAGNET,
        (
            "Mini-curso gratis",
            "Webinar de valor",
            "Ebook / guía PDF",
            "Masterclass de apertura",
        ),
        "Mini-curso gratis",
    ),
    (_EBT.ACADEMIA_INFOPRODUCTOR, _VL.ACTIVACION): _hint(
        _EBT.ACADEMIA_INFOPRODUCTOR,
        _VL.ACTIVACION,
        (
            "Tripwire $9-47",
            "Curso corto económico",
            "Masterclass pagada",
            "Toolkit + comunidad",
        ),
        "Tripwire / curso corto",
        price_min=9.0,
        price_max=97.0,
    ),
    (_EBT.ACADEMIA_INFOPRODUCTOR, _VL.TRANSFORMACION): _hint(
        _EBT.ACADEMIA_INFOPRODUCTOR,
        _VL.TRANSFORMACION,
        (
            "Bootcamp / cohorte",
            "Curso insignia $297-997",
            "Certificación base",
            "Academia online anual",
        ),
        "Bootcamp / cohorte",
        price_min=297.0,
        price_max=1997.0,
    ),
    (_EBT.ACADEMIA_INFOPRODUCTOR, _VL.MAXIMIZACION): _hint(
        _EBT.ACADEMIA_INFOPRODUCTOR,
        _VL.MAXIMIZACION,
        (
            "Cohorte VIP con 1:1",
            "Mastermind de graduados",
            "Programa élite con mentores",
            "Certificación avanzada",
        ),
        "Mastermind élite",
        price_min=1500.0,
        price_max=10000.0,
    ),
    (_EBT.ACADEMIA_INFOPRODUCTOR, _VL.CORPORATIVO): _hint(
        _EBT.ACADEMIA_INFOPRODUCTOR,
        _VL.CORPORATIVO,
        (
            "Licenciamiento white-label",
            "Capacitación corporativa interna",
            "Academia para empresa",
            "Programa de upskilling staff",
        ),
        "Licencia corporativa",
        price_min=10000.0,
        price_max=100000.0,
    ),
    # ── ANFITRION_PRODUCTOR ─────────────────────────────────────────────
    (_EBT.ANFITRION_PRODUCTOR, _VL.LEAD_MAGNET): _hint(
        _EBT.ANFITRION_PRODUCTOR,
        _VL.LEAD_MAGNET,
        (
            "Evento preview gratis",
            "Workshop introductorio",
            "Newsletter de la comunidad",
            "Acceso trial 7 días",
        ),
        "Evento preview",
    ),
    (_EBT.ANFITRION_PRODUCTOR, _VL.ACTIVACION): _hint(
        _EBT.ANFITRION_PRODUCTOR,
        _VL.ACTIVACION,
        (
            "Entrada early-bird",
            "Pase de comunidad mensual",
            "Pase workshop",
            "Mini-experiencia intro",
        ),
        "Pase comunidad",
        price_min=10.0,
        price_max=80.0,
    ),
    (_EBT.ANFITRION_PRODUCTOR, _VL.TRANSFORMACION): _hint(
        _EBT.ANFITRION_PRODUCTOR,
        _VL.TRANSFORMACION,
        (
            "Entrada al evento principal",
            "Membresía comunidad anual",
            "Pase mastermind",
            "Retiro de fin de semana",
        ),
        "Evento principal / membresía",
        price_min=200.0,
        price_max=1500.0,
    ),
    (_EBT.ANFITRION_PRODUCTOR, _VL.MAXIMIZACION): _hint(
        _EBT.ANFITRION_PRODUCTOR,
        _VL.MAXIMIZACION,
        (
            "VIP ticket del evento",
            "Mastermind high-ticket",
            "Retiro inmersivo multi-día",
            "Inner Circle anual",
        ),
        "VIP ticket / retiro",
        price_min=1500.0,
        price_max=15000.0,
    ),
    (_EBT.ANFITRION_PRODUCTOR, _VL.CORPORATIVO): _hint(
        _EBT.ANFITRION_PRODUCTOR,
        _VL.CORPORATIVO,
        (
            "Sponsorship del evento",
            "Evento corporativo privado",
            "Retiro para empresa",
            "Entradas al por mayor B2B",
        ),
        "Sponsorship / evento corp",
        price_min=5000.0,
        price_max=50000.0,
    ),
    # ── AGENCIA_FREELANCE ───────────────────────────────────────────────
    (_EBT.AGENCIA_FREELANCE, _VL.LEAD_MAGNET): _hint(
        _EBT.AGENCIA_FREELANCE,
        _VL.LEAD_MAGNET,
        (
            "Auditoría gratuita",
            "Diagnóstico + propuesta",
            "Plantilla / toolkit",
            "Masterclass de servicios",
        ),
        "Auditoría gratis",
    ),
    (_EBT.AGENCIA_FREELANCE, _VL.ACTIVACION): _hint(
        _EBT.AGENCIA_FREELANCE,
        _VL.ACTIVACION,
        (
            "Mini-proyecto pagado",
            "Auditoría premium",
            "Workshop para equipo",
            "Paquete de horas inicial",
        ),
        "Mini-proyecto",
        price_min=200.0,
        price_max=500.0,
    ),
    (_EBT.AGENCIA_FREELANCE, _VL.TRANSFORMACION): _hint(
        _EBT.AGENCIA_FREELANCE,
        _VL.TRANSFORMACION,
        (
            "Proyecto core (web, campaña, video)",
            "Rebranding completo",
            "Campaña de lanzamiento",
            "Desarrollo de producto digital",
        ),
        "Proyecto core",
        price_min=1500.0,
        price_max=10000.0,
    ),
    (_EBT.AGENCIA_FREELANCE, _VL.MAXIMIZACION): _hint(
        _EBT.AGENCIA_FREELANCE,
        _VL.MAXIMIZACION,
        (
            "Retainer senior mensual",
            "Programa anual integrado",
            "Fractional CMO / CFO",
            "Partner estratégico continuo",
        ),
        "Retainer senior",
        price_min=3000.0,
        price_max=20000.0,
    ),
    (_EBT.AGENCIA_FREELANCE, _VL.CORPORATIVO): _hint(
        _EBT.AGENCIA_FREELANCE,
        _VL.CORPORATIVO,
        (
            "Retainer enterprise",
            "Contrato multi-proyecto",
            "Cuenta corporativa dedicada",
            "Socio de ejecución de empresa",
        ),
        "Enterprise retainer",
        price_min=10000.0,
        price_max=100000.0,
    ),
    # ── MARCA_ECOMMERCE ─────────────────────────────────────────────────
    (_EBT.MARCA_ECOMMERCE, _VL.LEAD_MAGNET): _hint(
        _EBT.MARCA_ECOMMERCE,
        _VL.LEAD_MAGNET,
        (
            "Cupón primer pedido",
            "Muestra gratis",
            "Guía descargable",
            "Masterclass de uso del producto",
        ),
        "Cupón / muestra",
    ),
    (_EBT.MARCA_ECOMMERCE, _VL.ACTIVACION): _hint(
        _EBT.MARCA_ECOMMERCE,
        _VL.ACTIVACION,
        (
            "Producto entry $9-47",
            "Kit mini / sample box",
            "Descuento primera compra",
            "Bundle económico",
        ),
        "Producto entry",
        price_min=9.0,
        price_max=47.0,
    ),
    (_EBT.MARCA_ECOMMERCE, _VL.TRANSFORMACION): _hint(
        _EBT.MARCA_ECOMMERCE,
        _VL.TRANSFORMACION,
        (
            "Producto core del catálogo",
            "Bundle curado",
            "Reposición mensual / suscripción",
            "Línea completa",
        ),
        "Producto core",
        price_min=50.0,
        price_max=500.0,
    ),
    (_EBT.MARCA_ECOMMERCE, _VL.MAXIMIZACION): _hint(
        _EBT.MARCA_ECOMMERCE,
        _VL.MAXIMIZACION,
        (
            "Edición limitada",
            "Bundle premium / pack exclusivo",
            "Membresía VIP del producto",
            "Box coleccionista",
        ),
        "Edición limitada",
        price_min=200.0,
        price_max=2000.0,
    ),
    (_EBT.MARCA_ECOMMERCE, _VL.CORPORATIVO): _hint(
        _EBT.MARCA_ECOMMERCE,
        _VL.CORPORATIVO,
        (
            "Venta al por mayor",
            "Distribución B2B",
            "Catálogo corporativo",
            "White label a otras marcas",
        ),
        "Wholesale / distribución",
        price_min=3000.0,
        price_max=50000.0,
    ),
    # ── NEGOCIO_LOCAL ───────────────────────────────────────────────────
    (_EBT.NEGOCIO_LOCAL, _VL.LEAD_MAGNET): _hint(
        _EBT.NEGOCIO_LOCAL,
        _VL.LEAD_MAGNET,
        (
            "Clase prueba gratis",
            "Día gratis / pase trial",
            "Diagnóstico corporal gratuito",
            "Promoción de apertura",
        ),
        "Clase prueba",
    ),
    (_EBT.NEGOCIO_LOCAL, _VL.ACTIVACION): _hint(
        _EBT.NEGOCIO_LOCAL,
        _VL.ACTIVACION,
        (
            "Pase de día / semana",
            "Paquete mini entrada",
            "Mini-clase pagada",
            "Sesión express",
        ),
        "Pase día / semana",
        price_min=10.0,
        price_max=40.0,
    ),
    (_EBT.NEGOCIO_LOCAL, _VL.TRANSFORMACION): _hint(
        _EBT.NEGOCIO_LOCAL,
        _VL.TRANSFORMACION,
        (
            "Membresía mensual",
            "Paquete 10 clases / sesiones",
            "Plan trimestral",
            "Abono regular",
        ),
        "Membresía mensual",
        price_min=40.0,
        price_max=200.0,
    ),
    (_EBT.NEGOCIO_LOCAL, _VL.MAXIMIZACION): _hint(
        _EBT.NEGOCIO_LOCAL,
        _VL.MAXIMIZACION,
        (
            "Personal training VIP",
            "Plan transformación 12 semanas",
            "Programa premium con seguimiento",
            "Servicio boutique a medida",
        ),
        "Plan VIP",
        price_min=500.0,
        price_max=5000.0,
    ),
    (_EBT.NEGOCIO_LOCAL, _VL.CORPORATIVO): _hint(
        _EBT.NEGOCIO_LOCAL,
        _VL.CORPORATIVO,
        (
            "Convenio corporativo empleados",
            "Programa wellness para empresa",
            "Contrato de capacitación staff",
            "Plan descuento B2B",
        ),
        "Convenio corporativo",
        price_min=3000.0,
        price_max=30000.0,
    ),
    # ── SOFTWARE_SAAS ───────────────────────────────────────────────────
    (_EBT.SOFTWARE_SAAS, _VL.LEAD_MAGNET): _hint(
        _EBT.SOFTWARE_SAAS,
        _VL.LEAD_MAGNET,
        (
            "Free tier permanente",
            "Trial 14 días",
            "Plan freemium limitado",
            "Demo interactiva",
        ),
        "Free tier",
    ),
    (_EBT.SOFTWARE_SAAS, _VL.ACTIVACION): _hint(
        _EBT.SOFTWARE_SAAS,
        _VL.ACTIVACION,
        (
            "Starter plan $9-29/mes",
            "Plan individual básico",
            "Pack anual con descuento",
            "Plan estudiante",
        ),
        "Starter plan",
        price_min=9.0,
        price_max=29.0,
    ),
    (_EBT.SOFTWARE_SAAS, _VL.TRANSFORMACION): _hint(
        _EBT.SOFTWARE_SAAS,
        _VL.TRANSFORMACION,
        (
            "Pro plan $49-199/mes",
            "Plan equipo pequeño",
            "Suscripción anual completa",
            "Plan agencia",
        ),
        "Pro plan",
        price_min=29.0,
        price_max=299.0,
    ),
    (_EBT.SOFTWARE_SAAS, _VL.MAXIMIZACION): _hint(
        _EBT.SOFTWARE_SAAS,
        _VL.MAXIMIZACION,
        (
            "Business plan $299-999/mes",
            "Plan Growth con soporte premium",
            "Custom features + SLA",
            "Plan con dedicated CSM",
        ),
        "Business plan",
        price_min=299.0,
        price_max=999.0,
    ),
    (_EBT.SOFTWARE_SAAS, _VL.CORPORATIVO): _hint(
        _EBT.SOFTWARE_SAAS,
        _VL.CORPORATIVO,
        (
            "Enterprise plan $1000+/mes",
            "Contrato anual multi-seat",
            "White label / custom deploy",
            "Deploy on-premise",
        ),
        "Enterprise plan",
        price_min=1000.0,
        price_max=20000.0,
    ),
}


def get_ladder_hint(
    business_type: ExpertBusinessType,
    value_level: OfferValueLevel,
) -> LadderHint:
    """Return the hint for a ``(business_type, value_level)`` pair.

    The architecture test
    ``test_offer_ladder_hints_completeness`` guarantees every (EBT x VL)
    pair has an entry, so at runtime this lookup cannot raise.
    """
    return OFFER_LADDER_HINTS[(business_type, value_level)]


def get_ladder_hints_for_type(
    business_type: ExpertBusinessType,
) -> dict[OfferValueLevel, LadderHint]:
    """Return every hint for one business type, keyed by value level."""
    return {value_level: hint for (bt, value_level), hint in OFFER_LADDER_HINTS.items() if bt is business_type}
