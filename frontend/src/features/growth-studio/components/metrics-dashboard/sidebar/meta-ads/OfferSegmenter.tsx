'use client';

import { cn } from '@/lib/utils';
import { archetypeEmoji } from '../../../../types/offer-association';
import type { OfferMetrics } from '../../../../types/offer-association';

export type OfferSegmenterSelection = string | 'all' | 'unassigned' | 'branding';

interface OfferSegmenterProps {
  offers: OfferMetrics[];
  selectedOfferId: OfferSegmenterSelection;
  onSelect: (id: OfferSegmenterSelection) => void;
  hasUnassigned: boolean;
  hasBranding: boolean;
  className?: string;
}

interface ChipProps {
  label: string;
  emoji?: string;
  selected: boolean;
  onClick: () => void;
}

function Chip({ label, emoji, selected, onClick }: ChipProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors',
        selected
          ? 'border-blue-500 bg-blue-500/10 text-blue-500'
          : 'border-border bg-card text-muted-foreground hover:text-foreground hover:border-foreground/30',
      )}
    >
      {emoji && (
        <span aria-hidden="true" className="text-[13px]">
          {emoji}
        </span>
      )}
      {label}
    </button>
  );
}

export function OfferSegmenter({
  offers,
  selectedOfferId,
  onSelect,
  hasUnassigned,
  hasBranding,
  className,
}: OfferSegmenterProps) {
  return (
    <div
      className={cn('flex flex-wrap items-center gap-2', className)}
      role="group"
      aria-label="Filtrar por offer"
    >
      <Chip
        label="Todas"
        selected={selectedOfferId === 'all'}
        onClick={() => onSelect('all')}
      />
      {offers.map(offer => (
        <Chip
          key={offer.offerId}
          label={offer.offerName}
          emoji={archetypeEmoji(offer.archetype)}
          selected={selectedOfferId === offer.offerId}
          onClick={() => onSelect(offer.offerId)}
        />
      ))}
      {hasUnassigned && (
        <Chip
          label="Sin asignar"
          selected={selectedOfferId === 'unassigned'}
          onClick={() => onSelect('unassigned')}
        />
      )}
      {hasBranding && (
        <Chip
          label="Branding"
          selected={selectedOfferId === 'branding'}
          onClick={() => onSelect('branding')}
        />
      )}
    </div>
  );
}
