"use client";

import {
  CollapsibleFieldGroup,
  groupFieldsByGroup,
  hasFieldGroups,
} from "../../CollapsibleFieldGroup";
import { FieldLabelWithHelp } from "../../FieldLabelWithHelp";

import type { NestedFieldRenderer } from "./types";
import type { FieldSchema } from "@/lib/form-runtime/schema";

type Row = Record<string, unknown>;

export interface RenderItemFieldsProps {
  fields: readonly FieldSchema[];
  item: Row;
  onUpdate: (patch: Row) => void;
  renderField: NestedFieldRenderer;
  disabled?: boolean;
}

/**
 * Render an array item's sub-fields. Shared by ``ArrayCardsEditor`` and
 * ``ArraySplitEditor`` so both editors handle ``field.group`` identically.
 *
 * When any sub-field declares ``group``, adjacent fields with the same
 * group label are wrapped in a collapsible subsection. Schemas without
 * groups fall back to a flat list — same DOM shape as before, no visual
 * regression.
 */
export function ArrayItemFields({
  fields,
  item,
  onUpdate,
  renderField,
  disabled,
}: RenderItemFieldsProps) {
  const buckets = groupFieldsByGroup(fields);
  if (!hasFieldGroups(buckets)) {
    return (
      <>
        {fields.map((subField) => (
          <SubFieldRow
            key={subField.id}
            field={subField}
            value={item[subField.path]}
            onChange={(next) => onUpdate({ [subField.path]: next })}
            renderField={renderField}
            disabled={disabled}
          />
        ))}
      </>
    );
  }

  return (
    <>
      {buckets.map((bucket, bucketIdx) => {
        const bucketKey = bucket.group ?? `__ungrouped_${bucketIdx}`;
        const rows = bucket.fields.map((subField) => (
          <SubFieldRow
            key={subField.id}
            field={subField}
            value={item[subField.path]}
            onChange={(next) => onUpdate({ [subField.path]: next })}
            renderField={renderField}
            disabled={disabled}
          />
        ));
        if (bucket.group === null) {
          return (
            <div key={bucketKey} className="space-y-3">
              {rows}
            </div>
          );
        }
        return (
          <CollapsibleFieldGroup key={bucketKey} label={bucket.group} count={bucket.fields.length}>
            {rows}
          </CollapsibleFieldGroup>
        );
      })}
    </>
  );
}

interface SubFieldRowProps {
  field: FieldSchema;
  value: unknown;
  onChange: (next: unknown) => void;
  renderField: NestedFieldRenderer;
  disabled?: boolean;
}

function SubFieldRow({ field, value, onChange, renderField, disabled }: SubFieldRowProps) {
  return (
    <div>
      <FieldLabelWithHelp
        field={field}
        htmlFor={field.id}
        className="mb-1.5 text-xs text-muted-foreground"
      />
      {renderField({ field, value, onChange, disabled })}
    </div>
  );
}
