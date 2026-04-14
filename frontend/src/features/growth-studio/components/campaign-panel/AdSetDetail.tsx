"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { AdSet } from "../../types/campaigns";

const LEARNING_COLORS: Record<string, string> = {
  LEARNING: "bg-blue-100 text-blue-700",
  SUCCESS: "bg-green-100 text-green-700",
  FAIL: "bg-red-100 text-red-700",
};

function formatTargeting(targeting: Record<string, unknown> | null): string {
  if (!targeting) return "—";
  const parts: string[] = [];

  const ageMin = targeting.age_min as number | undefined;
  const ageMax = targeting.age_max as number | undefined;
  if (ageMin || ageMax) {
    parts.push(`${ageMin ?? "?"}-${ageMax ?? "?"} años`);
  }

  const genders = targeting.genders as number[] | undefined;
  if (genders?.length) {
    const labels = genders.map((g) => (g === 1 ? "H" : g === 2 ? "M" : "?"));
    parts.push(labels.join("/"));
  }

  const geo = targeting.geo_locations as Record<string, unknown> | undefined;
  if (geo) {
    const countries = geo.countries as string[] | undefined;
    const cities = geo.cities as Array<{ name?: string }> | undefined;
    if (countries?.length) parts.push(countries.join(", "));
    if (cities?.length) {
      parts.push(
        cities
          .slice(0, 3)
          .map((c) => c.name ?? "")
          .filter(Boolean)
          .join(", "),
      );
    }
  }

  const interests = targeting.interests as Array<{ name?: string }> | undefined;
  if (interests?.length) {
    parts.push(
      interests
        .slice(0, 3)
        .map((i) => i.name ?? "")
        .filter(Boolean)
        .join(", "),
    );
  }

  return parts.length > 0 ? parts.join(" · ") : "—";
}

interface AdSetDetailProps {
  adSet: AdSet;
}

export function AdSetDetail({ adSet }: AdSetDetailProps) {
  const learningClass = LEARNING_COLORS[adSet.learning_stage ?? ""] ?? "";

  return (
    <div className="rounded-lg border bg-muted/30 p-3 text-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <div
            className={cn(
              "h-2 w-2 rounded-full shrink-0",
              adSet.effective_status === "ACTIVE" ? "bg-green-500" : "bg-gray-400",
            )}
          />
          <span className="font-medium truncate">{adSet.name}</span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {adSet.learning_stage && (
            <Badge variant="outline" className={cn("text-xs", learningClass)}>
              {adSet.learning_stage}
            </Badge>
          )}
          {adSet.optimization_goal && (
            <Badge variant="secondary" className="text-xs">
              {adSet.optimization_goal}
            </Badge>
          )}
          <span className="text-xs text-muted-foreground">{adSet.ads_count} anuncios</span>
        </div>
      </div>

      <p className="mt-1 text-xs text-muted-foreground ml-4">
        {formatTargeting(adSet.targeting_summary)}
      </p>

      {adSet.daily_budget && (
        <p className="mt-1 text-xs text-muted-foreground ml-4">
          Presupuesto diario: ${(adSet.daily_budget / 100).toLocaleString("es-MX")}
        </p>
      )}
    </div>
  );
}
