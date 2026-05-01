/**
 * ARCH TEST: FE ContactFilterParams must mirror Pydantic ContactFilterParams.
 *
 * CANONICAL_FILTER_FIELDS is the ratchet: any field in the Pydantic schema
 * must exist in the FE schema. Shrink-only — removing a field fails CI.
 *
 * When PI-3 adds a new filter to BE:
 * 1. Add it to CONTACT_FILTER_FIELDS in frontend/src/features/crm-hub/types/index.ts
 * 2. Add it to contactFilterParamsSchema
 * 3. Update CANONICAL_PYDANTIC_FIELDS here
 */
import { test, expect } from "vitest";

import { CONTACT_FILTER_FIELDS, contactFilterParamsSchema } from "@/features/crm-hub/types";

const CANONICAL_PYDANTIC_FIELDS = [
  "lifecycle_stage_in",
  "score_min",
  "score_max",
  "source_in",
  "has_email",
  "has_phone",
  "has_telegram_id",
  "has_whatsapp_id",
  "has_instagram_id",
  "has_tiktok_id",
  "created_after",
  "created_before",
  "last_activity_after",
  "last_activity_before",
  "is_inactive",
  "has_campaign_engagement",
  "country_in",
  "q",
] as const;

test("CONTACT_FILTER_FIELDS mirrors Pydantic ContactFilterParams CANONICAL_FILTER_FIELDS", () => {
  const feFields = new Set(CONTACT_FILTER_FIELDS);
  const canonicalFields = new Set(CANONICAL_PYDANTIC_FIELDS);
  expect(feFields).toEqual(canonicalFields);
});

test("contactFilterParamsSchema includes all canonical keys", () => {
  const schemaKeys = new Set(Object.keys(contactFilterParamsSchema.shape));
  const canonicalFields = new Set(CANONICAL_PYDANTIC_FIELDS);
  expect(schemaKeys).toEqual(canonicalFields);
});
