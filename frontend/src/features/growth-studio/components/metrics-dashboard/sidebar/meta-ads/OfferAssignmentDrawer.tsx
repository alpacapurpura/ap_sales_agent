'use client';

import { useMemo, useState } from 'react';
import { Loader2, Sparkles, Check } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';
import {
  useApplySuggestions,
  useAutoDetectSuggestions,
  useCreateAssociation,
} from '../../../../api/offer-association-api';
import { archetypeEmoji } from '../../../../types/offer-association';
import type {
  AssociationConfidence,
  AssociationSuggestion,
  TargetType,
} from '../../../../types/offer-association';
import { BestPracticesBlock } from './BestPracticesBlock';

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

export interface AssignmentTarget {
  type: TargetType;
  externalId: string;
  name: string;
  objective: string | null;
  currentOfferId: string | null;
  suggestedOfferId?: string | null;
  suggestedConfidence?: AssociationConfidence | null;
}

export interface AssignmentOffer {
  id: string;
  name: string;
  archetype: string;
  expectedMetricLabelEs: string;
}

interface OfferAssignmentDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  targets: AssignmentTarget[];
  offers: AssignmentOffer[];
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Special values used in the Select for non-offer actions.
 * Using __ prefix so they never collide with a real UUID.
 */
const OPTION_NONE = '__none__';
const OPTION_BRANDING = '__branding__';

type PendingChoice = string | typeof OPTION_NONE | typeof OPTION_BRANDING;

function objectiveLabelEs(objective: string | null): string {
  if (!objective) return '';
  const map: Record<string, string> = {
    OUTCOME_SALES: 'Ventas',
    OUTCOME_LEADS: 'Leads',
    OUTCOME_ENGAGEMENT: 'Interacción',
    OUTCOME_AWARENESS: 'Alcance',
    OUTCOME_TRAFFIC: 'Tráfico',
    OUTCOME_APP_PROMOTION: 'App',
    CONVERSIONS: 'Conversiones',
    LINK_CLICKS: 'Clics',
    REACH: 'Alcance',
    BRAND_AWARENESS: 'Marca',
    POST_ENGAGEMENT: 'Interacción',
    VIDEO_VIEWS: 'Video',
    LEAD_GENERATION: 'Leads',
  };
  return map[objective] ?? objective.replace(/^OUTCOME_/, '').replace(/_/g, ' ');
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function OfferAssignmentDrawer(props: OfferAssignmentDrawerProps) {
  // Inner body is mounted only when the drawer is open, so its state
  // (pending changes, auto-suggestions) is automatically fresh each time.
  return (
    <Sheet open={props.open} onOpenChange={props.onOpenChange}>
      {props.open && <DrawerBody {...props} />}
    </Sheet>
  );
}

interface DrawerBodyProps extends OfferAssignmentDrawerProps {}

function DrawerBody({ onOpenChange, targets, offers }: DrawerBodyProps) {
  // Pending changes: key = "type:externalId", value = choice
  const [pending, setPending] = useState<Map<string, PendingChoice>>(new Map());

  const autoDetect = useAutoDetectSuggestions();
  const applyMutation = useApplySuggestions();
  const createMutation = useCreateAssociation();

  // Local state for auto-detected suggestions (overlayed on top of passed targets)
  const [autoSuggestions, setAutoSuggestions] = useState<
    Record<string, { offerId: string; confidence: AssociationConfidence }>
  >({});

  const effectiveTargets = useMemo(() => {
    return targets.map(t => {
      const key = `${t.type}:${t.externalId}`;
      const auto = autoSuggestions[key];
      if (auto) {
        return {
          ...t,
          suggestedOfferId: auto.offerId,
          suggestedConfidence: auto.confidence,
        };
      }
      return t;
    });
  }, [targets, autoSuggestions]);

  const pendingCount = pending.size;

  function keyFor(t: AssignmentTarget) {
    return `${t.type}:${t.externalId}`;
  }

  function handleSelect(target: AssignmentTarget, value: PendingChoice) {
    const key = keyFor(target);
    setPending(prev => {
      const next = new Map(prev);
      next.set(key, value);
      return next;
    });
  }

  async function handleAutoDetect() {
    try {
      const suggestions = await autoDetect.mutateAsync();
      const map: Record<string, { offerId: string; confidence: AssociationConfidence }> = {};
      for (const s of suggestions) {
        map[`${s.targetType}:${s.targetExternalId}`] = {
          offerId: s.suggestedOfferId,
          confidence: s.confidence,
        };
      }
      setAutoSuggestions(map);
    } catch {
      /* error surfaces via mutation.isError */
    }
  }

  async function handleSave() {
    // Convert pending map into API calls
    const manualSuggestions: AssociationSuggestion[] = [];
    const createPayloads: Array<{
      targetType: TargetType;
      targetExternalId: string;
      offerId: string | null;
      associationType: 'manual' | 'excluded_branding';
    }> = [];

    for (const [key, choice] of pending.entries()) {
      const [type, externalId] = key.split(':') as [TargetType, string];
      if (choice === OPTION_NONE) continue; // skip non-action
      if (choice === OPTION_BRANDING) {
        createPayloads.push({
          targetType: type,
          targetExternalId: externalId,
          offerId: null,
          associationType: 'excluded_branding',
        });
      } else {
        createPayloads.push({
          targetType: type,
          targetExternalId: externalId,
          offerId: choice,
          associationType: 'manual',
        });
      }
    }

    try {
      await Promise.all(
        createPayloads.map(p => createMutation.mutateAsync(p)),
      );
      // Apply auto-detected suggestions that the user accepted as-is
      if (manualSuggestions.length > 0) {
        await applyMutation.mutateAsync(manualSuggestions);
      }
      setPending(new Map());
      onOpenChange(false);
    } catch {
      /* surfaces via mutation.isError */
    }
  }

  const isSaving = createMutation.isPending || applyMutation.isPending;

  return (
    <SheetContent
      side="right"
      className="w-full sm:max-w-[560px] flex flex-col p-0"
    >
      <SheetHeader className="px-6 pt-6 pb-3 border-b">
          <SheetTitle>Asociar campañas a offers</SheetTitle>
          <SheetDescription>
            Conectá cada campaña con el producto al que pertenece para ver métricas por offer.
          </SheetDescription>
        </SheetHeader>

        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          <BestPracticesBlock />

          {/* Auto-detect header */}
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
              Campañas a asignar
            </p>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleAutoDetect}
              disabled={autoDetect.isPending || targets.length === 0}
              className="h-7 gap-1.5 text-xs"
            >
              {autoDetect.isPending ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Sparkles className="h-3 w-3" />
              )}
              Auto-detectar
            </Button>
          </div>

          {/* Targets list or empty state */}
          {effectiveTargets.length === 0 ? (
            <div className="rounded-md border border-dashed p-6 text-center space-y-2">
              <p className="text-sm font-medium">
                No se detectaron campañas
              </p>
              <p className="text-xs text-muted-foreground">
                No estamos recibiendo la lista de campañas desde el backend.
                Posibles causas:
              </p>
              <ul className="text-[11px] text-muted-foreground text-left inline-block space-y-0.5">
                <li>• Tu conexión de Meta Ads no está sincronizando</li>
                <li>• El periodo seleccionado no tiene campañas activas</li>
                <li>• Necesitás hacer un hard refresh del navegador (Ctrl+Shift+R)</li>
              </ul>
              {offers.length === 0 && (
                <p className="text-[11px] text-amber-500 pt-1">
                  Además, no hay offers activas en tu Offer Studio.
                </p>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              {effectiveTargets.map(target => {
                const key = keyFor(target);
                const pendingChoice = pending.get(key);
                const currentValue =
                  pendingChoice ??
                  target.currentOfferId ??
                  target.suggestedOfferId ??
                  OPTION_NONE;

                return (
                  <div
                    key={key}
                    className="rounded-lg border bg-card p-3 space-y-2"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{target.name}</p>
                        <div className="mt-0.5 flex items-center gap-2">
                          {target.objective && (
                            <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                              {objectiveLabelEs(target.objective)}
                            </span>
                          )}
                          <span className="text-[10px] text-muted-foreground">
                            {target.type === 'ad_set' ? 'Ad set' : 'Campaña'}
                          </span>
                        </div>
                      </div>
                      {target.suggestedOfferId && (
                        <span
                          className={cn(
                            'shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium',
                            target.suggestedConfidence === 'high'
                              ? 'bg-emerald-500/10 text-emerald-400'
                              : 'bg-blue-500/10 text-blue-400',
                          )}
                        >
                          Sugerido · {target.suggestedConfidence ?? 'media'}
                        </span>
                      )}
                    </div>

                    <Select
                      value={currentValue}
                      onValueChange={v => handleSelect(target, v as PendingChoice)}
                    >
                      <SelectTrigger className="h-8 text-xs">
                        <SelectValue placeholder="Elegir offer..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value={OPTION_NONE}>
                          No asignar todavía
                        </SelectItem>
                        <SelectItem value={OPTION_BRANDING}>
                          Marcar como Branding (sin offer)
                        </SelectItem>
                        {offers.map(o => {
                          const isSuggested = o.id === target.suggestedOfferId;
                          return (
                            <SelectItem key={o.id} value={o.id}>
                              <span className="flex items-center gap-1.5">
                                <span aria-hidden="true">
                                  {archetypeEmoji(o.archetype)}
                                </span>
                                <span>{o.name}</span>
                                <span className="text-[10px] text-muted-foreground">
                                  · {o.expectedMetricLabelEs}
                                </span>
                                {isSuggested && (
                                  <Check className="h-3 w-3 text-emerald-500" aria-hidden="true" />
                                )}
                              </span>
                            </SelectItem>
                          );
                        })}
                      </SelectContent>
                    </Select>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t px-6 py-3 flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            {pendingCount === 0
              ? 'Sin cambios pendientes'
              : `${pendingCount} cambio${pendingCount === 1 ? '' : 's'} pendiente${pendingCount === 1 ? '' : 's'}`}
          </p>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => onOpenChange(false)}
              disabled={isSaving}
            >
              Cancelar
            </Button>
            <Button
              type="button"
              size="sm"
              onClick={handleSave}
              disabled={pendingCount === 0 || isSaving}
              className="gap-1.5"
            >
              {isSaving && <Loader2 className="h-3 w-3 animate-spin" />}
              Guardar {pendingCount > 0 ? `${pendingCount} cambio${pendingCount === 1 ? '' : 's'}` : ''}
            </Button>
          </div>
        </div>
    </SheetContent>
  );
}
