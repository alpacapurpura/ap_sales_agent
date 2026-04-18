"use client";

import { Plus, Trash2 } from "lucide-react";
import { useState, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

import type { BaseInputProps } from "./types";
import type { FieldSchema } from "@/lib/form-runtime/schema";

type Row = Record<string, unknown>;

/**
 * Renderer injected by the parent FieldRenderer so ArrayInput can render
 * nested fields without a direct import dependency (breaks the import cycle).
 */
export type NestedFieldRenderer = (props: {
  field: FieldSchema;
  value: unknown;
  onChange: (next: unknown) => void;
  disabled?: boolean;
}) => ReactNode;

export interface ArrayInputProps extends BaseInputProps<Row[] | null | undefined> {
  renderField: NestedFieldRenderer;
}

/**
 * Renders an array of objects using a sub-schema. Each item renders its
 * fields via the injected renderField. New items start empty.
 */
export function ArrayInput({ field, value, onChange, disabled, renderField }: ArrayInputProps) {
  const items: Row[] = Array.isArray(value) ? value : [];
  const { itemSchema } = field;
  const [expandedIndex, setExpandedIndex] = useState<number | null>(items.length === 0 ? null : 0);

  if (!itemSchema) {
    return (
      <div className="text-xs text-destructive">
        Schema error: array field &quot;{field.id}&quot; missing itemSchema
      </div>
    );
  }

  function updateItem(index: number, itemPatch: Row) {
    const next = items.slice();
    next[index] = { ...next[index], ...itemPatch };
    onChange(next);
  }

  function removeItem(index: number) {
    const next = items.slice();
    next.splice(index, 1);
    onChange(next);
    setExpandedIndex(null);
  }

  function addItem() {
    const next = [...items, {}];
    onChange(next);
    setExpandedIndex(next.length - 1);
  }

  return (
    <div className="space-y-2">
      {items.map((item, index) => (
        <ArrayRow
          key={index}
          index={index}
          item={item}
          fields={itemSchema.fields}
          isExpanded={expandedIndex === index}
          onToggle={() => setExpandedIndex(expandedIndex === index ? null : index)}
          onPatch={(patch) => updateItem(index, patch)}
          onRemove={() => removeItem(index)}
          renderField={renderField}
          disabled={disabled}
        />
      ))}
      <Button type="button" variant="outline" size="sm" onClick={addItem} disabled={disabled}>
        <Plus className="mr-1 h-4 w-4" />
        Agregar
      </Button>
    </div>
  );
}

interface ArrayRowProps {
  index: number;
  item: Row;
  fields: FieldSchema[];
  isExpanded: boolean;
  onToggle: () => void;
  onPatch: (patch: Row) => void;
  onRemove: () => void;
  renderField: NestedFieldRenderer;
  disabled?: boolean;
}

function ArrayRow({
  index,
  item,
  fields,
  isExpanded,
  onToggle,
  onPatch,
  onRemove,
  renderField,
  disabled,
}: ArrayRowProps) {
  const summary = summarise(item, fields);

  return (
    <Card className="p-3">
      <div className="flex items-center justify-between gap-2">
        <button
          type="button"
          onClick={onToggle}
          className="flex-1 cursor-pointer truncate text-left text-sm hover:underline"
        >
          {summary || <span className="text-muted-foreground">Ítem {index + 1}</span>}
        </button>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={onRemove}
          disabled={disabled}
          aria-label="Eliminar ítem"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
      {isExpanded && (
        <div className="mt-3 space-y-3">
          {fields.map((subField) => (
            <div key={subField.id}>
              <label className="mb-1 block text-xs font-medium text-muted-foreground">
                {subField.label}
                {subField.required ? " *" : ""}
              </label>
              {renderField({
                field: subField,
                value: item[subField.path],
                onChange: (next) => onPatch({ [subField.path]: next }),
                disabled,
              })}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

function summarise(item: Row, fields: FieldSchema[]): string {
  for (const field of fields) {
    if (field.type === "text" || field.type === "textarea") {
      const v = item[field.path];
      if (typeof v === "string" && v.trim()) return v.slice(0, 60);
    }
  }
  return "";
}
