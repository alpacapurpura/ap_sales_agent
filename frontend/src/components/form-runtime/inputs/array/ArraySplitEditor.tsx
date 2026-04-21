"use client";

import { ChevronRight, Search } from "lucide-react";
import { useState } from "react";

import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
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

interface ArraySplitEditorProps {
  field: FieldSchema;
  value: Row[] | null | undefined;
  onChange: (next: Row[]) => void;
  renderField: NestedFieldRenderer;
  disabled?: boolean;
}

/**
 * Variante C — Split Master-Detail.
 *
 * Lista izquierda + editor derecha. Elimina empuje vertical.
 * Ideal para arrays con 4+ sub-campos por ítem.
 *
 * Mobile: stack vertical (lista arriba, editor abajo). MVP progresivo —
 * el grid colapsa en columna en pantallas < md. Fallback de drawer es Sprint
 * siguiente.
 *
 * Autosave: onChange se propaga en cada cambio — el debounce vive en
 * use-auto-save.ts, no aquí.
 */
export function ArraySplitEditor({
  field,
  value,
  onChange,
  renderField,
  disabled,
}: ArraySplitEditorProps) {
  const items: Row[] = Array.isArray(value) ? value : [];
  const { itemSchema, label } = field;
  const fields = itemSchema?.fields ?? [];

  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [search, setSearch] = useState("");

  function updateItem(index: number, patch: Row) {
    const next = items.slice();
    next[index] = { ...next[index], ...patch };
    onChange(next);
  }

  function addItem() {
    const next = [...items, {}];
    onChange(next);
    setSelectedIndex(next.length - 1);
  }

  function removeItem(index: number) {
    const next = items.slice();
    next.splice(index, 1);
    onChange(next);
    setSelectedIndex(null);
  }

  function duplicateItem(index: number) {
    const next = items.slice();
    next.splice(index + 1, 0, { ...items[index] });
    onChange(next);
    setSelectedIndex(index + 1);
  }

  const singularLabel = itemSchema?.itemNoun ?? singulariseES(label);
  const selectedItem =
    selectedIndex !== null && selectedIndex < items.length ? items[selectedIndex] : null;

  // Filter items by search query against primary summary
  const filteredIndices = items
    .map((item, i) => ({ item, i }))
    .filter(({ item }) => {
      if (!search.trim()) return true;
      const summary = summariseItem(item, fields).toLowerCase();
      return summary.includes(search.toLowerCase());
    });

  return (
    <Card className="overflow-hidden">
      <ArrayFieldHeader count={items.length} />

      {/* Split grid — collapses to column on mobile */}
      <div className="grid grid-cols-1 md:grid-cols-[280px_1fr] min-h-[480px]">
        {/* Left panel — list */}
        <div className="border-b md:border-b-0 md:border-r border-border flex flex-col">
          {/* Search */}
          <div className="p-2 border-b border-border">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
              <Input
                type="search"
                placeholder="Buscar en ítems…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="h-8 pl-8 text-xs"
              />
            </div>
          </div>

          {/* List */}
          <ul className="flex-1 overflow-y-auto">
            {filteredIndices.map(({ item, i }) => {
              const isSelected = selectedIndex === i;
              const summary = summariseItem(item, fields);
              const status = computeItemStatus(item, fields);
              const itemNumber = String(i + 1).padStart(2, "0");

              return (
                <li key={i}>
                  <button
                    type="button"
                    onClick={() => setSelectedIndex(i)}
                    className={cn(
                      "w-full flex items-center gap-2 px-3 py-2.5 text-left",
                      "border-l-2 transition-colors",
                      isSelected
                        ? "border-l-primary bg-primary/10"
                        : "border-l-transparent hover:bg-muted",
                    )}
                  >
                    <ArrayDragHandle disabled={disabled} className="shrink-0" />
                    <span className="font-mono text-[11px] text-muted-foreground w-6 shrink-0">
                      {itemNumber}
                    </span>
                    <span className="min-w-0 flex-1 truncate text-sm">
                      {summary || <span className="italic text-muted-foreground">Sin título</span>}
                    </span>
                    <ArrayItemBadge status={status} />
                    <ChevronRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                  </button>
                </li>
              );
            })}
          </ul>

          <ArrayAddButton
            label={singularLabel}
            onClick={addItem}
            disabled={disabled}
            className="border-t border-border border-b-0"
          />
        </div>

        {/* Right panel — editor */}
        <div className="flex flex-col">
          {selectedItem !== null && selectedIndex !== null ? (
            <>
              {/* Editor header */}
              <div className="flex items-start justify-between px-5 py-3.5 border-b border-border">
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">
                    {label}
                  </p>
                  <p className="text-sm font-semibold text-foreground mt-0.5">
                    {summariseItem(selectedItem, fields) || (
                      <span className="italic text-muted-foreground">Nuevo {singularLabel}</span>
                    )}
                  </p>
                </div>
                <ArrayItemActions
                  onDuplicate={() => duplicateItem(selectedIndex)}
                  onRemove={() => removeItem(selectedIndex)}
                  disabled={disabled}
                />
              </div>

              {/* Fields grid */}
              <div className="p-5 space-y-4 overflow-y-auto flex-1">
                {fields.map((subField) => (
                  <div
                    key={subField.id}
                    className={cn(
                      subField.type === "textarea" ||
                        subField.type === "array" ||
                        subField.type === "custom"
                        ? "col-span-2"
                        : "",
                    )}
                  >
                    <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
                      {subField.label}
                      {subField.required && <span className="ml-0.5 text-destructive">*</span>}
                    </label>
                    {renderField({
                      field: subField,
                      value: selectedItem[subField.path],
                      onChange: (next) => updateItem(selectedIndex, { [subField.path]: next }),
                      disabled,
                    })}
                    {subField.hint && (
                      <p className="mt-1 text-[11px] text-muted-foreground">{subField.hint}</p>
                    )}
                  </div>
                ))}
              </div>
            </>
          ) : (
            /* Empty state */
            <div className="flex flex-1 items-center justify-center text-center p-8">
              <div>
                <p className="text-sm text-muted-foreground">
                  Selecciona un ítem o agrega uno nuevo
                </p>
                <p className="text-xs text-muted-foreground/60 mt-1">
                  Los cambios se guardan automáticamente
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}

ArraySplitEditor.displayName = "ArraySplitEditor";
