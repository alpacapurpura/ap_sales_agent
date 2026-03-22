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
    DeliverableFormat
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
      description: meta.description
    }));
  };
  
  // --- PROGRAM METADATA ---
  export const PROGRAM_STRUCTURE_METADATA: Record<ProgramStructure, EnumMetadata> = {
    [ProgramStructure.FIXED_DATE_COHORT]: {
      label: "Cohorte con Fecha Fija (Lanzamiento)",
      description: "Todos los alumnos inician y terminan juntos. Ideal para crear comunidad, urgencia y altas tasas de finalización."
    },
    [ProgramStructure.ROLLING_ADMISSION]: {
      label: "Evergreen (Rolling Admission)",
      description: "Los alumnos pueden entrar en cualquier momento. Ideal para escalar sin depender de lanzamientos puntuales."
    },
    [ProgramStructure.CHALLENGE_SPRINT]: {
      label: "Challenge / Sprint (Corto Plazo)",
      description: "Experiencia intensiva de 3-7 días para lograr un resultado rápido. Excelente como Lead Magnet o Tripwire."
    }
  };
  
  export const LIVE_INTERACTION_METADATA: Record<LiveInteractionType, EnumMetadata> = {
    [LiveInteractionType.GROUP_Q_AND_A]: {
      label: "Sesiones de Q&A (Preguntas y Respuestas)",
      description: "El contenido es grabado, pero ofreces soporte en vivo para resolver dudas específicas de los alumnos."
    },
    [LiveInteractionType.WORKSHOP_PRACTICAL]: {
      label: "Workshops Prácticos (Implementación)",
      description: "Sesiones de trabajo donde los alumnos 'hacen' durante la llamada. Alto valor percibido."
    },
    [LiveInteractionType.LIVE_PROGRAM_DELIVERY]: {
      label: "Programa dictado en vivo",
      description: "El contenido se entrega en tiempo real. Ideal para cohortes y programas de alto engagement."
    },
    [LiveInteractionType.HYBRID_SUPPORT]: {
      label: "Soporte Híbrido (Clases + Q&A)",
      description: "Mezcla de clases magistrales en vivo y sesiones de soporte. El modelo más completo para High Ticket."
    },
    [LiveInteractionType.NO_LIVE_COMPONENTS]: {
      label: "100% Asíncrono (Sin en vivo)",
      description: "Todo el contenido está pre-grabado. El soporte se da por chat/email o no existe. Ideal para bajo ticket."
    }
  };
  
  export const COMMUNITY_PLATFORM_METADATA: Record<CommunityPlatform, EnumMetadata> = {
    [CommunityPlatform.CIRCLE_SKOOL]: {
      label: "Plataforma Dedicada (Skool/Circle)",
      description: "Experiencia premium. Hilos organizados, gamificación y cursos en un solo lugar."
    },
    [CommunityPlatform.WHATSAPP_TELEGRAM]: {
      label: "Chat App (WhatsApp/Telegram)",
      description: "Alta apertura, informal y rápido. Ideal para Challenges o soporte directo VIP."
    },
    [CommunityPlatform.FACEBOOK_GROUP]: {
      label: "Grupo de Facebook",
      description: "Clásico y gratuito. Bueno para masas, pero con menor alcance orgánico hoy en día."
    },
    [CommunityPlatform.DISCORD_SLACK]: {
      label: "Servidor de Chat (Discord/Slack)",
      description: "Ideal para comunidades técnicas o B2B que requieren canales temáticos organizados."
    },
    [CommunityPlatform.ZOOM]: {
      label: "Zoom",
      description: "Reuniones en vivo a través de Zoom."
    },
    [CommunityPlatform.GOOGLE_MEETS]: {
      label: "Google Meets",
      description: "Reuniones en vivo a través de Google Meets."
    },
    [CommunityPlatform.NONE]: {
      label: "Sin Comunidad",
      description: "El producto se consume individualmente. No hay interacción entre alumnos."
    }
  };
  
  // --- SERVICE METADATA ---
  export const SERVICE_CATEGORY_METADATA: Record<ServiceCategory, EnumMetadata> = {
    [ServiceCategory.ADVISORY_CONSULTING]: {
      label: "Consultoría / Asesoría (Done-With-You)",
      description: "Vendes tu cerebro y experiencia. Guías al cliente, pero ellos ejecutan."
    },
    [ServiceCategory.DONE_FOR_YOU_AGENCY]: {
      label: "Agencia / Ejecución (Done-For-You)",
      description: "Vendes tus manos. Tú haces el trabajo por el cliente (ej. Ads, Diseño, Copy)."
    },
    [ServiceCategory.B2B_AUTHORITY_RENTAL]: {
      label: "Alquiler de Autoridad (B2B)",
      description: "Prestas tu marca o credibilidad a otra empresa (ej. ser parte de su board, training corporativo)."
    }
  };
  
  export const SERVICE_FREQUENCY_METADATA: Record<ServiceFrequency, EnumMetadata> = {
    [ServiceFrequency.ONE_OFF_PROJECT]: {
      label: "Proyecto Único (One-Off)",
      description: "Tiene un inicio y fin claro. Se cobra por el entregable final."
    },
    [ServiceFrequency.RETAINER_RECURRING]: {
      label: "Retainer (Recurrente)",
      description: "Pago mensual fijo por disponibilidad o entregables continuos. Estabilidad financiera."
    },
    [ServiceFrequency.PACK_OF_SESSIONS]: {
      label: "Paquete de Sesiones",
      description: "Vendes un bloque de horas o citas (ej. Pack de 10 sesiones de coaching)."
    }
  };
  
  export const INTERACTION_MODE_METADATA: Record<InteractionMode, EnumMetadata> = {
    [InteractionMode.SYNCHRONOUS_LIVE]: {
      label: "Sincrónico (En Vivo)",
      description: "Requiere tu presencia en tiempo real (Zoom o Presencial). Menos escalable, más High Ticket."
    },
    [InteractionMode.ASYNC_DELIVERY]: {
      label: "Asíncrono (Entregables)",
      description: "Envías reportes, videos o documentos. No requiere coincidir en horarios."
    },
    [InteractionMode.HYBRID_MODEL]: {
      label: "Híbrido",
      description: "Lo mejor de ambos mundos. Trabajo asíncrono + llamadas de control estratégicas."
    }
  };
  
  // --- PRODUCT METADATA ---
  // Note: Using the second definition of FulfillmentType from schema (DIRECT_DOWNLOAD etc)
  // Check schema imports carefully. The schema file had a duplicate export.
  // Assuming standard product types:
  export const FULFILLMENT_TYPE_METADATA: Record<string, EnumMetadata> = {
    "DIRECT_DOWNLOAD": {
      label: "Descarga Directa",
      description: "El usuario recibe el archivo inmediatamente después de la compra."
    },
    "EXTERNAL_PLATFORM": {
      label: "Plataforma Externa",
      description: "Se le da acceso a una herramienta, software o portal de terceros."
    },
    "PHYSICAL_SHIPPING": {
      label: "Envío Físico",
      description: "Requiere logística, stock y paquetería."
    }
  };
  
  export const DIGITAL_FORMAT_METADATA: Record<DigitalFormat, EnumMetadata> = {
    [DigitalFormat.PDF_DOCUMENT]: {
      label: "Ebook / PDF",
      description: "Documento de texto, guía o checklist. Fácil de producir."
    },
    [DigitalFormat.VIDEO_FILE]: {
      label: "Video (Curso/Masterclass)",
      description: "Contenido audiovisual grabado."
    },
    [DigitalFormat.AUDIO_FILE]: {
      label: "Audio / Podcast Privado",
      description: "Consumo fácil 'on the go'. Ideal para meditaciones o audiolibros."
    },
    [DigitalFormat.SPREADSHEET]: {
      label: "Hoja de Cálculo (Excel/GSheets)",
      description: "Herramienta práctica, calculadora o sistema de gestión."
    },
    [DigitalFormat.NOTION_TEMPLATE]: {
      label: "Plantilla de Notion",
      description: "Sistema operativo o dashboard clonable."
    },
    [DigitalFormat.ZIP_BUNDLE]: {
      label: "Pack de Archivos (ZIP)",
      description: "Conjunto de recursos (ej. Pack de diseños, fuentes + iconos)."
    },
    [DigitalFormat.SAAS_ACCESS]: {
      label: "Licencia de Software (SaaS)",
      description: "Clave de acceso o cuenta para una aplicación."
    },
    [DigitalFormat.PHYSICAL_ITEM]: {
      label: "Item Físico",
      description: "Libro impreso, merch o equipo."
    }
  };
  
  // --- SUBSCRIPTION METADATA ---
  export const BILLING_FREQUENCY_METADATA: Record<BillingFrequency, EnumMetadata> = {
    [BillingFrequency.MONTHLY]: {
      label: "Mensual",
      description: "Cobro cada 30 días. Menor barrera de entrada, mayor churn potencial."
    },
    [BillingFrequency.QUARTERLY]: {
      label: "Trimestral",
      description: "Compromiso medio. Buen balance entre cashflow y retención."
    },
    [BillingFrequency.YEARLY]: {
      label: "Anual",
      description: "Pago único por 12 meses. Mejor LTV inmediato, mayor barrera de entrada."
    }
  };
  
  // --- EVENT METADATA ---
  export const EVENT_LOCATION_METADATA: Record<EventLocationType, EnumMetadata> = {
    [EventLocationType.VIRTUAL_REMOTE]: {
      label: "Virtual / Online",
      description: "Evento por Zoom/Stream. Sin límites geográficos, márgenes altos."
    },
    [EventLocationType.IN_PERSON_LOCAL]: {
      label: "Presencial (Local)",
      description: "Evento en una ciudad específica (Hotel/Auditorio). Experiencia inmersiva."
    },
    [EventLocationType.DESTINATION_RETREAT]: {
      label: "Retiro de Destino (Travel)",
      description: "Experiencia de lujo en un lugar turístico. High Ticket + Convivencia."
    }
  };
  
  export const ACCOMMODATION_METADATA: Record<AccommodationType, EnumMetadata> = {
    [AccommodationType.NOT_INCLUDED]: {
      label: "No Incluido (Solo Ticket)",
      description: "El asistente debe buscar su propio hotel."
    },
    [AccommodationType.SHARED_ROOM]: {
      label: "Habitación Compartida (Twin)",
      description: "Dos asistentes por habitación. Reduce costos y fomenta networking."
    },
    [AccommodationType.PRIVATE_ROOM]: {
      label: "Habitación Privada",
      description: "Estándar para ejecutivos o quienes valoran privacidad."
    },
    [AccommodationType.LUXURY_SUITE]: {
      label: "Suite de Lujo / VIP",
      description: "La mejor habitación disponible. Para el tier más alto de tickets."
    }
  };

  export const ACCESS_DURATION_METADATA: Record<AccessDuration, EnumMetadata> = {
    [AccessDuration.LIFETIME_CONTENT]: {
      label: "Acceso de por Vida (Lifetime)",
      description: "El cliente tiene acceso indefinido al contenido y sus actualizaciones futuras."
    },
    [AccessDuration.LIMITED_TIME_ACCESS]: {
      label: "Acceso por Tiempo Limitado",
      description: "El acceso expira después de un periodo fijo (ej. 1 año)."
    },
    [AccessDuration.DURATION_OF_PAYMENT]: {
      label: "Mientras dure el pago (Pay-to-Play)",
      description: "Si deja de pagar (Suscripción/Plan), pierde el acceso inmediatamente."
    },
    [AccessDuration.HYBRID_ACCESS]: {
      label: "Acceso Híbrido",
      description: "Ciertos componentes son de por vida, otros (como la comunidad) caducan."
    }
  };
  
  // --- GENERAL METADATA ---
  export const GUARANTEE_TYPE_METADATA: Record<GuaranteeType, EnumMetadata> = {
    [GuaranteeType.UNCONDITIONAL_X_DAY]: {
      label: "Incondicional (X Días)",
      description: "'Si no te gusta, te devuelvo tu dinero'. Elimina totalmente el riesgo. Aumenta conversión."
    },
    [GuaranteeType.CONDITIONAL_ACTION_BASED]: {
      label: "Condicional (Basada en Acción)",
      description: "'Si haces el trabajo y no ves resultados, te devuelvo el dinero'. Filtra curiosos."
    },
    [GuaranteeType.EXCHANGE_ONLY]: {
      label: "Solo Intercambio / Crédito",
      description: "No hay devolución de dinero, pero sí saldo a favor para otros productos."
    },
    [GuaranteeType.NO_REFUNDS]: {
      label: "Sin Devoluciones (All In)",
      description: "Venta final. Común en servicios High Ticket o descargas digitales inmediatas."
    }
  };
  
  export const DELIVERABLE_FORMAT_METADATA: Record<DeliverableFormat, EnumMetadata> = {
    [DeliverableFormat.RECORDED_CONTENT]: {
      label: "Contenido Grabado (Curso)",
      description: "Módulos de video, audio o texto que se consumen al propio ritmo."
    },
    [DeliverableFormat.LIVE_GROUP_CALL]: {
      label: "Llamada Grupal en Vivo",
      description: "Sesión de Zoom con varios alumnos (Q&A, Hot Seats, Clases)."
    },
    [DeliverableFormat.ONE_ON_ONE_CALL]: {
      label: "Llamada 1 a 1",
      description: "Sesión privada y personalizada. El entregable más costoso en tiempo."
    },
    [DeliverableFormat.DFY_ASSET]: {
      label: "Activo Hecho-Por-Ti (DFY)",
      description: "Un entregable finalizado por ti (ej. Logo, Web, Copy, Funnel)."
    },
    [DeliverableFormat.PHYSICAL_SHIPMENT]: {
      label: "Envío Físico (Box/Libro)",
      description: "Algo tangible que llega por correo a su casa."
    }
  };
