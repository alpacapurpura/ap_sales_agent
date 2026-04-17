"use client";

import { Calendar, HelpCircle, Sparkles } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

import { EditionPreviewCard } from "./EditionPreviewCard";

export interface InterviewDateAnswer {
  start_date: string | null;
  /** Present only when the user picked the "skip" option. */
  skipped: boolean;
}

export interface InterviewDateBlockProps {
  /** Question to render — server-side controls the copy. */
  question: string;
  /** Optional hint shown below the question. */
  hint?: string;
  /** AI-suggested default date (ISO 8601) — null if the backend had no hint. */
  suggestedDate: string | null;
  /** Archetype's edition noun ("cohorte", "salida", "convocatoria"). */
  editionNoun?: string;
  /** Called when the user confirms an answer (either a date or skip). */
  onSubmit: (answer: InterviewDateAnswer) => Promise<void> | void;
  /** When true the submit action is disabled (network call in flight). */
  submitting?: boolean;
}

function formatSuggestionLabel(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("es-PE", { day: "numeric", month: "long" });
}

/**
 * Final block of the offer interview asking when the first edition runs.
 *
 * Visual structure matches `prototype/copilot/interview-date.html`:
 * chat bubble on the left (question + three quick replies), live
 * `EditionPreviewCard` on the right that reacts instantly as the user
 * chooses a date or hits skip.
 */
export function InterviewDateBlock({
  question,
  hint,
  suggestedDate,
  editionNoun = "Edición",
  onSubmit,
  submitting = false,
}: InterviewDateBlockProps) {
  const [pendingDate, setPendingDate] = useState<string | null>(null);
  const [showPicker, setShowPicker] = useState(false);
  const [showSkipConfirm, setShowSkipConfirm] = useState(false);

  const confirmedDate = pendingDate ?? (showSkipConfirm ? null : null);

  const chooseSuggestion = async () => {
    if (!suggestedDate) return;
    setPendingDate(suggestedDate);
    await onSubmit({ start_date: suggestedDate, skipped: false });
  };

  const openDatePicker = () => setShowPicker(true);

  const commitPickerDate = async (value: string) => {
    if (!value) return;
    setShowPicker(false);
    setPendingDate(value);
    await onSubmit({ start_date: value, skipped: false });
  };

  const requestSkip = () => setShowSkipConfirm(true);

  const confirmSkip = async () => {
    setShowSkipConfirm(false);
    setPendingDate(null);
    await onSubmit({ start_date: null, skipped: true });
  };

  return (
    <section className="grid grid-cols-1 gap-6 lg:grid-cols-5">
      <div className="space-y-4 lg:col-span-3">
        <div className="rounded-xl rounded-tl-none bg-muted p-4 text-sm">
          <p className="mb-1 font-semibold">{question}</p>
          {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
        </div>

        <div className="flex flex-wrap gap-2">
          {suggestedDate ? (
            <QuickReplyButton variant="prominent" disabled={submitting} onClick={chooseSuggestion}>
              <Calendar className="h-4 w-4" aria-hidden />
              El {formatSuggestionLabel(suggestedDate)}
            </QuickReplyButton>
          ) : null}
          <QuickReplyButton disabled={submitting} onClick={openDatePicker}>
            <Sparkles className="h-4 w-4" aria-hidden />
            Elegir fecha…
          </QuickReplyButton>
          <QuickReplyButton disabled={submitting} onClick={requestSkip}>
            <HelpCircle className="h-4 w-4" aria-hidden />
            Todavía no sé
          </QuickReplyButton>
        </div>

        {showPicker ? <DatePickerRow onConfirm={commitPickerDate} /> : null}
        {showSkipConfirm ? (
          <SkipConfirmation
            editionNoun={editionNoun}
            onCancel={() => setShowSkipConfirm(false)}
            onConfirm={confirmSkip}
          />
        ) : null}

        <p className="text-xs italic text-muted-foreground">
          💡 Si no sabés, creo la {editionNoun.toLowerCase()} en borrador y la publicás cuando
          tengas la fecha. Mientras tanto el agente pondrá leads en <strong>lista de espera</strong>
          .
        </p>
      </div>

      <aside className="space-y-3 lg:col-span-2">
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Vista en vivo
        </p>
        <EditionPreviewCard startDate={confirmedDate} editionNoun={editionNoun} editionNumber={1} />
      </aside>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────

interface QuickReplyProps {
  variant?: "prominent" | "normal";
  children: React.ReactNode;
  disabled?: boolean;
  onClick: () => void;
}

function QuickReplyButton({ variant = "normal", children, disabled, onClick }: QuickReplyProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "flex items-center gap-2 rounded-lg border bg-background px-4 py-2 text-sm transition-colors",
        variant === "prominent"
          ? "border-2 border-primary/40 font-medium hover:border-primary/70"
          : "border-border hover:border-foreground/40",
        disabled && "cursor-not-allowed opacity-60",
      )}
    >
      {children}
    </button>
  );
}

interface DatePickerRowProps {
  onConfirm: (isoDate: string) => void;
}

function DatePickerRow({ onConfirm }: DatePickerRowProps) {
  const [value, setValue] = useState<string>("");
  return (
    <div className="flex items-center gap-2 rounded-lg border bg-muted/40 p-3">
      <Input
        type="date"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        className="max-w-[180px]"
      />
      <Button
        size="sm"
        onClick={() => value && onConfirm(new Date(value).toISOString())}
        disabled={!value}
      >
        Confirmar fecha
      </Button>
    </div>
  );
}

interface SkipConfirmationProps {
  editionNoun: string;
  onCancel: () => void;
  onConfirm: () => void;
}

function SkipConfirmation({ editionNoun, onCancel, onConfirm }: SkipConfirmationProps) {
  return (
    <div className="rounded-lg border border-amber-300 bg-amber-50 p-3">
      <p className="text-sm font-semibold text-amber-900">
        ¿Crear {editionNoun.toLowerCase()} sin fecha?
      </p>
      <p className="mt-1 text-xs text-amber-700">
        Quedará en borrador y privada. Los leads van a waitlist hasta que configures una fecha.
      </p>
      <div className="mt-3 flex gap-2">
        <Button variant="outline" size="sm" onClick={onCancel}>
          Cancelar
        </Button>
        <Button size="sm" onClick={onConfirm}>
          Sí, crear en borrador
        </Button>
      </div>
    </div>
  );
}
