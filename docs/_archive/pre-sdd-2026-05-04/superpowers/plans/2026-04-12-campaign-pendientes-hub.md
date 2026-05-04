# Campaign Pendientes Hub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Pendientes split-view tab for resolving unassigned campaigns in bulk, plus an inline Popover for changing offer assignments directly from the campaigns table.

**Architecture:** Two independent features sharing existing API hooks. (1) New `pendientes` tab inside MetaAdsDashboard with a split-view layout — campaign list left, detail + assignment dropdown right. (2) OfferReassignPopover component that replaces the drawer-open behavior when clicking an offer badge on an already-assigned campaign. No backend changes needed.

**Tech Stack:** Next.js 16 App Router, React 18, TypeScript, Tailwind CSS, Shadcn UI (Select, Popover, Tabs, Badge), React Query (existing hooks)

**UI Spec:** `docs/ui-specs/UI-SPEC-campaign-pendientes-hub.md`

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `frontend/src/features/growth-studio/types/metrics.ts:600` | Add `'pendientes'` to `MetaAdsDashboardTab` |
| Create | `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/OfferReassignPopover.tsx` | Inline popover for changing/removing offer on a campaign |
| Create | `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/OfferAssignmentDropdown.tsx` | Select with auto-save for assigning offers |
| Create | `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/PendienteItem.tsx` | Single campaign row in the pending list |
| Create | `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/PendientesList.tsx` | Left panel: filtered list of pending campaigns |
| Create | `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/PendienteDetailPanel.tsx` | Right panel: campaign context + assignment |
| Create | `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/PendientesView.tsx` | Main split-view container orchestrating data + layout |
| Create | `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/PendientesTab.tsx` | Thin wrapper passing dashboard props to PendientesView |
| Modify | `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/MetaAdsDashboard.tsx` | Add Pendientes tab + TabsTrigger with counter badge |
| Modify | `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/CampaignsTab.tsx` | Replace drawer-open with OfferReassignPopover for assigned campaigns |

---

### Task 1: Update MetaAdsDashboardTab type

**Files:**
- Modify: `frontend/src/features/growth-studio/types/metrics.ts:600`

- [ ] **Step 1: Add `'pendientes'` to the tab union type**

In `frontend/src/features/growth-studio/types/metrics.ts`, change line 600 from:

```typescript
export type MetaAdsDashboardTab = 'resumen' | 'campanas' | 'creativos' | 'audiencia' | 'costos';
```

to:

```typescript
export type MetaAdsDashboardTab = 'resumen' | 'campanas' | 'pendientes' | 'creativos' | 'audiencia' | 'costos';
```

- [ ] **Step 2: Verify no type errors**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -20`
Expected: No new errors (existing errors may appear but no new ones from this change)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/growth-studio/types/metrics.ts
git commit -m "feat(growth-studio): add 'pendientes' to MetaAdsDashboardTab type"
```

---

### Task 2: Create OfferReassignPopover

This component wraps an offer badge in a Popover. When opened, it shows the current offer + a dropdown to change + a desasignar button.

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/OfferReassignPopover.tsx`

- [ ] **Step 1: Create the component**

Create `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/OfferReassignPopover.tsx`:

```tsx
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
```

- [ ] **Step 2: Verify no type errors**

Run: `cd frontend && npx tsc --noEmit 2>&1 | grep -i "OfferReassignPopover" | head -10`
Expected: No errors referencing this file

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/OfferReassignPopover.tsx
git commit -m "feat(growth-studio): add OfferReassignPopover for inline offer changes"
```

---

### Task 3: Wire OfferReassignPopover into CampaignsTab

Replace the behavior where clicking an offer badge on an **already-assigned** campaign opens the full drawer. Instead, wrap the badge in OfferReassignPopover. Unassigned campaigns ("Sin offer asignada") still open the drawer.

**Files:**
- Modify: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/CampaignsTab.tsx`

- [ ] **Step 1: Add import for OfferReassignPopover**

At the top of `CampaignsTab.tsx`, add after the existing imports (near line 36):

```typescript
import { OfferReassignPopover } from '../OfferReassignPopover';
```

- [ ] **Step 2: Change CampaignRow to accept campaign data for popover**

Modify the `CampaignRow` function signature to also receive the campaign object for the popover. Change the `onAssignClick` prop to `onUnassignedClick` to clarify it's only for unassigned campaigns, and add a new approach: wrap assigned badges in the popover directly.

Replace the entire offer-badge section in `CampaignRow` (lines ~440-480 — the block starting with `{/* Offer association badge */}` and ending after the unassigned `</BadgeTooltip>`).

Find this code block (the three-way conditional: branding / associated / unassigned):

```tsx
            {/* Offer association badge — clickable to open the assignment drawer */}
            {association ? (
              association.associationType === 'excluded_branding' ? (
                <BadgeTooltip content="Esta campaña está marcada como branding (sin offer). Click para cambiar.">
                  <button
                    type="button"
                    onClick={onAssignClick}
                    className="inline-flex items-center gap-1 rounded-full border border-zinc-600/60 bg-zinc-700/10 px-2 py-0.5 text-[10px] text-zinc-400 transition-colors hover:border-zinc-500 hover:bg-zinc-700/20 hover:text-zinc-300"
                  >
                    <span aria-hidden="true">🎯</span>
                    Branding
                  </button>
                </BadgeTooltip>
              ) : (
                <BadgeTooltip
                  content={`Esta campaña está asociada a la offer "${association.offerName ?? 'sin nombre'}". Click para cambiar o desasignar.`}
                >
                  <button
                    type="button"
                    onClick={onAssignClick}
                    className="inline-flex items-center gap-1 rounded-full border border-blue-500/40 bg-blue-500/10 px-2 py-0.5 text-[10px] text-blue-400 transition-colors hover:border-blue-400 hover:bg-blue-500/20 hover:text-blue-300"
                  >
                    <span aria-hidden="true">
                      {archetypeEmoji(association.offerArchetype)}
                    </span>
                    {association.offerName ?? 'Offer asociada'}
                  </button>
                </BadgeTooltip>
              )
            ) : (
              <BadgeTooltip content="Click para asignar esta campaña a una offer del Offer Ladder.">
                <button
                  type="button"
                  onClick={onAssignClick}
                  className="inline-flex items-center gap-1 rounded-full border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-400 transition-colors hover:border-amber-400 hover:bg-amber-500/20 hover:text-amber-300"
                >
                  Sin offer asignada
                  <span aria-hidden="true">→</span>
                </button>
              </BadgeTooltip>
            )}
```

Replace with:

```tsx
            {/* Offer association badge */}
            {association ? (
              <OfferReassignPopover
                campaign={{ externalId: campaign.externalId, name: campaign.name }}
                association={association}
              >
                {association.associationType === 'excluded_branding' ? (
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 rounded-full border border-zinc-600/60 bg-zinc-700/10 px-2 py-0.5 text-[10px] text-zinc-400 transition-colors hover:border-zinc-500 hover:bg-zinc-700/20 hover:text-zinc-300"
                  >
                    <span aria-hidden="true">🎯</span>
                    Branding
                  </button>
                ) : (
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 rounded-full border border-blue-500/40 bg-blue-500/10 px-2 py-0.5 text-[10px] text-blue-400 transition-colors hover:border-blue-400 hover:bg-blue-500/20 hover:text-blue-300"
                  >
                    <span aria-hidden="true">
                      {archetypeEmoji(association.offerArchetype)}
                    </span>
                    {association.offerName ?? 'Offer asociada'}
                  </button>
                )}
              </OfferReassignPopover>
            ) : (
              <BadgeTooltip content="Click para asignar esta campaña a una offer del Offer Ladder.">
                <button
                  type="button"
                  onClick={onAssignClick}
                  className="inline-flex items-center gap-1 rounded-full border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-400 transition-colors hover:border-amber-400 hover:bg-amber-500/20 hover:text-amber-300"
                >
                  Sin offer asignada
                  <span aria-hidden="true">→</span>
                </button>
              </BadgeTooltip>
            )}
```

- [ ] **Step 3: Verify no type errors**

Run: `cd frontend && npx tsc --noEmit 2>&1 | grep -i "CampaignsTab\|OfferReassign" | head -10`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/CampaignsTab.tsx
git commit -m "feat(growth-studio): wire OfferReassignPopover into CampaignsTab badges"
```

---

### Task 4: Create OfferAssignmentDropdown (for Pendientes view)

A standalone Select component that auto-saves on selection. Used inside the Pendientes detail panel.

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/OfferAssignmentDropdown.tsx`

- [ ] **Step 1: Create the component**

```tsx
'use client';

import { useState } from 'react';
import { Loader2 } from 'lucide-react';

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useCreateAssociation } from '../../../../../api/offer-association-api';
import { archetypeEmoji } from '../../../../../types/offer-association';
import type { OfferSummary } from '../../../../../types/offer-association';

const OPTION_BRANDING = '__branding__';

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
          targetType: 'campaign',
          targetExternalId: campaignExternalId,
          offerId: null,
          associationType: 'excluded_branding',
        });
      } else {
        await createMutation.mutateAsync({
          targetType: 'campaign',
          targetExternalId: campaignExternalId,
          offerId: value,
          associationType: 'manual',
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
        <Select
          onValueChange={v => void handleSelect(v)}
          disabled={saving}
        >
          <SelectTrigger className="h-9 text-xs flex-1 border-amber-500/30 bg-amber-500/5">
            <SelectValue placeholder="Elegir offer..." />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={OPTION_BRANDING}>
              🎯 Marcar como Branding (sin offer)
            </SelectItem>
            {offers.map(o => (
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
        {saving && (
          <Loader2 className="h-4 w-4 animate-spin text-muted-foreground shrink-0" />
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/OfferAssignmentDropdown.tsx
git commit -m "feat(growth-studio): add OfferAssignmentDropdown for pendientes view"
```

---

### Task 5: Create PendienteItem

A single row in the left-panel list showing campaign name, status, summary metrics, and a pending-type badge.

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/PendienteItem.tsx`

- [ ] **Step 1: Create the component**

```tsx
'use client';

import { cn } from '@/lib/utils';
import { formatMoney } from '@/lib/format-money';
import type { CampaignWithMetrics } from '../../../../../types/metrics';

export type PendingReason = 'no_offer' | 'no_utm';

interface PendienteItemProps {
  campaign: CampaignWithMetrics;
  reason: PendingReason;
  currency: string;
  isSelected: boolean;
  onClick: () => void;
}

const REASON_LABEL: Record<PendingReason, string> = {
  no_offer: 'Sin offer',
  no_utm: 'Sin UTM',
};

const REASON_COLORS: Record<PendingReason, string> = {
  no_offer: 'bg-amber-500/10 text-amber-400',
  no_utm: 'bg-blue-500/10 text-blue-400',
};

function statusDotColor(status: string | null): string {
  const s = (status ?? '').toUpperCase();
  if (s === 'ACTIVE') return 'bg-emerald-500';
  if (s === 'PAUSED' || s === 'CAMPAIGN_PAUSED') return 'bg-zinc-500';
  return 'bg-zinc-500';
}

export function PendienteItem({
  campaign,
  reason,
  currency,
  isSelected,
  onClick,
}: PendienteItemProps) {
  const isPaused =
    (campaign.effectiveStatus ?? '').toUpperCase() === 'PAUSED' ||
    (campaign.effectiveStatus ?? '').toUpperCase() === 'CAMPAIGN_PAUSED';

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'w-full text-left px-4 py-3 border-b border-zinc-800/40 transition-colors',
        isSelected
          ? 'bg-blue-500/10 border-l-2 border-l-blue-500'
          : 'hover:bg-zinc-800/20 border-l-2 border-l-transparent',
        isPaused && 'opacity-60',
      )}
    >
      <div className="flex items-center gap-2">
        <span
          className={cn(
            'inline-block h-2 w-2 rounded-full shrink-0',
            statusDotColor(campaign.effectiveStatus),
          )}
        />
        <span className="text-sm font-medium truncate">{campaign.name}</span>
      </div>
      <div className="flex items-center gap-2 mt-1 ml-4">
        <span className="text-[10px] text-zinc-500">
          {isPaused ? 'Pausada · ' : ''}
          {formatMoney(campaign.metrics.spend, currency)}
          {campaign.metrics.roas != null && ` · ROAS ${campaign.metrics.roas.toFixed(1)}x`}
        </span>
        <span
          className={cn(
            'inline-flex items-center rounded-full px-1.5 py-0.5 text-[9px] font-medium',
            REASON_COLORS[reason],
          )}
        >
          {REASON_LABEL[reason]}
        </span>
      </div>
    </button>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/PendienteItem.tsx
git commit -m "feat(growth-studio): add PendienteItem component"
```

---

### Task 6: Create PendientesList

Left panel with filter pills and the list of PendienteItems. Handles empty/loading states.

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/PendientesList.tsx`

- [ ] **Step 1: Create the component**

```tsx
'use client';

import { useMemo, useState } from 'react';
import { CheckCircle2, Sparkles, Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { PendienteItem } from './PendienteItem';
import type { PendingReason } from './PendienteItem';
import type { CampaignWithMetrics } from '../../../../../types/metrics';

export interface PendingCampaign {
  campaign: CampaignWithMetrics;
  reason: PendingReason;
}

type FilterType = 'all' | 'no_offer' | 'no_utm';

interface PendientesListProps {
  items: PendingCampaign[];
  currency: string;
  selectedId: string | null;
  onSelect: (externalId: string) => void;
  isLoading: boolean;
  onAutoDetect: () => void;
  isAutoDetecting: boolean;
  onBackToCampaigns: () => void;
}

export function PendientesList({
  items,
  currency,
  selectedId,
  onSelect,
  isLoading,
  onAutoDetect,
  isAutoDetecting,
  onBackToCampaigns,
}: PendientesListProps) {
  const [filter, setFilter] = useState<FilterType>('all');

  const counts = useMemo(() => {
    const noOffer = items.filter(i => i.reason === 'no_offer').length;
    const noUtm = items.filter(i => i.reason === 'no_utm').length;
    return { noOffer, noUtm, total: items.length };
  }, [items]);

  const filtered = useMemo(() => {
    if (filter === 'all') return items;
    return items.filter(i => i.reason === filter);
  }, [items, filter]);

  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <div className="px-4 py-3 border-b border-zinc-800">
          <Skeleton className="h-5 w-32" />
          <div className="flex gap-1.5 mt-2">
            <Skeleton className="h-6 w-20 rounded-full" />
            <Skeleton className="h-6 w-20 rounded-full" />
          </div>
        </div>
        <div className="p-4 space-y-2">
          {[1, 2, 3, 4].map(i => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-zinc-800 bg-zinc-900/50">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-semibold flex items-center gap-2">
            Pendientes
            {counts.total > 0 && (
              <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-amber-500/15 text-amber-400 text-[10px] font-bold">
                {counts.total}
              </span>
            )}
          </h2>
          {counts.noOffer > 0 && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onAutoDetect}
              disabled={isAutoDetecting}
              className="h-7 gap-1 text-[10px]"
            >
              {isAutoDetecting ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Sparkles className="h-3 w-3" />
              )}
              Auto-detectar
            </Button>
          )}
        </div>

        {/* Filter pills */}
        <div className="flex gap-1.5">
          {counts.noOffer > 0 && (
            <button
              type="button"
              onClick={() => setFilter(f => (f === 'no_offer' ? 'all' : 'no_offer'))}
              className={cn(
                'rounded-full px-2.5 py-0.5 text-[10px] font-medium transition-colors',
                filter === 'no_offer'
                  ? 'bg-amber-500/15 border border-amber-500/30 text-amber-400'
                  : 'bg-zinc-800 border border-zinc-700 text-zinc-500 hover:text-zinc-400',
              )}
            >
              Sin offer ({counts.noOffer})
            </button>
          )}
          {counts.noUtm > 0 && (
            <button
              type="button"
              onClick={() => setFilter(f => (f === 'no_utm' ? 'all' : 'no_utm'))}
              className={cn(
                'rounded-full px-2.5 py-0.5 text-[10px] font-medium transition-colors',
                filter === 'no_utm'
                  ? 'bg-blue-500/15 border border-blue-500/30 text-blue-400'
                  : 'bg-zinc-800 border border-zinc-700 text-zinc-500 hover:text-zinc-400',
              )}
            >
              Sin UTM ({counts.noUtm})
            </button>
          )}
          {filter !== 'all' && (
            <button
              type="button"
              onClick={() => setFilter('all')}
              className="rounded-full bg-zinc-800 border border-zinc-700 px-2.5 py-0.5 text-[10px] text-zinc-500 hover:text-zinc-400"
            >
              Todos
            </button>
          )}
        </div>
      </div>

      {/* List or empty state */}
      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
            <CheckCircle2 className="h-8 w-8 text-emerald-500 mb-3" />
            <p className="text-sm font-medium">¡Todo resuelto!</p>
            <p className="text-xs text-muted-foreground mt-1">
              No hay campañas pendientes de configuración.
            </p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onBackToCampaigns}
              className="mt-4 text-xs"
            >
              Volver a Campañas
            </Button>
          </div>
        ) : (
          filtered.map(item => (
            <PendienteItem
              key={item.campaign.externalId}
              campaign={item.campaign}
              reason={item.reason}
              currency={currency}
              isSelected={selectedId === item.campaign.externalId}
              onClick={() => onSelect(item.campaign.externalId)}
            />
          ))
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/PendientesList.tsx
git commit -m "feat(growth-studio): add PendientesList component with filters"
```

---

### Task 7: Create PendienteDetailPanel

Right panel showing full campaign context + the OfferAssignmentDropdown.

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/PendienteDetailPanel.tsx`

- [ ] **Step 1: Create the component**

```tsx
'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { formatMoney } from '@/lib/format-money';
import { cn } from '@/lib/utils';
import { OfferAssignmentDropdown } from './OfferAssignmentDropdown';
import type { CampaignWithMetrics } from '../../../../../types/metrics';
import type { OfferSummary } from '../../../../../types/offer-association';

interface PendienteDetailPanelProps {
  campaign: CampaignWithMetrics | null;
  currency: string;
  offers: OfferSummary[];
  onAssigned: () => void;
}

function statusLabel(status: string | null): string {
  const s = (status ?? '').toUpperCase();
  if (s === 'ACTIVE') return 'Activa';
  if (s === 'PAUSED' || s === 'CAMPAIGN_PAUSED') return 'Pausada';
  if (s === 'COMPLETED' || s === 'ARCHIVED') return 'Completada';
  return status ?? 'Desconocido';
}

function objectiveLabel(objective: string | null): string {
  if (!objective) return '';
  const map: Record<string, string> = {
    OUTCOME_SALES: 'Ventas',
    OUTCOME_LEADS: 'Leads',
    OUTCOME_ENGAGEMENT: 'Interacción',
    OUTCOME_AWARENESS: 'Alcance',
    OUTCOME_TRAFFIC: 'Tráfico',
    CONVERSIONS: 'Conversiones',
    MESSAGES: 'Mensajes',
    LEAD_GENERATION: 'Leads',
  };
  return map[objective] ?? objective.replace(/^OUTCOME_/, '').replace(/_/g, ' ');
}

function healthColor(health: 'good' | 'warning' | 'critical'): string {
  switch (health) {
    case 'good': return 'text-emerald-400';
    case 'warning': return 'text-amber-400';
    case 'critical': return 'text-red-400';
  }
}

export function PendienteDetailPanel({
  campaign,
  currency,
  offers,
  onAssigned,
}: PendienteDetailPanelProps) {
  if (!campaign) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
        Selecciona una campaña de la lista
      </div>
    );
  }

  const { metrics } = campaign;
  const statusDot =
    (campaign.effectiveStatus ?? '').toUpperCase() === 'ACTIVE'
      ? 'bg-emerald-500'
      : 'bg-zinc-500';

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      {/* Header */}
      <div className="px-6 py-4 border-b border-zinc-800">
        <h2 className="text-lg font-semibold">{campaign.name}</h2>
        <div className="flex items-center gap-2 mt-1">
          <span className={cn('inline-block h-2 w-2 rounded-full', statusDot)} />
          <span className="text-xs text-zinc-500">
            {statusLabel(campaign.effectiveStatus)}
            {campaign.objective && ` · ${objectiveLabel(campaign.objective)}`}
            {` · ${campaign.adSetsCount} ad set${campaign.adSetsCount !== 1 ? 's' : ''}`}
            {` · ${campaign.adsCount} anuncio${campaign.adsCount !== 1 ? 's' : ''}`}
          </span>
        </div>
      </div>

      {/* Assignment section */}
      <div className="mx-6 mt-4 rounded-xl border-2 border-amber-500/30 bg-amber-500/5 p-4">
        <OfferAssignmentDropdown
          campaignExternalId={campaign.externalId}
          offers={offers}
          onAssigned={onAssigned}
        />
      </div>

      {/* Metrics grid */}
      <div className="px-6 py-4">
        <p className="text-[10px] font-medium uppercase tracking-wider text-zinc-500 mb-3">
          Rendimiento actual
        </p>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Card className="border-zinc-800 bg-zinc-900/50">
            <CardContent className="p-3">
              <p className="text-[10px] text-zinc-500">Inversión</p>
              <p className="text-lg font-bold mt-1 tabular-nums">
                {formatMoney(metrics.spend, currency)}
              </p>
            </CardContent>
          </Card>
          <Card className="border-zinc-800 bg-zinc-900/50">
            <CardContent className="p-3">
              <p className="text-[10px] text-zinc-500">Resultados</p>
              <p className="text-lg font-bold mt-1 tabular-nums">
                {metrics.conversions.toLocaleString()}
              </p>
              {campaign.objective && (
                <p className="text-[10px] text-zinc-600">
                  {objectiveLabel(campaign.objective).toLowerCase()}
                </p>
              )}
            </CardContent>
          </Card>
          <Card className="border-zinc-800 bg-zinc-900/50">
            <CardContent className="p-3">
              <p className="text-[10px] text-zinc-500">CPA</p>
              <p className={cn('text-lg font-bold mt-1 tabular-nums', healthColor(campaign.health))}>
                {metrics.cpa != null ? formatMoney(metrics.cpa, currency) : '—'}
              </p>
            </CardContent>
          </Card>
          <Card className="border-zinc-800 bg-zinc-900/50">
            <CardContent className="p-3">
              <p className="text-[10px] text-zinc-500">ROAS</p>
              <p className={cn('text-lg font-bold mt-1 tabular-nums', healthColor(campaign.health))}>
                {metrics.roas != null ? `${metrics.roas.toFixed(1)}x` : '—'}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Secondary metrics */}
        <div className="grid grid-cols-4 gap-3 mt-3">
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
            <p className="text-[10px] text-zinc-500">CTR</p>
            <p className="text-sm font-semibold mt-1 tabular-nums">
              {metrics.ctr != null ? `${metrics.ctr.toFixed(1)}%` : '—'}
            </p>
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
            <p className="text-[10px] text-zinc-500">CPC</p>
            <p className="text-sm font-semibold mt-1 tabular-nums">
              {metrics.cpc != null ? formatMoney(metrics.cpc, currency) : '—'}
            </p>
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
            <p className="text-[10px] text-zinc-500">Impresiones</p>
            <p className="text-sm font-semibold mt-1 tabular-nums">
              {metrics.impressions.toLocaleString()}
            </p>
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
            <p className="text-[10px] text-zinc-500">Frecuencia</p>
            <p className={cn(
              'text-sm font-semibold mt-1 tabular-nums',
              metrics.frequency != null && metrics.frequency > 4 ? 'text-red-400' :
              metrics.frequency != null && metrics.frequency > 3 ? 'text-amber-400' : '',
            )}>
              {metrics.frequency != null ? metrics.frequency.toFixed(1) : '—'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/PendienteDetailPanel.tsx
git commit -m "feat(growth-studio): add PendienteDetailPanel with metrics context"
```

---

### Task 8: Create PendientesView (main orchestrator)

The split-view container that fetches data, derives pending items, manages selection state, and composes the list + detail panel.

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/PendientesView.tsx`

- [ ] **Step 1: Create the component**

```tsx
'use client';

import { useMemo, useState, useCallback } from 'react';
import { useRouter, useParams, useSearchParams } from 'next/navigation';
import { ArrowLeft, AlertTriangle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { useCampaignPerformance } from '../../../../../api/campaigns-api';
import {
  useAssociations,
  useAutoDetectSuggestions,
  useOffersForAssignment,
  useMetaHealthCheck,
} from '../../../../../api/offer-association-api';
import { useTenantLocale } from '@/features/tenant/context/tenant-locale-context';
import type { MetaAdsPeriod } from '../../../../../types/metrics';
import { MetaAdsPeriodSelector } from '../MetaAdsPeriodSelector';
import { PendientesList } from './PendientesList';
import type { PendingCampaign } from './PendientesList';
import { PendienteDetailPanel } from './PendienteDetailPanel';

interface PendientesViewProps {
  period?: MetaAdsPeriod;
  onPeriodChange?: (p: MetaAdsPeriod) => void;
  onBackToCampaigns?: () => void;
}

export function PendientesView({
  period = '30d',
  onPeriodChange,
  onBackToCampaigns,
}: PendientesViewProps) {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const tenantId = params?.tenantId as string;
  const { currency: tenantCurrency } = useTenantLocale();

  // Pre-select campaign from URL param
  const campaignFromUrl = searchParams?.get('campaign') ?? null;
  const [selectedId, setSelectedId] = useState<string | null>(campaignFromUrl);

  const { data: campaignData, isLoading: campaignsLoading } = useCampaignPerformance(period);
  const { data: associations, isLoading: assocLoading } = useAssociations();
  const { data: offers } = useOffersForAssignment();
  const { data: healthCheck } = useMetaHealthCheck();
  const autoDetect = useAutoDetectSuggestions();

  const isLoading = campaignsLoading || assocLoading;

  // Set of campaign externalIds that already have an association
  const associatedIds = useMemo(() => {
    const set = new Set<string>();
    for (const a of associations ?? []) {
      if (a.targetType === 'campaign') {
        set.add(a.targetExternalId);
      }
    }
    return set;
  }, [associations]);

  // Set of campaign externalIds flagged by health check for UTM issues
  const utmIssueIds = useMemo(() => {
    const set = new Set<string>();
    if (healthCheck?.activeCampaigns) {
      for (const c of healthCheck.activeCampaigns) {
        if (c.hasIssue && c.issueText?.toLowerCase().includes('utm')) {
          set.add(c.externalId);
        }
      }
    }
    return set;
  }, [healthCheck]);

  // Derive pending items
  const pendingItems = useMemo<PendingCampaign[]>(() => {
    const campaigns = campaignData?.campaigns ?? [];
    const items: PendingCampaign[] = [];

    for (const c of campaigns) {
      if (!associatedIds.has(c.externalId)) {
        items.push({ campaign: c, reason: 'no_offer' });
      } else if (utmIssueIds.has(c.externalId)) {
        items.push({ campaign: c, reason: 'no_utm' });
      }
    }

    // Sort: active first, then paused
    items.sort((a, b) => {
      const aActive = (a.campaign.effectiveStatus ?? '').toUpperCase() === 'ACTIVE';
      const bActive = (b.campaign.effectiveStatus ?? '').toUpperCase() === 'ACTIVE';
      if (aActive && !bActive) return -1;
      if (!aActive && bActive) return 1;
      return a.campaign.name.localeCompare(b.campaign.name);
    });

    return items;
  }, [campaignData?.campaigns, associatedIds, utmIssueIds]);

  // Auto-select first item if nothing is selected
  const effectiveSelectedId = selectedId && pendingItems.some(i => i.campaign.externalId === selectedId)
    ? selectedId
    : pendingItems[0]?.campaign.externalId ?? null;

  const selectedCampaign = useMemo(
    () => pendingItems.find(i => i.campaign.externalId === effectiveSelectedId)?.campaign ?? null,
    [pendingItems, effectiveSelectedId],
  );

  const currency = campaignData?.currency ?? tenantCurrency;

  const handleAssigned = useCallback(() => {
    // After assignment, the item will disappear from the list on next render
    // (because associations query is invalidated). Auto-select next item.
    const currentIndex = pendingItems.findIndex(
      i => i.campaign.externalId === effectiveSelectedId,
    );
    const nextItem = pendingItems[currentIndex + 1] ?? pendingItems[currentIndex - 1];
    setSelectedId(nextItem?.campaign.externalId ?? null);
  }, [pendingItems, effectiveSelectedId]);

  const handleBack = useCallback(() => {
    if (onBackToCampaigns) {
      onBackToCampaigns();
    } else {
      router.push(
        `/${tenantId}/growth-studio/atraccion-captura/meta-ads?tab=campanas`,
      );
    }
  }, [onBackToCampaigns, router, tenantId]);

  // Error state
  if (!isLoading && !campaignData) {
    return (
      <Card className="m-6">
        <CardContent className="py-8 text-center">
          <AlertTriangle className="h-8 w-8 text-amber-500 mx-auto mb-3" />
          <p className="text-sm font-medium">Error al cargar pendientes</p>
          <p className="text-xs text-muted-foreground mt-1">
            Intenta de nuevo o vuelve a la vista de campañas.
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={handleBack}
            className="mt-4 text-xs"
          >
            Volver a Campañas
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleBack}
            className="gap-1.5 text-xs"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Campañas
          </Button>
          <h1 className="text-sm font-semibold flex items-center gap-2">
            Pendientes
            {pendingItems.length > 0 && (
              <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-amber-500/15 text-amber-400 text-[10px] font-bold">
                {pendingItems.length}
              </span>
            )}
          </h1>
        </div>
        {onPeriodChange && (
          <MetaAdsPeriodSelector value={period} onChange={onPeriodChange} />
        )}
      </div>

      {/* Split view — desktop: side by side, mobile: stack */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* Left panel */}
        <div className="w-full lg:w-[380px] lg:border-r border-zinc-800 overflow-hidden flex flex-col shrink-0">
          <PendientesList
            items={pendingItems}
            currency={currency}
            selectedId={effectiveSelectedId}
            onSelect={setSelectedId}
            isLoading={isLoading}
            onAutoDetect={() => void autoDetect.mutateAsync()}
            isAutoDetecting={autoDetect.isPending}
            onBackToCampaigns={handleBack}
          />
        </div>

        {/* Right panel — hidden on mobile (mobile shows inline dropdowns in PendienteItem) */}
        <div className="hidden lg:flex flex-1 overflow-hidden">
          <PendienteDetailPanel
            campaign={selectedCampaign}
            currency={currency}
            offers={offers ?? []}
            onAssigned={handleAssigned}
          />
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify no type errors**

Run: `cd frontend && npx tsc --noEmit 2>&1 | grep -i "pendientes" | head -10`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/
git commit -m "feat(growth-studio): add PendientesView split-view orchestrator"
```

---

### Task 9: Create PendientesTab wrapper + wire into MetaAdsDashboard

Add the "Pendientes" tab to MetaAdsDashboard. The tab content renders PendientesView.

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/PendientesTab.tsx`
- Modify: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/MetaAdsDashboard.tsx`

- [ ] **Step 1: Create PendientesTab**

Create `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/PendientesTab.tsx`:

```tsx
'use client';

import { PendientesView } from '../pendientes/PendientesView';
import type { MetaAdsPeriod } from '../../../../../types/metrics';

interface PendientesTabProps {
  period: MetaAdsPeriod;
  onPeriodChange: (p: MetaAdsPeriod) => void;
  onBackToCampaigns: () => void;
}

export function PendientesTab({
  period,
  onPeriodChange,
  onBackToCampaigns,
}: PendientesTabProps) {
  return (
    <div className="h-[calc(100vh-140px)]">
      <PendientesView
        period={period}
        onPeriodChange={onPeriodChange}
        onBackToCampaigns={onBackToCampaigns}
      />
    </div>
  );
}
```

- [ ] **Step 2: Modify MetaAdsDashboard — add import**

In `MetaAdsDashboard.tsx`, add after the CostosTab import (around line 28):

```typescript
import { PendientesTab } from './tabs/PendientesTab';
```

- [ ] **Step 3: Modify MetaAdsDashboard — update VALID_TABS**

Change line 43 from:

```typescript
const VALID_TABS: MetaAdsDashboardTab[] = ['resumen', 'campanas', 'creativos', 'audiencia', 'costos'];
```

to:

```typescript
const VALID_TABS: MetaAdsDashboardTab[] = ['resumen', 'campanas', 'pendientes', 'creativos', 'audiencia', 'costos'];
```

- [ ] **Step 4: Modify MetaAdsDashboard — compute unassigned count for badge**

After the `useHashScroll()` call (around line 66), add:

```typescript
  // Pending campaign count for the tab badge
  const unassignedCount = useMemo(() => {
    if (!campaignData?.campaigns || !associations) return 0;
    const assocSet = new Set(
      (associations ?? [])
        .filter(a => a.targetType === 'campaign')
        .map(a => a.targetExternalId),
    );
    return campaignData.campaigns.filter(c => !assocSet.has(c.externalId)).length;
  }, [campaignData?.campaigns, associations]);
```

Add `useMemo` to the existing imports from `react` if not already there (it is already imported on line 3: `import { useState, useCallback, useMemo } from 'react';`).

- [ ] **Step 5: Modify MetaAdsDashboard — add Pendientes TabsTrigger**

In the TabsList (around line 223-253), add the Pendientes tab trigger after the Campañas trigger. Find:

```tsx
            <TabsTrigger value="creativos">
```

Insert BEFORE it:

```tsx
            <TabsTrigger value="pendientes">
              Pendientes
              {unassignedCount > 0 && (
                <span className="ml-1.5 inline-flex items-center justify-center min-w-[18px] h-[18px] rounded-full bg-amber-500/15 px-1 text-[10px] font-bold text-amber-400">
                  {unassignedCount}
                </span>
              )}
            </TabsTrigger>
```

- [ ] **Step 6: Modify MetaAdsDashboard — add Pendientes TabsContent**

After the `campanas` TabsContent block (around line 276), add:

```tsx
          <TabsContent value="pendientes" className="m-0 flex-1">
            <PendientesTab
              period={period}
              onPeriodChange={handlePeriodChange}
              onBackToCampaigns={() => handleTabChange('campanas')}
            />
          </TabsContent>
```

- [ ] **Step 7: Verify no type errors**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -20`
Expected: No new errors

- [ ] **Step 8: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/PendientesTab.tsx frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/MetaAdsDashboard.tsx
git commit -m "feat(growth-studio): add Pendientes tab to MetaAdsDashboard with counter badge"
```

---

### Task 10: Add pendientes badge link in CampaignsTab header

Add a clickable "N pendientes →" link in the CampaignsTab header that switches to the Pendientes tab.

**Files:**
- Modify: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/CampaignsTab.tsx`

- [ ] **Step 1: Add onNavigateToPendientes prop**

Change the `CampaignsTabProps` interface to add:

```typescript
  onNavigateToPendientes?: () => void;
```

Add it to the function signature destructuring too.

- [ ] **Step 2: Add badge next to the "Asociar offers" button**

In the tab header section (around line 893-927), find the "Asociar offers" Button. Replace the entire header `<div className="flex flex-wrap items-start justify-between gap-3">` block with:

```tsx
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">Campañas</h2>
              <p className="mt-0.5 text-xs text-zinc-500">
                Rendimiento individual por campaña
                {data.lastSynced && (
                  <>
                    {' '}
                    &middot; Última sincronización:{' '}
                    {formatTenantDateTime(data.lastSynced, timezone)}
                  </>
                )}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {unassignedActiveCount > 0 && onNavigateToPendientes && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={onNavigateToPendientes}
                  className="gap-1.5 text-amber-400 border-amber-500/30 hover:bg-amber-500/10"
                >
                  {unassignedActiveCount} pendientes →
                </Button>
              )}
              <Button
                type="button"
                variant={unassignedActiveCount > 0 ? 'default' : 'outline'}
                size="sm"
                onClick={() => setIsDrawerOpen(true)}
                className="gap-1.5"
              >
                <Sparkles className="h-3.5 w-3.5" />
                Asociar offers
              </Button>
            </div>
          </div>
```

- [ ] **Step 3: Pass the prop from MetaAdsDashboard**

In `MetaAdsDashboard.tsx`, modify the CampaignsTab usage (around line 269) to pass the new prop:

```tsx
            <CampaignsTab
              data={campaignData}
              isLoading={isCampaignLoading}
              currency={campaignData?.currency ?? dashboardData?.kpis.find(k => k.currency)?.currency}
              period={period}
              notices={noticesSummary.byTab.campanas}
              noticesSeverity={noticesSummary.severityPerTab.campanas}
              onNavigateToPendientes={() => handleTabChange('pendientes')}
            />
```

- [ ] **Step 4: Verify no type errors**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -20`
Expected: No new errors

- [ ] **Step 5: Run lint**

Run: `cd frontend && npx eslint src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/ --max-warnings=0 2>&1 | tail -20`
Expected: No new lint errors from our changes

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/CampaignsTab.tsx frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/MetaAdsDashboard.tsx
git commit -m "feat(growth-studio): add pendientes badge link in CampaignsTab header"
```

---

### Task 11: Final verification

- [ ] **Step 1: Full TypeScript check**

Run: `cd frontend && npx tsc --noEmit`
Expected: No new errors

- [ ] **Step 2: Lint check**

Run: `cd frontend && npx eslint src/features/growth-studio/ --max-warnings=0 2>&1 | tail -30`
Expected: No new errors from our files

- [ ] **Step 3: Run existing tests**

Run: `cd frontend && npx vitest run src/features/growth-studio/ 2>&1 | tail -20`
Expected: All existing tests pass (no regressions)

- [ ] **Step 4: Verify the new files exist and directory structure is correct**

Run: `find frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/ -type f -name "*.tsx" | sort`

Expected output:
```
frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/OfferAssignmentDropdown.tsx
frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/PendienteDetailPanel.tsx
frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/PendienteItem.tsx
frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/PendientesList.tsx
frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/pendientes/PendientesView.tsx
```
