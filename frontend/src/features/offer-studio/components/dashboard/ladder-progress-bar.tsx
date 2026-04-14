import { OfferValueLevel } from "@/features/offer-studio/types";
import { cn } from "@/lib/utils";
import { Lightbulb, Zap, Users, Trophy, Building2 } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface LadderProgressBarProps {
  filledGroups: Set<OfferValueLevel>;
  score: string;
  percentage: number;
}

const STEPS = [
  {
    level: OfferValueLevel.LEAD_MAGNET,
    label: "Lead Magnet",
    shortLabel: "Magnet",
    icon: Lightbulb,
    color: "emerald",
    filledBg: "bg-emerald-500/15 dark:bg-emerald-500/20",
    filledBorder: "border-emerald-500/40",
    filledText: "text-emerald-700 dark:text-emerald-400",
    filledIcon: "text-emerald-600 dark:text-emerald-400",
    filledDot: "bg-emerald-500",
    barColor: "bg-emerald-500",
  },
  {
    level: OfferValueLevel.ACTIVACION,
    label: "Activación",
    shortLabel: "Activ.",
    icon: Zap,
    color: "blue",
    filledBg: "bg-blue-500/15 dark:bg-blue-500/20",
    filledBorder: "border-blue-500/40",
    filledText: "text-blue-700 dark:text-blue-400",
    filledIcon: "text-blue-600 dark:text-blue-400",
    filledDot: "bg-blue-500",
    barColor: "bg-blue-500",
  },
  {
    level: OfferValueLevel.TRANSFORMACION,
    label: "Transformación",
    shortLabel: "Trans.",
    icon: Users,
    color: "violet",
    filledBg: "bg-violet-500/15 dark:bg-violet-500/20",
    filledBorder: "border-violet-500/40",
    filledText: "text-violet-700 dark:text-violet-400",
    filledIcon: "text-violet-600 dark:text-violet-400",
    filledDot: "bg-violet-500",
    barColor: "bg-violet-500",
  },
  {
    level: OfferValueLevel.MAXIMIZACION,
    label: "Maximización",
    shortLabel: "Max.",
    icon: Trophy,
    color: "amber",
    filledBg: "bg-amber-500/15 dark:bg-amber-500/20",
    filledBorder: "border-amber-500/40",
    filledText: "text-amber-700 dark:text-amber-400",
    filledIcon: "text-amber-600 dark:text-amber-400",
    filledDot: "bg-amber-500",
    barColor: "bg-amber-500",
  },
  {
    level: OfferValueLevel.CORPORATIVO,
    label: "Corporativo",
    shortLabel: "Corp.",
    icon: Building2,
    color: "slate",
    filledBg: "bg-slate-500/15 dark:bg-slate-400/15",
    filledBorder: "border-slate-500/40",
    filledText: "text-slate-700 dark:text-slate-300",
    filledIcon: "text-slate-600 dark:text-slate-400",
    filledDot: "bg-slate-500",
    barColor: "bg-slate-500",
  },
];

export function LadderProgressBar({ filledGroups, score, percentage }: LadderProgressBarProps) {
  const filledCount = STEPS.filter((s) => filledGroups.has(s.level)).length;

  return (
    <TooltipProvider delayDuration={200}>
      <div className="w-full flex items-center gap-3 pt-4 pb-4">
        {/* Segmented bar */}
        <div className="flex-1 flex items-stretch gap-1 h-11">
          {STEPS.map((step, i) => {
            const filled = filledGroups.has(step.level);
            const Icon = step.icon;

            const isFirst = i === 0;
            const isLast = i === STEPS.length - 1;
            const roundedLeft = isFirst ? "rounded-l-lg" : "";
            const roundedRight = isLast ? "rounded-r-lg" : "";

            return (
              <Tooltip key={step.level}>
                <TooltipTrigger asChild>
                  <div
                    className={cn(
                      "flex-1 flex items-center justify-center gap-1.5 px-2 border transition-all duration-300 cursor-default min-w-0",
                      roundedLeft,
                      roundedRight,
                      filled
                        ? cn(step.filledBg, step.filledBorder)
                        : "bg-muted/30 border-dashed border-muted-foreground/15 dark:bg-muted/10",
                    )}
                  >
                    {/* Status dot — tiny indicator */}
                    <div
                      className={cn(
                        "h-1.5 w-1.5 rounded-full shrink-0 transition-colors duration-300",
                        filled ? step.filledDot : "bg-muted-foreground/20",
                      )}
                    />

                    {/* Icon */}
                    <Icon
                      className={cn(
                        "h-3.5 w-3.5 shrink-0 transition-colors duration-300",
                        filled ? step.filledIcon : "text-muted-foreground/40",
                      )}
                    />

                    {/* Label — hidden on narrow, visible when there's room */}
                    <span
                      className={cn(
                        "text-[11px] font-medium truncate hidden min-[900px]:inline transition-colors duration-300",
                        filled ? step.filledText : "text-muted-foreground/40",
                      )}
                    >
                      {step.shortLabel}
                    </span>
                  </div>
                </TooltipTrigger>
                <TooltipContent side="bottom" className="text-xs">
                  <span className="font-semibold">{step.label}</span>
                  {" — "}
                  <span>{filled ? "Activo" : "Sin ofertas"}</span>
                </TooltipContent>
              </Tooltip>
            );
          })}
        </div>

        {/* Score badge */}
        <div className="shrink-0 flex items-center gap-2 pl-2 border-l border-border/50">
          <div className="flex flex-col items-end leading-none">
            <span className="text-[11px] text-muted-foreground font-medium tracking-wide uppercase">
              Ladder
            </span>
            <span className="text-sm font-bold tabular-nums text-foreground">
              {filledCount}/{STEPS.length}
            </span>
          </div>
          {/* Circular percentage */}
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
