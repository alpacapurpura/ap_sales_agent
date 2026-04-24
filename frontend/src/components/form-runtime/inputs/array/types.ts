import type { ReactNode } from "react";

import type { FieldSchema } from "@/lib/form-runtime/schema";

/**
 * Renderer inyectado por el parent FieldRenderer para que los editores
 * de array rendericen campos anidados sin depender directamente de
 * ArrayInput. Vive en array/types.ts para romper el ciclo
 * ArrayInput ↔ ArrayCardsEditor / ArraySplitEditor.
 */
export type NestedFieldRenderer = (props: {
  field: FieldSchema;
  value: unknown;
  onChange: (next: unknown) => void;
  disabled?: boolean;
}) => ReactNode;
