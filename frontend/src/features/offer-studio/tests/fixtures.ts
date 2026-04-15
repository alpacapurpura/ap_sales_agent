import {
  OfferArchetype,
  OfferValueLevel,
  OfferDeliveryModel,
  OfferStatus,
  GuaranteeType,
} from "../types";

import type { Offer } from "../types";

export const MOCK_BACKEND_RESPONSE = {
  id: "217ff363-8e96-4132-9542-935499bc7efc",
  public_name: "Guía: Liberar la Mente",
  archetype: "producto",
  status: "active",
  offer_value_level: "lead_magnet",
  delivery_model: "diy",
  pricing_options: [{ total_amount: 0, currency: "USD" }],
};

export const MOCK_OFFER_NORMALIZED: Offer = {
  id: "217ff363-8e96-4132-9542-935499bc7efc",
  name: "Guía: Liberar la Mente",
  archetype: OfferArchetype.PRODUCTO,
  value_level: OfferValueLevel.LEAD_MAGNET,
  delivery_model: OfferDeliveryModel.DIY,
  status: OfferStatus.ACTIVE,
  pricing: [
    {
      label: "Standard",
      total_amount: 0,
      currency: "USD",
      deposit_required: 0,
      number_of_installments: 1,
      installment_amount: 0,
    },
  ],
  currency: "USD",
  specific_details: {},
  marketing_pain_points: [],
  marketing_desires: [],
  deliverables: [],
  target_avatar_match: [],
  prerequisites: [],
  includes_offers: [],
  assets: [],
  guarantee_type: GuaranteeType.NONE,
  instructors: [],
};
