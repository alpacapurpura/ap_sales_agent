"use client";

import { forwardRef } from "react";
import TextareaAutosize from "react-textarea-autosize";

import { cn } from "@/lib/utils";

import type { InputHTMLAttributes } from "react";
import type { TextareaAutosizeProps } from "react-textarea-autosize";

/**
 * Inline-editable inputs with a seamless chrome: when not focused the field
 * reads as plain text; hover reveals a subtle affordance; focus lifts the
 * background, borders and ring to full input chrome. Height auto-grows with
 * content (textarea variant) so long fields like "Historia" read entirely
 * without internal scrollbars.
 *
 * See docs/ux-sessions/2026-04-20-brand-studio-finder-nav/UI-SPEC-locked-dimensions.md
 * for the design contract.
 */

export type InlineEditableTone = "default" | "lg" | "xl";

const TONE_CLASS: Record<InlineEditableTone, string> = {
  default: "text-base leading-relaxed",
  lg: "text-lg leading-relaxed",
  xl: "text-xl font-medium leading-snug tracking-tight",
};

const BASE_CLASS = cn(
  "block w-full rounded-md border border-transparent bg-transparent",
  "px-[14px] py-3 text-foreground",
  "transition-[background-color,border-color,box-shadow] duration-100",
  "placeholder:italic placeholder:text-muted-foreground/70",
  "hover:not-focus:cursor-text hover:not-focus:bg-muted/25 hover:not-focus:border-border",
  "focus:bg-background focus:border-ring/50 focus:outline-none",
  "focus:ring-2 focus:ring-ring/20",
  "disabled:cursor-not-allowed disabled:opacity-60",
);

const TEXTAREA_CLASS = cn(BASE_CLASS, "resize-none overflow-hidden");

export interface InlineEditableTextareaProps
  extends Omit<TextareaAutosizeProps, "onChange" | "value"> {
  value: string;
  onChange: (next: string) => void;
  tone?: InlineEditableTone;
  /** Minimum rows (lines) to reserve before content grows. */
  minRows?: number;
}

export const InlineEditableTextarea = forwardRef<HTMLTextAreaElement, InlineEditableTextareaProps>(
  function InlineEditableTextarea(
    { value, onChange, tone = "default", minRows = 2, className, ...rest },
    ref,
  ) {
    return (
      <TextareaAutosize
        ref={ref}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        minRows={minRows}
        className={cn(TEXTAREA_CLASS, TONE_CLASS[tone], className)}
        {...rest}
      />
    );
  },
);

export interface InlineEditableInputProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, "onChange" | "value" | "type"> {
  value: string;
  onChange: (next: string) => void;
  tone?: InlineEditableTone;
  type?: "text" | "url" | "email" | "tel" | "number";
}

export const InlineEditableInput = forwardRef<HTMLInputElement, InlineEditableInputProps>(
  function InlineEditableInput(
    { value, onChange, tone = "default", type = "text", className, ...rest },
    ref,
  ) {
    return (
      <input
        ref={ref}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={cn(BASE_CLASS, TONE_CLASS[tone], className)}
        {...rest}
      />
    );
  },
);
