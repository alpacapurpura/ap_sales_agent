import { OfferValueLevel } from "@/features/offer-studio/types";
import { cn } from "@/lib/utils";
import { Lightbulb, Zap, Users, Trophy, Building2 } from "lucide-react";

interface LadderProgressBarProps {
  filledGroups: Set<OfferValueLevel>;
  score: string;
  percentage: number;
  compact?: boolean;
}

const STEPS = [
  { level: OfferValueLevel.LEAD_MAGNET, label: "Lead Magnet", icon: Lightbulb },
  { level: OfferValueLevel.ACTIVACION, label: "Activacion", icon: Zap },
  { level: OfferValueLevel.TRANSFORMACION, label: "Transformacion", icon: Users },
  { level: OfferValueLevel.MAXIMIZACION, label: "Maximizacion", icon: Trophy },
  { level: OfferValueLevel.CORPORATIVO, label: "Corporativo", icon: Building2 },
];

export function LadderProgressBar({ filledGroups, score, percentage, compact = false }: LadderProgressBarProps) {
  if (compact) {
    return (
      <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 bg-muted/50 rounded-lg border border-border/50">
        {STEPS.map((step, i) => {
          const filled = filledGroups.has(step.level);
          const Icon = step.icon;
          return (
            <div key={step.level} className="flex items-center">
              <div
                className={cn(
                  "h-6 w-6 rounded-full flex items-center justify-center border-2 transition-colors",
                  filled
                    ? "bg-primary border-primary text-primary-foreground"
                    : "bg-muted border-muted-foreground/30 text-muted-foreground"
                )}
                title={step.label}
              >
                <Icon className="h-3 w-3" />
              </div>
              {i < STEPS.length - 1 && (
                <div
                  className={cn(
                    "h-0.5 w-3",
                    filled && filledGroups.has(STEPS[i + 1].level)
                      ? "bg-primary"
                      : "bg-muted-foreground/20"
                  )}
                />
              )}
            </div>
          );
        })}
        <span className="text-xs font-bold text-foreground ml-1">{percentage}%</span>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-muted-foreground">
          Escalera de Valor: <span className="text-foreground capitalize">{score}</span>
        </p>
        <span className="text-sm font-bold text-foreground">{percentage}%</span>
      </div>

      <div className="flex items-center gap-0">
        {STEPS.map((step, i) => {
          const filled = filledGroups.has(step.level);
          const Icon = step.icon;
          return (
            <div key={step.level} className="flex items-center flex-1">
              <div className="flex flex-col items-center gap-1 flex-1">
                <div
                  className={cn(
                    "h-8 w-8 rounded-full flex items-center justify-center border-2 transition-colors",
                    filled
                      ? "bg-primary border-primary text-primary-foreground"
                      : "bg-muted border-muted-foreground/30 text-muted-foreground"
                  )}
                >
                  <Icon className="h-4 w-4" />
                </div>
                <span className={cn(
                  "text-[10px] text-center leading-tight",
                  filled ? "text-foreground font-medium" : "text-muted-foreground"
                )}>
                  {step.label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div
                  className={cn(
                    "h-0.5 flex-1 -mx-1",
                    filled && filledGroups.has(STEPS[i + 1].level)
                      ? "bg-primary"
                      : "bg-muted-foreground/20"
                  )}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
