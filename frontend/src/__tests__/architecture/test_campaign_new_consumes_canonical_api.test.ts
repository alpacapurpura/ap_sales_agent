/**
 * ARCH TEST: CampaignNewClient must only call canonical API endpoints.
 *
 * Forward-compat invariant: CampaignNewClient consumes only:
 *   /api/v1/campaigns
 *   /api/v1/segments
 *
 * Any other /api/v1/ path in the component source = drift warning.
 * This prevents FE-fabricated endpoints that don't exist in BE.
 */
import * as fs from "node:fs";
import * as path from "node:path";

import { test, expect } from "vitest";

test("CampaignNewClient imports only canonical API hooks (campaigns + segments)", () => {
  const filePath = path.resolve(
    __dirname,
    "../../features/campaigns-lite/components/CampaignNewClient.tsx",
  );
  const source = fs.readFileSync(filePath, "utf-8");

  // Check that only canonical API hooks are imported (not arbitrary api paths)
  const apiImports = source.match(/from ["']\.\.\/api\/([^"']+)["']/g) ?? [];
  for (const importLine of apiImports) {
    // Must be one of: use-create-campaign-mutation, use-add-campaign-step-mutation, use-schedule-campaign-mutation
    expect(importLine).toMatch(
      /use-(create-campaign|add-campaign-step|schedule-campaign)-mutation/,
    );
  }
});

test("CampaignNewClient does not hardcode non-canonical /api/v1/ paths", () => {
  const filePath = path.resolve(
    __dirname,
    "../../features/campaigns-lite/components/CampaignNewClient.tsx",
  );
  const source = fs.readFileSync(filePath, "utf-8");

  // Extract any raw /api/v1/... strings used inline (not from imported hooks)
  const rawApiCalls = source.match(/`\${API_URL}\/api\/v1\/[^`]+`/g) ?? [];
  for (const call of rawApiCalls) {
    // Should only reference /campaigns or /segments
    expect(call).toMatch(/\/api\/v1\/(campaigns|segments)/);
  }
});

test("CampaignNewClient file exists at canonical path", () => {
  const filePath = path.resolve(
    __dirname,
    "../../features/campaigns-lite/components/CampaignNewClient.tsx",
  );
  expect(fs.existsSync(filePath)).toBe(true);
});

test("campaigns-lite feature index.ts exports CampaignNewClient", () => {
  const filePath = path.resolve(__dirname, "../../features/campaigns-lite/index.ts");
  const source = fs.readFileSync(filePath, "utf-8");
  expect(source).toContain("CampaignNewClient");
  expect(source).toContain("CampaignDetailClient");
});
