"use client";

import { cn } from "@/lib/utils";

import { useFormRuntime } from "./FormRuntimeContext";

import type { FieldSchema } from "@/lib/form-runtime/schema";

export interface FieldListProps {
  onFieldSelect: (fieldId: string) => void;
  activeFieldId: string | null;
  className?: string;
}

/**
 * Left pane — compact list of fields with truncated value preview. The active
 * row is highlighted. Clicking a row sets the detail pane focus.
 */
export function FieldList({ onFieldSelect, activeFieldId, className }: FieldListProps) {
  const { schema, values } = useFormRuntime();

  return (
    <ul className={cn("divide-y divide-border rounded-md border", className)} role="listbox">
      {schema.fields.map((field) => (
        <FieldRow
          key={field.id}
          field={field}
          value={values[field.path]}
          isActive={field.id === activeFieldId}
          onClick={() => onFieldSelect(field.id)}
        />
      ))}
    </ul>
  );
}

interface FieldRowProps {
  field: FieldSchema;
  value: unknown;
  isActive: boolean;
  onClick: () => void;
}

function FieldRow({ field, value, isActive, onClick }: FieldRowProps) {
  return (
    <li>
      <button
        type="button"
        onClick={onClick}
        aria-selected={isActive}
        role="option"
        className={cn(
          "flex w-full items-start justify-between gap-3 px-4 py-3 text-left text-sm transition-colors",
          isActive ? "bg-muted" : "hover:bg-muted/50",
        )}
      >
        <div className="min-w-0 flex-1">
          <div className="font-medium">{field.label}</div>
          <div className="mt-0.5 truncate text-xs text-muted-foreground">
            {preview(field, value)}
          </div>
        </div>
      </button>
    </li>
  );
}

function isEmpty(value: unknown): boolean {
  return value === null || value === undefined || value === "";
}

function previewArrayCount(value: unknown): string {
  const count = Array.isArray(value) ? value.length : 0;
  if (count === 0) return "—";
  return `${count} ítem${count === 1 ? "" : "s"}`;
}

function preview(field: FieldSchema, value: unknown): string {
  if (isEmpty(value)) return field.placeholder ? "" : "—";
  if (field.type === "boolean") return value ? "Sí" : "No";
  if (field.type === "array") return previewArrayCount(value);
  if (typeof value === "string") return value.slice(0, 80);
  if (typeof value === "number") return String(value);
  return "";
}
