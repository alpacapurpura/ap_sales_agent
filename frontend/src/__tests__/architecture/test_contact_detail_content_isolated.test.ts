/**
 * ARCH TEST: ContactDetailContent must NOT import Sheet/Drawer/Dialog.
 *
 * ContactDetailContent is designed to be host-agnostic:
 * - PR-11: hosted inside a Sheet (drawer)
 * - PI-3: hosted inside a full page route
 *
 * If ContactDetailContent imports Sheet/Dialog, it becomes coupled to
 * one host and cannot be reused in the other context.
 */
import * as fs from "node:fs";
import * as path from "node:path";

import { test, expect } from "vitest";

test("ContactDetailContent does NOT import Sheet/Drawer/Dialog (drawer-host agnostic)", () => {
  const filePath = path.resolve(
    __dirname,
    "../../features/crm-hub/components/ContactDetailContent.tsx",
  );

  expect(fs.existsSync(filePath), `File not found: ${filePath}`).toBe(true);

  const source = fs.readFileSync(filePath, "utf-8");
  expect(source).not.toMatch(/from\s+["']@\/components\/ui\/sheet["']/);
  expect(source).not.toMatch(/from\s+["']@\/components\/ui\/dialog["']/);
  expect(source).not.toMatch(/from\s+["']@\/components\/ui\/drawer["']/);
});
