/**
 * Pure helpers for the InstancePicker column: avatar initials and completion
 * tone buckets. Kept framework-free so they can be unit-tested and reused by
 * the copilot when generating instance previews.
 */

export type CompletionTone = "empty" | "partial" | "filled";

/** Returns the first uppercase letter of the name, or "?" on empty. */
export function initialsOf(name: string): string {
  const trimmed = name.trim();
  if (!trimmed) return "?";
  return trimmed.charAt(0).toUpperCase();
}

/**
 * Maps a 0–100 completion score to a three-bucket tone used by the status bar:
 *   [0,34)   → empty   (destructive tint)
 *   [34,80)  → partial (warning tint)
 *   [80,100] → filled  (success tint)
 */
export function computeCompletionTone(score: number): CompletionTone {
  if (score < 34) return "empty";
  if (score < 80) return "partial";
  return "filled";
}

/** CSS class (background) to apply to the fill span of the status bar. */
export function toneToFillClass(tone: CompletionTone): string {
  switch (tone) {
    case "empty":
      return "bg-destructive/60";
    case "partial":
      return "bg-[hsl(var(--warning))]";
    case "filled":
      return "bg-[hsl(var(--success))]";
  }
}

/**
 * Stable palette hash for persona/instance avatars. Avoids random colors
 * between renders — same id → same tint.
 */
const AVATAR_PALETTE = [
  "bg-[hsl(25_80%_55%_/_0.25)] text-[hsl(25_80%_45%)] dark:text-[hsl(25_80%_75%)]",
  "bg-[hsl(200_80%_55%_/_0.25)] text-[hsl(200_80%_40%)] dark:text-[hsl(200_80%_75%)]",
  "bg-[hsl(280_65%_60%_/_0.25)] text-[hsl(280_65%_45%)] dark:text-[hsl(280_65%_80%)]",
  "bg-[hsl(142_60%_45%_/_0.25)] text-[hsl(142_60%_30%)] dark:text-[hsl(142_60%_70%)]",
  "bg-[hsl(340_70%_55%_/_0.25)] text-[hsl(340_70%_40%)] dark:text-[hsl(340_70%_80%)]",
];

/**
 *
 */
export function avatarClassFor(id: string): string {
  let hash = 0;
  for (let i = 0; i < id.length; i += 1) hash = (hash * 31 + id.charCodeAt(i)) >>> 0;
  return AVATAR_PALETTE[hash % AVATAR_PALETTE.length] ?? AVATAR_PALETTE[0];
}
