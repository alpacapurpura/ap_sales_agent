"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCreateAssociation } from "../../../../../api/offer-association-api";
import { archetypeEmoji } from "../../../../../types/offer-association";
import type { OfferSummary } from "../../../../../types/offer-association";

const OPTION_BRANDING = "__branding__";

interface OfferAssignmentDropdownProps {
  campaignExternalId: string;
  offers: OfferSummary[];
  onAssigned: () => void;
}

export function OfferAssignmentDropdown({
  campaignExternalId,
  offers,
  onAssigned,
}: OfferAssignmentDropdownProps) {
  const [saving, setSaving] = useState(false);
  const createMutation = useCreateAssociation();

  async function handleSelect(value: string) {
    setSaving(true);
    try {
      if (value === OPTION_BRANDING) {
        await createMutation.mutateAsync({
          targetType: "campaign",
          targetExternalId: campaignExternalId,
          offerId: null,
          associationType: "excluded_branding",
        });
      } else {
        await createMutation.mutateAsync({
          targetType: "campaign",
          targetExternalId: campaignExternalId,
          offerId: value,
          associationType: "manual",
        });
      }
      onAssigned();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-1.5">
      <p className="text-xs font-medium uppercase tracking-wider text-amber-400">
        Asignar offer a esta campaña
      </p>
      <div className="flex items-center gap-2">
        <Select onValueChange={(v) => void handleSelect(v)} disabled={saving}>
          <SelectTrigger className="h-9 text-xs flex-1 border-amber-500/30 bg-amber-500/5">
            <SelectValue placeholder="Elegir offer..." />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={OPTION_BRANDING}>🎯 Marcar como Branding (sin offer)</SelectItem>
            {offers.map((o) => (
              <SelectItem key={o.id} value={o.id}>
                <span className="flex items-center gap-1.5">
                  <span aria-hidden="true">{archetypeEmoji(o.archetype)}</span>
                  <span>{o.name}</span>
                  <span className="text-[10px] text-muted-foreground">
                    · {o.expectedMetricLabelEs}
                  </span>
                </span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {saving && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground shrink-0" />}
      </div>
    </div>
  );
}
