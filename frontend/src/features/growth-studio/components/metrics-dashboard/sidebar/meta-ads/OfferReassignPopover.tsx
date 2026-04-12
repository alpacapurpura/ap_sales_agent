'use client';

import { useState } from 'react';
import { Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import {
  useCreateAssociation,
  useDeleteAssociation,
  useOffersForAssignment,
} from '../../../../api/offer-association-api';
import { archetypeEmoji } from '../../../../types/offer-association';
import type { Association } from '../../../../types/offer-association';

const OPTION_BRANDING = '__branding__';

interface OfferReassignPopoverProps {
  campaign: {
    externalId: string;
    name: string;
  };
  association: Association;
  children: React.ReactNode;
}

export function OfferReassignPopover({
  campaign,
  association,
  children,
}: OfferReassignPopoverProps) {
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const { data: offers } = useOffersForAssignment(open);
  const createMutation = useCreateAssociation();
  const deleteMutation = useDeleteAssociation();

  const isBranding = association.associationType === 'excluded_branding';
  const currentLabel = isBranding
    ? '🎯 Branding'
    : `${archetypeEmoji(association.offerArchetype)} ${association.offerName ?? 'Offer asociada'}`;

  async function handleChange(value: string) {
    setSaving(true);
    try {
      if (value === OPTION_BRANDING) {
        await createMutation.mutateAsync({
          targetType: 'campaign',
          targetExternalId: campaign.externalId,
          offerId: null,
          associationType: 'excluded_branding',
        });
      } else {
        await createMutation.mutateAsync({
          targetType: 'campaign',
          targetExternalId: campaign.externalId,
          offerId: value,
          associationType: 'manual',
        });
      }
      setOpen(false);
    } finally {
      setSaving(false);
    }
  }

  async function handleDesasignar() {
    setSaving(true);
    try {
      await deleteMutation.mutateAsync(association.id);
      setOpen(false);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>{children}</PopoverTrigger>
      <PopoverContent
        side="bottom"
        align="start"
        className="w-[280px] p-4 space-y-3"
      >
        {/* Current offer */}
        <div>
          <p className="text-xs font-medium text-muted-foreground">
            Offer actual:
          </p>
          <p className="text-sm mt-0.5">{currentLabel}</p>
        </div>

        <Separator />

        {/* Change dropdown */}
        <div className="space-y-1.5">
          <p className="text-xs font-medium text-muted-foreground">
            Cambiar a:
          </p>
          <div className="flex items-center gap-2">
            <Select
              onValueChange={v => void handleChange(v)}
              disabled={saving}
            >
              <SelectTrigger className="h-8 text-xs flex-1">
                <SelectValue placeholder="Elegir offer..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={OPTION_BRANDING}>
                  🎯 Marcar como Branding
                </SelectItem>
                {(offers ?? [])
                  .filter(o => o.id !== association.offerId)
                  .map(o => (
                    <SelectItem key={o.id} value={o.id}>
                      <span className="flex items-center gap-1.5">
                        <span aria-hidden="true">
                          {archetypeEmoji(o.archetype)}
                        </span>
                        <span>{o.name}</span>
                        <span className="text-[10px] text-muted-foreground">
                          · {o.expectedMetricLabelEs}
                        </span>
                      </span>
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
            {saving && (
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground shrink-0" />
            )}
          </div>
        </div>

        <Separator />

        {/* Desasignar */}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="w-full text-xs text-muted-foreground hover:text-destructive"
          onClick={() => void handleDesasignar()}
          disabled={saving}
        >
          Desasignar
        </Button>
      </PopoverContent>
    </Popover>
  );
}
