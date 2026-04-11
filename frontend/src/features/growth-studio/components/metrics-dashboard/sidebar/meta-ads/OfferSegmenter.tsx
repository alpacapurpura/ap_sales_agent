'use client';

import { useCallback, useMemo, useRef } from 'react';
import type { KeyboardEvent, ReactNode } from 'react';
import { AlertTriangle, Check, Sparkles } from 'lucide-react';

import { cn } from '@/lib/utils';
import { archetypeEmoji } from '../../../../types/offer-association';
import type { OfferMetrics } from '../../../../types/offer-association';

export type OfferSegmenterSelection = string | 'all' | 'unassigned' | 'branding';

type ChipKind = 'all' | 'offer' | 'unassigned' | 'branding';

interface OfferSegmenterProps {
  offers: OfferMetrics[];
  selectedOfferId: OfferSegmenterSelection;
  onSelect: (id: OfferSegmenterSelection) => void;
  hasUnassigned: boolean;
  hasBranding: boolean;
  className?: string;
}

interface ChipProps {
  kind: ChipKind;
  label: string;
  emoji?: string;
  selected: boolean;
  tabIndex: 0 | -1;
  ariaLabel?: string;
  onClick: () => void;
  onKeyDown: (event: KeyboardEvent<HTMLButtonElement>) => void;
  registerRef: (el: HTMLButtonElement | null) => void;
}

const CHIP_BASE = cn(
  'group/chip inline-flex shrink-0 snap-start items-center gap-1.5 rounded-full border px-3 min-h-9 py-1.5 text-xs font-medium',
  'transition-colors duration-150',
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background',
  'disabled:opacity-50 disabled:cursor-not-allowed',
);

const KIND_CLASSES: Record<ChipKind, { inactive: string; active: string }> = {
  all: {
    inactive:
      'border-border bg-card text-muted-foreground hover:text-foreground hover:border-foreground/30',
    active: 'border-blue-500 bg-blue-500/10 text-blue-500',
  },
  offer: {
    inactive:
      'border-border bg-card text-muted-foreground hover:text-foreground hover:border-foreground/30',
    active: 'border-blue-500 bg-blue-500/10 text-blue-500',
  },
  unassigned: {
    inactive:
      'border-amber-500/40 bg-amber-50 text-amber-700 hover:bg-amber-100 dark:bg-amber-950/30 dark:text-amber-300 dark:hover:bg-amber-950/50',
    active:
      'border-amber-500 bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-200',
  },
  branding: {
    inactive:
      'border-violet-500/40 bg-violet-50 text-violet-700 hover:bg-violet-100 dark:bg-violet-950/30 dark:text-violet-300 dark:hover:bg-violet-950/50',
    active:
      'border-violet-500 bg-violet-100 text-violet-800 dark:bg-violet-900/50 dark:text-violet-200',
  },
};

function Chip({
  kind,
  label,
  emoji,
  selected,
  tabIndex,
  ariaLabel,
  onClick,
  onKeyDown,
  registerRef,
}: ChipProps) {
  const palette = KIND_CLASSES[kind];

  // Leading icon: AlertTriangle for unassigned, Sparkles for branding.
  // Offer chips use the archetype emoji (no icon). "Todas" has no leading icon.
  let leadingIcon: ReactNode = null;
  if (kind === 'unassigned') {
    leadingIcon = <AlertTriangle aria-hidden="true" className="h-3.5 w-3.5" />;
  } else if (kind === 'branding') {
    leadingIcon = <Sparkles aria-hidden="true" className="h-3.5 w-3.5" />;
  }

  return (
    <button
      ref={registerRef}
      type="button"
      role="button"
      onClick={onClick}
      onKeyDown={onKeyDown}
      tabIndex={tabIndex}
      aria-pressed={selected}
      aria-label={ariaLabel}
      data-chip-kind={kind}
      data-selected={selected ? 'true' : 'false'}
      className={cn(CHIP_BASE, selected ? palette.active : palette.inactive)}
    >
      {leadingIcon}
      {emoji && (
        <span aria-hidden="true" className="text-[13px] leading-none">
          {emoji}
        </span>
      )}
      {/* Active indicator check — shown for "Todas" and offer chips when selected.
          For unassigned/branding the border+bg tint shift already signals active; adding
          a Check would crowd the chip next to the leading warning/sparkle icon. */}
      {selected && (kind === 'all' || kind === 'offer') && (
        <Check aria-hidden="true" className="h-3.5 w-3.5" />
      )}
      <span className="max-w-[12rem] truncate">{label}</span>
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
  // Build the ordered list of chips that will be rendered. This drives both the
  // render loop and the keyboard navigation order.
  type ChipDescriptor = {
    key: string;
    kind: ChipKind;
    value: OfferSegmenterSelection;
    label: string;
    emoji?: string;
    ariaLabel?: string;
  };

  const chips = useMemo<ChipDescriptor[]>(() => {
    const list: ChipDescriptor[] = [
      { key: 'all', kind: 'all', value: 'all', label: 'Todas' },
    ];
    for (const offer of offers) {
      list.push({
        key: offer.offerId,
        kind: 'offer',
        value: offer.offerId,
        label: offer.offerName,
        emoji: archetypeEmoji(offer.archetype),
      });
    }
    if (hasUnassigned) {
      list.push({
        key: 'unassigned',
        kind: 'unassigned',
        value: 'unassigned',
        label: 'Sin asignar',
        ariaLabel: 'Filtrar por campañas sin asignar a offer',
      });
    }
    if (hasBranding) {
      list.push({
        key: 'branding',
        kind: 'branding',
        value: 'branding',
        label: 'Branding',
        ariaLabel: 'Filtrar por campañas de branding (awareness)',
      });
    }
    return list;
  }, [offers, hasUnassigned, hasBranding]);

  // Roving tabindex: a single chip holds tabIndex=0 at a time (the selected one,
  // or the first chip if none match), the rest are -1. Arrow keys move focus.
  const selectedIndex = Math.max(
    0,
    chips.findIndex(c => c.value === selectedOfferId),
  );

  const chipRefs = useRef<Array<HTMLButtonElement | null>>([]);

  const focusChipAt = useCallback((index: number) => {
    const el = chipRefs.current[index];
    if (el) {
      el.focus();
    }
  }, []);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
      const lastIndex = chips.length - 1;
      switch (event.key) {
        case 'ArrowRight':
        case 'ArrowDown': {
          event.preventDefault();
          const next = index >= lastIndex ? 0 : index + 1;
          focusChipAt(next);
          break;
        }
        case 'ArrowLeft':
        case 'ArrowUp': {
          event.preventDefault();
          const prev = index <= 0 ? lastIndex : index - 1;
          focusChipAt(prev);
          break;
        }
        case 'Home': {
          event.preventDefault();
          focusChipAt(0);
          break;
        }
        case 'End': {
          event.preventDefault();
          focusChipAt(lastIndex);
          break;
        }
        default:
          break;
      }
    },
    [chips.length, focusChipAt],
  );

  return (
    <div
      className={cn(
        'flex items-center gap-2',
        // Mobile: horizontal scroll with snap. Desktop (sm+): wrap to multiple rows.
        'overflow-x-auto sm:overflow-visible sm:flex-wrap',
        'snap-x snap-mandatory sm:snap-none',
        'scrollbar-thin pb-1 sm:pb-0',
        className,
      )}
      role="group"
      aria-label="Filtrar por offer"
    >
      {chips.map((chip, index) => (
        <Chip
          key={chip.key}
          kind={chip.kind}
          label={chip.label}
          emoji={chip.emoji}
          ariaLabel={chip.ariaLabel}
          selected={chip.value === selectedOfferId}
          tabIndex={index === selectedIndex ? 0 : -1}
          registerRef={el => {
            chipRefs.current[index] = el;
          }}
          onClick={() => onSelect(chip.value)}
          onKeyDown={event => handleKeyDown(event, index)}
        />
      ))}
    </div>
  );
}
