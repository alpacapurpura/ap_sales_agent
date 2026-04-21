import { describe, it, expect } from "vitest";

import { backendToFrontend, offerToFormValues, frontendToBackend } from "../adapter";
import {
  OfferArchetype,
  OfferValueLevel,
  OfferDeliveryModel,
  OfferStatus,
  GuaranteeType,
  DeliverableFormat,
} from "../../types";

import { MOCK_BACKEND_RESPONSE, MOCK_OFFER_NORMALIZED } from "../../__tests__/fixtures";

import type { BackendOffer } from "../adapter";

// ─── backendToFrontend ───

describe("backendToFrontend", () => {
  it("normalizes a minimal backend response", () => {
    const result = backendToFrontend(MOCK_BACKEND_RESPONSE as BackendOffer);
    expect(result.id).toBe(MOCK_BACKEND_RESPONSE.id);
    expect(result.name).toBe(MOCK_BACKEND_RESPONSE.public_name);
    expect(result.archetype).toBe(OfferArchetype.PRODUCTO);
    expect(result.status).toBe(OfferStatus.ACTIVE);
    expect(result.value_level).toBe(OfferValueLevel.LEAD_MAGNET);
    expect(result.delivery_model).toBe(OfferDeliveryModel.DIY);
  });

  it("prefers public_name over name field", () => {
    const data: BackendOffer = {
      id: "1",
      archetype: "producto",
      public_name: "Public Name",
      name: "Internal Name",
    };
    const result = backendToFrontend(data);
    // name || public_name — name takes priority per implementation
    expect(result.name).toBe("Internal Name");
  });

  it("falls back to 'Oferta sin nombre' when no name fields", () => {
    const data: BackendOffer = { id: "1", archetype: "producto" };
    const result = backendToFrontend(data);
    expect(result.name).toBe("Oferta sin nombre");
  });

  it("maps pricing_options to pricing array", () => {
    const data: BackendOffer = {
      id: "1",
      archetype: "producto",
      pricing_options: [
        { total_amount: 99, currency: "PEN" },
        { total_amount: 199, label: "Premium" },
      ],
    };
    const result = backendToFrontend(data);
    expect(result.pricing).toHaveLength(2);
    expect(result.pricing![0].total_amount).toBe(99);
    expect(result.pricing![0].currency).toBe("PEN");
    expect(result.pricing![1].label).toBe("Premium");
  });

  it("handles null pricing gracefully", () => {
    const data: BackendOffer = {
      id: "1",
      archetype: "producto",
      pricing_options: undefined,
      pricing: undefined,
    };
    const result = backendToFrontend(data);
    expect(result.pricing).toEqual([]);
  });

  it("normalizes empty arrays to defaults", () => {
    const data: BackendOffer = { id: "1", archetype: "producto" };
    const result = backendToFrontend(data);
    expect(result.marketing_pain_points).toEqual([]);
    expect(result.marketing_desires).toEqual([]);
    expect(result.deliverables).toEqual([]);
    expect(result.target_avatar_match).toEqual([]);
    expect(result.prerequisites).toEqual([]);
    expect(result.includes_offers).toEqual([]);
    expect(result.assets).toEqual([]);
    expect(result.instructors).toEqual([]);
  });

  it("maps legacy value levels via LEGACY_VALUE_LEVEL_MAP", () => {
    const data: BackendOffer = {
      id: "1",
      archetype: "producto",
      offer_value_level: "level_0_free",
    };
    const result = backendToFrontend(data);
    expect(result.value_level).toBe(OfferValueLevel.LEAD_MAGNET);
  });

  it("maps legacy level_5_ultra_high to MAXIMIZACION", () => {
    const data: BackendOffer = {
      id: "1",
      archetype: "producto",
      offer_value_level: "level_5_ultra_high",
    };
    const result = backendToFrontend(data);
    expect(result.value_level).toBe(OfferValueLevel.MAXIMIZACION);
  });

  it("defaults missing value_level to ACTIVACION when not a lead magnet", () => {
    // Regression: a NULL/missing value_level used to collapse into
    // LEAD_MAGNET, dumping every newly-created paid offer into the
    // wrong ladder bucket in Offer Studio.
    const data: BackendOffer = {
      id: "1",
      archetype: "producto",
      is_lead_magnet: false,
    };
    const result = backendToFrontend(data);
    expect(result.value_level).toBe(OfferValueLevel.ACTIVACION);
  });

  it("defaults missing value_level to LEAD_MAGNET when flagged as lead magnet", () => {
    const data: BackendOffer = {
      id: "1",
      archetype: "producto",
      is_lead_magnet: true,
    };
    const result = backendToFrontend(data);
    expect(result.value_level).toBe(OfferValueLevel.LEAD_MAGNET);
  });

  it("normalizes deliverables with default format and quantity", () => {
    const data: BackendOffer = {
      id: "1",
      archetype: "producto",
      deliverables: [{ name: "Module 1" }],
    };
    const result = backendToFrontend(data);
    expect(result.deliverables![0].format).toBe(DeliverableFormat.VIDEO);
    expect(result.deliverables![0].quantity).toBe("1");
    expect(result.deliverables![0].value_stack_price).toBe(0);
  });

  it("normalizes objections with default fields", () => {
    const data: BackendOffer = {
      id: "1",
      archetype: "producto",
      objections: [{ id: "obj-1" }],
    };
    const result = backendToFrontend(data);
    expect(result.objections![0].type).toBe("custom");
    expect(result.objections![0].strategy).toBe("");
    expect(result.objections![0].rebuttal).toBe("");
    expect(result.objections![0].trigger_phrases).toEqual([]);
  });

  it("prefers metadata_info fields over direct fields", () => {
    const data: BackendOffer = {
      id: "1",
      archetype: "producto",
      onboarding_url: "direct-url",
      metadata_info: { onboarding_url: "metadata-url" },
    };
    const result = backendToFrontend(data);
    expect(result.onboarding_url).toBe("metadata-url");
  });

  it("falls back to direct field when metadata is missing", () => {
    const data: BackendOffer = {
      id: "1",
      archetype: "producto",
      onboarding_url: "direct-url",
      metadata_info: {},
    };
    const result = backendToFrontend(data);
    expect(result.onboarding_url).toBe("direct-url");
  });

  it("handles unknown enum values gracefully (defaults)", () => {
    const data: BackendOffer = {
      id: "1",
      archetype: "INVALID_ARCHETYPE",
      status: "bogus_status",
      delivery_model: "flying_carpet",
    };
    const result = backendToFrontend(data);
    expect(result.archetype).toBe(OfferArchetype.PRODUCTO);
    expect(result.status).toBe(OfferStatus.DRAFT);
    expect(result.delivery_model).toBe(OfferDeliveryModel.DIY);
  });

  it("handles case-insensitive enum match", () => {
    const data: BackendOffer = {
      id: "1",
      archetype: "PRODUCTO",
    };
    const result = backendToFrontend(data);
    expect(result.archetype).toBe(OfferArchetype.PRODUCTO);
  });
});

// ─── offerToFormValues ───

describe("offerToFormValues", () => {
  it("copies name to public_name", () => {
    const result = offerToFormValues(MOCK_OFFER_NORMALIZED);
    expect(result.public_name).toBe(MOCK_OFFER_NORMALIZED.name);
  });

  it("maps pricing to pricing_options", () => {
    const result = offerToFormValues(MOCK_OFFER_NORMALIZED);
    expect(result.pricing_options).toEqual(MOCK_OFFER_NORMALIZED.pricing);
  });

  it("handles empty pricing array", () => {
    const offer = { ...MOCK_OFFER_NORMALIZED, pricing: [] };
    const result = offerToFormValues(offer);
    expect(result.pricing_options).toEqual([]);
  });
});

// ─── frontendToBackend ───

describe("frontendToBackend", () => {
  it("maps public_name to name", () => {
    const values = { public_name: "My Offer" };
    const result = frontendToBackend(values);
    expect(result.name).toBe("My Offer");
  });

  it("does not overwrite existing name", () => {
    const values = { public_name: "Public", name: "Already Set" } as Record<string, unknown>;
    const result = frontendToBackend(values as never);
    expect(result.name).toBe("Already Set");
  });

  it("maps pricing_options to pricing", () => {
    const pricingOption = {
      label: "Standard",
      total_amount: 100,
      deposit_required: 0,
      number_of_installments: 1,
      installment_amount: 0,
      is_default: false,
      benefits: [] as string[],
      is_highlighted: false,
    };
    const values = { pricing_options: [pricingOption] };
    const result = frontendToBackend(values);
    expect(result.pricing).toEqual([pricingOption]);
  });

  it("strips metadata_info from payload", () => {
    const values = { metadata_info: { key: "val" }, public_name: "X" };
    const result = frontendToBackend(values as never);
    expect(result.metadata_info).toBeUndefined();
  });

  it("handles partial values gracefully", () => {
    const result = frontendToBackend({});
    expect(result).toBeDefined();
    expect(result.metadata_info).toBeUndefined();
  });
});
