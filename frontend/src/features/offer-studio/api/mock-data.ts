import {
  Offer,
  OfferArchetype,
  OfferStatus,
  OfferValueLevel,
  OfferDeliveryModel,
  GuaranteeType,
} from "../types";

const createMockOffer = (
  id: string,
  name: string,
  archetype: OfferArchetype,
  price: number,
  valueLevel: OfferValueLevel = OfferValueLevel.ACTIVACION,
  status: OfferStatus = OfferStatus.ACTIVE,
): Offer => ({
  id,
  name,
  internal_sku: `MOCK-${archetype.substring(0, 4).toUpperCase()}-${id}`,
  archetype,
  value_level: valueLevel,
  delivery_model: OfferDeliveryModel.DIY,
  status,
  headline_promise: `Promesa principal para ${name}`,
  primary_outcome: `Resultado transformador de ${name}`,
  time_to_value: "30 dias",
  pricing: [
    {
      label: "Pago Unico",
      total_amount: price,
      plan_type: "one_time",
      currency: "USD",
      deposit_required: 0,
      number_of_installments: 1,
      installment_amount: 0,
    },
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
  guarantee_type: GuaranteeType.UNCONDITIONAL_30_DAY,
  guarantee_terms: "30 dias de garantia",
  landing_page_config: {
    is_published: status === OfferStatus.ACTIVE,
    slug: `offer-${id}`,
    template: "sales-letter",
    sections: {
      hero: { title: name, subtitle: "La solucion definitiva" },
    },
  },
});

export const MOCK_OFFERS: Offer[] = [
  createMockOffer(
    "1",
    "Curso Grabado Completo",
    OfferArchetype.PRODUCTO,
    497,
    OfferValueLevel.ACTIVACION,
  ),
  createMockOffer(
    "2",
    "Programa Grupal",
    OfferArchetype.PROGRAMA,
    2500,
    OfferValueLevel.TRANSFORMACION,
  ),
  createMockOffer(
    "3",
    "Servicio Productizado",
    OfferArchetype.SERVICIO,
    2000,
    OfferValueLevel.TRANSFORMACION,
  ),
  createMockOffer(
    "4",
    "Comunidad Premium",
    OfferArchetype.MEMBRESIA,
    97,
    OfferValueLevel.ACTIVACION,
  ),
  createMockOffer(
    "5",
    "Retiro de Lujo",
    OfferArchetype.EXPERIENCIA,
    8000,
    OfferValueLevel.MAXIMIZACION,
  ),
];

export const MOCK_OFFER_FULL = MOCK_OFFERS[0];
export const MOCK_OFFER_EMPTY = createMockOffer(
  "new",
  "Nueva Oferta",
  OfferArchetype.PRODUCTO,
  0,
  OfferValueLevel.LEAD_MAGNET,
  OfferStatus.DRAFT,
);
