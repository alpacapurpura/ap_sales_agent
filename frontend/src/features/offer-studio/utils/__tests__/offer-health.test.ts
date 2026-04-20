import { describe, expect, it } from "vitest";

import {
  GuaranteeType,
  OfferArchetype,
  OfferDeliveryModel,
  OfferStatus,
  OfferValueLevel,
} from "../../types";
import { getOfferHealth, validateSection } from "../offer-health";

import type { Offer } from "../../types";

const BASE_OFFER: Offer = {
  id: "offer-1",
  name: "Offer under test",
  archetype: OfferArchetype.PROGRAMA,
  value_level: OfferValueLevel.ACTIVACION,
  delivery_model: OfferDeliveryModel.DWY,
  status: OfferStatus.DRAFT,
  pricing: [],
  currency: "USD",
  specific_details: {},
  marketing_pain_points: [],
  marketing_desires: [],
  target_avatar_match: [],
  objections: [],
  instructors: [],
  deliverables: [],
  assets: [],
  headline_promise: "",
  guarantee_type: GuaranteeType.NONE,
  guarantee_terms: "",
};

describe("validateSection", () => {
  it("marks identity incomplete when core fields are missing", () => {
    const offer = { ...BASE_OFFER, name: "" };
    expect(validateSection("identity", offer).status).toBe("incomplete");
  });

  it("marks strategy incomplete when no avatar or pain points", () => {
    expect(validateSection("strategy", BASE_OFFER).status).toBe("incomplete");
  });

  it("marks promise incomplete when headline_promise is empty", () => {
    expect(validateSection("promise", BASE_OFFER).status).toBe("incomplete");
  });

  it("marks pricing incomplete when pricing list is empty", () => {
    expect(validateSection("pricing", BASE_OFFER).status).toBe("incomplete");
  });

  it("marks pricing complete when at least one pricing tier exists", () => {
    const offer: Offer = {
      ...BASE_OFFER,
      pricing: [
        {
          label: "Standard",
          total_amount: 100,
          currency: "USD",
          deposit_required: 0,
          number_of_installments: 1,
          installment_amount: 100,
        },
      ],
    };
    expect(validateSection("pricing", offer).status).toBe("complete");
  });

  it("marks instructors optional when list is empty", () => {
    expect(validateSection("instructors", BASE_OFFER).status).toBe("optional");
  });

  it("marks resources optional regardless of data", () => {
    expect(validateSection("resources", BASE_OFFER).status).toBe("optional");
  });

  it("returns optional for unknown section keys", () => {
    expect(validateSection("custom_future_section", BASE_OFFER).status).toBe("optional");
  });
});

describe("getOfferHealth", () => {
  it("reports 0% with explanatory entry when sections list is empty", () => {
    const health = getOfferHealth(BASE_OFFER, []);
    expect(health.completionPercentage).toBe(0);
    expect(health.missingFields).toHaveLength(1);
    expect(health.sections).toStrictEqual({});
  });

  it("aggregates required sections only, ignoring optional ones", () => {
    const offer: Offer = { ...BASE_OFFER, name: "" };
    const health = getOfferHealth(offer, ["identity", "instructors", "resources"]);
    // identity is required and incomplete; instructors + resources are optional.
    expect(health.completionPercentage).toBe(0);
    expect(health.missingFields.some((m) => m.startsWith("identity:"))).toBe(true);
    expect(health.missingFields.some((m) => m.startsWith("instructors:"))).toBe(false);
  });

  it("returns 100% when every required section is complete", () => {
    const offer: Offer = {
      ...BASE_OFFER,
      headline_promise: "Transformá tu mente en 30 días",
      pricing: [
        {
          label: "Standard",
          total_amount: 100,
          currency: "USD",
          deposit_required: 0,
          number_of_installments: 1,
          installment_amount: 100,
        },
      ],
      guarantee_type: GuaranteeType.UNCONDITIONAL_30_DAY,
      marketing_pain_points: ["estrés"],
      marketing_desires: ["paz mental"],
      target_avatar_match: ["adulto profesional"],
      specific_details: { structure: "cohort" },
    };
    const sections = ["identity", "strategy", "psychology", "promise", "pricing", "closing"];
    const health = getOfferHealth(offer, sections);
    expect(health.completionPercentage).toBe(100);
    expect(health.missingFields).toHaveLength(0);
  });

  it("exposes a health record for every supplied section key", () => {
    const keys = ["identity", "strategy", "instructors"] as const;
    const health = getOfferHealth(BASE_OFFER, [...keys]);
    for (const key of keys) {
      expect(health.sections[key]).toBeDefined();
    }
  });
});
