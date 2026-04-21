"use client";

import { Info } from "lucide-react";

import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";

import type { ConditionalQuestion } from "@/features/offer-studio/api/offer-type-preset-catalog-api";

interface ConditionalQuestionsStepProps {
  /** Questions the selected preset declares as applicable. Filtered from
   *  the catalog by ``conditional_question_ids`` in the picker step. */
  questions: readonly ConditionalQuestion[];
  answers: Readonly<Record<string, boolean>>;
  onChange: (next: Record<string, boolean>) => void;
  /** User-facing label for the preset chosen, so the user has context
   *  about which decisions these questions refine. */
  presetLabel: string;
}

/**
 * Step 3 of the preset-first wizard. Renders a yes/no toggle per
 * conditional question declared by the selected preset.
 *
 * Zero-question case: the caller (``CreateOfferWizard``) detects an
 * empty ``questions`` tuple and skips this step entirely. This component
 * does not render a passthrough state.
 *
 * Defaults: the parent holds ``answers`` state. Toggles start at
 * ``false`` (no) and flip on user interaction.
 */
export function ConditionalQuestionsStep({
  questions,
  answers,
  onChange,
  presetLabel,
}: ConditionalQuestionsStepProps) {
  const handleToggle = (questionId: string, next: boolean) => {
    onChange({ ...answers, [questionId]: next });
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">Refina tu {presetLabel.toLowerCase()}</h3>
        <p className="text-sm text-muted-foreground">
          Responde esto para que la oferta quede configurada con los detalles correctos desde el
          principio. Puedes cambiarlo después.
        </p>
      </div>

      <div className="space-y-3">
        {questions.map((question) => (
          <QuestionRow
            key={question.question_id}
            question={question}
            checked={Boolean(answers[question.question_id])}
            onChange={(next) => handleToggle(question.question_id, next)}
          />
        ))}
      </div>
    </div>
  );
}

interface QuestionRowProps {
  question: ConditionalQuestion;
  checked: boolean;
  onChange: (next: boolean) => void;
}

function QuestionRow({ question, checked, onChange }: QuestionRowProps) {
  return (
    <label
      className="flex items-start gap-4 rounded-md border bg-card p-4 cursor-pointer hover:border-primary/50 transition"
      htmlFor={`cond-q-${question.question_id}`}
    >
      <div className="flex-1 min-w-0 space-y-1">
        <div className="font-medium text-sm">{question.question_es}</div>
        {question.help_es && (
          <p className="text-xs text-muted-foreground flex items-start gap-1.5">
            <Info className="h-3 w-3 shrink-0 mt-0.5" aria-hidden />
            <span>{question.help_es}</span>
          </p>
        )}
      </div>
      <Switch id={`cond-q-${question.question_id}`} checked={checked} onCheckedChange={onChange} />
      <Label htmlFor={`cond-q-${question.question_id}`} className="sr-only">
        {question.question_es}
      </Label>
    </label>
  );
}
