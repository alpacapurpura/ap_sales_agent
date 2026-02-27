import { Offer, OfferType, OfferStatus, OfferValueLevel, OfferDeliveryModel, GuaranteeType } from "../types";

// Helper para generar ofertas consistentes
const createMockOffer = (
    id: string,
    name: string,
    type: OfferType,
    price: number,
    status: OfferStatus = OfferStatus.ACTIVE
): Offer => ({
    id,
    name,
    internal_sku: `MOCK-${type.substring(0, 4)}-${id}`,
    type,
    value_level: OfferValueLevel.N1,
    delivery_model: OfferDeliveryModel.DIY,
    status,
    headline_promise: `Promesa principal para ${name}`,
    primary_outcome: `Resultado transformador de ${name}`,
    time_to_value: "30 días",
    pricing: [
        {
            label: "Pago Único",
            total_amount: price,
            plan_type: "one_time",
            currency: "USD",
            deposit_required: 0,
            number_of_installments: 1,
            installment_amount: 0
        }
    ],
    currency: "USD",
    specific_details: {},
    metadata_info: {},
    marketing_pain_points: ["Falta de claridad", "Estancamiento", "Bajos ingresos"],
    marketing_desires: ["Libertad", "Impacto", "Crecimiento"],
    deliverables: [],
    target_avatar_match: [],
    prerequisites: [],
    includes_offers: [],
    assets: [],
    guarantee_type: GuaranteeType.UNCONDITIONAL_X_DAY,
    guarantee_terms: "30 días de garantía",
    landing_page_config: {
        is_published: status === OfferStatus.ACTIVE,
        slug: `offer-${id}`,
        template: "sales-letter",
        sections: {
            hero: { title: name, subtitle: "La solución definitiva" }
        }
    }
});

export const MOCK_OFFERS: Offer[] = [
    createMockOffer("1", "Guía Gratuita de Inicio", OfferType.FREE_RESOURCE, 0),
    createMockOffer("2", "Comunidad Lite", OfferType.COMMUNITY_LITE, 27),
    createMockOffer("3", "Podcast Premium", OfferType.CONTENT_ASSET_PODCAST, 0),
    createMockOffer("4", "Reto de 5 Días", OfferType.FREE_WEBINAR_CHALLENGE, 0),
    createMockOffer("5", "Oferta Tripwire", OfferType.TRIPWIRE_OFFER, 47),
    createMockOffer("6", "Curso Grabado Completo", OfferType.SELF_PACED_COURSE, 497),
    createMockOffer("7", "Newsletter de Pago", OfferType.PAID_NEWSLETTER_SUBSCRIPTION, 15),
    createMockOffer("8", "Merch Exclusivo", OfferType.PHYSICAL_MERCH, 50),
    createMockOffer("9", "Mentoría Híbrida", OfferType.HYBRID_MENTORSHIP, 2500),
    createMockOffer("10", "Curso por Cohortes", OfferType.COHORT_BASED_COURSE, 1500),
    createMockOffer("11", "Programa de Coaching Grupal", OfferType.GROUP_COACHING_PROGRAM, 3000),
    createMockOffer("12", "Día VIP de Estrategia", OfferType.VIP_DAY_STRATEGY, 5000),
    createMockOffer("13", "Mentoría 1 a 1", OfferType.ONE_ON_ONE_PRIVATE_MENTORING, 10000),
    createMockOffer("14", "Auditoría Profunda", OfferType.DEEP_DIVE_AUDIT, 1500),
    createMockOffer("15", "Servicio Productizado", OfferType.PRODUCTIZED_SERVICE, 2000),
    createMockOffer("16", "Desarrollo E-commerce", OfferType.ECOMMERCE_DEVELOPMENT, 8000),
    createMockOffer("17", "Retainer Mensual", OfferType.MONTHLY_RETAINER, 3000),
    createMockOffer("18", "Rev Share Partnership", OfferType.PERFORMANCE_REV_SHARE, 0),
    createMockOffer("19", "Mastermind Network", OfferType.MASTERMIND_NETWORK, 15000),
    createMockOffer("20", "Retiro de Lujo", OfferType.LUXURY_RETREAT, 8000),
    createMockOffer("21", "Entrenamiento Corporativo", OfferType.CORPORATE_TRAINING, 12000),
    createMockOffer("22", "Patrocinio de Marca", OfferType.BRAND_SPONSORSHIP, 5000),
    createMockOffer("23", "Keynote Speaking", OfferType.KEYNOTE_SPEAKING, 7500)
];

// Exportaciones legacy para mantener compatibilidad
export const MOCK_OFFER_FULL = MOCK_OFFERS.find(o => o.type === OfferType.SELF_PACED_COURSE) || MOCK_OFFERS[0];
export const MOCK_OFFER_EMPTY = createMockOffer("new", "Nueva Oferta", OfferType.FREE_RESOURCE, 0, OfferStatus.DRAFT);
