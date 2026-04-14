import {
  ProgramStructure,
  LiveInteractionType,
  CommunityPlatform,
  ServiceCategory,
  ServiceFrequency,
  InteractionMode,
  FulfillmentType,
  DigitalFormat,
  BillingFrequency,
  EventLocationType,
  AccommodationType,
  AccessDuration,
  GuaranteeType,
  DeliverableFormat,
} from ".";

// --- UTILS ---
export interface EnumMetadata {
  label: string;
  description: string;
}

export const getEnumOptions = (metadataRecord: Record<string, EnumMetadata>) => {
  return Object.entries(metadataRecord).map(([key, meta]) => ({
    value: key,
    label: meta.label,
    description: meta.description,
  }));
};

// --- PROGRAM METADATA ---
export const PROGRAM_STRUCTURE_METADATA: Record<ProgramStructure, EnumMetadata> = {
  [ProgramStructure.FIXED_COHORT]: {
    label: "Cohorte con Fecha Fija (Lanzamiento)",
    description:
      "Todos los alumnos inician y terminan juntos. Ideal para crear comunidad, urgencia y altas tasas de finalización.",
  },
  [ProgramStructure.ROLLING_ADMISSION]: {
    label: "Evergreen (Rolling Admission)",
    description:
      "Los alumnos pueden entrar en cualquier momento. Ideal para escalar sin depender de lanzamientos puntuales.",
  },
  [ProgramStructure.CHALLENGE]: {
    label: "Challenge / Sprint (Corto Plazo)",
    description:
      "Experiencia intensiva de 3-7 días para lograr un resultado rápido. Excelente como Lead Magnet o Tripwire.",
  },
  [ProgramStructure.MEMBERSHIP]: {
    label: "Membresía (Acceso Continuo)",
    description:
      "Los miembros pagan recurrentemente por acceso continuo a contenido, comunidad y recursos.",
  },
};

export const LIVE_INTERACTION_METADATA: Record<LiveInteractionType, EnumMetadata> = {
  [LiveInteractionType.NONE]: {
    label: "100% Asíncrono (Sin en vivo)",
    description:
      "Todo el contenido está pre-grabado. El soporte se da por chat/email o no existe. Ideal para bajo ticket.",
  },
  [LiveInteractionType.GROUP_Q_AND_A]: {
    label: "Sesiones de Q&A (Preguntas y Respuestas)",
    description:
      "El contenido es grabado, pero ofreces soporte en vivo para resolver dudas específicas de los alumnos.",
  },
  [LiveInteractionType.ONE_ON_ONE_CHECKINS]: {
    label: "Check-ins 1 a 1",
    description: "Sesiones individuales de seguimiento para asegurar progreso personalizado.",
  },
  [LiveInteractionType.HOT_SEATS]: {
    label: "Hot Seats (Sesiones de Coaching en Grupo)",
    description:
      "Un alumno presenta su caso y recibe feedback directo mientras los demás aprenden.",
  },
  [LiveInteractionType.WORKSHOPS]: {
    label: "Workshops Prácticos (Implementación)",
    description:
      "Sesiones de trabajo donde los alumnos 'hacen' durante la llamada. Alto valor percibido.",
  },
};

export const COMMUNITY_PLATFORM_METADATA: Record<CommunityPlatform, EnumMetadata> = {
  [CommunityPlatform.NONE]: {
    label: "Sin Comunidad",
    description: "El producto se consume individualmente. No hay interacción entre alumnos.",
  },
  [CommunityPlatform.WHATSAPP]: {
    label: "WhatsApp",
    description: "Alta apertura, informal y rápido. Ideal para Challenges o soporte directo VIP.",
  },
  [CommunityPlatform.TELEGRAM]: {
    label: "Telegram",
    description:
      "Canales y grupos con bots, ideal para comunidades tech o audiencias internacionales.",
  },
  [CommunityPlatform.DISCORD]: {
    label: "Discord",
    description:
      "Servidor de chat con canales temáticos organizados. Ideal para comunidades técnicas.",
  },
  [CommunityPlatform.SKOOL]: {
    label: "Skool",
    description: "Plataforma dedicada con gamificación, cursos y comunidad en un solo lugar.",
  },
  [CommunityPlatform.CIRCLE]: {
    label: "Circle",
    description: "Experiencia premium con hilos organizados y marca propia.",
  },
  [CommunityPlatform.FACEBOOK_GROUP]: {
    label: "Grupo de Facebook",
    description:
      "Clásico y gratuito. Bueno para masas, pero con menor alcance orgánico hoy en día.",
  },
  [CommunityPlatform.SLACK]: {
    label: "Slack",
    description: "Ideal para comunidades B2B y profesionales que ya usan Slack en su trabajo.",
  },
};

// --- SERVICE METADATA ---
export const SERVICE_CATEGORY_METADATA: Record<ServiceCategory, EnumMetadata> = {
  [ServiceCategory.ADVISORY]: {
    label: "Consultoría / Asesoría (Done-With-You)",
    description: "Vendes tu cerebro y experiencia. Guías al cliente, pero ellos ejecutan.",
  },
  [ServiceCategory.AGENCY]: {
    label: "Agencia / Ejecución (Done-For-You)",
    description: "Vendes tus manos. Tú haces el trabajo por el cliente (ej. Ads, Diseño, Copy).",
  },
  [ServiceCategory.AUTHORITY]: {
    label: "Alquiler de Autoridad (B2B)",
    description:
      "Prestas tu marca o credibilidad a otra empresa (ej. ser parte de su board, training corporativo).",
  },
};

export const SERVICE_FREQUENCY_METADATA: Record<ServiceFrequency, EnumMetadata> = {
  [ServiceFrequency.ONE_OFF]: {
    label: "Proyecto Único (One-Off)",
    description: "Tiene un inicio y fin claro. Se cobra por el entregable final.",
  },
  [ServiceFrequency.RETAINER]: {
    label: "Retainer (Recurrente)",
    description:
      "Pago mensual fijo por disponibilidad o entregables continuos. Estabilidad financiera.",
  },
};

export const INTERACTION_MODE_METADATA: Record<InteractionMode, EnumMetadata> = {
  [InteractionMode.SYNC]: {
    label: "Sincrónico (En Vivo)",
    description:
      "Requiere tu presencia en tiempo real (Zoom o Presencial). Menos escalable, más High Ticket.",
  },
  [InteractionMode.ASYNC]: {
    label: "Asíncrono (Entregables)",
    description: "Envías reportes, videos o documentos. No requiere coincidir en horarios.",
  },
  [InteractionMode.HYBRID]: {
    label: "Híbrido",
    description: "Lo mejor de ambos mundos. Trabajo asíncrono + llamadas de control estratégicas.",
  },
};

// --- PRODUCT METADATA ---
export const FULFILLMENT_TYPE_METADATA: Record<FulfillmentType, EnumMetadata> = {
  [FulfillmentType.DIGITAL_DOWNLOAD]: {
    label: "Descarga Digital",
    description: "El usuario recibe el archivo inmediatamente después de la compra.",
  },
  [FulfillmentType.LMS_ACCESS]: {
    label: "Acceso LMS / Plataforma",
    description: "Se le da acceso a una herramienta, software o portal de terceros.",
  },
  [FulfillmentType.PHYSICAL_SHIPPING]: {
    label: "Envío Físico",
    description: "Requiere logística, stock y paquetería.",
  },
  [FulfillmentType.MANUAL_PROVISIONING]: {
    label: "Provisión Manual",
    description: "Configuración manual del acceso o entregable por parte del equipo.",
  },
};

export const DIGITAL_FORMAT_METADATA: Record<DigitalFormat, EnumMetadata> = {
  [DigitalFormat.PDF_EBOOK]: {
    label: "Ebook / PDF",
    description: "Documento de texto, guía o checklist. Fácil de producir.",
  },
  [DigitalFormat.VIDEO_COURSE]: {
    label: "Video (Curso/Masterclass)",
    description: "Contenido audiovisual grabado.",
  },
  [DigitalFormat.AUDIO_SERIES]: {
    label: "Audio / Podcast Privado",
    description: "Consumo fácil 'on the go'. Ideal para meditaciones o audiolibros.",
  },
  [DigitalFormat.NOTION_TEMPLATE]: {
    label: "Plantilla de Notion",
    description: "Sistema operativo o dashboard clonable.",
  },
  [DigitalFormat.SOFTWARE_SAAS]: {
    label: "Licencia de Software (SaaS)",
    description: "Clave de acceso o cuenta para una aplicación.",
  },
  [DigitalFormat.PHYSICAL_ITEM]: {
    label: "Item Físico",
    description: "Libro impreso, merch o equipo.",
  },
};

// --- SUBSCRIPTION METADATA ---
export const BILLING_FREQUENCY_METADATA: Record<BillingFrequency, EnumMetadata> = {
  [BillingFrequency.MONTHLY]: {
    label: "Mensual",
    description: "Cobro cada 30 días. Menor barrera de entrada, mayor churn potencial.",
  },
  [BillingFrequency.QUARTERLY]: {
    label: "Trimestral",
    description: "Compromiso medio. Buen balance entre cashflow y retención.",
  },
  [BillingFrequency.ANNUAL]: {
    label: "Anual",
    description: "Pago único por 12 meses. Mejor LTV inmediato, mayor barrera de entrada.",
  },
  [BillingFrequency.ONE_OFF]: {
    label: "Pago Único",
    description: "Un solo cobro, sin recurrencia. Ideal para productos de precio fijo.",
  },
};

// --- EVENT METADATA ---
export const EVENT_LOCATION_METADATA: Record<EventLocationType, EnumMetadata> = {
  [EventLocationType.VIRTUAL]: {
    label: "Virtual / Online",
    description: "Evento por Zoom/Stream. Sin límites geográficos, márgenes altos.",
  },
  [EventLocationType.PHYSICAL_LOCAL]: {
    label: "Presencial (Local)",
    description: "Evento en una ciudad específica (Hotel/Auditorio). Experiencia inmersiva.",
  },
  [EventLocationType.DESTINATION_RETREAT]: {
    label: "Retiro de Destino (Travel)",
    description: "Experiencia de lujo en un lugar turístico. High Ticket + Convivencia.",
  },
};

export const ACCOMMODATION_METADATA: Record<AccommodationType, EnumMetadata> = {
  [AccommodationType.NOT_INCLUDED]: {
    label: "No Incluido (Solo Ticket)",
    description: "El asistente debe buscar su propio hotel.",
  },
  [AccommodationType.SHARED_ROOM]: {
    label: "Habitación Compartida (Twin)",
    description: "Dos asistentes por habitación. Reduce costos y fomenta networking.",
  },
  [AccommodationType.PRIVATE_ROOM]: {
    label: "Habitación Privada",
    description: "Estándar para ejecutivos o quienes valoran privacidad.",
  },
  [AccommodationType.LUXURY_SUITE]: {
    label: "Suite de Lujo / VIP",
    description: "La mejor habitación disponible. Para el tier más alto de tickets.",
  },
};

export const ACCESS_DURATION_METADATA: Record<AccessDuration, EnumMetadata> = {
  [AccessDuration.LIFETIME]: {
    label: "Acceso de por Vida (Lifetime)",
    description: "El cliente tiene acceso indefinido al contenido y sus actualizaciones futuras.",
  },
  [AccessDuration.LIMITED_TIME]: {
    label: "Acceso por Tiempo Limitado",
    description: "El acceso expira después de un periodo fijo (ej. 1 año).",
  },
  [AccessDuration.SUBSCRIPTION_ACTIVE]: {
    label: "Mientras dure la Suscripción",
    description: "Si deja de pagar (Suscripción/Plan), pierde el acceso inmediatamente.",
  },
};

// --- GENERAL METADATA ---
export const GUARANTEE_TYPE_METADATA: Record<GuaranteeType, EnumMetadata> = {
  [GuaranteeType.NONE]: {
    label: "Sin Devoluciones (All In)",
    description: "Venta final. Común en servicios High Ticket o descargas digitales inmediatas.",
  },
  [GuaranteeType.CONDITIONAL_ACTION_BASED]: {
    label: "Condicional (Basada en Acción)",
    description:
      "'Si haces el trabajo y no ves resultados, te devuelvo el dinero'. Filtra curiosos.",
  },
  [GuaranteeType.UNCONDITIONAL_30_DAY]: {
    label: "Incondicional (30 Días)",
    description:
      "'Si no te gusta, te devuelvo tu dinero'. Elimina totalmente el riesgo. Aumenta conversión.",
  },
  [GuaranteeType.DOUBLE_MONEY_BACK]: {
    label: "Doble Devolución",
    description: "Si no funciona, devuelves el doble. Máxima confianza y señal de calidad.",
  },
  [GuaranteeType.SATISFACTION_OR_FREE_WORK]: {
    label: "Satisfacción o Trabajo Gratis",
    description: "Si no estás satisfecho, trabajo adicional sin costo hasta lograrlo.",
  },
};

export const DELIVERABLE_FORMAT_METADATA: Record<DeliverableFormat, EnumMetadata> = {
  [DeliverableFormat.PDF]: {
    label: "PDF / Documento",
    description: "Guía, checklist o ebook en formato PDF.",
  },
  [DeliverableFormat.VIDEO]: {
    label: "Video (Curso/Grabado)",
    description: "Módulos de video que se consumen al propio ritmo.",
  },
  [DeliverableFormat.AUDIO]: {
    label: "Audio / Podcast",
    description: "Contenido en formato de audio para consumir en movimiento.",
  },
  [DeliverableFormat.LIVE_SESSION]: {
    label: "Sesión en Vivo",
    description: "Sesión de Zoom o presencial con interacción en tiempo real.",
  },
  [DeliverableFormat.TEMPLATE]: {
    label: "Plantilla / Template",
    description: "Recurso clonable o adaptable (Notion, Sheets, Canva, etc.).",
  },
  [DeliverableFormat.COMMUNITY_ACCESS]: {
    label: "Acceso a Comunidad",
    description: "Entrada a un grupo privado (Discord, Skool, WhatsApp, etc.).",
  },
  [DeliverableFormat.SOFTWARE_ACCESS]: {
    label: "Acceso a Software",
    description: "Licencia o cuenta para una herramienta o plataforma.",
  },
  [DeliverableFormat.PHYSICAL_ITEM]: {
    label: "Envío Físico (Box/Libro)",
    description: "Algo tangible que llega por correo a su casa.",
  },
  [DeliverableFormat.SERVICE_HOURS]: {
    label: "Horas de Servicio",
    description: "Tiempo de trabajo profesional dedicado al cliente.",
  },
};
