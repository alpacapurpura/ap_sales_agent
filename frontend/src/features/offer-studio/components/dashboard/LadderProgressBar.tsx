import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useValueLevelCatalog } from "@/features/offer-studio/hooks/use-value-level-catalog";
import { resolveIconByName } from "@/features/offer-studio/lib/icon-name-resolver";
import { OfferValueLevel } from "@/features/offer-studio/types";
import { cn } from "@/lib/utils";

interface LadderProgressBarProps {
  filledGroups: Set<OfferValueLevel>;
  score: string;
  percentage: number;
}

interface RungTheme {
  filledBg: string;
  filledBorder: string;
  filledText: string;
  filledIcon: string;
  filledDot: string;
}

/**
 * UI theme per rung. Colors are presentational — not domain data — so they
 * live here, not in the catalog. Keys must stay aligned with
 * ``OfferValueLevel``; the component iterates the catalog response (which
 * the arch test keeps aligned with the enum).
 */
const RUNG_THEME: Record<OfferValueLevel, RungTheme> = {
  [OfferValueLevel.LEAD_MAGNET]: {
    filledBg: "bg-emerald-500/15 dark:bg-emerald-500/20",
    filledBorder: "border-emerald-500/40",
    filledText: "text-emerald-700 dark:text-emerald-400",
    filledIcon: "text-emerald-600 dark:text-emerald-400",
    filledDot: "bg-emerald-500",
  },
  [OfferValueLevel.ACTIVACION]: {
    filledBg: "bg-blue-500/15 dark:bg-blue-500/20",
    filledBorder: "border-blue-500/40",
    filledText: "text-blue-700 dark:text-blue-400",
    filledIcon: "text-blue-600 dark:text-blue-400",
    filledDot: "bg-blue-500",
  },
  [OfferValueLevel.TRANSFORMACION]: {
    filledBg: "bg-violet-500/15 dark:bg-violet-500/20",
    filledBorder: "border-violet-500/40",
    filledText: "text-violet-700 dark:text-violet-400",
    filledIcon: "text-violet-600 dark:text-violet-400",
    filledDot: "bg-violet-500",
  },
  [OfferValueLevel.MAXIMIZACION]: {
    filledBg: "bg-amber-500/15 dark:bg-amber-500/20",
    filledBorder: "border-amber-500/40",
    filledText: "text-amber-700 dark:text-amber-400",
    filledIcon: "text-amber-600 dark:text-amber-400",
    filledDot: "bg-amber-500",
  },
  [OfferValueLevel.CORPORATIVO]: {
    filledBg: "bg-slate-500/15 dark:bg-slate-400/15",
    filledBorder: "border-slate-500/40",
    filledText: "text-slate-700 dark:text-slate-300",
    filledIcon: "text-slate-600 dark:text-slate-400",
    filledDot: "bg-slate-500",
  },
};

/**
 *
 */
export function LadderProgressBar({
  filledGroups,
  score: _score,
  percentage,
}: LadderProgressBarProps) {
  const { data } = useValueLevelCatalog();
  const steps = data?.value_levels ?? [];
  const filledCount = steps.filter((s) => filledGroups.has(s.value_level)).length;

  return (
    <TooltipProvider delayDuration={200}>
      <div className="w-full flex items-center gap-3 pt-4 pb-4">
        <div className="flex-1 flex items-stretch gap-1 h-11">
          {steps.map((step, i) => {
            const filled = filledGroups.has(step.value_level);
            const Icon = resolveIconByName(step.icon_name);
            const theme = RUNG_THEME[step.value_level];

            const isFirst = i === 0;
            const isLast = i === steps.length - 1;
            const roundedLeft = isFirst ? "rounded-l-lg" : "";
            const roundedRight = isLast ? "rounded-r-lg" : "";

            return (
              <Tooltip key={step.value_level}>
                <TooltipTrigger asChild>
                  <div
                    className={cn(
                      "flex-1 flex items-center justify-center gap-1.5 px-2 border transition-all duration-300 cursor-default min-w-0",
                      roundedLeft,
                      roundedRight,
                      filled
                        ? cn(theme.filledBg, theme.filledBorder)
                        : "bg-muted/30 border-dashed border-muted-foreground/15 dark:bg-muted/10",
                    )}
                  >
                    <div
                      className={cn(
                        "h-1.5 w-1.5 rounded-full shrink-0 transition-colors duration-300",
                        filled ? theme.filledDot : "bg-muted-foreground/20",
                      )}
                    />
                    <Icon
                      className={cn(
                        "h-3.5 w-3.5 shrink-0 transition-colors duration-300",
                        filled ? theme.filledIcon : "text-muted-foreground/40",
                      )}
                    />
                    <span
                      className={cn(
                        "text-[11px] font-medium truncate hidden min-[900px]:inline transition-colors duration-300",
                        filled ? theme.filledText : "text-muted-foreground/40",
                      )}
                    >
                      {step.label_es}
                    </span>
                  </div>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">
                  <span className="font-semibold">{step.label_es}</span>
                  {" — "}
                  <span>{filled ? "Activo" : "Sin ofertas"}</span>
                </TooltipContent>
              </Tooltip>
            );
          })}
        </div>

        <div className="shrink-0 flex items-center gap-2 pl-2 border-l border-border/50">
          <div className="flex flex-col items-end leading-none">
            <span className="text-[11px] text-muted-foreground font-medium tracking-wide uppercase">
              Ladder
            </span>
            <span className="text-sm font-bold tabular-nums text-foreground">
              {filledCount}/{steps.length}
            </span>
          </div>
          <div className="relative h-9 w-9">
            <svg viewBox="0 0 36 36" className="h-9 w-9 -rotate-90">
              <circle
                cx="18"
                cy="18"
                r="15"
                fill="none"
                stroke="currentColor"
                strokeWidth="3"
                className="text-muted/60"
              />
              <circle
                cx="18"
                cy="18"
                r="15"
                fill="none"
                strokeWidth="3"
                strokeLinecap="round"
                strokeDasharray={`${percentage * 0.9425} 94.25`}
                className={cn(
                  "transition-all duration-700",
                  percentage >= 80
                    ? "text-emerald-500"
                    : percentage >= 40
                      ? "text-blue-500"
                      : "text-amber-500",
                )}
              />
            </svg>
            <span className="absolute inset-0 flex items-center justify-center text-[10px] font-bold tabular-nums text-foreground">
              {percentage}
            </span>
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
}
