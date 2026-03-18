"use client";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ComponentEntry } from "@/lib/design-system/types";

interface ComponentCardProps {
  component: ComponentEntry;
}

const LEVEL_COLORS: Record<string, string> = {
  atom: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  molecule: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  organism: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
};

const SOURCE_COLORS: Record<string, string> = {
  shadcn: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
  shared: "bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-200",
  feature: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
};

export function ComponentCard({ component }: ComponentCardProps) {
  const hasIssues = component.issues && component.issues.length > 0;

  return (
    <Card
      className={cn(
        "transition-shadow hover:shadow-md",
        hasIssues && "border-amber-300 dark:border-amber-700"
      )}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base leading-tight">{component.name}</CardTitle>
          <div className="flex gap-1 shrink-0">
            <span
              className={cn(
                "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold",
                LEVEL_COLORS[component.atomicLevel]
              )}
            >
              {component.atomicLevel}
            </span>
            <span
              className={cn(
                "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold",
                SOURCE_COLORS[component.source]
              )}
            >
              {component.source}
            </span>
          </div>
        </div>
        <p className="text-xs text-muted-foreground leading-relaxed">
          {component.description}
        </p>
      </CardHeader>
      <CardContent className="pt-0 space-y-3">
        {/* File path */}
        <p className="text-[11px] font-mono text-muted-foreground bg-muted px-2 py-1 rounded truncate">
          {component.filePath}
        </p>

        {/* Feature slice */}
        {component.featureSlice && (
          <div className="flex items-center gap-1">
            <span className="text-[10px] text-muted-foreground">Slice:</span>
            <Badge variant="outline" className="text-[10px] h-5">
              {component.featureSlice}
            </Badge>
          </div>
        )}

        {/* Variants */}
        {component.variants && component.variants.length > 0 && (
          <div>
            <span className="text-[10px] text-muted-foreground block mb-1">Variants</span>
            <div className="flex flex-wrap gap-1">
              {component.variants.map((v) => (
                <Badge key={v} variant="secondary" className="text-[10px] h-5">
                  {v}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Props */}
        {component.props && component.props.length > 0 && (
          <div>
            <span className="text-[10px] text-muted-foreground block mb-1">Props</span>
            <div className="flex flex-wrap gap-1">
              {component.props.map((p) => (
                <span
                  key={p}
                  className="inline-flex items-center rounded bg-muted px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground"
                >
                  {p}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Issues */}
        {hasIssues && (
          <div className="border-t border-amber-200 dark:border-amber-800 pt-2">
            <span className="text-[10px] text-amber-600 dark:text-amber-400 font-medium block mb-1">
              Issues
            </span>
            <ul className="space-y-0.5">
              {component.issues!.map((issue, i) => (
                <li
                  key={i}
                  className="text-[10px] text-amber-700 dark:text-amber-300 leading-tight"
                >
                  {issue}
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
