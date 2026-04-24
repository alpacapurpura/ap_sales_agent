/**
 * Path-contract test — every field `path` in the OFFER_LEVEL schemas must
 * exist as an attribute on the `Offer` aggregate (represented here as an
 * allowlist of canonical DB / domain paths). Fails if a phantom path is added.
 *
 * Allowlist source: CONTRACT §13.4 + backend Offer domain aggregate fields.
 * Regenerate with: backend/.venv/bin/python scripts/dump_offer_fields.py
 */
import { describe, expect, it } from "vitest";

import { offerClosingSchema } from "../closing.schema";
import { offerIdentitySchema } from "../identity.schema";
import { offerPromiseSchema } from "../promise.schema";
import { offerPsychologySchema } from "../psychology.schema";
import { offerStrategySchema } from "../strategy.schema";

import type { FieldSchema } from "@/lib/form-runtime/schema";

// Canonical paths that exist on the Offer domain aggregate / ProductResponse DTO.
// CONTRACT §13.4. Add here when backend adds a new field; never add phantom paths.
const ALLOWED_OFFER_PATHS: ReadonlySet<string> = new Set([
  // identity
  "name",
  "internal_sku",
  "headline_promise",
  "primary_outcome",
  "time_to_value",
  // promise (narrative)
  "before_state",
  "after_state",
  "why_now",
  "measurable_outcomes",
  // strategy
  "avatar_id",
  "value_level",
  "delivery_model",
  "target_avatar_match",
  "anti_avatar_keywords",
  "marketing_pain_points",
  "marketing_desires",
  // psychology
  "objections",
  "cultural_trust_barriers",
  "emotional_triggers",
  "status_drivers",
  "regret_scenarios",
  // closing
  "guarantee_type",
  "guarantee_terms",
  "checkout_page_url",
  "calendar_type_id",
  "onboarding_action",
  "onboarding_url",
  "downsell_offer_id",
  "upsell_offer_id",
  "vsl_link",
  "refund_process_description",
  "urgency_drivers",
  "scarcity_reason_honest",
  "bonus_if_act_now",
  "final_push_copy",
  "support_duration_days",
]);

// Paths allowed in itemSchema sub-fields (ObjectionItem sub-fields)
const ALLOWED_ITEM_PATHS: ReadonlySet<string> = new Set([
  "type",
  "trigger_phrases",
  "rebuttal",
  "strategy",
]);

function collectPaths(fields: FieldSchema[]): { id: string; path: string }[] {
  return fields.map((f) => ({ id: f.id, path: f.path }));
}

const schemas = [
  offerIdentitySchema,
  offerPromiseSchema,
  offerStrategySchema,
  offerPsychologySchema,
  offerClosingSchema,
];

describe("Offer schema paths — canonical DB alignment (CONTRACT §13.4)", () => {
  for (const schema of schemas) {
    describe(`${schema.key}`, () => {
      const topLevelFields = collectPaths(schema.fields);

      for (const { id, path } of topLevelFields) {
        it(`field "${id}" uses canonical path "${path}"`, () => {
          expect(ALLOWED_OFFER_PATHS).toContain(path);
        });
      }

      // Validate sub-fields inside itemSchema (array fields)
      for (const field of schema.fields) {
        if (field.type === "array" && field.itemSchema) {
          const { itemSchema } = field;
          describe(`${field.id} (array) itemSchema`, () => {
            for (const subField of itemSchema.fields) {
              it(`sub-field "${subField.id}" uses known item path "${subField.path}"`, () => {
                expect(ALLOWED_ITEM_PATHS).toContain(subField.path);
              });
            }
          });
        }
      }
    });
  }
});

describe("identity schema — specific path assertions (CONTRACT §9.1)", () => {
  it("public_name field uses path 'name' (canonical DB column)", () => {
    const field = offerIdentitySchema.fields.find((f) => f.id === "public_name");
    expect(field?.path).toBe("name");
  });
});

describe("strategy schema — _raw paths removed (CONTRACT §9.3)", () => {
  it("target_avatar_match uses canonical path (not _raw suffix)", () => {
    const field = offerStrategySchema.fields.find((f) => f.id === "target_avatar_match");
    expect(field?.path).toBe("target_avatar_match");
  });

  it("marketing_pain_points uses canonical path (not _raw suffix)", () => {
    const field = offerStrategySchema.fields.find((f) => f.id === "marketing_pain_points");
    expect(field?.path).toBe("marketing_pain_points");
  });

  it("marketing_desires uses canonical path (not _raw suffix)", () => {
    const field = offerStrategySchema.fields.find((f) => f.id === "marketing_desires");
    expect(field?.path).toBe("marketing_desires");
  });

  it("anti_avatar_keywords uses canonical path (not _raw suffix)", () => {
    const field = offerStrategySchema.fields.find((f) => f.id === "anti_avatar_keywords");
    expect(field?.path).toBe("anti_avatar_keywords");
  });
});

describe("strategy schema — storeAs newline_array on JSONB fields (CONTRACT §9.3)", () => {
  const arrayFields = [
    "target_avatar_match",
    "marketing_pain_points",
    "marketing_desires",
    "anti_avatar_keywords",
  ];

  for (const fieldId of arrayFields) {
    it(`${fieldId} declares storeAs: "newline_array"`, () => {
      const field = offerStrategySchema.fields.find((f) => f.id === fieldId);
      expect(field?.storeAs).toBe("newline_array");
    });
  }
});

describe("promise schema — measurable_outcomes storeAs (CONTRACT §9.2)", () => {
  it('measurable_outcomes declares storeAs: "newline_array"', () => {
    const field = offerPromiseSchema.fields.find((f) => f.id === "measurable_outcomes");
    expect(field?.storeAs).toBe("newline_array");
    expect(field?.path).toBe("measurable_outcomes");
  });
});

describe("psychology schema — objections as structured array (CONTRACT §9.4)", () => {
  it("objections field is type:array with path 'objections'", () => {
    const field = offerPsychologySchema.fields.find((f) => f.id === "objections");
    expect(field?.type).toBe("array");
    expect(field?.path).toBe("objections");
  });

  it("objections declares renderAs: 'cards' with documented override", () => {
    const field = offerPsychologySchema.fields.find((f) => f.id === "objections");
    expect(field?.renderAs).toBe("cards");
  });

  it("objections declares bulkPasteAction for structure_objections tool", () => {
    const field = offerPsychologySchema.fields.find((f) => f.id === "objections");
    expect(field?.bulkPasteAction?.toolName).toBe("structure_objections");
  });

  it("objections itemSchema has 4 sub-fields (type, trigger_phrases, rebuttal, strategy)", () => {
    const field = offerPsychologySchema.fields.find((f) => f.id === "objections");
    const subFieldIds = field?.itemSchema?.fields.map((f) => f.id);
    expect(subFieldIds).toContain("type");
    expect(subFieldIds).toContain("trigger_phrases");
    expect(subFieldIds).toContain("rebuttal");
    expect(subFieldIds).toContain("strategy");
  });

  it("trigger_phrases sub-field uses storeAs: newline_array", () => {
    const objField = offerPsychologySchema.fields.find((f) => f.id === "objections");
    const triggerField = objField?.itemSchema?.fields.find((f) => f.id === "trigger_phrases");
    expect(triggerField?.storeAs).toBe("newline_array");
  });
});

describe("psychology schema — narrative fields storeAs (CONTRACT §9.4)", () => {
  const narrativeFields = [
    "cultural_trust_barriers",
    "emotional_triggers",
    "status_drivers",
    "regret_scenarios",
  ];

  for (const fieldId of narrativeFields) {
    it(`${fieldId} declares storeAs: "newline_array"`, () => {
      const field = offerPsychologySchema.fields.find((f) => f.id === fieldId);
      expect(field?.storeAs).toBe("newline_array");
    });
  }
});

describe("closing schema — urgency_drivers storeAs (CONTRACT §9.5)", () => {
  it('urgency_drivers declares storeAs: "newline_array"', () => {
    const field = offerClosingSchema.fields.find((f) => f.id === "urgency_drivers");
    expect(field?.storeAs).toBe("newline_array");
    expect(field?.path).toBe("urgency_drivers");
  });
});
