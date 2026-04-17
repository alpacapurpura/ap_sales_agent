"""ExpertBusinessType — cross-module SSoT for the expert business a tenant runs.

This classification drives:

- **Brand Studio** captures ``business_types: list[ExpertBusinessType]`` on
  the tenant's ``BrandIdentity`` (multi-select — a course creator can also
  be a coach).
- **Offer Studio Format Catalog** declares per-format suitability
  (``suitable_for: dict[ExpertBusinessType, float]``) so the offer wizard
  surfaces formats that fit the tenant's profile and hides the ones that
  don't (a lawyer-consultant is unlikely to run a multi-day retreat).

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
    """The nine canonical kinds of expert business Nicolify targets.

    Multi-select by convention: most real businesses blend two or three
    types (e.g. an educator who also coaches, or a community host who
    produces experiences).
    """

    CONSULTOR_ASESOR = "consultor_asesor"
    COACH_MENTOR = "coach_mentor"
    EDUCADOR_INFOPRODUCTOR = "educador_infoproductor"
    AGENCIA_DFY = "agencia_dfy"
    HOST_COMUNIDAD = "host_comunidad"
    HOST_EXPERIENCIA = "host_experiencia"
    CREADOR_CONTENIDO = "creador_contenido"
    PRODUCT_MAKER = "product_maker"
    SAAS_FOUNDER = "saas_founder"


@dataclass(frozen=True, slots=True)
class ExpertBusinessTypeMetadata:
    """Localized presentation data for one ``ExpertBusinessType``.

    ``icon_name`` is a Lucide React component name (PascalCase) — the
    frontend resolves the string to an icon component via a typed map.
    """

    business_type: ExpertBusinessType
    label_es: str
    description_es: str
    sells_es: str  # "sells X" — one-liner capturing the value proposition
    icon_name: str  # Lucide React PascalCase
    examples_es: tuple[str, ...] = field(default_factory=tuple)


EXPERT_BUSINESS_TYPE_CATALOG: dict[ExpertBusinessType, ExpertBusinessTypeMetadata] = {
    ExpertBusinessType.CONSULTOR_ASESOR: ExpertBusinessTypeMetadata(
        business_type=ExpertBusinessType.CONSULTOR_ASESOR,
        label_es="Consultor / Asesor",
        description_es=("Vende expertise estratégica 1:1. Tickets altos, entregables por proyecto o retainer."),
        sells_es="Sabiduría estratégica y criterio profesional",
        icon_name="Briefcase",
        examples_es=(
            "Consultor de estrategia de negocio",
            "Asesor financiero",
            "Asesor legal",
            "Consultor de operaciones",
        ),
    ),
    ExpertBusinessType.COACH_MENTOR: ExpertBusinessTypeMetadata(
        business_type=ExpertBusinessType.COACH_MENTOR,
        label_es="Coach / Mentor",
        description_es=(
            "Facilita transformación personal o profesional. Trabaja 1:1, en grupo, "
            "o en masterminds de acompañamiento continuo."
        ),
        sells_es="Transformación personal acompañada",
        icon_name="Compass",
        examples_es=(
            "Life coach",
            "Executive coach",
            "Coach ejecutivo de ventas",
            "Mentor de carrera",
        ),
    ),
    ExpertBusinessType.EDUCADOR_INFOPRODUCTOR: ExpertBusinessTypeMetadata(
        business_type=ExpertBusinessType.EDUCADOR_INFOPRODUCTOR,
        label_es="Educador / Infoproductor",
        description_es=(
            "Empaqueta conocimiento en cursos, cohortes y certificaciones. "
            "Vende la estructura y el método, no solo su tiempo."
        ),
        sells_es="Conocimiento empaquetado y método reproducible",
        icon_name="GraduationCap",
        examples_es=(
            "Creador de cursos online",
            "Autor de libros y guías",
            "Formador certificado",
            "Instructor especializado",
        ),
    ),
    ExpertBusinessType.AGENCIA_DFY: ExpertBusinessTypeMetadata(
        business_type=ExpertBusinessType.AGENCIA_DFY,
        label_es="Agencia / Done For You",
        description_es=(
            "Ejecuta el trabajo por el cliente. Vende resultados entregables — "
            "campañas, diseños, desarrollo, producciones."
        ),
        sells_es="Ejecución profesional end-to-end",
        icon_name="Wrench",
        examples_es=(
            "Agencia de marketing",
            "Estudio de diseño",
            "Agencia de desarrollo web",
            "Productora audiovisual",
        ),
    ),
    ExpertBusinessType.HOST_COMUNIDAD: ExpertBusinessTypeMetadata(
        business_type=ExpertBusinessType.HOST_COMUNIDAD,
        label_es="Host de Comunidad",
        description_es=(
            "Construye y monetiza una comunidad. Vende pertenencia, acceso y networking a miembros recurrentes."
        ),
        sells_es="Pertenencia, acceso y networking",
        icon_name="Users",
        examples_es=(
            "Founder de membresía paga",
            "Host de mastermind",
            "Líder de círculo profesional",
            "Operador de comunidad privada",
        ),
    ),
    ExpertBusinessType.HOST_EXPERIENCIA: ExpertBusinessTypeMetadata(
        business_type=ExpertBusinessType.HOST_EXPERIENCIA,
        label_es="Host de Experiencias",
        description_es=(
            "Produce reuniones en vivo — retiros, eventos, workshops. Vende la "
            "experiencia inmersiva en persona o streaming."
        ),
        sells_es="Experiencias en vivo memorables",
        icon_name="Tent",
        examples_es=(
            "Organizador de retiros",
            "Productor de eventos",
            "Host de summits",
            "Facilitador de talleres presenciales",
        ),
    ),
    ExpertBusinessType.CREADOR_CONTENIDO: ExpertBusinessTypeMetadata(
        business_type=ExpertBusinessType.CREADOR_CONTENIDO,
        label_es="Creador de Contenido",
        description_es=(
            "Monetiza audiencia e influencia. Vende productos de marca, patrocinios y acceso privado con su comunidad."
        ),
        sells_es="Influencia, contenido y acceso",
        icon_name="Mic",
        examples_es=(
            "Creador YouTube / TikTok",
            "Podcaster",
            "Influencer con tienda propia",
            "Autor de newsletter paga",
        ),
    ),
    ExpertBusinessType.PRODUCT_MAKER: ExpertBusinessTypeMetadata(
        business_type=ExpertBusinessType.PRODUCT_MAKER,
        label_es="Product Maker",
        description_es=(
            "Crea y vende productos — físicos o digitales — como core del negocio. "
            "El artefacto es el producto, no el servicio."
        ),
        sells_es="Productos listos para usar",
        icon_name="Package",
        examples_es=(
            "Vendedor de productos físicos",
            "Maker de productos digitales",
            "Artesano con tienda online",
            "Creador de plantillas y kits",
        ),
    ),
    ExpertBusinessType.SAAS_FOUNDER: ExpertBusinessTypeMetadata(
        business_type=ExpertBusinessType.SAAS_FOUNDER,
        label_es="Fundador SaaS",
        description_es=(
            "Opera software como servicio. Vende suscripciones a una herramienta que el cliente usa recurrentemente."
        ),
        sells_es="Software recurrente que resuelve un dolor",
        icon_name="Cloud",
        examples_es=(
            "SaaS B2B de productividad",
            "Plataforma vertical para un nicho",
            "Micro-SaaS indie",
            "Software de automatización",
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
