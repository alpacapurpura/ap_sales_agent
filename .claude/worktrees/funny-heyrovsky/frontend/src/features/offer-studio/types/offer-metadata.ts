import { OfferType, OfferValueLevel, OfferDeliveryModel } from ".";

export interface OfferTypeDefinition {
  type: OfferType;
  level: OfferValueLevel;
  delivery: OfferDeliveryModel;
  label: string;
  hint: string;
  description: string;
}

export const OFFER_TYPE_METADATA: Record<OfferType, OfferTypeDefinition> = {
  // --- NIVEL 0 ---
  [OfferType.FREE_RESOURCE]: {
    type: OfferType.FREE_RESOURCE,
    level: OfferValueLevel.N0,
    delivery: OfferDeliveryModel.DIY,
    label: "Recurso Gratuito",
    hint: "Lead Magnet clásico (PDF, Checklist).",
    description: "Atrae tráfico frío y construye tu lista de correos."
  },
  [OfferType.COMMUNITY_LITE]: {
    type: OfferType.COMMUNITY_LITE,
    level: OfferValueLevel.N0,
    delivery: OfferDeliveryModel.DIY,
    label: "Comunidad Gratuita",
    hint: "Grupo de Facebook, Discord o Telegram.",
    description: "Nutre a tus prospectos en un entorno controlado."
  },
  [OfferType.CONTENT_ASSET_PODCAST]: {
    type: OfferType.CONTENT_ASSET_PODCAST,
    level: OfferValueLevel.N0,
    delivery: OfferDeliveryModel.DIY,
    label: "Activo de Contenido",
    hint: "Podcast, Blog o Canal de YouTube.",
    description: "Construye autoridad y confianza a largo plazo."
  },
  [OfferType.FREE_WEBINAR_CHALLENGE]: {
    type: OfferType.FREE_WEBINAR_CHALLENGE,
    level: OfferValueLevel.N0,
    delivery: OfferDeliveryModel.DWY,
    label: "Webinar o Reto Gratuito",
    hint: "Evento en vivo para lanzar una oferta.",
    description: "Genera urgencia y conexión masiva."
  },

  // --- NIVEL 1 ---
  [OfferType.TRIPWIRE_OFFER]: {
    type: OfferType.TRIPWIRE_OFFER,
    level: OfferValueLevel.N1,
    delivery: OfferDeliveryModel.DIY,
    label: "Oferta Tripwire",
    hint: "Oferta irresistible de bajo costo ($7-$97).",
    description: "Autofinancia la publicidad y convierte leads en clientes."
  },
  [OfferType.SELF_PACED_COURSE]: {
    type: OfferType.SELF_PACED_COURSE,
    level: OfferValueLevel.N1,
    delivery: OfferDeliveryModel.DIY,
    label: "Curso Auto-dirigido",
    hint: "Curso grabado sin soporte en vivo.",
    description: "Escalabilidad infinita, el cliente aprende a su ritmo."
  },
  [OfferType.PAID_NEWSLETTER_SUBSCRIPTION]: {
    type: OfferType.PAID_NEWSLETTER_SUBSCRIPTION,
    level: OfferValueLevel.N1,
    delivery: OfferDeliveryModel.DIY,
    label: "Suscripción Premium",
    hint: "Contenido exclusivo recurrente.",
    description: "Ingresos recurrentes de bajo ticket para fidelizar."
  },
  [OfferType.PHYSICAL_MERCH]: {
    type: OfferType.PHYSICAL_MERCH,
    level: OfferValueLevel.N1,
    delivery: OfferDeliveryModel.DIY,
    label: "Producto Físico / Merch",
    hint: "Libros, ropa, accesorios.",
    description: "Productos tangibles que requieren envío y logística."
  },

  // --- NIVEL 2 ---
  [OfferType.HYBRID_MENTORSHIP]: {
    type: OfferType.HYBRID_MENTORSHIP,
    level: OfferValueLevel.N2,
    delivery: OfferDeliveryModel.DWY,
    label: "Mentoría Híbrida",
    hint: "El 'Gold Standard'. Curso + Q&A semanal.",
    description: "Alta rentabilidad y soporte grupal eficiente."
  },
  [OfferType.COHORT_BASED_COURSE]: {
    type: OfferType.COHORT_BASED_COURSE,
    level: OfferValueLevel.N2,
    delivery: OfferDeliveryModel.DWY,
    label: "Curso por Cohortes",
    hint: "Curso en vivo con fecha de inicio/fin.",
    description: "Maximiza la tasa de finalización mediante presión de grupo."
  },
  [OfferType.GROUP_COACHING_PROGRAM]: {
    type: OfferType.GROUP_COACHING_PROGRAM,
    level: OfferValueLevel.N2,
    delivery: OfferDeliveryModel.DWY,
    label: "Coaching Grupal",
    hint: "Facilitación en vivo, menos contenido grabado.",
    description: "Enfoque en desbloqueo emocional o estratégico."
  },

  // --- NIVEL 3 ---
  [OfferType.VIP_DAY_STRATEGY]: {
    type: OfferType.VIP_DAY_STRATEGY,
    level: OfferValueLevel.N3,
    delivery: OfferDeliveryModel.DWY,
    label: "VIP Day / Strategy Day",
    hint: "4-8 horas intensivas 1:1.",
    description: "Solución rápida y profunda a un problema específico."
  },
  [OfferType.ONE_ON_ONE_PRIVATE_MENTORING]: {
    type: OfferType.ONE_ON_ONE_PRIVATE_MENTORING,
    level: OfferValueLevel.N3,
    delivery: OfferDeliveryModel.DWY,
    label: "Mentoría Privada 1:1",
    hint: "Acompañamiento a largo plazo.",
    description: "Máxima personalización y transformación."
  },
  [OfferType.DEEP_DIVE_AUDIT]: {
    type: OfferType.DEEP_DIVE_AUDIT,
    level: OfferValueLevel.N3,
    delivery: OfferDeliveryModel.DWY,
    label: "Auditoría Profunda",
    hint: "Análisis exhaustivo + Plan de Acción.",
    description: "Diagnóstico experto con ruta de implementación clara."
  },

  // --- NIVEL 4 ---
  [OfferType.PRODUCTIZED_SERVICE]: {
    type: OfferType.PRODUCTIZED_SERVICE,
    level: OfferValueLevel.N4,
    delivery: OfferDeliveryModel.DFY,
    label: "Servicio Productizado",
    hint: "Alcance fijo, precio fijo.",
    description: "Vendes un resultado específico (ej. 'Te monto el funnel')."
  },
  [OfferType.ECOMMERCE_DEVELOPMENT]: {
    type: OfferType.ECOMMERCE_DEVELOPMENT,
    level: OfferValueLevel.N4,
    delivery: OfferDeliveryModel.DFY,
    label: "Desarrollo Ecommerce",
    hint: "Creación de tienda online completa.",
    description: "Servicio llave en mano para lanzar un comercio electrónico."
  },
  [OfferType.MONTHLY_RETAINER]: {
    type: OfferType.MONTHLY_RETAINER,
    level: OfferValueLevel.N4,
    delivery: OfferDeliveryModel.DFY,
    label: "Retainer Mensual",
    hint: "Gestión continua recurrente.",
    description: "Ingresos predecibles a cambio de ejecución constante."
  },
  [OfferType.PERFORMANCE_REV_SHARE]: {
    type: OfferType.PERFORMANCE_REV_SHARE,
    level: OfferValueLevel.N4,
    delivery: OfferDeliveryModel.DFY,
    label: "Partnership / RevShare",
    hint: "Cobro base bajo + % de resultados.",
    description: "Alto riesgo, alta recompensa. Modelo de socio."
  },

  // --- NIVEL 5 ---
  [OfferType.MASTERMIND_NETWORK]: {
    type: OfferType.MASTERMIND_NETWORK,
    level: OfferValueLevel.N5,
    delivery: OfferDeliveryModel.DWY,
    label: "Red de Mastermind",
    hint: "Acceso a conexiones y pares de alto nivel.",
    description: "El valor está en la red, no en el contenido."
  },
  [OfferType.LUXURY_RETREAT]: {
    type: OfferType.LUXURY_RETREAT,
    level: OfferValueLevel.N5,
    delivery: OfferDeliveryModel.DWY,
    label: "Retiro Inmersivo",
    hint: "Experiencia presencial de lujo.",
    description: "Conexión profunda y estatus fuera del entorno habitual."
  },

  // --- NIVEL 6 ---
  [OfferType.CORPORATE_TRAINING]: {
    type: OfferType.CORPORATE_TRAINING,
    level: OfferValueLevel.N6,
    delivery: OfferDeliveryModel.B2B,
    label: "Capacitación Corporativa",
    hint: "Venta a empresas (B2B).",
    description: "Entrenamiento para equipos o departamentos."
  },
  [OfferType.BRAND_SPONSORSHIP]: {
    type: OfferType.BRAND_SPONSORSHIP,
    level: OfferValueLevel.N6,
    delivery: OfferDeliveryModel.B2B,
    label: "Patrocinio de Marca",
    hint: "Venta de acceso a tu audiencia.",
    description: "Monetización de tu alcance mediático."
  },
  [OfferType.KEYNOTE_SPEAKING]: {
    type: OfferType.KEYNOTE_SPEAKING,
    level: OfferValueLevel.N6,
    delivery: OfferDeliveryModel.B2B,
    label: "Conferencias / Keynotes",
    hint: "Ponencias pagadas.",
    description: "Monetización de tu autoridad y oratoria."
  }
};

export const getOffersByLevel = (level: OfferValueLevel): OfferTypeDefinition[] => {
  return Object.values(OFFER_TYPE_METADATA).filter(def => def.level === level);
};
