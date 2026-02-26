import {
  Offer,
  OfferType,
  OfferStatus,
  OfferValueLevel,
  OfferDeliveryModel,
  GuaranteeType,
  DeliverableFormat,
  ProgramStructure,
  LiveInteractionType,
  CommunityPlatform,
  AccessDuration,
  FinancialCapacity,
  FulfillmentType,
  DigitalFormat,
  ServiceCategory,
  InteractionMode,
  ServiceFrequency,
  PaymentPlanType
} from "../types";

export const MOCK_OFFERS: Offer[] = [
  // 1. PROGRAMA: Coaching Grupal de Alto Ticket
  {
    id: "mock-program-001",
    name: "Mastermind de Ventas B2B",
    public_name: "Mastermind de Ventas B2B",
    internal_sku: "MM-B2B-2024",
    type: OfferType.GROUP_COACHING_PROGRAM,
    value_level: OfferValueLevel.N4,
    delivery_model: OfferDeliveryModel.DWY,
    status: OfferStatus.ACTIVE,
    
    headline_promise: "Duplica tus cierres B2B en 90 días sin aumentar tu gasto publicitario",
    primary_outcome: "Sistema de ventas predecible y escalable",
    time_to_value: "30 días para primeras victorias",
    
    marketing_pain_points: [
      "Ciclos de venta interminables",
      "Leads cualificados que no convierten",
      "Falta de un proceso de seguimiento estructurado"
    ],
    marketing_desires: [
      "Autoridad en el mercado",
      "Flujo de caja predecible",
      "Equipo de ventas autónomo"
    ],

    pricing: [
      {
        label: "Pago Único",
        plan_type: PaymentPlanType.PAY_IN_FULL,
        total_amount: 5000,
        currency: "USD",
        savings_claim: "Ahorra $1000"
      },
      {
        label: "Plan de Pagos",
        plan_type: PaymentPlanType.INTERNAL_SPLIT_PAY,
        total_amount: 6000,
        currency: "USD",
        number_of_installments: 3,
        installment_amount: 2000
      }
    ],

    deliverables: [
      {
        name: "Sesiones Semanales de Q&A",
        format: DeliverableFormat.LIVE_GROUP_CALL,
        quantity: "12",
        value_stack_price: 3000
      },
      {
        name: "Portal de Contenidos Exclusivo",
        format: DeliverableFormat.RECORDED_CONTENT,
        quantity: "1",
        value_stack_price: 2000
      },
      {
        name: "Auditoría de Pipeline",
        format: DeliverableFormat.ONE_ON_ONE_CALL,
        quantity: "1",
        value_stack_price: 1000
      }
    ],

    specific_details: {
      program_details: {
        structure_type: ProgramStructure.FIXED_DATE_COHORT,
        start_date: "2024-03-01T00:00:00Z",
        end_date: "2024-06-01T00:00:00Z",
        duration_weeks: 12,
        cohort_limit: 20,
        interaction_type: LiveInteractionType.GROUP_Q_AND_A,
        community_platform: CommunityPlatform.CIRCLE_SKOOL,
        has_certification: true
      }
    },

    guarantee_type: GuaranteeType.CONDITIONAL_ACTION_BASED,
    guarantee_terms: "Si implementas todo y no recuperas tu inversión, te devolvemos el dinero + $1000.",
    access_duration: AccessDuration.LIFETIME_CONTENT,
    support_duration_days: 90,
    instructors: ["Chris Sales", "Ana Marketing"],
    min_financial_capacity: FinancialCapacity.HIGH
  },

  // 2. SERVICIO: Auditoría SEO (Productized Service)
  {
    id: "mock-service-001",
    public_name: "Auditoría SEO Técnica Profunda",
    internal_sku: "SEO-AUDIT-Q1",
    type: OfferType.PRODUCTIZED_SERVICE,
    value_level: OfferValueLevel.N3,
    delivery_model: OfferDeliveryModel.DFY,
    status: OfferStatus.DRAFT,
    
    headline_promise: "Identifica los errores técnicos que están matando tu tráfico orgánico",
    primary_outcome: "Hoja de ruta clara para recuperar posicionamiento",
    time_to_value: "7 días hábiles",

    pricing: [
      {
        label: "Auditoría Estándar",
        plan_type: PaymentPlanType.PAY_IN_FULL,
        total_amount: 1500,
        currency: "USD"
      }
    ],

    specific_details: {
      service_details: {
        category: ServiceCategory.ADVISORY_CONSULTING,
        interaction_mode: InteractionMode.ASYNC_DELIVERY,
        frequency_type: ServiceFrequency.ONE_OFF_PROJECT,
        turnaround_time_days: 7,
        deliverables_list: [
          "Informe PDF de 50+ páginas",
          "Video Loom explicativo (30 min)",
          "Plan de acción en Notion"
        ]
      }
    },

    deliverables: [
      {
        name: "Informe Técnico Completo",
        format: DeliverableFormat.DFY_ASSET,
        quantity: "1",
        value_stack_price: 2000
      }
    ],
    
    guarantee_type: GuaranteeType.NO_REFUNDS
  },

  // 3. PRODUCTO: Curso Self-Paced
  {
    id: "mock-product-001",
    name: "Kit de Plantillas de Email Marketing",
    public_name: "Kit de Plantillas de Email Marketing",
    internal_sku: "EMAIL-KIT-V1",
    type: OfferType.SELF_PACED_COURSE,
    value_level: OfferValueLevel.N1,
    delivery_model: OfferDeliveryModel.DIY,
    status: OfferStatus.ACTIVE,
    
    headline_promise: "Escribe emails que venden en minutos, no horas",
    primary_outcome: "Ahorro de tiempo y aumento de conversiones",
    time_to_value: "Inmediato tras la descarga",

    pricing: [
      {
        label: "Acceso Inmediato",
        plan_type: PaymentPlanType.PAY_IN_FULL,
        total_amount: 97,
        currency: "USD"
      }
    ],

    specific_details: {
      product_details: {
        fulfillment_type: FulfillmentType.DIRECT_DOWNLOAD,
        format: DigitalFormat.ZIP_BUNDLE,
        is_downloadable: true,
        estimated_consumption_time_minutes: 120
      }
    },

    deliverables: [
      {
        name: "50+ Plantillas de Email",
        format: DeliverableFormat.RECORDED_CONTENT,
        quantity: "1",
        value_stack_price: 497
      },
      {
        name: "Guía de Asuntos Irresistibles",
        format: DeliverableFormat.RECORDED_CONTENT,
        quantity: "1",
        value_stack_price: 97
      }
    ],

    guarantee_type: GuaranteeType.UNCONDITIONAL_X_DAY,
    guarantee_terms: "30 días de garantía de satisfacción total.",
    access_duration: AccessDuration.LIFETIME_CONTENT
  }
];
