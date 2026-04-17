"use client";

import { Check } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { useExpertBusinessTypesCatalog } from "@/features/brand/hooks/use-expert-business-types-catalog";
import { resolveIconByName } from "@/features/offer-studio/lib/icon-name-resolver";
import { cn } from "@/lib/utils";

import type { ExpertBusinessType } from "@/features/brand/api/expert-business-types-api";

interface BusinessTypeSelectorProps {
  value: readonly ExpertBusinessType[];
  onChange: (value: ExpertBusinessType[]) => void;
  /** When true, renders compact cards with less padding. */
  compact?: boolean;
}

/**
 * Grid of selectable cards for the tenant's ``business_types``. Multi-select
 * by design — most real expert businesses blend 2-3 types (e.g. a course
 * creator who also coaches).
 *
 * Card metadata (label, description, sells, icon, examples) comes from the
 * ``/brand/expert-business-types/catalog`` endpoint via
 * ``useExpertBusinessTypesCatalog`` so the frontend has a single source
 * of truth for every surface that shows these options.
 */
export function BusinessTypeSelector({
  value,
  onChange,
  compact = false,
}: BusinessTypeSelectorProps) {
  const { data, isLoading } = useExpertBusinessTypesCatalog();
  const selected = new Set<ExpertBusinessType>(value);

  const toggle = (type: ExpertBusinessType) => {
    const next = new Set(selected);
    if (next.has(type)) next.delete(type);
    else next.add(type);
    onChange(Array.from(next));
  };

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {Array.from({ length: 9 }).map((_, i) => (
          <div key={i} className="h-28 bg-muted/50 animate-pulse rounded-lg" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {data?.business_types?.map((t) => {
        const Icon = resolveIconByName(t.icon_name);
        const isSelected = selected.has(t.business_type);
        return (
          <Card
            key={t.business_type}
            onClick={() => toggle(t.business_type)}
            className={cn(
              "cursor-pointer transition border-2",
              compact ? "p-3" : "p-4",
              isSelected
                ? "border-primary bg-primary/5 shadow-sm"
                : "border-border hover:border-primary/40",
            )}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-start gap-3 flex-1 min-w-0">
                <div
                  className={cn(
                    "shrink-0 h-9 w-9 rounded-md flex items-center justify-center",
                    isSelected
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-foreground/80",
                  )}
                >
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0 space-y-1">
                  <div className="font-semibold text-sm">{t.label_es}</div>
                  <p className="text-xs text-muted-foreground line-clamp-2">{t.description_es}</p>
                  {!compact && t.examples_es.length > 0 && (
                    <Badge variant="secondary" className="text-[10px] font-normal">
                      {t.examples_es[0]}
                    </Badge>
                  )}
                </div>
              </div>
              {isSelected && <Check className="h-4 w-4 text-primary shrink-0" />}
            </div>
          </Card>
        );
      })}
    </div>
  );
}
