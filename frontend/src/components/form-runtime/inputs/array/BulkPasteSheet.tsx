"use client";

import { AlertTriangle, Loader2, Sparkles } from "lucide-react";
import { useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import { fetchClient } from "@/lib/http-client";

import type { BulkPasteActionConfig } from "@/lib/form-runtime/schema";

type Row = Record<string, unknown>;

interface BulkPasteSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  config: BulkPasteActionConfig;
  fieldPath: string;
  onResult: (proposed: Row[]) => void;
}

/**
 * Generic Sheet for bulk-paste → AI structuring of array field items.
 *
 * Domain-agnostic: the copilot tool name and copy come from BulkPasteActionConfig.
 * The result is delivered via onResult (caller merges with existing items).
 *
 * Following the CONTRACT Addendum corrección D7: the result is passed directly
 * to onResult (merge with existing items), not via the copilot propose_field_updates
 * flow. The user initiated the action explicitly by opening the Sheet and clicking
 * "Estructurar con IA".
 *
 * Reusable by any studio that declares bulkPasteAction on an array field.
 */
export function BulkPasteSheet({
  open,
  onOpenChange,
  config,
  fieldPath,
  onResult,
}: BulkPasteSheetProps) {
  const [rawText, setRawText] = useState("");
  const [isPending, setIsPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const nonEmptyLines = rawText.split("\n").filter((l) => l.trim().length > 0);
  const lineCount = nonEmptyLines.length;
  const canSubmit = lineCount >= 2 && !isPending;

  function handleOpenChange(next: boolean) {
    if (!isPending) {
      onOpenChange(next);
      if (!next) {
        setRawText("");
        setError(null);
      }
    }
  }

  async function handleStructure() {
    if (!canSubmit) return;
    setIsPending(true);
    setError(null);

    try {
      const response = await fetchClient(`/api/v1/copilot/tools/${config.toolName}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_text: rawText }),
      });

      if (!response.ok) {
        throw new Error(`Error ${response.status}`);
      }

      const data = (await response.json()) as {
        status: string;
        draft_fields?: Record<string, Row[]>;
      };

      const proposed = data.draft_fields?.[fieldPath] ?? [];
      onResult(proposed);
      handleOpenChange(false);
    } catch {
      setError("No pudimos estructurar. Revisa que sean frases claras, una por línea.");
    } finally {
      setIsPending(false);
    }
  }

  return (
    <Sheet open={open} onOpenChange={handleOpenChange}>
      <SheetContent side="right" className="w-[400px] lg:w-[480px] flex flex-col gap-0 p-0">
        <SheetHeader className="px-6 pt-6 pb-4 border-b border-border">
          <SheetTitle>{config.label}</SheetTitle>
          <SheetDescription>
            {config.hint ??
              "Pega el texto con los elementos, uno por línea. La IA los analizará y estructurará."}
          </SheetDescription>
        </SheetHeader>

        <div className="flex-1 px-6 py-4 flex flex-col gap-3 overflow-auto">
          <Textarea
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            placeholder={config.placeholder}
            className="min-h-[240px] resize-none text-sm leading-relaxed"
            aria-label="Texto para estructurar con IA"
            disabled={isPending}
          />

          {lineCount > 0 && (
            <p className="text-xs text-muted-foreground">
              {lineCount} {lineCount === 1 ? "línea detectada" : "líneas detectadas"}
            </p>
          )}

          {isPending && (
            <div role="status" aria-live="polite" className="flex flex-col gap-2">
              <Progress className="h-1.5 animate-pulse" />
              <p className="text-xs text-muted-foreground text-center">Estructurando con IA...</p>
            </div>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </div>

        <SheetFooter className="px-6 py-4 border-t border-border flex gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={isPending}
            className="flex-1"
          >
            Cancelar
          </Button>
          <Button
            type="button"
            onClick={() => {
              void handleStructure();
            }}
            disabled={!canSubmit}
            className="flex-1"
          >
            {isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Procesando...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Estructurar con IA
              </>
            )}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}

BulkPasteSheet.displayName = "BulkPasteSheet";
