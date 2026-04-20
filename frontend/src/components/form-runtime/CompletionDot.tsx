import { cn } from "@/lib/utils";

export type CompletionState = "filled" | "empty";

export interface CompletionDotProps {
  state: CompletionState;
  className?: string;
}

/**
 * 6px round dot indicating whether a field has a value. Filled = success token,
 * empty = destructive (muted). Used inside Finder-style field rows.
 */
export function CompletionDot({ state, className }: CompletionDotProps) {
  const label = state === "filled" ? "Campo completo" : "Campo vacío";
  return (
    <span
      role="img"
      aria-label={label}
      className={cn(
        "inline-block h-1.5 w-1.5 shrink-0 rounded-full",
        state === "filled" ? "bg-[hsl(var(--success))]" : "bg-destructive/60",
        className,
      )}
    />
  );
}
