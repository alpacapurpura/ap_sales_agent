"use client";

import { useOfferMetadata } from "../../../hooks/use-offer-metadata";
import { OfferType } from "../../../types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Lightbulb, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ContextualHintProps {
  type: OfferType;
  className?: string;
}

export function ContextualHint({ type, className }: ContextualHintProps) {
  const { data: metadata, isLoading } = useOfferMetadata();

  if (isLoading) return <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />;
  if (!metadata || !metadata[type]) return null;

  const info = metadata[type];

  return (
    <Card className={cn("bg-blue-50/50 border-blue-100 dark:bg-blue-950/20 dark:border-blue-900", className)}>
      <CardHeader className="pb-2 flex flex-row items-center gap-2 space-y-0">
        <Lightbulb className="h-4 w-4 text-blue-500" />
        <CardTitle className="text-sm font-medium text-blue-700 dark:text-blue-300">
          Consejo de Estrategia
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          {info.description}
        </p>
        {info.best_for && (
          <div className="mt-2 text-xs text-muted-foreground">
            <strong>Ideal para:</strong> {info.best_for}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
