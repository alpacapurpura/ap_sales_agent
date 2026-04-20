"""ExpertBusinessType — cross-module SSoT for the expert business a tenant runs.

This classification drives:

- **Brand Studio** captures ``business_types: list[ExpertBusinessType]`` on
  the tenant's ``BrandIdentity`` (multi-select — a nutricionist with a
  consultorio can also sell a course).
- **Offer Studio Format Catalog** declares per-format suitability
  (``suitable_for: dict[ExpertBusinessType, float]``) so the offer wizard
  surfaces formats that fit the tenant's profile and hides the ones that
  don't.

The 9 types are tuned for Latam mass-market: each one captures a distinct
way of monetizing expertise via digital marketing — from the doctor with a
consultorio to the founder of a micro-SaaS. Multi-select is the norm
(e.g. a psychologist who also runs a course → marks ``PROFESIONAL_SALUD``
and ``ACADEMIA_INFOPRODUCTOR``).

Living in ``shared/domain`` avoids a DDD cross-module import: the enum is
owned by the platform, not by any single bounded context, and is safe to
reference from brand, offer, analytics, and any future consumer.

The metadata catalog is colocated with the enum for the same reason. Both
the Brand Studio onboarding UI and the Offer Studio wizard need the same
labels, descriptions, and icons — a single frozen record per type prevents
drift.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ExpertBusinessType(StrEnum):
    """The nine canonical kinds of expert business Nicolify targets in Latam.

    Multi-select by convention: most real businesses blend two or three
    types (e.g. a dentist who also hosts a paid community, or an agency
    owner who also teaches a bootcamp).
    """

    PROFESIONAL_SALUD = "profesional_salud"
    CONSULTOR_PROFESIONAL = "consultor_profesional"
    COACH_MENTOR = "coach_mentor"
    ACADEMIA_INFOPRODUCTOR = "academia_infoproductor"
    ANFITRION_PRODUCTOR = "anfitrion_productor"
    AGENCIA_FREELANCE = "agencia_freelance"
    MARCA_ECOMMERCE = "marca_ecommerce"
    NEGOCIO_LOCAL = "negocio_local"
    SOFTWARE_SAAS = "software_saas"


@dataclass(frozen=True, slots=True)
class ExpertBusinessTypeMetadata:
    """Localized presentation data for one ``ExpertBusinessType``.

    ``icon_name`` is a Lucide React component name (PascalCase) — the
    frontend resolves the string to an icon component via a typed map.

    ``value_proposition_es`` is a 3-5 word chip used in badges and compact
    cards; ``revenue_model_es`` is a single sentence describing how the
    business typically charges — used in wizard copy and analytics hints.
    """

    business_type: ExpertBusinessType
    label_es: str
    description_es: str
    value_proposition_es: str  # 3-5 words for chip/badge UI
    revenue_model_es: str  # one-liner describing typical billing model
    icon_name: str  # Lucide React PascalCase
    examples_es: tuple[str, ...] = field(default_factory=tuple)


EXPERT_BUSINESS_TYPE_CATALOG: dict[ExpertBusinessType, ExpertBusinessTypeMetadata] = {
    ExpertBusinessType.PROFESIONAL_SALUD: ExpertBusinessTypeMetadata(
        business_type=ExpertBusinessType.PROFESIONAL_SALUD,
        label_es="Profesional / Consultorio Salud",
        description_es=(
            "Tu título profesional es tu marca y atendés por cita. Cada paciente agenda una consulta "
            "y vuelve por tratamientos o controles."
        ),
        value_proposition_es="Salud con cita",
        revenue_model_es="Consulta por sesión + paquetes de tratamiento recurrentes",
        icon_name="Stethoscope",
        examples_es=(
            "Odontólogo",
            "Nutricionista online",
            "Psicólogo con consulta virtual",
            "Cirujano estético",
            "Fisioterapeuta / kinesiólogo",
            "Veterinario",
        ),
    ),
    ExpertBusinessType.CONSULTOR_PROFESIONAL: ExpertBusinessTypeMetadata(
        business_type=ExpertBusinessType.CONSULTOR_PROFESIONAL,
        label_es="Consultorías Profesionales",
        description_es=(
            "Ejercés una profesión del conocimiento con clientes propios. Vendés tu criterio "
            "por proyecto, retainer o asesoría puntual."
        ),
        value_proposition_es="Criterio aplicado a proyectos",
        revenue_model_es="Proyecto por scope + retainer mensual o consultas puntuales",
        icon_name="Scale",
        examples_es=(
            "Abogado especialista (laboral, migratorio, familia)",
            "Contador para PYMES",
            "Arquitecto / diseñador de interiores",
            "Asesor financiero",
            "Consultor de marketing digital",
            "Consultor estratégico de negocios",
        ),
    ),
    ExpertBusinessType.COACH_MENTOR: ExpertBusinessTypeMetadata(
        business_type=ExpertBusinessType.COACH_MENTOR,
        label_es="Coach / Mentor",
        description_es=(
            "Acompañás a otros a crecer o transformarse. Vendés procesos de acompañamiento "
            "con resultados medibles en tiempo definido."
        ),
        value_proposition_es="Acompañamiento transformador",
        revenue_model_es="Paquetes de sesiones 1:1 o grupales de 3-6 meses",
        icon_name="Compass",
        examples_es=(
            "Coach de negocios / mentor empresarial",
            "Coach de finanzas personales",
            "Coach de salud y pérdida de peso",
            "Coach de pareja y relaciones",
            "Mentor de ventas high-ticket",
            "Coach fitness y transformación",
        ),
    ),
    ExpertBusinessType.ACADEMIA_INFOPRODUCTOR: ExpertBusinessTypeMetadata(
        business_type=ExpertBusinessType.ACADEMIA_INFOPRODUCTOR,
        label_es="Academia / Infoproductor",
        description_es=(
            "Enseñás tu método a muchos en formato empaquetado. Tu expertise vive en cursos, "
            "cohortes o certificaciones con alumnos a escala."
        ),
        value_proposition_es="Método empaquetado escalable",
        revenue_model_es="Cursos one-shot + cohortes con lanzamiento + membresía académica",
        icon_name="BookMarked",
        examples_es=(
            "Bootcamp de programación",
            "Academia de inglés online",
            "Curso de trading e inversiones",
            "Cohorte de marketing digital",
            "Certificación profesional (Scrum / PMP)",
            "Academia de música o canto online",
        ),
    ),
    ExpertBusinessType.ANFITRION_PRODUCTOR: ExpertBusinessTypeMetadata(
        business_type=ExpertBusinessType.ANFITRION_PRODUCTOR,
        label_es="Anfitrión / Productor",
        description_es=(
            "Reunís gente en vivo o construís pertenencia. Producís eventos, retiros o "
            "comunidades donde el valor es estar adentro."
        ),
        value_proposition_es="Experiencias y pertenencia",
        revenue_model_es="Entradas o ticket único + membresía de comunidad",
        icon_name="Sparkles",
        examples_es=(
            "Organizador de retiros (yoga / wellness / espiritual)",
            "Productor de masterminds high-ticket",
            "Host de conferencias y summits",
            "Fundador de comunidad paga",
            "Productor de eventos corporativos",
            "Organizador de festivales temáticos",
        ),
    ),
    ExpertBusinessType.AGENCIA_FREELANCE: ExpertBusinessTypeMetadata(
        business_type=ExpertBusinessType.AGENCIA_FREELANCE,
        label_es="Agencia / Freelance",
        description_es=(
            "Tu equipo (o vos solo) ejecuta proyectos para clientes. Entregás el trabajo "
            "terminado — el cliente aprueba, no hace."
        ),
        value_proposition_es="Ejecución hecha por vos",
        revenue_model_es="Proyecto por scope + retainer mensual recurrente",
        icon_name="Cog",
        examples_es=(
            "Agencia de marketing digital / ads",
            "Estudio de diseño y branding",
            "Estudio de desarrollo web",
            "Productora audiovisual y reels",
            "Consultora SEO y contenido",
            "Freelancer senior (copy / diseño / dev)",
        ),
    ),
    ExpertBusinessType.MARCA_ECOMMERCE: ExpertBusinessTypeMetadata(
        business_type=ExpertBusinessType.MARCA_ECOMMERCE,
        label_es="Marca / Ecommerce",
        description_es=(
            "Vendés productos propios o curados. Tu negocio vive en el catálogo, el carrito y la logística de entrega."
        ),
        value_proposition_es="Producto propio en escala",
        revenue_model_es="Venta transaccional + suscripción de reposición opcional",
        icon_name="ShoppingBag",
        examples_es=(
            "Marca de ropa o moda",
            "Cosmética natural / suplementos",
            "Productos saludables y fitness",
            "Productos para mascotas",
            "Artesanía o diseño propio",
            "Dropshipping / tienda online",
        ),
    ),
    ExpertBusinessType.NEGOCIO_LOCAL: ExpertBusinessTypeMetadata(
        business_type=ExpertBusinessType.NEGOCIO_LOCAL,
        label_es="Negocio Local",
        description_es=(
            "Tenés un local físico con clientes recurrentes y un equipo que atiende. "
            "La marca es del negocio, no tuya personal."
        ),
        value_proposition_es="Local físico con recurrencia",
        revenue_model_es="Membresía mensual o paquete de sesiones recurrentes",
        icon_name="Store",
        examples_es=(
            "Gimnasio / box de CrossFit",
            "Estudio de pilates o yoga",
            "Salón de belleza / barbería",
            "Clínica odontológica multi-doctor",
            "Academia de baile o idiomas",
            "Restaurante o cafetería",
        ),
    ),
    ExpertBusinessType.SOFTWARE_SAAS: ExpertBusinessTypeMetadata(
        business_type=ExpertBusinessType.SOFTWARE_SAAS,
        label_es="Software / SaaS",
        description_es=(
            "Tu producto es software que el cliente usa de forma continua. Cobrás por "
            "suscripción y el valor se entrega solo al usarlo."
        ),
        value_proposition_es="Software recurrente",
        revenue_model_es="Suscripción mensual o anual con tiers",
        icon_name="Terminal",
        examples_es=(
            "SaaS B2B para PYMEs",
            "Plataforma vertical (fintech / edtech / healthtech)",
            "Micro-SaaS indie",
            "App móvil vertical",
            "Herramienta de automatización",
        ),
    ),
}


def get_expert_business_type_metadata(
    business_type: ExpertBusinessType,
) -> ExpertBusinessTypeMetadata:
    """Return the metadata record for ``business_type``.

    The architecture test ``test_expert_business_type_catalog_completeness``
    guarantees every enum value has an entry, so in practice this lookup
    cannot raise at runtime.
    """
    return EXPERT_BUSINESS_TYPE_CATALOG[business_type]
