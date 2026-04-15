"use client";

import { Pencil, Copy, Trash2, CalendarDays, Users } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { formatMoney } from "@/lib/format-money";
import { cn } from "@/lib/utils";

import { EditionStatus } from "../../types";

import { EditionStatusBadge } from "./EditionStatusBadge";

import type { LaunchEdition } from "../../types";

const STATUS_BORDER: Record<EditionStatus, string> = {
  [EditionStatus.DRAFT]: "border-l-amber-500 border-dashed",
  [EditionStatus.UPCOMING]: "border-l-blue-500",
  [EditionStatus.ACTIVE]: "border-l-green-500",
  [EditionStatus.COMPLETED]: "opacity-60",
  [EditionStatus.CANCELLED]: "opacity-40",
};

function formatDateRange(start: string, end: string | null): string {
  const s = new Date(start);
  const opts: Intl.DateTimeFormatOptions = { day: "numeric", month: "short", year: "numeric" };
  if (!end) return s.toLocaleDateString("es", opts);
  const e = new Date(end);
  return `${s.toLocaleDateString("es", opts)} — ${e.toLocaleDateString("es", opts)}`;
}

interface EditionCardProps {
  edition: LaunchEdition;
  onEdit: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
}

export function EditionCard({ edition, onEdit, onDuplicate, onDelete }: EditionCardProps) {
  const isCompleted = edition.status === EditionStatus.COMPLETED;
  const hasOverride = edition.pricing_override !== null;
  const mainPrice = edition.effective_pricing[0];

  return (
    <Card
      className={cn("border-l-4 transition-all hover:bg-muted/30", STATUS_BORDER[edition.status])}
    >
      <CardContent className="p-4 space-y-3">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm">{edition.edition_name}</span>
            <EditionStatusBadge status={edition.status} />
          </div>
          <div className="flex gap-1">
            {!isCompleted && (
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onEdit}>
                <Pencil className="h-3.5 w-3.5" />
              </Button>
            )}
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onDuplicate}>
              <Copy className="h-3.5 w-3.5" />
            </Button>
            {!isCompleted && (
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-destructive"
                onClick={onDelete}
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>
        </div>

        {/* Meta */}
        <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <CalendarDays className="h-3 w-3" />
            {formatDateRange(edition.start_date, edition.end_date)}
          </span>
          {edition.capacity && (
            <span className="flex items-center gap-1">
              <Users className="h-3 w-3" />
              {edition.enrollment_count} / {edition.capacity} inscritos
            </span>
          )}
        </div>

        {/* Pricing */}
        {mainPrice && (
          <div className="flex items-center gap-3 pt-1 border-t text-sm">
            <span className="font-bold">
              {formatMoney(mainPrice.total_amount, edition.currency)}
            </span>
            <span className="text-xs text-muted-foreground">{mainPrice.label}</span>
            {hasOverride ? (
              <span className="text-xs text-amber-500 font-medium">Precio especial</span>
            ) : (
              <span className="text-xs text-muted-foreground">= precio base</span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
