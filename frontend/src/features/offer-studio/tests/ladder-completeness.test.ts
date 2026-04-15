import { describe, it, expect } from "vitest";

import {
  OfferArchetype,
  OfferValueLevel,
  OfferDeliveryModel,
  OfferStatus,
  GuaranteeType,
} from "../types";
import { computeLadderCompleteness } from "../utils/ladder-completeness";

import type { Offer } from "../types";

const makeOffer = (level: OfferValueLevel): Offer => ({
  id: `test-${level}`,
  name: `Offer ${level}`,
  archetype: OfferArchetype.PRODUCTO,
  value_level: level,
  delivery_model: OfferDeliveryModel.DIY,
  status: OfferStatus.ACTIVE,
  pricing: [],
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
});

describe("computeLadderCompleteness", () => {
  it("returns vacia score with no offers", () => {
    const result = computeLadderCompleteness([]);
    expect(result.score).toBe("vacia");
    expect(result.percentage).toBe(0);
    expect(result.gaps).toHaveLength(5);
    expect(result.filledGroups.size).toBe(0);
  });

  it("returns iniciando score with 1 group filled", () => {
    const result = computeLadderCompleteness([makeOffer(OfferValueLevel.LEAD_MAGNET)]);
    expect(result.score).toBe("iniciando");
    expect(result.percentage).toBe(20);
    expect(result.gaps).toHaveLength(4);
    expect(result.filledGroups.has(OfferValueLevel.LEAD_MAGNET)).toBe(true);
  });

  it("returns creciendo with 2-3 groups filled", () => {
    const result = computeLadderCompleteness([
      makeOffer(OfferValueLevel.LEAD_MAGNET),
      makeOffer(OfferValueLevel.TRANSFORMACION),
    ]);
    expect(result.score).toBe("creciendo");
    expect(result.percentage).toBe(40);
    expect(result.gaps).toHaveLength(3);
  });

  it("returns completa with 4 groups filled", () => {
    const result = computeLadderCompleteness([
      makeOffer(OfferValueLevel.LEAD_MAGNET),
      makeOffer(OfferValueLevel.ACTIVACION),
      makeOffer(OfferValueLevel.TRANSFORMACION),
      makeOffer(OfferValueLevel.MAXIMIZACION),
    ]);
    expect(result.score).toBe("completa");
    expect(result.percentage).toBe(80);
    expect(result.gaps).toHaveLength(1);
  });

  it("returns avanzada with all 5 groups filled", () => {
    const result = computeLadderCompleteness([
      makeOffer(OfferValueLevel.LEAD_MAGNET),
      makeOffer(OfferValueLevel.ACTIVACION),
      makeOffer(OfferValueLevel.TRANSFORMACION),
      makeOffer(OfferValueLevel.MAXIMIZACION),
      makeOffer(OfferValueLevel.CORPORATIVO),
    ]);
    expect(result.score).toBe("avanzada");
    expect(result.percentage).toBe(100);
    expect(result.gaps).toHaveLength(0);
  });

  it("sorts gaps by priority: critico first", () => {
    const result = computeLadderCompleteness([
      makeOffer(OfferValueLevel.ACTIVACION),
      makeOffer(OfferValueLevel.MAXIMIZACION),
    ]);
    // Gaps: lead_magnet (critico), transformacion (critico), corporativo (opcional)
    expect(result.gaps[0].priority).toBe("critico");
    expect(result.gaps[1].priority).toBe("critico");
    expect(result.gaps[2].priority).toBe("opcional");
  });

  it("counts multiple offers in same group as one filled group", () => {
    const result = computeLadderCompleteness([
      makeOffer(OfferValueLevel.TRANSFORMACION),
      makeOffer(OfferValueLevel.TRANSFORMACION),
      makeOffer(OfferValueLevel.TRANSFORMACION),
    ]);
    expect(result.filledGroups.size).toBe(1);
    expect(result.percentage).toBe(20);
  });
});
