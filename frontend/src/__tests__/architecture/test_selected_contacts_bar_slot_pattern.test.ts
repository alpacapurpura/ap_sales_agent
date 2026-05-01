/**
 * ARCH TEST: SelectedContactsBar must accept slot pattern actions prop.
 *
 * The `actions: SelectedContactsBarAction[]` prop is the PI-3 extension point.
 * PR-12 will inject "Crear segmento" as the first action.
 * PI-3 will inject more bulk actions.
 *
 * If this prop is removed, the slot pattern breaks and PI-3 requires refactor.
 * This test enforces the contract at the TypeScript structural typing level.
 */
import { test, expect } from "vitest";

import type { SelectedContactsBar } from "@/features/crm-hub/components/SelectedContactsBar";
import type { SelectedContactsBarAction } from "@/features/crm-hub/types";
import type * as React from "react";

test("SelectedContactsBar accepts actions slot prop (PI-3 expansion contract)", () => {
  // Type-level structural test: if the prop interface changes, tsc fails.
  type Props = React.ComponentProps<typeof SelectedContactsBar>;
  const sample: Props = {
    selectedIds: [],
    actions: [] as SelectedContactsBarAction[],
    onClearSelection: () => {},
  };
  expect(sample.actions).toBeDefined();
  expect(Array.isArray(sample.actions)).toBe(true);
});

test("SelectedContactsBarAction type has required id, label, onClick fields", () => {
  const action: SelectedContactsBarAction = {
    id: "test-action",
    label: "Acción de prueba",
    onClick: (_ids: string[]) => {},
  };
  expect(action.id).toBe("test-action");
  expect(action.label).toBe("Acción de prueba");
  expect(typeof action.onClick).toBe("function");
});
