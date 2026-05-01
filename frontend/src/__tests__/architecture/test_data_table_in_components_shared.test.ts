/**
 * ARCH TEST: DataTable must live in components/shared/, NOT in features/.
 *
 * DataTable is a cross-feature primitive (crm-hub today, campaigns/segments PI-3).
 * Placing it inside a feature would require a refactor in PI-3.
 *
 * This test enforces the FSD-Lite boundary: shared primitives → components/shared/.
 */
import * as fs from "node:fs";
import * as path from "node:path";

import { test, expect } from "vitest";

test("DataTable lives in components/shared/data-table/, not in features/", () => {
  const sharedPath = path.resolve(__dirname, "../../components/shared/data-table/DataTable.tsx");
  expect(fs.existsSync(sharedPath), `Expected DataTable at ${sharedPath}`).toBe(true);
});

test("DataTable does NOT exist in features/crm-hub/components/ (boundary enforcement)", () => {
  const featuresPath = path.resolve(__dirname, "../../features/crm-hub/components/DataTable.tsx");
  expect(
    fs.existsSync(featuresPath),
    `DataTable found in features/crm-hub/components/ — move to components/shared/data-table/`,
  ).toBe(false);
});
