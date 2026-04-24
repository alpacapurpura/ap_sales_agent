"use client";

import { ArrayInput } from "./inputs/ArrayInput";
import { BooleanInput } from "./inputs/BooleanInput";
import { CustomInput } from "./inputs/CustomInput";
import { EmailInput } from "./inputs/EmailInput";
import { EnumInput } from "./inputs/EnumInput";
import { NumberInput } from "./inputs/NumberInput";
import { TextareaInput } from "./inputs/TextareaInput";
import { TextInput } from "./inputs/TextInput";
import { UrlInput } from "./inputs/UrlInput";

import type { FieldSchema, FieldType } from "@/lib/form-runtime/schema";
import type { ReactElement } from "react";

export interface FieldRendererProps {
  field: FieldSchema;
  value: unknown;
  onChange: (next: unknown) => void;
  disabled?: boolean;
  autoFocus?: boolean;
  onBlur?: () => void;
}

type InputRenderer = (props: FieldRendererProps) => ReactElement;

function renderText(p: FieldRendererProps) {
  return (
    <TextInput
      field={p.field}
      value={p.value as string}
      onChange={p.onChange as (v: string) => void}
      disabled={p.disabled}
      autoFocus={p.autoFocus}
      onBlur={p.onBlur}
    />
  );
}

function renderTextarea(p: FieldRendererProps) {
  return (
    <TextareaInput
      field={p.field}
      value={p.value as string | string[] | null}
      onChange={p.onChange as (v: string | string[] | null) => void}
      disabled={p.disabled}
      autoFocus={p.autoFocus}
      onBlur={p.onBlur}
    />
  );
}

function renderEnum(p: FieldRendererProps) {
  return (
    <EnumInput
      field={p.field}
      value={p.value as string}
      onChange={p.onChange as (v: string) => void}
      disabled={p.disabled}
    />
  );
}

function renderNumber(p: FieldRendererProps) {
  return (
    <NumberInput
      field={p.field}
      value={p.value as number | null}
      onChange={p.onChange as (v: number | null) => void}
      disabled={p.disabled}
      autoFocus={p.autoFocus}
      onBlur={p.onBlur}
    />
  );
}

function renderBoolean(p: FieldRendererProps) {
  return (
    <BooleanInput
      field={p.field}
      value={p.value as boolean}
      onChange={p.onChange as (v: boolean) => void}
      disabled={p.disabled}
    />
  );
}

function renderUrl(p: FieldRendererProps) {
  return (
    <UrlInput
      field={p.field}
      value={p.value as string}
      onChange={p.onChange as (v: string) => void}
      disabled={p.disabled}
      autoFocus={p.autoFocus}
      onBlur={p.onBlur}
    />
  );
}

function renderEmail(p: FieldRendererProps) {
  return (
    <EmailInput
      field={p.field}
      value={p.value as string}
      onChange={p.onChange as (v: string) => void}
      disabled={p.disabled}
      autoFocus={p.autoFocus}
      onBlur={p.onBlur}
    />
  );
}

function renderArray(p: FieldRendererProps) {
  return (
    <ArrayInput
      field={p.field}
      value={p.value as Record<string, unknown>[] | null | undefined}
      onChange={p.onChange as (v: Record<string, unknown>[] | null | undefined) => void}
      disabled={p.disabled}
      renderField={FieldRenderer}
    />
  );
}

function renderCustom(p: FieldRendererProps) {
  return <CustomInput field={p.field} value={p.value} onChange={p.onChange} />;
}

const RENDERERS: Record<FieldType, InputRenderer> = {
  text: renderText,
  textarea: renderTextarea,
  enum: renderEnum,
  number: renderNumber,
  boolean: renderBoolean,
  url: renderUrl,
  email: renderEmail,
  array: renderArray,
  custom: renderCustom,
};

/**
 * Dispatches to the correct input component based on field.type.
 * The source of truth for "which React component handles which FieldType".
 */
export function FieldRenderer(props: FieldRendererProps): ReactElement {
  return RENDERERS[props.field.type](props);
}
