"""Offer Type Preset Catalog — 7th SSoT axis of the offer-studio system.

This catalog solves the "which archetype is this?" ambiguity microempresarios
face in the wizard. A nutricionist selling "consulta médica" could be
modeled as SERVICIO (one-shot), PROGRAMA (multi-session treatment) or
MEMBRESIA (continuous monitoring plan). Forcing the user to pick an
archetype is marketer jargon — instead we surface **presets** in the
user's own vocabulary, filtered by their declared ``business_types``, and
the archetype becomes an internal tag derived from the preset.

Architecture
~~~~~~~~~~~~

``OfferTypePreset`` is a composite record keyed by a stable ``preset_id``
and depending on three base axes plus one intermediate axis:

- ``business_type: ExpertBusinessType``  (who sells it)
- ``archetype: OfferArchetype``          (internal fulfillment model)
- ``base_sections: tuple[SectionKey]``   (editor sections always visible)
- ``conditional_question_ids``           (which Q's refine the section set)

Per ``.claude/rules/offer-catalogs.md``, this is the **7th catalog** in
the offer-studio DAG, sitting alongside ``OfferFormat`` and
``OfferLadderHints`` as a composite that depends on multiple upstream
axes. It does not introduce new base axes — it only composes them.

Runtime flow
~~~~~~~~~~~~

1. The wizard reads the tenant's ``business_types`` from Brand Studio.
2. ``get_presets_for_business_types(...)`` returns filtered presets.
3. The user picks a preset in their language ("Consulta única").
4. The wizard asks the preset's ``conditional_question_ids`` (3-5 Q's).
5. ``resolve_preset_sections(preset_id, answers)`` produces the final
   ordered section tuple the editor renders.
6. Backend persists ``Offer.preset_id`` alongside ``Offer.archetype`` so
   analytics, sales-agent grounding and landing generators can
   segment by either axis.

Invariants (arch-test-enforced)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. ``preset_id`` is snake_case, globally unique, prefixed by
   business_type slug (e.g. ``salud_consulta_unica``).
2. Every ``ExpertBusinessType`` has >= 3 presets.
3. Every preset self-references a valid ``business_type`` + ``archetype``
   pair consistent with ``archetype_catalog.ARCHETYPE_CATALOG`` (i.e. the
   archetype must exist in the catalog).
4. Every section in ``base_sections`` exists in ``SECTION_CATALOG``.
5. Every ``conditional_question_id`` references an entry in
   ``QUESTION_REGISTRY``.
6. ``base_sections`` covers at least IDENTITY + PROMISE + PRICING +
   CLOSING (the universal minimum a Latam oferta needs to be sellable).
7. Lead magnets (``IS_LEAD_MAGNET`` flag in ``default_flags``) must NOT
   include ``SectionKey.PRICING`` — they're free by definition.
8. ``examples_es`` is non-empty and has >= 2 entries so the user
   recognises the preset instantly.

See ``tests/architecture/test_offer_type_preset_catalog_completeness.py``
for the full gate list.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from src.modules.offer.domain.enums import OfferArchetype, OfferValueLevel, VariantStructure
from src.modules.offer.domain.section_catalog import SectionKey
from src.shared.domain.expert_business_type import ExpertBusinessType


class PresetFlag(StrEnum):
    """Composable flags toggled by conditional questions or declared by default.

    Flags are semantic signals downstream consumers (arch checks,
    wizard, landing generator, sales agent) read to specialize behavior
    without hard-coding preset-by-preset logic.
    """

    SUPPORTS_CAPACITY = "supports_capacity"
    REQUIRES_START_DATE = "requires_start_date"
    DELIVERY_HYBRID = "delivery_hybrid"
    IS_LEAD_MAGNET = "is_lead_magnet"
    RECURRING_BILLING = "recurring_billing"
    HIGH_TICKET = "high_ticket"


@dataclass(frozen=True, slots=True)
class ConditionalQuestion:
    """A binary refinement question rendered after preset selection.

    ``on_yes_sections`` are added to the preset's ``base_sections`` when
    the user answers YES. Order of addition is stable — duplicates are
    de-duplicated preserving the base_sections ordering first.
    """

    question_id: str
    question_es: str
    help_es: str
    on_yes_sections: tuple[SectionKey, ...] = ()
    on_yes_flags: tuple[PresetFlag, ...] = ()


QUESTION_REGISTRY: dict[str, ConditionalQuestion] = {
    "requires_physical_location": ConditionalQuestion(
        question_id="requires_physical_location",
        question_es="¿Requiere que el cliente esté físicamente en un lugar?",
        help_es=(
            "Si atiendes en un consultorio, estudio, tienda, gimnasio o salón. "
            "Las ofertas 100% online no necesitan esta sección."
        ),
        on_yes_sections=(SectionKey.LOCATION,),
    ),
    "has_specific_dates": ConditionalQuestion(
        question_id="has_specific_dates",
        question_es="¿Tiene fechas específicas de inicio o de evento?",
        help_es=(
            "Una cohorte empieza el 1 de junio, un retiro es el 15-18. Las "
            "ofertas evergreen (siempre disponibles) no tienen fechas fijas."
        ),
        on_yes_sections=(SectionKey.EVENT_DETAILS,),
        on_yes_flags=(PresetFlag.REQUIRES_START_DATE,),
    ),
    "delivers_downloadable_materials": ConditionalQuestion(
        question_id="delivers_downloadable_materials",
        question_es="¿Entregás materiales descargables o accesos extras?",
        help_es=(
            "PDFs, plantillas, grabaciones, logins a herramientas o comunidades. "
            "Separate de los entregables principales — son bonus o recursos."
        ),
        on_yes_sections=(SectionKey.RESOURCES,),
    ),
    "has_team_or_speakers": ConditionalQuestion(
        question_id="has_team_or_speakers",
        question_es="¿Hay un equipo o lineup de instructores involucrado?",
        help_es=(
            "Tú + 2 coaches invitados, un panel de speakers para un summit, o el staff médico para un procedimiento."
        ),
        on_yes_sections=(SectionKey.INSTRUCTORS,),
    ),
    "is_hybrid_modality": ConditionalQuestion(
        question_id="is_hybrid_modality",
        question_es="¿Es híbrido (presencial + online combinados)?",
        help_es=(
            "Clases presenciales con grabaciones disponibles, o consultas que "
            "pueden ser virtuales u on-site según el cliente."
        ),
        on_yes_sections=(SectionKey.LOCATION,),
        on_yes_flags=(PresetFlag.DELIVERY_HYBRID,),
    ),
    "has_limited_capacity": ConditionalQuestion(
        question_id="has_limited_capacity",
        question_es="¿Hay cupos limitados o capacidad máxima?",
        help_es=(
            "Un retiro tiene 20 lugares, un bootcamp 50, un workshop 30. "
            "Escasez real activa lista de espera y urgencia honesta."
        ),
        on_yes_flags=(PresetFlag.SUPPORTS_CAPACITY,),
    ),
    "has_portfolio_cases": ConditionalQuestion(
        question_id="has_portfolio_cases",
        question_es="¿Puedes mostrar casos de éxito o proyectos previos?",
        help_es=(
            "Agencias y consultores venden con portfolio. Coaches con métricas "
            "de transformación de clientes. Salud con antes/después."
        ),
        on_yes_sections=(SectionKey.PORTFOLIO,),
    ),
}


@dataclass(frozen=True, slots=True)
class OfferTypePreset:
    """A user-facing offer template for a specific ExpertBusinessType.

    The wizard renders ``label_es`` + ``description_es`` + ``icon_name`` on
    the preset picker grid. ``examples_es`` surface as chips on the card.
    When the user selects a preset, the wizard enters the
    ``conditional_question_ids`` flow; on completion it persists the
    preset_id and derived section set to the Offer row.
    """

    preset_id: str
    business_type: ExpertBusinessType
    archetype: OfferArchetype
    label_es: str
    description_es: str
    icon_name: str
    base_sections: tuple[SectionKey, ...]
    # Sprint 15 — typical ladder rung this preset occupies. Promoted from
    # the wizard's 2nd step into the catalog so the wizard can derive the
    # value level from the preset choice (microempresario picks "qué
    # vendo", not "en qué rung"). Invariants: if ``IS_LEAD_MAGNET`` is in
    # ``default_flags`` this MUST be ``LEAD_MAGNET``; otherwise MUST NOT.
    # Enforced by ``test_preset_typical_value_level_alignment``.
    typical_value_level: OfferValueLevel = OfferValueLevel.ACTIVACION
    conditional_question_ids: tuple[str, ...] = ()
    default_flags: tuple[PresetFlag, ...] = ()
    suitability_note_es: str = ""
    examples_es: tuple[str, ...] = field(default_factory=tuple)
    # Sprint 15.1 — optional override of the archetype's
    # ``default_variant_structure``. Presets that model a specific variant
    # shape (e.g. ``consultor_retainer`` forcing ``TIER`` even though
    # SERVICIO defaults to ``RECURRING_INTAKE``) set this field; every other
    # preset leaves it ``None`` to inherit the archetype default.
    #
    # Invariants (enforced by
    # ``test_preset_default_variant_structure_valid``):
    #   - if non-None, the value MUST appear in the parent archetype's
    #     ``supported_variant_structures`` tuple.
    #   - if the archetype does NOT ``supports_editions``, this MUST stay
    #     None.
    default_variant_structure: VariantStructure | None = None


# ── Section tuple helpers (readable shorthands) ─────────────────────────────
# Not constants — each preset still declares its full tuple to keep arch tests
# honest. These are used inline below to prevent typos, never reassigned.
SK = SectionKey


def _base_servicio() -> tuple[SectionKey, ...]:
    """Default section skeleton for SERVICIO archetype presets.

    Includes: identity/strategy/psychology/promise (universal),
    service_details + instructors, value_stack, pricing/closing/knowledge,
    faq/testimonials, gallery.
    """
    return (
        SK.IDENTITY,
        SK.STRATEGY,
        SK.PSYCHOLOGY,
        SK.PROMISE,
        SK.SERVICE_DETAILS,
        SK.INSTRUCTORS,
        SK.VALUE_STACK,
        SK.PRICING,
        SK.CLOSING,
        SK.KNOWLEDGE,
        SK.FAQ,
        SK.TESTIMONIALS,
        SK.GALLERY,
    )


def _base_programa() -> tuple[SectionKey, ...]:
    """Default section skeleton for PROGRAMA archetype presets."""
    return (
        SK.IDENTITY,
        SK.STRATEGY,
        SK.PSYCHOLOGY,
        SK.PROMISE,
        SK.PROGRAM_DETAILS,
        SK.INSTRUCTORS,
        SK.VALUE_STACK,
        SK.PRICING,
        SK.CLOSING,
        SK.KNOWLEDGE,
        SK.FAQ,
        SK.TESTIMONIALS,
        SK.GALLERY,
        SK.RESOURCES,
    )


def _base_membresia() -> tuple[SectionKey, ...]:
    """Default section skeleton for MEMBRESIA archetype presets."""
    return (
        SK.IDENTITY,
        SK.STRATEGY,
        SK.PSYCHOLOGY,
        SK.PROMISE,
        SK.SUBSCRIPTION_DETAILS,
        SK.INSTRUCTORS,
        SK.VALUE_STACK,
        SK.PRICING,
        SK.CLOSING,
        SK.KNOWLEDGE,
        SK.FAQ,
        SK.TESTIMONIALS,
        SK.GALLERY,
    )


def _base_producto() -> tuple[SectionKey, ...]:
    """Default section skeleton for PRODUCTO archetype presets."""
    return (
        SK.IDENTITY,
        SK.STRATEGY,
        SK.PSYCHOLOGY,
        SK.PROMISE,
        SK.PRODUCT_DETAILS,
        SK.VALUE_STACK,
        SK.PRICING,
        SK.CLOSING,
        SK.KNOWLEDGE,
        SK.FAQ,
        SK.TESTIMONIALS,
        SK.GALLERY,
    )


def _base_experiencia() -> tuple[SectionKey, ...]:
    """Default section skeleton for EXPERIENCIA archetype presets."""
    return (
        SK.IDENTITY,
        SK.STRATEGY,
        SK.PSYCHOLOGY,
        SK.PROMISE,
        SK.EVENT_DETAILS,
        SK.LOCATION,
        SK.INSTRUCTORS,
        SK.VALUE_STACK,
        SK.PRICING,
        SK.CLOSING,
        SK.KNOWLEDGE,
        SK.FAQ,
        SK.TESTIMONIALS,
        SK.GALLERY,
    )


_EBT = ExpertBusinessType
_A = OfferArchetype


OFFER_TYPE_PRESET_CATALOG: dict[str, OfferTypePreset] = {
    # ────────────────────────────────────────────────────────────────────────
    # 1. PROFESIONAL_SALUD (8 presets)
    # ────────────────────────────────────────────────────────────────────────
    "salud_consulta_unica": OfferTypePreset(
        preset_id="salud_consulta_unica",
        business_type=_EBT.PROFESIONAL_SALUD,
        archetype=_A.SERVICIO,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Consulta única",
        description_es=(
            "Atención profesional puntual — primera visita, evaluación o "
            "consulta de segunda opinión. Un solo encuentro con valor propio."
        ),
        icon_name="Stethoscope",
        base_sections=(*_base_servicio(), SK.LOCATION),
        conditional_question_ids=("is_hybrid_modality",),
        suitability_note_es=(
            "Declará obras sociales (AR/CO), EPS (CO), Seguro Social (PE) o "
            "seguros aceptados en PRICING. WhatsApp es el canal dominante de reserva."
        ),
        examples_es=(
            "Primera consulta odontológica",
            "Evaluación nutricional inicial",
            "Sesión de psicología online",
            "Consulta de segunda opinión médica",
            "Control veterinario de rutina",
        ),
    ),
    "salud_paquete_tratamiento": OfferTypePreset(
        preset_id="salud_paquete_tratamiento",
        business_type=_EBT.PROFESIONAL_SALUD,
        archetype=_A.PROGRAMA,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Paquete de tratamiento",
        description_es=(
            "Conjunto de sesiones con un objetivo clínico común — "
            "blanqueamiento, kinesiología, tratamiento estético, "
            "terapia breve. Se cobra anticipado por el paquete completo."
        ),
        icon_name="SquareStack",
        base_sections=(*_base_programa(), SK.LOCATION, SK.PORTFOLIO),
        conditional_question_ids=("is_hybrid_modality", "has_limited_capacity"),
        suitability_note_es=(
            "Cuotas sin interés decisivas en paquetes > USD 300. Documentá "
            "qué incluye cada sesión en PROGRAM_DETAILS para evitar disputas."
        ),
        examples_es=(
            "Blanqueamiento dental (4 sesiones)",
            "Paquete kinesiología post-quirúrgica (10 sesiones)",
            "Plan nutricional 3 meses",
            "Terapia breve de ansiedad (12 sesiones)",
            "Tratamiento facial completo",
        ),
    ),
    "salud_plan_seguimiento": OfferTypePreset(
        preset_id="salud_plan_seguimiento",
        business_type=_EBT.PROFESIONAL_SALUD,
        archetype=_A.MEMBRESIA,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Plan de seguimiento continuo",
        description_es=(
            "Suscripción mensual o anual que incluye consultas periódicas, "
            "chat con el profesional y seguimiento de indicadores. Para "
            "pacientes crónicos o transformaciones largas."
        ),
        icon_name="CalendarHeart",
        base_sections=(*_base_membresia(), SK.LOCATION),
        conditional_question_ids=(
            "requires_physical_location",
            "delivers_downloadable_materials",
        ),
        default_flags=(PresetFlag.RECURRING_BILLING,),
        suitability_note_es=(
            "Aclará política de cancelación y renovación automática en "
            "SUBSCRIPTION_DETAILS — en Latam la desconfianza por cargos "
            "recurrentes es alta. Permití pausas por vacaciones."
        ),
        examples_es=(
            "Plan nutricional anual con controles mensuales",
            "Membresía salud mental (4 sesiones/mes + chat)",
            "Seguimiento post-cirugía anual",
            "Plan wellness familiar",
        ),
    ),
    "salud_cirugia_procedimiento": OfferTypePreset(
        preset_id="salud_cirugia_procedimiento",
        business_type=_EBT.PROFESIONAL_SALUD,
        archetype=_A.SERVICIO,
        typical_value_level=OfferValueLevel.MAXIMIZACION,
        label_es="Cirugía / procedimiento mayor",
        description_es=(
            "Intervención única de alto ticket con pre-consulta, ejecución y "
            "seguimiento post-operatorio. Requiere casos previos fotográficos "
            "o documentados."
        ),
        icon_name="Scissors",
        base_sections=(*_base_servicio(), SK.LOCATION, SK.PORTFOLIO),
        conditional_question_ids=("has_team_or_speakers", "has_limited_capacity"),
        default_flags=(PresetFlag.HIGH_TICKET,),
        suitability_note_es=(
            "Financiación es el make-or-break — cuotas 12+ meses son normales "
            "en cirugía estética Latam. Documentá riesgos y garantías con "
            "cuidado: evitá promesas médicas irrealistas."
        ),
        examples_es=(
            "Rinoplastia",
            "Implantes dentales (boca completa)",
            "Cirugía refractiva LASIK",
            "Mamoplastia de aumento",
            "Lipoescultura",
        ),
    ),
    "salud_curso_colegas": OfferTypePreset(
        preset_id="salud_curso_colegas",
        business_type=_EBT.PROFESIONAL_SALUD,
        archetype=_A.PROGRAMA,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Curso para otros profesionales",
        description_es=(
            "Capacitación B2B dirigida a colegas del rubro — técnicas, "
            "actualización profesional, certificaciones internas. Vivo o "
            "cohortes con entrega de certificado."
        ),
        icon_name="GraduationCap",
        base_sections=(*_base_programa(), SK.PORTFOLIO),
        conditional_question_ids=(
            "requires_physical_location",
            "has_specific_dates",
            "is_hybrid_modality",
        ),
        suitability_note_es=(
            "Factura B2B en Latam requiere razón social del asistente. "
            "Validar con colegio profesional si el certificado cuenta como "
            "crédito continuado."
        ),
        examples_es=(
            "Workshop técnicas de sutura",
            "Actualización farmacológica anual",
            "Certificación en odontología digital",
            "Curso de acupuntura para kinesiólogos",
        ),
    ),
    "salud_retiro_taller": OfferTypePreset(
        preset_id="salud_retiro_taller",
        business_type=_EBT.PROFESIONAL_SALUD,
        archetype=_A.EXPERIENCIA,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Retiro o taller de salud",
        description_es=(
            "Experiencia grupal inmersiva con fecha específica — yoga "
            "terapéutico, meditación guiada, retiro de mindfulness. "
            "Conecta salud mental y física en un formato evento."
        ),
        icon_name="Flower2",
        base_sections=(*_base_experiencia(), SK.PORTFOLIO, SK.RESOURCES),
        conditional_question_ids=("has_limited_capacity", "has_team_or_speakers"),
        suitability_note_es=(
            "Alojamiento incluido vs no es la diferencia decisiva en Latam. "
            "Si son múltiples salidas, usa Variant TEMPORAL_SINGLE_DATE."
        ),
        examples_es=(
            "Retiro de yoga terapéutico 3 días",
            "Taller de meditación y sueño",
            "Detox nutricional 5 días",
            "Encuentro de mindfulness familiar",
        ),
    ),
    "salud_guia_digital": OfferTypePreset(
        preset_id="salud_guia_digital",
        business_type=_EBT.PROFESIONAL_SALUD,
        archetype=_A.PRODUCTO,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Guía o plan digital",
        description_es=(
            "Material descargable de bajo ticket — meal plan, rutina de "
            "ejercicios, guía de prevención. Lead magnet o tripwire para "
            "escalar hacia consultas."
        ),
        icon_name="FileText",
        base_sections=_base_producto(),
        conditional_question_ids=("delivers_downloadable_materials",),
        suitability_note_es=(
            "Excelente para capturar leads de alta calidad. Linkear al final "
            "de la guía a una consulta inicial descontada convierte 5-10%."
        ),
        examples_es=(
            "Meal plan 4 semanas PDF",
            "Guía ejercicios post-parto",
            "Plan de sueño infantil descargable",
            "Calendario de vacunación veterinario",
        ),
    ),
    "salud_corporativo_wellness": OfferTypePreset(
        preset_id="salud_corporativo_wellness",
        business_type=_EBT.PROFESIONAL_SALUD,
        archetype=_A.MEMBRESIA,
        typical_value_level=OfferValueLevel.CORPORATIVO,
        label_es="Convenio de bienestar empresarial",
        description_es=(
            "Plan de salud o bienestar contratado por una empresa para sus "
            "empleados — chequeos, consultas grupales, talleres en sitio. "
            "Cobro mensual o anual a la organización."
        ),
        icon_name="Building2",
        base_sections=(*_base_membresia(), SK.LOCATION, SK.PORTFOLIO),
        conditional_question_ids=(
            "requires_physical_location",
            "has_team_or_speakers",
        ),
        default_flags=(PresetFlag.RECURRING_BILLING,),
        suitability_note_es=(
            "Decisor es RR.HH. o área de beneficios. Cotización formal a "
            "razón social + reporte trimestral de uso sostienen el contrato. "
            "Mínimo N empleados activos justifica el precio."
        ),
        examples_es=(
            "Plan chequeos anuales empresa 100+ empleados",
            "Convenio salud mental corporativo",
            "Programa wellness in-company trimestral",
            "Atención médica ocupacional",
        ),
    ),
    # ────────────────────────────────────────────────────────────────────────
    # 2. CONSULTOR_PROFESIONAL (9 presets)
    # ────────────────────────────────────────────────────────────────────────
    "consultor_consulta_puntual": OfferTypePreset(
        preset_id="consultor_consulta_puntual",
        business_type=_EBT.CONSULTOR_PROFESIONAL,
        archetype=_A.SERVICIO,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Consulta puntual",
        description_es=(
            "Asesoría de una hora sobre un tema específico — revisión de "
            "contrato, diagnóstico fiscal, segunda opinión estratégica. "
            "Cierre rápido, sin compromiso largo."
        ),
        icon_name="MessageCircle",
        base_sections=(*_base_servicio(), SK.PORTFOLIO),
        conditional_question_ids=("is_hybrid_modality", "requires_physical_location"),
        suitability_note_es=(
            "WhatsApp Business es el canal B2B dominante Latam. Factura a "
            "nombre de la empresa del cliente (RFC/CUIT/RUC) es crítica."
        ),
        examples_es=(
            "Consulta legal 1h",
            "Diagnóstico fiscal express",
            "Asesoría financiera puntual",
            "Revisión de contrato comercial",
            "Segunda opinión estratégica",
        ),
    ),
    "consultor_proyecto_scope": OfferTypePreset(
        preset_id="consultor_proyecto_scope",
        business_type=_EBT.CONSULTOR_PROFESIONAL,
        archetype=_A.SERVICIO,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Proyecto por scope",
        description_es=(
            "Trabajo con inicio, entregables claros y fin — caso laboral "
            "completo, declaración anual, diseño de plan de negocio, "
            "auditoría. Scope-in/out decisivo para evitar discusiones."
        ),
        icon_name="FolderKanban",
        base_sections=(*_base_servicio(), SK.PORTFOLIO),
        conditional_question_ids=(
            "has_specific_dates",
            "has_team_or_speakers",
            "delivers_downloadable_materials",
        ),
        suitability_note_es=(
            "Definí scope-in y scope-out con brutal claridad en "
            "SERVICE_DETAILS. 'Incluye X, Y, Z. NO incluye A, B, C.' "
            "Cotización por hitos vs fee fijo depende de complejidad."
        ),
        examples_es=(
            "Defensa laboral completa (caso)",
            "Declaración de impuestos anual empresa",
            "Plan de negocio 90 días",
            "Auditoría de sistemas",
            "Diseño arquitectónico vivienda",
        ),
    ),
    "consultor_retainer": OfferTypePreset(
        preset_id="consultor_retainer",
        business_type=_EBT.CONSULTOR_PROFESIONAL,
        archetype=_A.MEMBRESIA,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Retainer mensual",
        description_es=(
            "Honorarios mensuales por disponibilidad continua — contador "
            "PYMES, abogado de confianza, asesor financiero recurrente. "
            "Cliente tiene acceso cotidiano dentro del scope mensual."
        ),
        icon_name="Repeat",
        base_sections=(*_base_membresia(), SK.PORTFOLIO),
        conditional_question_ids=("delivers_downloadable_materials",),
        default_flags=(PresetFlag.RECURRING_BILLING,),
        suitability_note_es=(
            "Horas máximas/mes y fuera-de-alcance deben estar en "
            "SUBSCRIPTION_DETAILS. Comunicación asíncrona WhatsApp/email "
            "es estándar Latam B2B."
        ),
        examples_es=(
            "Contador PYMES retainer",
            "Abogado corporativo retainer",
            "Asesor financiero familiar mensual",
            "Consultor de marketing digital mensual",
        ),
    ),
    "consultor_programa_transformacion": OfferTypePreset(
        preset_id="consultor_programa_transformacion",
        business_type=_EBT.CONSULTOR_PROFESIONAL,
        archetype=_A.PROGRAMA,
        typical_value_level=OfferValueLevel.MAXIMIZACION,
        label_es="Programa largo de transformación",
        description_es=(
            "Proceso de 6-12 meses con hitos — plan financiero personal, "
            "transformación empresarial, reestructuración patrimonial. "
            "Mezcla de consultas + documentos + seguimiento."
        ),
        icon_name="TrendingUp",
        base_sections=(*_base_programa(), SK.PORTFOLIO),
        conditional_question_ids=("has_specific_dates", "has_limited_capacity"),
        suitability_note_es=(
            "Escalonar el pago por hitos reduce fricción y mantiene accountability. Típicamente 30-30-40 por fases."
        ),
        examples_es=(
            "Plan financiero personal 12 meses",
            "Reestructuración patrimonial",
            "Transformación fiscal familiar",
            "Roadmap estratégico empresarial",
        ),
    ),
    "consultor_bolsa_horas": OfferTypePreset(
        preset_id="consultor_bolsa_horas",
        business_type=_EBT.CONSULTOR_PROFESIONAL,
        archetype=_A.PROGRAMA,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Bolsa de horas prepagadas",
        description_es=(
            "Pack de horas que el cliente consume cuando necesita — típico "
            "para abogados o consultores estratégicos con clientes "
            "recurrentes pero sin retainer formal."
        ),
        icon_name="Clock",
        base_sections=(*_base_programa(), SK.PORTFOLIO),
        suitability_note_es=(
            "Caducidad de la bolsa (ej: 6 meses) debe estar explícita. "
            "Fracción mínima facturable (15min/30min) evita disputas."
        ),
        examples_es=(
            "Bolsa 10h consultoría estratégica",
            "Pack 20h asesoría legal",
            "Horas de diseño arquitectónico",
            "Horas de asesoría financiera",
        ),
    ),
    "consultor_dictamen": OfferTypePreset(
        preset_id="consultor_dictamen",
        business_type=_EBT.CONSULTOR_PROFESIONAL,
        archetype=_A.PRODUCTO,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Dictamen o informe escrito",
        description_es=(
            "Entregable intelectual tangible — dictamen legal, informe "
            "pericial, estudio de factibilidad. Una vez entregado, "
            "transacción cerrada."
        ),
        icon_name="FileCheck",
        base_sections=(*_base_producto(), SK.PORTFOLIO),
        suitability_note_es=(
            "Plazo de entrega + número de revisiones incluidas son críticos. "
            "Anticipo del 50% es estándar en dictámenes caros."
        ),
        examples_es=(
            "Dictamen legal contractual",
            "Informe pericial técnico",
            "Estudio de factibilidad",
            "Auditoría tributaria (informe)",
        ),
    ),
    "consultor_curso_b2b": OfferTypePreset(
        preset_id="consultor_curso_b2b",
        business_type=_EBT.CONSULTOR_PROFESIONAL,
        archetype=_A.PROGRAMA,
        typical_value_level=OfferValueLevel.MAXIMIZACION,
        label_es="Curso o capacitación B2B",
        description_es=(
            "Capacitación a equipos de empresa cliente — in-company o en "
            "aula propia. Venta al área de RR.HH. o al directivo."
        ),
        icon_name="Presentation",
        base_sections=(*_base_programa(), SK.PORTFOLIO),
        conditional_question_ids=(
            "requires_physical_location",
            "has_specific_dates",
            "is_hybrid_modality",
        ),
        suitability_note_es=(
            "Venta B2B requiere cotización formal en PDF, orden de compra "
            "y facturación empresarial. WhatsApp para primer contacto, "
            "email formal para cerrar."
        ),
        examples_es=(
            "Capacitación liderazgo in-company",
            "Workshop normativa fiscal al equipo",
            "Curso de compliance corporativo",
            "Training de ventas B2B",
        ),
    ),
    "consultor_club_actualizaciones": OfferTypePreset(
        preset_id="consultor_club_actualizaciones",
        business_type=_EBT.CONSULTOR_PROFESIONAL,
        archetype=_A.MEMBRESIA,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Club de actualizaciones",
        description_es=(
            "Suscripción para recibir actualizaciones periódicas del área — "
            "boletín fiscal mensual, alertas regulatorias, FAQ privado. "
            "Alto margen, bajo costo marginal."
        ),
        icon_name="Newspaper",
        base_sections=_base_membresia(),
        conditional_question_ids=("delivers_downloadable_materials",),
        default_flags=(PresetFlag.RECURRING_BILLING,),
        suitability_note_es=(
            "Plataforma elegida (email, Circle, Telegram privado) afecta "
            "percepción de exclusividad. Minimo 3 meses de cancelación "
            "reduce churn."
        ),
        examples_es=(
            "Boletín fiscal mensual PYMES",
            "Club jurisprudencia laboral",
            "Alertas regulatorias financieras",
            "Membresía actualización normativa salud",
        ),
    ),
    "consultor_enterprise_retainer": OfferTypePreset(
        preset_id="consultor_enterprise_retainer",
        business_type=_EBT.CONSULTOR_PROFESIONAL,
        archetype=_A.MEMBRESIA,
        typical_value_level=OfferValueLevel.CORPORATIVO,
        label_es="Retainer corporativo multi-área",
        description_es=(
            "Honorarios mensuales/anuales para empresa con scope multi-disciplinario "
            "— legal + fiscal + compliance, o cualquier combinación. SLA, comité de "
            "cuenta y equipo dedicado. Vs el retainer PYME, opera a escala enterprise."
        ),
        icon_name="Briefcase",
        base_sections=(*_base_membresia(), SK.PORTFOLIO),
        conditional_question_ids=("has_team_or_speakers",),
        default_flags=(PresetFlag.RECURRING_BILLING, PresetFlag.HIGH_TICKET),
        suitability_note_es=(
            "Contrato formal con SLA, NDA y comité de cuenta. Facturación B2B "
            "mensual con orden de compra. Renovación anual condicionada a "
            "reporte de impacto. WhatsApp + email + reuniones quincenales."
        ),
        examples_es=(
            "Retainer legal corporativo anual",
            "Asesoría fiscal + compliance enterprise",
            "Counsel general fraccional",
            "Retainer estratégico C-level",
        ),
    ),
    # ────────────────────────────────────────────────────────────────────────
    # 3. COACH_MENTOR (11 presets)
    # ────────────────────────────────────────────────────────────────────────
    "coach_sesion_unica": OfferTypePreset(
        preset_id="coach_sesion_unica",
        business_type=_EBT.COACH_MENTOR,
        archetype=_A.SERVICIO,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Sesión 1:1 suelta",
        description_es=(
            "Una sesión individual sin compromiso de continuidad. Para "
            "tenes-de-pie lateral, diagnóstico inicial o cliente que "
            "prefiere probar antes de contratar paquete."
        ),
        icon_name="UserRound",
        base_sections=_base_servicio(),
        conditional_question_ids=("is_hybrid_modality",),
        suitability_note_es=(
            "INST peso alto — tu historia y credenciales son la venta. "
            "Ofrecer upsell a paquete al final de la sesión convierte 30-40%."
        ),
        examples_es=(
            "Sesión diagnóstico coaching",
            "Mentoría 1h ejecutivo",
            "Sesión suelta negocios",
            "Coaching de pareja puntual",
        ),
    ),
    "coach_paquete_sesiones": OfferTypePreset(
        preset_id="coach_paquete_sesiones",
        business_type=_EBT.COACH_MENTOR,
        archetype=_A.PROGRAMA,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Paquete de sesiones",
        description_es=(
            "Conjunto de 3-10 sesiones 1:1 con objetivo común. Continuidad "
            "con costo unitario decreciente respecto a sesión suelta."
        ),
        icon_name="Layers",
        base_sections=(*_base_programa(), SK.PORTFOLIO),
        suitability_note_es=(
            "Caducidad del paquete (ej: 3 meses para 10 sesiones) protege "
            "contra dilación infinita. Permití reagendar con 24h de aviso."
        ),
        examples_es=(
            "10 sesiones coaching ejecutivo",
            "5 sesiones pareja",
            "Pack 8 mentorías ventas",
            "6 sesiones transformación fitness",
        ),
    ),
    "coach_programa_transformacion": OfferTypePreset(
        preset_id="coach_programa_transformacion",
        business_type=_EBT.COACH_MENTOR,
        archetype=_A.PROGRAMA,
        typical_value_level=OfferValueLevel.MAXIMIZACION,
        label_es="Programa de transformación",
        description_es=(
            "Proceso estructurado de 3-6 meses con metodología propia, "
            "materiales, sesiones y seguimiento. El signature offer del "
            "coach — lo que lo define."
        ),
        icon_name="Rocket",
        base_sections=(*_base_programa(), SK.PORTFOLIO),
        conditional_question_ids=("has_team_or_speakers", "has_specific_dates"),
        default_flags=(PresetFlag.HIGH_TICKET,),
        suitability_note_es=(
            "Promise mensurable ('bajar 6kg', 'cerrar 3 clientes') convierte "
            "más que vagas. Pagos en cuotas de 3-6 son esperadas."
        ),
        examples_es=(
            "Programa Libertad Financiera 6 meses",
            "Transformación fitness 90 días",
            "Programa cerrá tu primer cliente high-ticket",
            "Recuperación pareja 5 meses",
        ),
    ),
    "coach_mastermind": OfferTypePreset(
        preset_id="coach_mastermind",
        business_type=_EBT.COACH_MENTOR,
        archetype=_A.MEMBRESIA,
        typical_value_level=OfferValueLevel.MAXIMIZACION,
        label_es="Mastermind grupal",
        description_es=(
            "Comunidad mensual de alto nivel con encuentros regulares, "
            "acceso al coach y red de pares. Alta exclusividad, ticket "
            "mensual o anual recurrente."
        ),
        icon_name="Crown",
        base_sections=(*_base_membresia(), SK.PORTFOLIO),
        conditional_question_ids=("has_team_or_speakers", "has_limited_capacity"),
        default_flags=(PresetFlag.RECURRING_BILLING, PresetFlag.HIGH_TICKET),
        suitability_note_es=(
            "Aplicación + entrevista de ingreso sostienen la exclusividad. "
            "Cupos cerrados (12-20 miembros) incrementan valor percibido."
        ),
        examples_es=(
            "Mastermind founders USD 500/mes",
            "Círculo mujeres líderes",
            "Mastermind agencia de ventas",
            "Club VIP de transformación fitness",
        ),
    ),
    "coach_bootcamp": OfferTypePreset(
        preset_id="coach_bootcamp",
        business_type=_EBT.COACH_MENTOR,
        archetype=_A.PROGRAMA,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Bootcamp intensivo",
        description_es=(
            "Cohorte intensiva de 1-4 semanas con entrada por lanzamiento. Compresión de tiempo genera urgencia y foco."
        ),
        icon_name="Zap",
        base_sections=(*_base_programa(), SK.PORTFOLIO),
        conditional_question_ids=(
            "has_specific_dates",
            "has_limited_capacity",
            "requires_physical_location",
        ),
        default_flags=(PresetFlag.REQUIRES_START_DATE, PresetFlag.SUPPORTS_CAPACITY),
        suitability_note_es=(
            "Early-bird con descuento por compra anticipada es estándar. "
            "Lista de espera para cohortes futuras captura demanda excedente."
        ),
        examples_es=(
            "Bootcamp cerrá tu primera venta 14 días",
            "Intensivo habla inglés 21 días",
            "Bootcamp negocios online 2 semanas",
            "Sprint de foco 7 días",
        ),
    ),
    "coach_curso_grabado": OfferTypePreset(
        preset_id="coach_curso_grabado",
        business_type=_EBT.COACH_MENTOR,
        archetype=_A.PRODUCTO,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Curso grabado (método empaquetado)",
        description_es=(
            "Método empaquetado en video on-demand. El cliente avanza a "
            "su ritmo, sin contacto directo del coach. Ticket medio, "
            "escalable sin consumir tu tiempo."
        ),
        icon_name="PlayCircle",
        base_sections=_base_producto(),
        conditional_question_ids=("delivers_downloadable_materials",),
        suitability_note_es=(
            "Duración acceso (anual, de por vida) es decisión clave. "
            "Comunidad asociada (WhatsApp/Discord) aumenta completion rate 3x."
        ),
        examples_es=(
            "Método de finanzas personales (curso)",
            "Sistema ventas por WhatsApp",
            "Masterclass productividad",
            "Curso grabado fitness en casa",
        ),
    ),
    "coach_retreat": OfferTypePreset(
        preset_id="coach_retreat",
        business_type=_EBT.COACH_MENTOR,
        archetype=_A.EXPERIENCIA,
        typical_value_level=OfferValueLevel.MAXIMIZACION,
        label_es="Retiro presencial",
        description_es=(
            "Inmersión de 3-7 días en un venue especial — fusión de "
            "transformación + experiencia. Alto ticket, alto impacto."
        ),
        icon_name="Mountain",
        base_sections=(*_base_experiencia(), SK.PORTFOLIO, SK.RESOURCES),
        conditional_question_ids=("has_limited_capacity", "has_team_or_speakers"),
        default_flags=(PresetFlag.HIGH_TICKET, PresetFlag.REQUIRES_START_DATE),
        suitability_note_es=(
            "Alojamiento, comidas y transporte son la mayoría del costo — "
            "documentá qué está incluido con precisión quirúrgica."
        ),
        examples_es=(
            "Retiro líderes alto impacto Cartagena",
            "Immersion founders 5 días Tulum",
            "Retreat mujeres poderosas",
            "Retiro meditación + negocios",
        ),
    ),
    "coach_vip_day": OfferTypePreset(
        preset_id="coach_vip_day",
        business_type=_EBT.COACH_MENTOR,
        archetype=_A.SERVICIO,
        typical_value_level=OfferValueLevel.MAXIMIZACION,
        label_es="VIP Day",
        description_es=(
            "Un día completo 1:1 intenso — plan estratégico, roadmap, "
            "auditoría profunda. Ticket alto comprimido en 6-8 horas "
            "focales."
        ),
        icon_name="Gem",
        base_sections=(*_base_servicio(), SK.PORTFOLIO),
        conditional_question_ids=("requires_physical_location", "is_hybrid_modality"),
        default_flags=(PresetFlag.HIGH_TICKET,),
        suitability_note_es=(
            "Pre-work (cuestionario, revisión previa) es lo que diferencia "
            "VIP Day profesional de 'sesión larga'. Cobrar 100% upfront."
        ),
        examples_es=(
            "VIP Day estrategia de contenido",
            "Día intensivo roadmap 12 meses",
            "Deep dive posicionamiento",
            "VIP Day reestructuración comercial",
        ),
    ),
    "coach_challenge_gratis": OfferTypePreset(
        preset_id="coach_challenge_gratis",
        business_type=_EBT.COACH_MENTOR,
        archetype=_A.PROGRAMA,
        typical_value_level=OfferValueLevel.LEAD_MAGNET,
        label_es="Challenge gratuito (lead magnet)",
        description_es=(
            "Reto de 3-7 días gratuito con sesiones vivas diarias. Genera "
            "compromiso y precede a una oferta paga de lanzamiento."
        ),
        icon_name="Flag",
        base_sections=(
            SK.IDENTITY,
            SK.STRATEGY,
            SK.PROMISE,
            SK.PROGRAM_DETAILS,
            SK.INSTRUCTORS,
            SK.CLOSING,
            SK.KNOWLEDGE,
            SK.FAQ,
            SK.GALLERY,
        ),
        conditional_question_ids=("has_specific_dates", "has_limited_capacity"),
        default_flags=(PresetFlag.IS_LEAD_MAGNET, PresetFlag.REQUIRES_START_DATE),
        suitability_note_es=(
            "Sin PRICING section — es gratuito. CLOSING se re-enfoca en la "
            "oferta paga que sigue al challenge. Conversión post-challenge "
            "a oferta paga ronda 3-8%."
        ),
        examples_es=(
            "Challenge 5 días vendé tu primer curso",
            "Reto 7 días cambio de hábitos",
            "Bootcamp gratuito 3 días de copywriting",
            "Challenge fitness 5 días",
        ),
    ),
    "coach_ebook_workbook": OfferTypePreset(
        preset_id="coach_ebook_workbook",
        business_type=_EBT.COACH_MENTOR,
        archetype=_A.PRODUCTO,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Ebook o workbook",
        description_es=(
            "Material escrito descargable — ebook, workbook con ejercicios, "
            "plantilla de diagnóstico. Tripwire de bajo ticket (USD 7-47)."
        ),
        icon_name="BookOpen",
        base_sections=_base_producto(),
        conditional_question_ids=("delivers_downloadable_materials",),
        suitability_note_es=(
            "Ideal como producto de entrada post-lead-magnet. Upsell inmediato a curso grabado o sesión 1:1."
        ),
        examples_es=(
            "Ebook método ventas WhatsApp",
            "Workbook hábitos atómicos",
            "Plantilla plan financiero personal",
            "Guía 30 días productividad",
        ),
    ),
    "coach_corporate_program": OfferTypePreset(
        preset_id="coach_corporate_program",
        business_type=_EBT.COACH_MENTOR,
        archetype=_A.PROGRAMA,
        typical_value_level=OfferValueLevel.CORPORATIVO,
        label_es="Programa de coaching corporativo",
        description_es=(
            "Programa estructurado contratado por una empresa para su equipo "
            "ejecutivo o de líderes. Sesiones grupales + 1:1 + materiales. "
            "Vendido a la organización (no al individuo). Cohorte cerrada por "
            "compañía."
        ),
        icon_name="Building",
        base_sections=(*_base_programa(), SK.LOCATION, SK.PORTFOLIO),
        conditional_question_ids=(
            "requires_physical_location",
            "has_specific_dates",
            "has_team_or_speakers",
        ),
        default_flags=(PresetFlag.REQUIRES_START_DATE, PresetFlag.HIGH_TICKET),
        suitability_note_es=(
            "Decisor es Director RR.HH., L&D o el CEO directamente. Cotización "
            "formal con resultados esperados + KPIs medibles. Pre-assessment "
            "del equipo y reporte ejecutivo final son entregables clave."
        ),
        examples_es=(
            "Programa liderazgo C-suite 6 meses",
            "Coaching ejecutivo team-wide trimestral",
            "Desarrollo de líderes high-potential",
            "Programa transformación cultural dirección",
        ),
    ),
    # ────────────────────────────────────────────────────────────────────────
    # 4. ACADEMIA_INFOPRODUCTOR (11 presets)
    # ────────────────────────────────────────────────────────────────────────
    "academia_curso_grabado": OfferTypePreset(
        preset_id="academia_curso_grabado",
        business_type=_EBT.ACADEMIA_INFOPRODUCTOR,
        archetype=_A.PRODUCTO,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Curso grabado (self-paced)",
        description_es=(
            "Infoproducto clásico: video on-demand estructurado en módulos. "
            "El alumno avanza a su ritmo sin fechas fijas."
        ),
        icon_name="GraduationCap",
        base_sections=_base_producto(),
        conditional_question_ids=("delivers_downloadable_materials",),
        suitability_note_es=(
            "Hotmart/Eduzz dominan Brasil; Kiwify + pasarelas locales en "
            "hispanohablante. Comunidad WhatsApp/Telegram asociada sube "
            "completion rate y LTV."
        ),
        examples_es=(
            "Curso de trading (grabado)",
            "Academia de inglés online",
            "Curso marketing digital completo",
            "Formación en Excel avanzado",
        ),
    ),
    "academia_cohorte_vivo": OfferTypePreset(
        preset_id="academia_cohorte_vivo",
        business_type=_EBT.ACADEMIA_INFOPRODUCTOR,
        archetype=_A.PROGRAMA,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Cohorte en vivo",
        description_es=(
            "Bootcamp o cohorte con fechas fijas y sesiones vivas. Grupo "
            "que empieza y termina junto — alta tasa de completion vs "
            "grabado self-paced."
        ),
        icon_name="Users",
        base_sections=(*_base_programa(), SK.PORTFOLIO),
        conditional_question_ids=(
            "has_specific_dates",
            "has_limited_capacity",
            "requires_physical_location",
        ),
        default_flags=(PresetFlag.REQUIRES_START_DATE, PresetFlag.SUPPORTS_CAPACITY),
        suitability_note_es=(
            "Lanzamientos escalonados (open cart / close cart) generan "
            "urgencia. Early-bird 30-50% off convierte mejor. Pagos en "
            "3-6 cuotas."
        ),
        examples_es=(
            "Bootcamp programación 12 semanas",
            "Cohorte copywriting Q2",
            "Cohorte inversiones 8 semanas",
            "Bootcamp ventas high-ticket",
        ),
    ),
    "academia_cohorte_hibrida": OfferTypePreset(
        preset_id="academia_cohorte_hibrida",
        business_type=_EBT.ACADEMIA_INFOPRODUCTOR,
        archetype=_A.PROGRAMA,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Cohorte híbrida (material + lives)",
        description_es=(
            "Material grabado + encuentros vivos semanales. Alumno tiene "
            "flexibilidad del grabado pero con acountability grupal y "
            "Q&A en tiempo real."
        ),
        icon_name="Monitor",
        base_sections=(*_base_programa(), SK.PORTFOLIO),
        conditional_question_ids=("has_specific_dates", "has_limited_capacity"),
        default_flags=(PresetFlag.REQUIRES_START_DATE,),
        suitability_note_es=(
            "Balance óptimo entre escalabilidad del PRODUCTO y acompañamiento "
            "del PROGRAMA. Cohortes de 50-200 son manejables con TAs."
        ),
        examples_es=(
            "Programa mentor premium híbrido 4 meses",
            "Academia marketing con calls semanales",
            "Curso trading + grupo de análisis",
            "Formación diseño + reviews grupales",
        ),
    ),
    "academia_membresia_academia": OfferTypePreset(
        preset_id="academia_membresia_academia",
        business_type=_EBT.ACADEMIA_INFOPRODUCTOR,
        archetype=_A.MEMBRESIA,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Membresía academia (todo incluido)",
        description_es=(
            "Acceso continuo a toda la biblioteca de cursos, comunidad y "
            "nuevos lanzamientos. Modelo Netflix para el saber."
        ),
        icon_name="Library",
        base_sections=(*_base_membresia(), SK.PLATFORM_DETAILS, SK.RESOURCES),
        conditional_question_ids=("delivers_downloadable_materials",),
        default_flags=(PresetFlag.RECURRING_BILLING,),
        suitability_note_es=(
            "Anual con 2 meses gratis reduce churn drásticamente. "
            "Plataforma (Teachable, Kajabi, Hotmart, propia) define UX."
        ),
        examples_es=(
            "Academia trading anual",
            "Biblioteca inglés premium",
            "Academia de negocios completa",
            "Membresía design school",
        ),
    ),
    "academia_masterclass_vivo": OfferTypePreset(
        preset_id="academia_masterclass_vivo",
        business_type=_EBT.ACADEMIA_INFOPRODUCTOR,
        archetype=_A.EXPERIENCIA,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Masterclass en vivo",
        description_es=(
            "Clase única intensiva de 2-4 horas — alto valor comprimido. "
            "Puede ser gratis (lead magnet) o pago de bajo ticket."
        ),
        icon_name="Mic",
        base_sections=_base_experiencia(),
        conditional_question_ids=(
            "has_limited_capacity",
            "has_team_or_speakers",
            "requires_physical_location",
        ),
        default_flags=(PresetFlag.REQUIRES_START_DATE,),
        suitability_note_es=(
            "Reposición por 48h post-evento suma valor sin diluir urgencia. "
            "Upsell durante la masterclass a curso completo es clásico."
        ),
        examples_es=(
            "Masterclass 'Tu primer USD 1000 online'",
            "Masterclass inteligencia financiera",
            "Taller diseño UX 3 horas",
            "Masterclass IA para emprendedores",
        ),
    ),
    "academia_certificacion_cohort": OfferTypePreset(
        preset_id="academia_certificacion_cohort",
        business_type=_EBT.ACADEMIA_INFOPRODUCTOR,
        archetype=_A.PROGRAMA,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Certificación con cohorte",
        description_es=(
            "Programa estructurado que culmina con examen y certificado "
            "verificable. Cohortes con fechas fijas y evaluación."
        ),
        icon_name="Award",
        base_sections=(*_base_programa(), SK.PORTFOLIO),
        conditional_question_ids=("has_specific_dates", "has_limited_capacity"),
        default_flags=(PresetFlag.REQUIRES_START_DATE,),
        suitability_note_es=(
            "Certificado verificable (QR, Accredible) eleva valor percibido. "
            "Alianza con colegio profesional o universidad amplifica venta."
        ),
        examples_es=(
            "Certificación Scrum Master",
            "Certificación coaching ICF",
            "Certificación inglés TOEFL prep",
            "Certificación diseño UX/UI",
        ),
    ),
    "academia_certificacion_self": OfferTypePreset(
        preset_id="academia_certificacion_self",
        business_type=_EBT.ACADEMIA_INFOPRODUCTOR,
        archetype=_A.PRODUCTO,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Certificación self-paced",
        description_es=(
            "Curso grabado + examen automatizado con certificado. Escalable, "
            "sin fechas fijas. Ticket medio-alto por el respaldo."
        ),
        icon_name="ShieldCheck",
        base_sections=_base_producto(),
        conditional_question_ids=("delivers_downloadable_materials",),
        suitability_note_es=(
            "Examen con múltiples intentos (2-3) vs bloqueo por fallar "
            "afecta NPS y completion. Transparentar criterios de aprobación."
        ),
        examples_es=(
            "Certificación Google Ads (self)",
            "Certificación Meta Blueprint",
            "Curso + examen contabilidad PYMES",
            "Certificado programación Python",
        ),
    ),
    "academia_ebook_guia": OfferTypePreset(
        preset_id="academia_ebook_guia",
        business_type=_EBT.ACADEMIA_INFOPRODUCTOR,
        archetype=_A.PRODUCTO,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Ebook o guía premium",
        description_es=("Material escrito comprehensivo — tripwire (USD 7-47) o mini-curso en formato PDF/EPUB."),
        icon_name="BookMarked",
        base_sections=_base_producto(),
        suitability_note_es=(
            "Upsell inmediato post-compra a curso completo convierte 10-20%. "
            "Bundle con plantillas o workbook multiplica percepción de valor."
        ),
        examples_es=(
            "Ebook inversiones para principiantes",
            "Guía avanzada Excel PYMES",
            "Ebook 100 headlines que venden",
            "Guía SEO completa 2026",
        ),
    ),
    "academia_curso_gratis": OfferTypePreset(
        preset_id="academia_curso_gratis",
        business_type=_EBT.ACADEMIA_INFOPRODUCTOR,
        archetype=_A.PRODUCTO,
        typical_value_level=OfferValueLevel.LEAD_MAGNET,
        label_es="Mini-curso gratuito (lead magnet)",
        description_es=(
            "3-5 lecciones gratis que preceden al lanzamiento de un curso pago. Genera email list calificada."
        ),
        icon_name="Gift",
        base_sections=(
            SK.IDENTITY,
            SK.STRATEGY,
            SK.PROMISE,
            SK.PRODUCT_DETAILS,
            SK.INSTRUCTORS,
            SK.CLOSING,
            SK.KNOWLEDGE,
            SK.FAQ,
            SK.GALLERY,
        ),
        default_flags=(PresetFlag.IS_LEAD_MAGNET,),
        suitability_note_es=(
            "Sin PRICING — es gratuito. CLOSING redirige al lanzamiento "
            "pago. Conversión mini-curso → curso pago ronda 5-15%."
        ),
        examples_es=(
            "Mini-curso intro trading 3 lecciones",
            "Webinar gratuito marketing digital",
            "Serie email 7 días copywriting",
            "Clase gratis fundamentos finanzas",
        ),
    ),
    "academia_challenge_edu": OfferTypePreset(
        preset_id="academia_challenge_edu",
        business_type=_EBT.ACADEMIA_INFOPRODUCTOR,
        archetype=_A.PROGRAMA,
        typical_value_level=OfferValueLevel.LEAD_MAGNET,
        label_es="Challenge educativo (lead magnet)",
        description_es=(
            "Reto de 5-7 días con ejercicios diarios y comunidad. Maximiza engagement previo al open cart."
        ),
        icon_name="Target",
        base_sections=(
            SK.IDENTITY,
            SK.STRATEGY,
            SK.PROMISE,
            SK.PROGRAM_DETAILS,
            SK.INSTRUCTORS,
            SK.CLOSING,
            SK.KNOWLEDGE,
            SK.FAQ,
            SK.GALLERY,
        ),
        conditional_question_ids=("has_specific_dates",),
        default_flags=(PresetFlag.IS_LEAD_MAGNET, PresetFlag.REQUIRES_START_DATE),
        suitability_note_es=(
            "Grupo de WhatsApp o Telegram durante el challenge genera pertenencia y presión social para completar."
        ),
        examples_es=(
            "Challenge 5 días tu primer USD 100 online",
            "Reto 7 días habla inglés",
            "Bootcamp gratuito 3 días IA",
            "Challenge productividad 5 días",
        ),
    ),
    "academia_b2b_license": OfferTypePreset(
        preset_id="academia_b2b_license",
        business_type=_EBT.ACADEMIA_INFOPRODUCTOR,
        archetype=_A.MEMBRESIA,
        typical_value_level=OfferValueLevel.CORPORATIVO,
        label_es="Licencia B2B para empresas",
        description_es=(
            "Acceso enterprise a tu academia o curso para N empleados de una "
            "empresa. Licencia anual con seats predefinidos, reporte de uso y "
            "soporte dedicado. Vs el plan individual, opera por contrato corporativo."
        ),
        icon_name="Network",
        base_sections=(*_base_membresia(), SK.PLATFORM_DETAILS, SK.PORTFOLIO),
        conditional_question_ids=("delivers_downloadable_materials",),
        default_flags=(PresetFlag.RECURRING_BILLING, PresetFlag.HIGH_TICKET),
        suitability_note_es=(
            "Decisor: L&D, RR.HH. o director de área. SSO, reporte de progreso "
            "por empleado y certificados verificables son must-have. Pricing por "
            "seats con descuento de volumen. Cotización + OC + factura anual."
        ),
        examples_es=(
            "Licencia academia trading 50 seats",
            "Plan corporativo academia inglés",
            "Acceso enterprise biblioteca cursos",
            "Bundle formación + certificación equipo",
        ),
    ),
    # ────────────────────────────────────────────────────────────────────────
    # 5. ANFITRION_PRODUCTOR (9 presets)
    # ────────────────────────────────────────────────────────────────────────
    "anfitrion_retiro": OfferTypePreset(
        preset_id="anfitrion_retiro",
        business_type=_EBT.ANFITRION_PRODUCTOR,
        archetype=_A.EXPERIENCIA,
        typical_value_level=OfferValueLevel.MAXIMIZACION,
        label_es="Retiro / inmersión",
        description_es=(
            "Experiencia presencial de 3-7 días en un venue especial. "
            "Alojamiento + actividades + comidas. Signature offer del host."
        ),
        icon_name="Palmtree",
        base_sections=(*_base_experiencia(), SK.PORTFOLIO, SK.RESOURCES),
        conditional_question_ids=("has_limited_capacity", "has_team_or_speakers"),
        default_flags=(
            PresetFlag.HIGH_TICKET,
            PresetFlag.REQUIRES_START_DATE,
            PresetFlag.SUPPORTS_CAPACITY,
        ),
        suitability_note_es=(
            "Fotos del venue venden el retiro. Testimonios con ubicación "
            "(PE/MX/CO) incrementan credibilidad regional. Cancelación "
            "flexible justifica ticket alto."
        ),
        examples_es=(
            "Retiro yoga Baja California 5 días",
            "Retiro founders Tulum",
            "Retiro wellness femenino Cartagena",
            "Immersion mindfulness Sacred Valley",
        ),
    ),
    "anfitrion_evento_1dia": OfferTypePreset(
        preset_id="anfitrion_evento_1dia",
        business_type=_EBT.ANFITRION_PRODUCTOR,
        archetype=_A.EXPERIENCIA,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Evento 1 día",
        description_es=(
            "Conferencia, summit o taller presencial de un día. Sin "
            "alojamiento. Venta ticketizada con capacidad definida."
        ),
        icon_name="CalendarDays",
        base_sections=(*_base_experiencia(), SK.PORTFOLIO),
        conditional_question_ids=("has_limited_capacity", "has_team_or_speakers"),
        default_flags=(PresetFlag.REQUIRES_START_DATE, PresetFlag.SUPPORTS_CAPACITY),
        suitability_note_es=(
            "Entrada anticipada, general y VIP es estándar. Mercado Pago + "
            "Paypalco en evento Latam. Estacionamiento y transporte en LOC."
        ),
        examples_es=(
            "Conferencia liderazgo anual",
            "Summit marketing digital",
            "Jornada mujeres en negocios",
            "Evento founders Latam",
        ),
    ),
    "anfitrion_summit_virtual": OfferTypePreset(
        preset_id="anfitrion_summit_virtual",
        business_type=_EBT.ANFITRION_PRODUCTOR,
        archetype=_A.EXPERIENCIA,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Summit virtual",
        description_es=(
            "Cumbre online multi-speaker durante 1-5 días. Modelo freemium: "
            "acceso gratuito limitado + pase VIP pago con reposición y bonus."
        ),
        icon_name="Globe2",
        base_sections=(
            SK.IDENTITY,
            SK.STRATEGY,
            SK.PSYCHOLOGY,
            SK.PROMISE,
            SK.EVENT_DETAILS,
            SK.INSTRUCTORS,
            SK.VALUE_STACK,
            SK.PRICING,
            SK.CLOSING,
            SK.KNOWLEDGE,
            SK.FAQ,
            SK.TESTIMONIALS,
            SK.GALLERY,
            SK.PORTFOLIO,
        ),
        conditional_question_ids=("has_limited_capacity",),
        default_flags=(PresetFlag.REQUIRES_START_DATE,),
        suitability_note_es=(
            "Pase VIP con acceso de por vida + bonus exclusivos convierte "
            "10-25% del audience gratuito. Lineup de speakers es la venta."
        ),
        examples_es=(
            "Summit de productividad 3 días",
            "Cumbre finanzas personales Latam",
            "Summit mujeres emprendedoras",
            "Digital marketing summit regional",
        ),
    ),
    "anfitrion_mastermind": OfferTypePreset(
        preset_id="anfitrion_mastermind",
        business_type=_EBT.ANFITRION_PRODUCTOR,
        archetype=_A.MEMBRESIA,
        typical_value_level=OfferValueLevel.MAXIMIZACION,
        label_es="Mastermind high-ticket",
        description_es=(
            "Círculo privado con encuentros regulares — mensuales online + "
            "1-2 retiros anuales presenciales. Red de pares + host visible."
        ),
        icon_name="Crown",
        base_sections=(*_base_membresia(), SK.PORTFOLIO),
        conditional_question_ids=("has_limited_capacity", "has_team_or_speakers"),
        default_flags=(PresetFlag.RECURRING_BILLING, PresetFlag.HIGH_TICKET),
        suitability_note_es=(
            "Aplicación con entrevista filtra y eleva exclusividad. Anual "
            "con descuento vs mensual reduce churn. USD 500-5000/mes es típico."
        ),
        examples_es=(
            "Mastermind founders high-ticket",
            "Círculo CEOs Latam",
            "Mastermind mujeres poderosas",
            "Red privada de inversionistas",
        ),
    ),
    "anfitrion_comunidad_paga": OfferTypePreset(
        preset_id="anfitrion_comunidad_paga",
        business_type=_EBT.ANFITRION_PRODUCTOR,
        archetype=_A.MEMBRESIA,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Comunidad paga continua",
        description_es=(
            "Acceso continuo a un espacio privado (Circle, Discord, WhatsApp) "
            "con contenido exclusivo, eventos mensuales y host activo."
        ),
        icon_name="MessagesSquare",
        base_sections=(*_base_membresia(), SK.PLATFORM_DETAILS),
        conditional_question_ids=("has_team_or_speakers",),
        default_flags=(PresetFlag.RECURRING_BILLING,),
        suitability_note_es=(
            "Circle > Discord > WhatsApp según formalidad. Contenido "
            "exclusivo mensual + encuentro mensual justifica suscripción."
        ),
        examples_es=(
            "Comunidad creadores de contenido",
            "Club founders Latam USD 49/mes",
            "Comunidad inversionistas principiantes",
            "Red de coaches profesionales",
        ),
    ),
    "anfitrion_taller_grupal": OfferTypePreset(
        preset_id="anfitrion_taller_grupal",
        business_type=_EBT.ANFITRION_PRODUCTOR,
        archetype=_A.EXPERIENCIA,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Taller grupal",
        description_es=(
            "Sesión grupal de 2-4 horas con práctica y facilitación. Presencial o virtual. Ticket bajo-medio."
        ),
        icon_name="Users2",
        base_sections=_base_experiencia(),
        conditional_question_ids=(
            "has_limited_capacity",
            "requires_physical_location",
            "is_hybrid_modality",
        ),
        default_flags=(PresetFlag.REQUIRES_START_DATE,),
        suitability_note_es=(
            "Taller puede repetirse — usa Variant TEMPORAL_SINGLE_DATE para "
            "gestionar múltiples ediciones con misma ficha."
        ),
        examples_es=(
            "Taller de meditación presencial",
            "Workshop pintura al óleo",
            "Taller crianza respetuosa",
            "Clase magistral cocina",
        ),
    ),
    "anfitrion_tour_experiencia": OfferTypePreset(
        preset_id="anfitrion_tour_experiencia",
        business_type=_EBT.ANFITRION_PRODUCTOR,
        archetype=_A.EXPERIENCIA,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Tour / experiencia cultural",
        description_es=(
            "Recorrido guiado de pocas horas — city tour, experiencia "
            "gastronómica, ruta cultural. Turismo de nicho con host experto."
        ),
        icon_name="Compass",
        base_sections=_base_experiencia(),
        conditional_question_ids=("has_limited_capacity", "has_team_or_speakers"),
        default_flags=(PresetFlag.SUPPORTS_CAPACITY,),
        suitability_note_es=(
            "Punto de encuentro preciso (LOC) evita pérdidas. Turismo internacional paga en USD; local en moneda local."
        ),
        examples_es=(
            "City tour gastronómico CDMX",
            "Ruta del café en Colombia",
            "Tour arte urbano Medellín",
            "Experiencia mezcal Oaxaca",
        ),
    ),
    "anfitrion_festival": OfferTypePreset(
        preset_id="anfitrion_festival",
        business_type=_EBT.ANFITRION_PRODUCTOR,
        archetype=_A.EXPERIENCIA,
        typical_value_level=OfferValueLevel.MAXIMIZACION,
        label_es="Festival multi-actividad",
        description_es=(
            "Evento de 2-5 días con múltiples actividades, venues, shows. "
            "Venta de entradas por día o pass completo. Sponsor-driven."
        ),
        icon_name="Sparkles",
        base_sections=(*_base_experiencia(), SK.PORTFOLIO, SK.RESOURCES),
        conditional_question_ids=("has_limited_capacity", "has_team_or_speakers"),
        default_flags=(
            PresetFlag.REQUIRES_START_DATE,
            PresetFlag.SUPPORTS_CAPACITY,
            PresetFlag.HIGH_TICKET,
        ),
        suitability_note_es=(
            "Múltiples tipos de entrada (general, VIP, backstage) con "
            "Variant TIER es la estructura óptima. Preventa escalonada "
            "genera cashflow inicial para producción."
        ),
        examples_es=(
            "Festival wellness Latam 3 días",
            "Encuentro de emprendedoras festival",
            "Festival internacional de coaching",
            "Festival de marketing y creatividad",
        ),
    ),
    "anfitrion_evento_corporativo": OfferTypePreset(
        preset_id="anfitrion_evento_corporativo",
        business_type=_EBT.ANFITRION_PRODUCTOR,
        archetype=_A.EXPERIENCIA,
        typical_value_level=OfferValueLevel.CORPORATIVO,
        label_es="Evento corporativo a medida",
        description_es=(
            "Evento privado producido para una empresa cliente — offsite, "
            "kickoff anual, summit interno, team-building. Fee único por la "
            "producción completa: contenido, venue, catering, facilitación."
        ),
        icon_name="Briefcase",
        base_sections=(*_base_experiencia(), SK.PORTFOLIO, SK.RESOURCES),
        conditional_question_ids=(
            "has_limited_capacity",
            "has_team_or_speakers",
            "requires_physical_location",
        ),
        default_flags=(PresetFlag.REQUIRES_START_DATE, PresetFlag.HIGH_TICKET),
        suitability_note_es=(
            "Vendido a área de Marketing, RR.HH. o C-level. Propuesta visual "
            "(deck) + cotización detallada + cronograma + responsables. 30-50% "
            "de anticipo es estándar. Cláusula de cancelación clara protege contra "
            "cambios de último momento."
        ),
        examples_es=(
            "Offsite anual líderes empresa",
            "Kickoff comercial regional Latam",
            "Summit interno transformación digital",
            "Team-building experiencial 2 días",
        ),
    ),
    # ────────────────────────────────────────────────────────────────────────
    # 6. AGENCIA_FREELANCE (9 presets)
    # ────────────────────────────────────────────────────────────────────────
    "agencia_proyecto_unico": OfferTypePreset(
        preset_id="agencia_proyecto_unico",
        business_type=_EBT.AGENCIA_FREELANCE,
        archetype=_A.SERVICIO,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Proyecto llave en mano",
        description_es=(
            "Entregable único de alcance definido — sitio web, branding, "
            "campaña. Inicio, ejecución, aprobación y cierre."
        ),
        icon_name="Briefcase",
        base_sections=(*_base_servicio(), SK.PORTFOLIO),
        conditional_question_ids=("has_specific_dates", "has_team_or_speakers"),
        suitability_note_es=(
            "50% upfront es estándar Latam. Scope-in/scope-out en "
            "SERVICE_DETAILS con brutal claridad evita scope creep."
        ),
        examples_es=(
            "Sitio web corporativo",
            "Branding completo startup",
            "Campaña publicitaria 3 meses",
            "Video corporativo llave en mano",
        ),
    ),
    "agencia_retainer": OfferTypePreset(
        preset_id="agencia_retainer",
        business_type=_EBT.AGENCIA_FREELANCE,
        archetype=_A.MEMBRESIA,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Retainer mensual",
        description_es=(
            "Gestión continua — ads, redes sociales, SEO, contenido. Fee "
            "mensual por servicios recurrentes con scope definido."
        ),
        icon_name="TrendingUp",
        base_sections=(*_base_membresia(), SK.PORTFOLIO),
        conditional_question_ids=("has_team_or_speakers",),
        default_flags=(PresetFlag.RECURRING_BILLING,),
        suitability_note_es=(
            "Reporte mensual visible en dashboard sostiene la renovación. "
            "Permanencia mínima 3 meses justifica curva aprendizaje."
        ),
        examples_es=(
            "Gestión de Meta Ads mensual",
            "Community management retainer",
            "SEO + contenido mensual",
            "Gestión redes + reportes",
        ),
    ),
    "agencia_vip_day": OfferTypePreset(
        preset_id="agencia_vip_day",
        business_type=_EBT.AGENCIA_FREELANCE,
        archetype=_A.SERVICIO,
        typical_value_level=OfferValueLevel.MAXIMIZACION,
        label_es="VIP Day",
        description_es=(
            "Un día de trabajo concentrado entregable — auditoría + plan, "
            "landing page terminada, brand kit express. Alto ticket "
            "comprimido."
        ),
        icon_name="Zap",
        base_sections=(*_base_servicio(), SK.PORTFOLIO),
        default_flags=(PresetFlag.HIGH_TICKET,),
        suitability_note_es=(
            "Pre-work (onboarding, material previo) es lo que separa VIP Day de 'día largo'. Cobro 100% upfront."
        ),
        examples_es=(
            "VIP Day estrategia SEO",
            "Día intensivo landing + copy",
            "Brand kit express 1 día",
            "Auditoría + roadmap ads 1 día",
        ),
    ),
    "agencia_productized_service": OfferTypePreset(
        preset_id="agencia_productized_service",
        business_type=_EBT.AGENCIA_FREELANCE,
        archetype=_A.SERVICIO,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Servicio empaquetado (productized)",
        description_es=(
            "Servicio estandarizado con precio fijo y alcance cerrado — "
            "auditoría de X, landing para Y. Compra directa sin cotización."
        ),
        icon_name="Package",
        base_sections=(*_base_servicio(), SK.PORTFOLIO),
        suitability_note_es=(
            "Modelo productized elimina fricción de venta. Ideal para "
            "servicios repetibles. Checkout directo estilo ecommerce."
        ),
        examples_es=(
            "Auditoría SEO técnica (precio fijo)",
            "Landing de alta conversión (pack)",
            "Video reel 30s producido",
            "Brand audit express USD 497",
        ),
    ),
    "agencia_template_digital": OfferTypePreset(
        preset_id="agencia_template_digital",
        business_type=_EBT.AGENCIA_FREELANCE,
        archetype=_A.PRODUCTO,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Template o asset digital",
        description_es=(
            "Recurso digital reutilizable — template Framer, brand guidelines, "
            "pack de iconos, preset. Monetización pasiva del know-how."
        ),
        icon_name="Palette",
        base_sections=_base_producto(),
        conditional_question_ids=("delivers_downloadable_materials",),
        suitability_note_es=(
            "Gumroad / Lemon Squeezy / Kiwify para distribución. Licencia "
            "claramente documentada (uso personal vs comercial)."
        ),
        examples_es=(
            "Template Framer portfolio",
            "Brand guidelines template",
            "Pack de Lightroom presets",
            "Notion OS freelance",
        ),
    ),
    "agencia_workshop_b2b": OfferTypePreset(
        preset_id="agencia_workshop_b2b",
        business_type=_EBT.AGENCIA_FREELANCE,
        archetype=_A.PROGRAMA,
        typical_value_level=OfferValueLevel.MAXIMIZACION,
        label_es="Workshop B2B in-company",
        description_es=(
            "Capacitación al equipo del cliente — ads, SEO, contenido, "
            "IA para marketing. Venta B2B a directivo o RR.HH."
        ),
        icon_name="Presentation",
        base_sections=(*_base_programa(), SK.PORTFOLIO),
        conditional_question_ids=("requires_physical_location", "has_specific_dates"),
        suitability_note_es=(
            "Cotización formal con alcance + entregables + fechas + costo "
            "para que el departamento de compras apruebe. Factura B2B."
        ),
        examples_es=(
            "Workshop Meta Ads equipo in-house",
            "Training IA para marketing",
            "Formación SEO técnico equipo",
            "Workshop copywriting comercial",
        ),
    ),
    "agencia_consultoria_estrategica": OfferTypePreset(
        preset_id="agencia_consultoria_estrategica",
        business_type=_EBT.AGENCIA_FREELANCE,
        archetype=_A.SERVICIO,
        typical_value_level=OfferValueLevel.MAXIMIZACION,
        label_es="Consultoría estratégica (sin ejecución)",
        description_es=(
            "Diagnóstico + plan estratégico sin ejecución incluida. El cliente implementa con su equipo. Alto margen."
        ),
        icon_name="Telescope",
        base_sections=(*_base_servicio(), SK.PORTFOLIO),
        suitability_note_es=(
            "Separar consultoría de ejecución permite vender a clientes "
            "con capacidad in-house. Follow-up de 30 días incluido suma valor."
        ),
        examples_es=(
            "Consultoría estratégica digital",
            "Plan de marketing anual",
            "Estrategia de contenido 12 meses",
            "Diagnóstico growth para Series A",
        ),
    ),
    "agencia_diagnostico_gratis": OfferTypePreset(
        preset_id="agencia_diagnostico_gratis",
        business_type=_EBT.AGENCIA_FREELANCE,
        archetype=_A.SERVICIO,
        typical_value_level=OfferValueLevel.LEAD_MAGNET,
        label_es="Diagnóstico gratuito (lead magnet)",
        description_es=(
            "Auditoría corta gratis que entrega valor real y posiciona la "
            "agencia. Cierre a servicio pago en 30-40% de casos."
        ),
        icon_name="Search",
        base_sections=(
            SK.IDENTITY,
            SK.STRATEGY,
            SK.PROMISE,
            SK.SERVICE_DETAILS,
            SK.INSTRUCTORS,
            SK.CLOSING,
            SK.KNOWLEDGE,
            SK.FAQ,
            SK.GALLERY,
            SK.PORTFOLIO,
        ),
        default_flags=(PresetFlag.IS_LEAD_MAGNET,),
        suitability_note_es=(
            "Sin PRICING — es gratuito. Delivery automatizado (template + "
            "video Loom) mantiene margen. CLOSING propone servicio pago."
        ),
        examples_es=(
            "Auditoría SEO gratuita 15min",
            "Diagnóstico ads gratis + Loom",
            "Revisión web express sin costo",
            "Análisis competencia 30min gratis",
        ),
    ),
    "agencia_enterprise_msa": OfferTypePreset(
        preset_id="agencia_enterprise_msa",
        business_type=_EBT.AGENCIA_FREELANCE,
        archetype=_A.MEMBRESIA,
        typical_value_level=OfferValueLevel.CORPORATIVO,
        label_es="MSA enterprise / contrato anual",
        description_es=(
            "Master Service Agreement con scope multi-proyecto, equipo "
            "dedicado y SLA. Vs el retainer PYME, opera con statement of work "
            "por iniciativa, comité de gobierno y facturación enterprise."
        ),
        icon_name="ScrollText",
        base_sections=(*_base_membresia(), SK.PORTFOLIO),
        conditional_question_ids=("has_team_or_speakers",),
        default_flags=(PresetFlag.RECURRING_BILLING, PresetFlag.HIGH_TICKET),
        suitability_note_es=(
            "Decisor: CMO, CTO o área de Procurement. Contrato MSA + SOW por "
            "proyecto + NDA + SLA con créditos por incumplimiento. Reporte "
            "mensual de horas/entregables. Renovación anual con review de QBR."
        ),
        examples_es=(
            "MSA anual marketing digital enterprise",
            "Contrato desarrollo software dedicated team",
            "MSA branding multi-marca corporativo",
            "Acuerdo anual gestión campañas regional",
        ),
    ),
    # ────────────────────────────────────────────────────────────────────────
    # 7. MARCA_ECOMMERCE (8 presets)
    # ────────────────────────────────────────────────────────────────────────
    "ecom_producto_fisico": OfferTypePreset(
        preset_id="ecom_producto_fisico",
        business_type=_EBT.MARCA_ECOMMERCE,
        archetype=_A.PRODUCTO,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Producto físico",
        description_es=(
            "Ítem individual del catálogo — ropa, cosmética, suplemento, "
            "artesanía. Compra transaccional con envío a domicilio."
        ),
        icon_name="ShoppingBag",
        base_sections=_base_producto(),
        suitability_note_es=(
            "Costo envío + tiempo de entrega + cobertura geográfica es "
            "decisivo. Cuotas sin interés y COD (cash on delivery) suben "
            "conversión Latam."
        ),
        examples_es=(
            "Remera minimalista",
            "Crema facial natural",
            "Suplemento proteína vegetal",
            "Collar artesanal",
        ),
    ),
    "ecom_kit_combo": OfferTypePreset(
        preset_id="ecom_kit_combo",
        business_type=_EBT.MARCA_ECOMMERCE,
        archetype=_A.PRODUCTO,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Kit o combo",
        description_es=(
            "Bundle de 2-5 productos con precio combinado inferior al "
            "individual. Eleva ticket medio y reduce costo de adquisición."
        ),
        icon_name="Boxes",
        base_sections=_base_producto(),
        suitability_note_es=(
            "VALUE_STACK con precio individual vs kit muestra ahorro real. "
            "Combos de regalo (día de la madre, navidad) son estacionales fuertes."
        ),
        examples_es=(
            "Kit skincare completo",
            "Combo suplementos deportivos",
            "Set 3 remeras básicas",
            "Bundle accesorios mascota",
        ),
    ),
    "ecom_suscripcion_reposicion": OfferTypePreset(
        preset_id="ecom_suscripcion_reposicion",
        business_type=_EBT.MARCA_ECOMMERCE,
        archetype=_A.MEMBRESIA,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Suscripción de reposición",
        description_es=(
            "Envío recurrente automático — cosmética mensual, suplemento "
            "trimestral. LTV alto, churn moderado si producto es consumible."
        ),
        icon_name="RefreshCw",
        base_sections=_base_membresia(),
        default_flags=(PresetFlag.RECURRING_BILLING,),
        suitability_note_es=(
            "Descuento vs compra única (10-20%) + flexibilidad de pausar/"
            "saltar envío reduce churn. Primer envío gratis es potente hook."
        ),
        examples_es=(
            "Skincare mensual membresía",
            "Café especial trimestral",
            "Suscripción suplementos deportivos",
            "Reposición limpiadores ecológicos",
        ),
    ),
    "ecom_membresia_vip": OfferTypePreset(
        preset_id="ecom_membresia_vip",
        business_type=_EBT.MARCA_ECOMMERCE,
        archetype=_A.MEMBRESIA,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Membresía VIP / club",
        description_es=(
            "Acceso exclusivo a preventa, descuentos permanentes, ediciones "
            "limitadas, regalos de aniversario. Customer loyalty."
        ),
        icon_name="Medal",
        base_sections=_base_membresia(),
        default_flags=(PresetFlag.RECURRING_BILLING,),
        suitability_note_es=(
            "Anual con 1-2 productos exclusivos incluidos amortiza la membresía y aumenta perceived value."
        ),
        examples_es=(
            "Club moda anual con preventa",
            "VIP skincare con drops exclusivos",
            "Membresía suplementos 15% off permanente",
            "Club colecciones limitadas",
        ),
    ),
    "ecom_producto_digital": OfferTypePreset(
        preset_id="ecom_producto_digital",
        business_type=_EBT.MARCA_ECOMMERCE,
        archetype=_A.PRODUCTO,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Producto digital asociado",
        description_es=(
            "Ebook, meal plan, guía de uso, rutina descargable. Upsell "
            "digital de alto margen post-compra de producto físico."
        ),
        icon_name="FileDown",
        base_sections=_base_producto(),
        conditional_question_ids=("delivers_downloadable_materials",),
        suitability_note_es=(
            "Potente como upsell inmediato post-checkout (+30% AOV típico). "
            "Cross-sell con el producto físico en retargeting email."
        ),
        examples_es=(
            "Meal plan 4 semanas veganas",
            "Guía cuidado prendas premium",
            "Rutina ejercicios con material propio",
            "Recetario premium marca de condimentos",
        ),
    ),
    "ecom_popup_evento": OfferTypePreset(
        preset_id="ecom_popup_evento",
        business_type=_EBT.MARCA_ECOMMERCE,
        archetype=_A.EXPERIENCIA,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Pop-up / evento de marca",
        description_es=(
            "Experiencia presencial temporal — tienda pop-up, fitting day, "
            "launch event. Brand building + ventas presenciales."
        ),
        icon_name="Tent",
        base_sections=_base_experiencia(),
        conditional_question_ids=("has_limited_capacity", "has_specific_dates"),
        default_flags=(PresetFlag.REQUIRES_START_DATE,),
        suitability_note_es=(
            "RSVP via WhatsApp permite tracking de asistencia. Influencers locales pueden amplificar alcance."
        ),
        examples_es=(
            "Pop-up CDMX fin de semana",
            "Launch de colección en Polanco",
            "Fitting day en Miraflores",
            "Evento marca de café en Medellín",
        ),
    ),
    "ecom_asesoria_uso": OfferTypePreset(
        preset_id="ecom_asesoria_uso",
        business_type=_EBT.MARCA_ECOMMERCE,
        archetype=_A.SERVICIO,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Asesoría de uso de producto",
        description_es=(
            "Consulta 1:1 para personalizar el uso del producto — rutina "
            "skincare, plan nutricional con suplementos, estilismo. "
            "Post-venta opcional."
        ),
        icon_name="HeadphonesIcon",
        base_sections=_base_servicio(),
        suitability_note_es=(
            "Edge case ecommerce — usa solo si aporta margen diferencial. Brand loyalty efecto secundario potente."
        ),
        examples_es=(
            "Asesoría skincare personalizada",
            "Estilismo con prendas de la marca",
            "Plan nutrición con suplementos propios",
            "Asesoría cuidado mascota + productos",
        ),
    ),
    "ecom_corporate_bulk": OfferTypePreset(
        preset_id="ecom_corporate_bulk",
        business_type=_EBT.MARCA_ECOMMERCE,
        archetype=_A.PRODUCTO,
        typical_value_level=OfferValueLevel.CORPORATIVO,
        label_es="Pedido corporativo bulk",
        description_es=(
            "Compra al por mayor de productos para uso empresarial — regalos "
            "corporativos, merchandising, gift-pack para clientes/empleados, "
            "pedido para reventa. Ticket único alto, customización opcional."
        ),
        icon_name="PackageCheck",
        base_sections=(*_base_producto(), SK.PORTFOLIO),
        conditional_question_ids=("delivers_downloadable_materials",),
        default_flags=(PresetFlag.HIGH_TICKET,),
        suitability_note_es=(
            "Cotización formal + factura B2B + plazo de producción claro. "
            "Customización (logo, packaging) suma margen. Estacionalidad fuerte "
            "Latam: día de la madre, navidad, fin de año fiscal. Mínimo de "
            "unidades + descuento por volumen escalonado."
        ),
        examples_es=(
            "Gift-pack navidad para clientes (500 uds)",
            "Welcome kit empleados nuevos",
            "Merchandising aniversario corporativo",
            "Pedido mayorista para reventa B2B",
        ),
    ),
    # ────────────────────────────────────────────────────────────────────────
    # 8. NEGOCIO_LOCAL (11 presets)
    # ────────────────────────────────────────────────────────────────────────
    "local_sesion_suelta": OfferTypePreset(
        preset_id="local_sesion_suelta",
        business_type=_EBT.NEGOCIO_LOCAL,
        archetype=_A.SERVICIO,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Sesión / entrada suelta",
        description_es=(
            "Uso puntual del local — pase de día gym, corte suelto "
            "peluquería, clase individual de pilates. Sin compromiso."
        ),
        icon_name="Ticket",
        base_sections=(*_base_servicio(), SK.LOCATION),
        suitability_note_es=(
            "Conversión a plan mensual post-uso es la métrica clave. "
            "Pago efectivo en punto de venta sigue vigente Latam."
        ),
        examples_es=(
            "Pase día gimnasio",
            "Corte de pelo suelto",
            "Clase individual yoga",
            "Entrada clase de baile",
        ),
    ),
    "local_bono_sesiones": OfferTypePreset(
        preset_id="local_bono_sesiones",
        business_type=_EBT.NEGOCIO_LOCAL,
        archetype=_A.PROGRAMA,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Bono de sesiones",
        description_es=(
            "Pack de 10-30 sesiones prepagadas con descuento vs suelta. "
            "Entrada al plan mensual sin compromiso continuo."
        ),
        icon_name="Layers",
        base_sections=(*_base_programa(), SK.LOCATION),
        suitability_note_es=(
            "Caducidad (3-6 meses) protege contra dilación. Transferibles a familiares suma valor percibido."
        ),
        examples_es=(
            "10 clases pilates",
            "Bono 20 sesiones gym",
            "Pack 5 cortes peluquería",
            "Bono 30 clases baile",
        ),
    ),
    "local_plan_mensual": OfferTypePreset(
        preset_id="local_plan_mensual",
        business_type=_EBT.NEGOCIO_LOCAL,
        archetype=_A.MEMBRESIA,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Plan mensual",
        description_es=(
            "Acceso ilimitado al local por un mes con cargo recurrente. Producto estrella de gym, estudio, spa."
        ),
        icon_name="Calendar",
        base_sections=(*_base_membresia(), SK.LOCATION),
        default_flags=(PresetFlag.RECURRING_BILLING,),
        suitability_note_es=(
            "Permanencia mínima (3 meses) vs mes-a-mes con prima son "
            "modelos Latam dominantes. Mercado Pago débito automático."
        ),
        examples_es=(
            "Plan mensual gym ilimitado",
            "Membresía estudio pilates",
            "Plan mensual spa + clases",
            "Membresía box crossfit",
        ),
    ),
    "local_plan_anual": OfferTypePreset(
        preset_id="local_plan_anual",
        business_type=_EBT.NEGOCIO_LOCAL,
        archetype=_A.MEMBRESIA,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Plan anual con descuento",
        description_es=(
            "Cargo único anual con descuento de 2-3 meses vs mensual. Locks in long-term member y mejora cashflow."
        ),
        icon_name="CalendarClock",
        base_sections=(*_base_membresia(), SK.LOCATION),
        default_flags=(PresetFlag.RECURRING_BILLING,),
        suitability_note_es=(
            "Cuotas de 12 meses sin interés vs cargo único tienen LTV equivalente pero financiación aumenta acceso."
        ),
        examples_es=(
            "Plan anual gym (2 meses free)",
            "Membresía anual pilates",
            "Plan anual spa familiar",
            "Membresía anual estudio danza",
        ),
    ),
    "local_servicio_premium": OfferTypePreset(
        preset_id="local_servicio_premium",
        business_type=_EBT.NEGOCIO_LOCAL,
        archetype=_A.SERVICIO,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Servicio premium",
        description_es=(
            "Servicio específico de alto valor — corte + color, tratamiento facial, masaje terapéutico. Cita reservada."
        ),
        icon_name="Sparkle",
        base_sections=(*_base_servicio(), SK.LOCATION),
        conditional_question_ids=("has_team_or_speakers",),
        suitability_note_es=(
            "Reserva online o WhatsApp es el estándar. Permitir elegir profesional específico sube ticket medio."
        ),
        examples_es=(
            "Color + corte premium",
            "Tratamiento facial express",
            "Masaje terapéutico 90min",
            "Spa full body + alimentos",
        ),
    ),
    "local_clase_especial": OfferTypePreset(
        preset_id="local_clase_especial",
        business_type=_EBT.NEGOCIO_LOCAL,
        archetype=_A.EXPERIENCIA,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Clase especial / masterclass",
        description_es=(
            "Evento único dentro del local — masterclass yoga con invitado, "
            "taller cocina especial, clase temática. Ticketizado."
        ),
        icon_name="PartyPopper",
        base_sections=_base_experiencia(),
        conditional_question_ids=("has_limited_capacity", "has_team_or_speakers"),
        default_flags=(PresetFlag.REQUIRES_START_DATE, PresetFlag.SUPPORTS_CAPACITY),
        suitability_note_es=("Abierto a no-miembros con ticket más alto. Acquisition de leads para plan mensual."),
        examples_es=(
            "Masterclass con coach invitado",
            "Taller pilates embarazadas",
            "Clase especial día de la madre",
            "Sesión sound healing",
        ),
    ),
    "local_retail": OfferTypePreset(
        preset_id="local_retail",
        business_type=_EBT.NEGOCIO_LOCAL,
        archetype=_A.PRODUCTO,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Retail en el local",
        description_es=(
            "Productos físicos vendidos en el local — shakes proteicos "
            "en gym, productos capilares en salón. Upsell presencial."
        ),
        icon_name="ShoppingCart",
        base_sections=_base_producto(),
        suitability_note_es=(
            "Edge case — se compra en persona, sin envío. PRODUCT_DETAILS enfocado en uso + beneficio + marca."
        ),
        examples_es=(
            "Shakes proteicos del gym",
            "Shampoo profesional del salón",
            "Suplementos clínicos del centro",
            "Merchandising de la academia",
        ),
    ),
    "local_gift_card": OfferTypePreset(
        preset_id="local_gift_card",
        business_type=_EBT.NEGOCIO_LOCAL,
        archetype=_A.PRODUCTO,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Gift card",
        description_es=(
            "Voucher de valor pre-cargado para usar en el local. Canjeable por servicios o productos. Regalo ideal."
        ),
        icon_name="Gift",
        base_sections=(
            SK.IDENTITY,
            SK.PROMISE,
            SK.PRODUCT_DETAILS,
            SK.PRICING,
            SK.CLOSING,
            SK.GALLERY,
            SK.FAQ,
        ),
        suitability_note_es=(
            "Edge case: compras valor, no servicio específico. Caducidad "
            "legal varía por país — en Argentina no caduca, México sí."
        ),
        examples_es=(
            "Gift card salón USD 50",
            "Voucher spa regalo",
            "Gift card gym 1 mes",
            "Tarjeta regalo peluquería",
        ),
    ),
    "local_challenge_transformacion": OfferTypePreset(
        preset_id="local_challenge_transformacion",
        business_type=_EBT.NEGOCIO_LOCAL,
        archetype=_A.PROGRAMA,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Challenge de transformación",
        description_es=(
            "Reto de 4-8 semanas con resultado visible — fitness 6 semanas "
            "en gym, transformación capilar, detox. Inscripción con fecha "
            "fija."
        ),
        icon_name="TrendingUp",
        base_sections=(*_base_programa(), SK.LOCATION, SK.PORTFOLIO),
        conditional_question_ids=("has_specific_dates", "has_limited_capacity"),
        default_flags=(PresetFlag.REQUIRES_START_DATE,),
        suitability_note_es=(
            "Antes/después en GALLERY + PORTFOLIO es la venta. Premio "
            "al finalizar (mes gratis, producto) maximiza completion."
        ),
        examples_es=(
            "Challenge fitness 6 semanas",
            "Reto transformación capilar",
            "Programa detox 4 semanas",
            "Challenge bikini summer",
        ),
    ),
    "local_evento_local": OfferTypePreset(
        preset_id="local_evento_local",
        business_type=_EBT.NEGOCIO_LOCAL,
        archetype=_A.EXPERIENCIA,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Grand opening / evento local",
        description_es=(
            "Evento del local para la comunidad — inauguración, aniversario, "
            "open house. Brand building + customer acquisition."
        ),
        icon_name="Cake",
        base_sections=_base_experiencia(),
        conditional_question_ids=("has_limited_capacity",),
        default_flags=(PresetFlag.REQUIRES_START_DATE,),
        suitability_note_es=(
            "Gratis o simbolico generates footfall. Oferta exclusiva del "
            "día (descuento en plan mensual) convierte asistentes a miembros."
        ),
        examples_es=(
            "Grand opening nuevo gym",
            "Aniversario salón 10 años",
            "Open house clínica",
            "Fiesta anual estudio danza",
        ),
    ),
    "local_convenio_empresarial": OfferTypePreset(
        preset_id="local_convenio_empresarial",
        business_type=_EBT.NEGOCIO_LOCAL,
        archetype=_A.MEMBRESIA,
        typical_value_level=OfferValueLevel.CORPORATIVO,
        label_es="Convenio empresarial B2B",
        description_es=(
            "Plan para empresas con descuento al equipo — gym corporativo, "
            "spa para empleados. Venta a RR.HH. o beneficios."
        ),
        icon_name="Building",
        base_sections=(*_base_membresia(), SK.LOCATION, SK.PORTFOLIO),
        conditional_question_ids=("has_team_or_speakers",),
        default_flags=(PresetFlag.RECURRING_BILLING,),
        suitability_note_es=(
            "Contrato formal + facturación B2B + mínimo de empleados activos "
            "sostiene el modelo. Reporte trimestral de uso renueva el contrato."
        ),
        examples_es=(
            "Gym corporativo empresa 50+ empleados",
            "Spa beneficio RR.HH.",
            "Pilates corporativo semanal",
            "Plan bienestar laboral",
        ),
    ),
    # ────────────────────────────────────────────────────────────────────────
    # 9. SOFTWARE_SAAS (8 presets)
    # ────────────────────────────────────────────────────────────────────────
    "saas_plan_tier": OfferTypePreset(
        preset_id="saas_plan_tier",
        business_type=_EBT.SOFTWARE_SAAS,
        archetype=_A.MEMBRESIA,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Plan Starter / Pro / Enterprise",
        description_es=(
            "Tiered subscription típica SaaS — plan por funcionalidades "
            "y seats. Starter = entrada, Pro = mainstream, Enterprise = "
            "custom."
        ),
        icon_name="Layers3",
        base_sections=(*_base_membresia(), SK.PLATFORM_DETAILS, SK.PORTFOLIO),
        default_flags=(PresetFlag.RECURRING_BILLING,),
        suitability_note_es=(
            "Anual con 15-20% off reduce churn. Facturación USD para "
            "LATAM puede requerir dLocal, Kushki o Mercado Pago. Usar "
            "Variant TIER para estructurar los 3 planes."
        ),
        examples_es=(
            "SaaS CRM PYMEs 3 planes",
            "Plataforma email marketing",
            "Tool analítica Pro/Enterprise",
            "App productividad freemium",
        ),
    ),
    "saas_trial_gratis": OfferTypePreset(
        preset_id="saas_trial_gratis",
        business_type=_EBT.SOFTWARE_SAAS,
        archetype=_A.MEMBRESIA,
        typical_value_level=OfferValueLevel.LEAD_MAGNET,
        label_es="Trial gratuito",
        description_es=(
            "Free tier o trial de 14-30 días con todas las features. "
            "Product-led growth — el usuario se convierte al experimentar valor."
        ),
        icon_name="PlayCircle",
        base_sections=(
            SK.IDENTITY,
            SK.STRATEGY,
            SK.PROMISE,
            SK.SUBSCRIPTION_DETAILS,
            SK.PLATFORM_DETAILS,
            SK.CLOSING,
            SK.KNOWLEDGE,
            SK.FAQ,
            SK.GALLERY,
        ),
        default_flags=(PresetFlag.IS_LEAD_MAGNET,),
        suitability_note_es=(
            "Sin PRICING — es gratis. Requiere tarjeta o no afecta conversión "
            "significativamente. Onboarding guiado en app es lo que convierte."
        ),
        examples_es=(
            "Trial 14 días SaaS CRM",
            "Free tier con limit de uso",
            "Trial 30 días email marketing",
            "Freemium tool de productividad",
        ),
    ),
    "saas_onboarding": OfferTypePreset(
        preset_id="saas_onboarding",
        business_type=_EBT.SOFTWARE_SAAS,
        archetype=_A.SERVICIO,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Onboarding / setup inicial",
        description_es=(
            "Servicio one-time de configuración, importación de datos, "
            "entrenamiento inicial. Ticket único que asegura time-to-value."
        ),
        icon_name="Rocket",
        base_sections=(*_base_servicio(), SK.PORTFOLIO),
        suitability_note_es=(
            "Enterprise plans suelen incluir onboarding gratis. SMB plan "
            "cobra aparte USD 500-2000. Acelera activación y reduce churn."
        ),
        examples_es=(
            "Setup CRM enterprise",
            "Importación + training 1 semana",
            "Onboarding premium SaaS",
            "Setup dedicado PYMEs",
        ),
    ),
    "saas_integracion_custom": OfferTypePreset(
        preset_id="saas_integracion_custom",
        business_type=_EBT.SOFTWARE_SAAS,
        archetype=_A.SERVICIO,
        typical_value_level=OfferValueLevel.CORPORATIVO,
        label_es="Integración custom enterprise",
        description_es=(
            "Desarrollo específico para un cliente enterprise — conector, "
            "workflow custom, feature particular. Alto ticket, largo "
            "sales cycle."
        ),
        icon_name="Cog",
        base_sections=(*_base_servicio(), SK.PORTFOLIO),
        conditional_question_ids=("has_specific_dates", "has_team_or_speakers"),
        default_flags=(PresetFlag.HIGH_TICKET,),
        suitability_note_es=(
            "Scope-in/out crítico. SLA de entrega + maintenance post-delivery "
            "en SERVICE_DETAILS. Factura hitos del proyecto."
        ),
        examples_es=(
            "Integración Salesforce custom",
            "Workflow específico enterprise",
            "API custom para banco",
            "Conector ERP legacy",
        ),
    ),
    "saas_training_certificacion": OfferTypePreset(
        preset_id="saas_training_certificacion",
        business_type=_EBT.SOFTWARE_SAAS,
        archetype=_A.PROGRAMA,
        typical_value_level=OfferValueLevel.TRANSFORMACION,
        label_es="Training / certificación",
        description_es=(
            "Programa educativo sobre uso avanzado de la plataforma. "
            "Certificación verificable que usuarios pueden listar en LinkedIn."
        ),
        icon_name="Award",
        base_sections=(*_base_programa(), SK.PORTFOLIO),
        conditional_question_ids=("has_specific_dates",),
        suitability_note_es=(
            "Certificación verificable (QR + página pública) suma valor "
            "para el profesional y publicidad gratis para el SaaS."
        ),
        examples_es=(
            "Certificación HubSpot Ads",
            "Training avanzado Notion",
            "Certificación Shopify Partner",
            "Curso certificado Airtable",
        ),
    ),
    "saas_comunidad_usuarios": OfferTypePreset(
        preset_id="saas_comunidad_usuarios",
        business_type=_EBT.SOFTWARE_SAAS,
        archetype=_A.MEMBRESIA,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Comunidad de usuarios",
        description_es=(
            "Espacio privado para clientes — Circle, Slack privado, Discord. "
            "Puede ser gratis (incluida en plan) o paga (premium tier)."
        ),
        icon_name="MessageSquare",
        base_sections=(*_base_membresia(), SK.PLATFORM_DETAILS),
        default_flags=(PresetFlag.RECURRING_BILLING,),
        suitability_note_es=(
            "Puede ser acceso gratis (valor percibido del plan) o tier "
            "premium separado. Eventos mensuales + AMAs con el equipo."
        ),
        examples_es=(
            "Comunidad Circle usuarios SaaS",
            "Slack privado clientes enterprise",
            "Discord de power users",
            "Comunidad Pro-plan",
        ),
    ),
    "saas_addon": OfferTypePreset(
        preset_id="saas_addon",
        business_type=_EBT.SOFTWARE_SAAS,
        archetype=_A.MEMBRESIA,
        typical_value_level=OfferValueLevel.ACTIVACION,
        label_es="Addon / feature adicional",
        description_es=(
            "Extensión cobrada aparte del plan base — SMS pack, storage extra, AI credits. Expansion revenue puro."
        ),
        icon_name="Puzzle",
        base_sections=(*_base_membresia(), SK.PLATFORM_DETAILS),
        default_flags=(PresetFlag.RECURRING_BILLING,),
        suitability_note_es=(
            "Edge case: puede modelarse como Variant del plan base o "
            "oferta independiente. Usa oferta independiente si tiene "
            "landing propia o se vende cross-sell."
        ),
        examples_es=(
            "Pack AI credits 10k/mes",
            "Storage extra 100GB",
            "SMS pack 1000/mes",
            "Módulo analytics avanzado",
        ),
    ),
    "saas_enterprise_license": OfferTypePreset(
        preset_id="saas_enterprise_license",
        business_type=_EBT.SOFTWARE_SAAS,
        archetype=_A.MEMBRESIA,
        typical_value_level=OfferValueLevel.CORPORATIVO,
        label_es="Plan Enterprise (SLA + dedicated)",
        description_es=(
            "Plan corporativo del SaaS con SLA garantizado, customer success "
            "dedicado, SSO, audit logs y features enterprise. Vs los planes "
            "tier (Starter/Pro), opera con contrato anual y procurement formal."
        ),
        icon_name="ShieldCheck",
        base_sections=(*_base_membresia(), SK.PLATFORM_DETAILS, SK.PORTFOLIO),
        conditional_question_ids=("has_team_or_speakers",),
        default_flags=(PresetFlag.RECURRING_BILLING, PresetFlag.HIGH_TICKET),
        suitability_note_es=(
            "Sales cycle 3-9 meses. Decisor: CTO/CIO + Procurement + Legal. "
            "MSA + DPA + cuestionario de seguridad son entregables previos al "
            "contrato. SOC 2, GDPR/LGPD compliance son table stakes. Pricing "
            "negociado por seats + features + commitment anual."
        ),
        examples_es=(
            "Plan Enterprise CRM con SSO + audit",
            "Licencia anual plataforma comunicación",
            "SaaS B2B Enterprise tier custom",
            "Plan dedicated con CSM asignado",
        ),
    ),
}


def get_preset(preset_id: str) -> OfferTypePreset:
    """Return the preset record for ``preset_id``.

    Raises :class:`KeyError` if the id is unknown. Under the architecture
    test ``test_every_preset_has_unique_id`` collisions are impossible —
    the catalog dict enforces uniqueness at module load.
    """
    return OFFER_TYPE_PRESET_CATALOG[preset_id]


def get_presets_for_business_types(
    business_types: tuple[ExpertBusinessType, ...] | None = None,
) -> tuple[OfferTypePreset, ...]:
    """Return presets filtered by tenant's business_types.

    When ``business_types`` is ``None`` or empty, returns the full catalog
    (useful for the admin view or the initial discovery flow). Otherwise,
    returns only presets whose ``business_type`` is in the set — tenants
    marked with multiple types get the union.
    """
    if not business_types:
        return tuple(OFFER_TYPE_PRESET_CATALOG.values())
    allowed = set(business_types)
    return tuple(p for p in OFFER_TYPE_PRESET_CATALOG.values() if p.business_type in allowed)


def resolve_preset_sections(preset_id: str, answers: dict[str, bool]) -> tuple[SectionKey, ...]:
    """Resolve the final ordered section list for ``preset_id`` + answers.

    Starts from ``base_sections`` in declared order, then appends any
    ``on_yes_sections`` from conditional questions the user answered
    affirmatively. Duplicates are removed preserving first-occurrence
    order so the base sections stay on top of the editor rail.
    """
    preset = OFFER_TYPE_PRESET_CATALOG[preset_id]
    result: list[SectionKey] = list(preset.base_sections)
    for qid in preset.conditional_question_ids:
        if answers.get(qid, False):
            question = QUESTION_REGISTRY[qid]
            for section in question.on_yes_sections:
                if section not in result:
                    result.append(section)
    return tuple(result)


def resolve_preset_flags(preset_id: str, answers: dict[str, bool]) -> tuple[PresetFlag, ...]:
    """Resolve the combined flags for ``preset_id`` + answers.

    Default flags from the preset are combined with flags contributed by
    YES-answered conditional questions. Order is preserved and duplicates
    are removed.
    """
    preset = OFFER_TYPE_PRESET_CATALOG[preset_id]
    result: list[PresetFlag] = list(preset.default_flags)
    for qid in preset.conditional_question_ids:
        if answers.get(qid, False):
            question = QUESTION_REGISTRY[qid]
            for flag in question.on_yes_flags:
                if flag not in result:
                    result.append(flag)
    return tuple(result)
