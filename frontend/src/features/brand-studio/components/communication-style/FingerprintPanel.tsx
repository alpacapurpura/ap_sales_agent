"use client";

import type { LinguisticPatterns } from "@/features/brand-studio/types/personality";

interface FingerprintPanelProps {
  patterns: LinguisticPatterns;
}

/**
 * Read-only display of `LinguisticPatterns` extracted from a personality
 * profile. Shows greeting, farewell, favorite emojis, filler phrases,
 * average message length and punctuation style.
 */
export function FingerprintPanel({ patterns }: FingerprintPanelProps) {
  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-border bg-card/50 px-4 py-3">
        <dl className="space-y-2 text-[13px]">
          {patterns.greeting && (
            <div className="flex gap-2">
              <dt className="w-28 flex-shrink-0 font-medium text-muted-foreground">Saludo:</dt>
              <dd className="text-foreground">{patterns.greeting}</dd>
            </div>
          )}
          {patterns.farewell && (
            <div className="flex gap-2">
              <dt className="w-28 flex-shrink-0 font-medium text-muted-foreground">Despedida:</dt>
              <dd className="text-foreground">{patterns.farewell}</dd>
            </div>
          )}
          {patterns.favorite_emojis.length > 0 && (
            <div className="flex gap-2">
              <dt className="w-28 flex-shrink-0 font-medium text-muted-foreground">Emojis:</dt>
              <dd className="text-foreground">{patterns.favorite_emojis.join(" ")}</dd>
            </div>
          )}
          {patterns.filler_phrases.length > 0 && (
            <div className="flex gap-2">
              <dt className="w-28 flex-shrink-0 font-medium text-muted-foreground">Muletillas:</dt>
              <dd className="text-foreground">
                {patterns.filler_phrases.map((p, i) => (
                  <span key={p}>
                    {i > 0 && <span className="mx-1 text-muted-foreground">·</span>}
                    <span className="italic">&ldquo;{p}&rdquo;</span>
                  </span>
                ))}
              </dd>
            </div>
          )}
          {patterns.avg_message_length && (
            <div className="flex gap-2">
              <dt className="w-28 flex-shrink-0 font-medium text-muted-foreground">Longitud:</dt>
              <dd className="text-foreground">{patterns.avg_message_length}</dd>
            </div>
          )}
          {patterns.humor_type && (
            <div className="flex gap-2">
              <dt className="w-28 flex-shrink-0 font-medium text-muted-foreground">Humor:</dt>
              <dd className="text-foreground">{patterns.humor_type}</dd>
            </div>
          )}
        </dl>
      </div>
    </div>
  );
}
