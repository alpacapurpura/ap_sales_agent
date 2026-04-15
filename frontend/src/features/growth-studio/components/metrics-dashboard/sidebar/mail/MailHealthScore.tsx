"use client";

import { cn } from "@/lib/utils";

import type { EmailHealthScore } from "../../../../types/mail-types";

interface MailHealthScoreProps {
  healthScore: EmailHealthScore;
}

/** Map color strings from backend to Tailwind classes */
const COLOR_MAP: Record<string, { bar: string; text: string }> = {
  green: { bar: "bg-emerald-500", text: "text-emerald-500" },
  yellow: { bar: "bg-amber-500", text: "text-amber-500" },
  red: { bar: "bg-red-500", text: "text-red-500" },
};

function getScoreColor(score: number): { text: string; bg: string } {
  if (score >= 70) return { text: "text-emerald-500", bg: "bg-emerald-500" };
  if (score >= 50) return { text: "text-amber-500", bg: "bg-amber-500" };
  return { text: "text-red-500", bg: "bg-red-500" };
}

export function MailHealthScore({ healthScore }: MailHealthScoreProps) {
  const { text: totalColor } = getScoreColor(healthScore.total);

  return (
    <div className="space-y-3">
      <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
        Salud del Email
      </h4>

      <div className="rounded-lg border bg-card p-4">
        {/* Main score */}
        <div className="flex items-center gap-3 mb-4">
          <span className={cn("text-4xl font-bold tabular-nums", totalColor)}>
            {healthScore.total}
          </span>
          <span className="text-sm text-muted-foreground">/100</span>
        </div>

        {/* Sub-scores */}
        <div className="grid grid-cols-2 gap-3">
          {healthScore.subScores.map((sub) => {
            const colorConfig = COLOR_MAP[sub.color] ?? COLOR_MAP.green;

            return (
              <div key={sub.area} className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-muted-foreground">{sub.label}</span>
                  <span className={cn("text-[11px] font-medium tabular-nums", colorConfig.text)}>
                    {sub.score}
                  </span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                  <div
                    role="meter"
                    aria-valuenow={sub.score}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label={sub.label}
                    className={cn("h-full rounded-full transition-all", colorConfig.bar)}
                    // Inline style required for dynamic percentage width
                    style={{ width: `${Math.max(sub.score, 2)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
