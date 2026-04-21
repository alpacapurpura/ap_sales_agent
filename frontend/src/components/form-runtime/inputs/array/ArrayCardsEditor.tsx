"use client";

import { ChevronRight } from "lucide-react";
import { useState } from "react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

import { ArrayAddButton } from "./array-add-button";
import { ArrayDragHandle } from "./array-drag-handle";
import { ArrayFieldHeader } from "./array-field-header";
import { ArrayItemActions } from "./array-item-actions";
import { ArrayItemBadge } from "./array-item-badge";
import { singulariseES } from "./array-singularise";
import { summariseItem } from "./array-summary";
import { computeItemStatus } from "./array-validation";

import type { NestedFieldRenderer } from "../ArrayInput";
import type { FieldSchema } from "@/lib/form-runtime/schema";

type Row = Record<string, unknown>;

interface ArrayCardsEditorProps {
  field: FieldSchema;
  value: Row[] | null | undefined;
  onChange: (next: Row[]) => void;
  renderField: NestedFieldRenderer;
  disabled?: boolean;
}

/**
 * Variante A — Enhanced Cards.
 *
 * Items como cards apiladas con expand/collapse inline. Un ítem expandido a la vez.
 * Ideal para arrays de 1–3 sub-campos.
 * Autosave: propaga onChange al padre en cada cambio de campo — el debounce vive
 * en use-auto-save.ts, no aquí.
 */
export function ArrayCardsEditor({
  field,
  value,
  onChange,
  renderField,
  disabled,
}: ArrayCardsEditorProps) {
  const items: Row[] = Array.isArray(value) ? value : [];
  const { itemSchema, label } = field;
  const fields = itemSchema?.fields ?? [];

  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  function toggle(index: number) {
    setExpandedIndex((prev) => (prev === index ? null : index));
  }

  function updateItem(index: number, patch: Row) {
    const next = items.slice();
    next[index] = { ...next[index], ...patch };
    onChange(next);
  }

  function addItem() {
    const next = [...items, {}];
    onChange(next);
    setExpandedIndex(next.length - 1);
  }

  function removeItem(index: number) {
    const next = items.slice();
    next.splice(index, 1);
    onChange(next);
    setExpandedIndex(null);
  }

  function duplicateItem(index: number) {
    const next = items.slice();
    next.splice(index + 1, 0, { ...items[index] });
    onChange(next);
    setExpandedIndex(index + 1);
  }

  function collapseAll() {
    setExpandedIndex(null);
  }

  function expandAll() {
    // In single-expand mode, expand the first item if multiple exist
    if (items.length > 0) setExpandedIndex(0);
  }

  const singularLabel = itemSchema?.itemNoun ?? singulariseES(label);

  return (
    <Card className="overflow-hidden">
      <ArrayFieldHeader
        count={items.length}
        onCollapseAll={items.length > 1 ? collapseAll : undefined}
        onExpandAll={items.length > 1 ? expandAll : undefined}
      />

      <div className="p-4 space-y-2.5">
        {items.map((item, index) => {
          const isExpanded = expandedIndex === index;
          const status = computeItemStatus(item, fields);
          const summary = summariseItem(item, fields);
          const itemNumber = String(index + 1).padStart(2, "0");
          const firstRequiredField = fields.find((f) => f.required);
          const fieldLabel = status.startsWith("required-")
            ? (fields.find((f) => `required-${f.path}` === status)?.label ?? "campo")
            : undefined;

          return (
            <div
              key={index}
              className={cn(
                "rounded-lg border transition-colors",
                isExpanded
                  ? "border-primary/50 bg-card ring-1 ring-primary/20"
                  : "border-border bg-muted/50 hover:border-border",
              )}
            >
              {/* Item header row */}
              <div
                className={cn(
                  "flex items-center gap-2 px-3 py-2.5",
                  isExpanded && "border-b border-border",
                )}
              >
                <ArrayDragHandle disabled={disabled} />

                <button
                  type="button"
                  aria-label={
                    isExpanded ? `Colapsar ítem ${index + 1}` : `Expandir ítem ${index + 1}`
                  }
                  onClick={() => toggle(index)}
                  className="flex h-5 w-5 items-center justify-center text-muted-foreground hover:text-foreground"
                >
                  <ChevronRight
                    className={cn(
                      "h-4 w-4 transition-transform duration-200",
                      isExpanded && "rotate-90",
                      isExpanded && "text-primary",
                    )}
                  />
                </button>

                <span
                  className={cn(
                    "w-6 font-mono text-[11px]",
                    isExpanded ? "text-primary" : "text-muted-foreground",
                  )}
                >
                  {itemNumber}
                </span>

                <button
                  type="button"
                  onClick={() => toggle(index)}
                  className="min-w-0 flex-1 truncate text-left"
                >
                  {summary ? (
                    <span className="truncate text-sm text-foreground">{summary}</span>
                  ) : (
                    <span className="truncate text-sm italic text-muted-foreground">
                      Nuevo {singularLabel} — agrega{" "}
                      {firstRequiredField?.label?.toLowerCase() ?? "título"}
                    </span>
                  )}
                </button>

                <ArrayItemBadge status={status} fieldLabel={fieldLabel} />

                <ArrayItemActions
                  onDuplicate={() => duplicateItem(index)}
                  onRemove={() => removeItem(index)}
                  disabled={disabled}
                  className="ml-1"
                />
              </div>

              {/* Expanded fields */}
              {isExpanded && (
                <div className="px-4 py-4 space-y-4">
                  {fields.map((subField) => (
                    <div key={subField.id}>
                      <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
                        {subField.label}
                        {subField.required && <span className="ml-0.5 text-destructive">*</span>}
                      </label>
                      {renderField({
                        field: subField,
                        value: item[subField.path],
                        onChange: (next) => updateItem(index, { [subField.path]: next }),
                        disabled,
                      })}
                      {subField.hint && (
                        <p className="mt-1 text-[11px] text-muted-foreground">{subField.hint}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <ArrayAddButton label={singularLabel} onClick={addItem} disabled={disabled} />
    </Card>
  );
}

ArrayCardsEditor.displayName = "ArrayCardsEditor";
