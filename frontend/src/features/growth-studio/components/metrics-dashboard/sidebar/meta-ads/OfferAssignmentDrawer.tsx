"use client";

import { useMemo, useState } from "react";
import { CheckCircle2, Loader2, Sparkles, Check } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import {
  useApplySuggestions,
  useAutoDetectSuggestions,
  useCreateAssociation,
} from "../../../../api/offer-association-api";
import { archetypeEmoji } from "../../../../types/offer-association";
import type { AssociationConfidence, TargetType } from "../../../../types/offer-association";
import { BestPracticesBlock } from "./BestPracticesBlock";

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
const OPTION_NONE = "__none__";
const OPTION_BRANDING = "__branding__";

type PendingChoice = string | typeof OPTION_NONE | typeof OPTION_BRANDING;

function objectiveLabelEs(objective: string | null): string {
  if (!objective) return "";
  const map: Record<string, string> = {
    OUTCOME_SALES: "Ventas",
    OUTCOME_LEADS: "Leads",
    OUTCOME_ENGAGEMENT: "Interacción",
    OUTCOME_AWARENESS: "Alcance",
    OUTCOME_TRAFFIC: "Tráfico",
    OUTCOME_APP_PROMOTION: "App",
    CONVERSIONS: "Conversiones",
    LINK_CLICKS: "Clics",
    REACH: "Alcance",
    BRAND_AWARENESS: "Marca",
    POST_ENGAGEMENT: "Interacción",
    VIDEO_VIEWS: "Video",
    LEAD_GENERATION: "Leads",
  };
  return map[objective] ?? objective.replace(/^OUTCOME_/, "").replace(/_/g, " ");
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
  // Track which targets are currently being saved (for per-row spinners).
  // A Set keyed by "type:externalId" so multiple saves can run in parallel
  // without blocking the UI.
  const [savingKeys, setSavingKeys] = useState<Set<string>>(new Set());
  // Targets that were just saved in this drawer session. We keep them out
  // of the rendered list immediately (optimistic removal) until the next
  // refetch of useAssociations propagates via the parent's targets prop.
  const [savedKeys, setSavedKeys] = useState<Set<string>>(new Set());

  const autoDetect = useAutoDetectSuggestions();
  const applyMutation = useApplySuggestions();
  const createMutation = useCreateAssociation();

  // Local state for auto-detected suggestions (overlayed on top of passed targets)
  const [autoSuggestions, setAutoSuggestions] = useState<
    Record<string, { offerId: string; confidence: AssociationConfidence }>
  >({});

  function keyFor(t: AssignmentTarget) {
    return `${t.type}:${t.externalId}`;
  }

  // Effective list = incoming targets + auto-suggestions overlayed, MINUS
  // anything that's already associated or was just saved in this session.
  const effectiveTargets = useMemo(() => {
    return targets
      .filter((t) => !t.currentOfferId && !savedKeys.has(keyFor(t)))
      .map((t) => {
        const key = keyFor(t);
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
  }, [targets, autoSuggestions, savedKeys]);

  // Count of saved associations — used for the footer summary banner.
  const savedCount = savedKeys.size;

  async function handleSelect(target: AssignmentTarget, value: PendingChoice) {
    // "No asignar todavía" is a no-op.
    if (value === OPTION_NONE) return;

    const key = keyFor(target);
    setSavingKeys((prev) => new Set(prev).add(key));

    try {
      if (value === OPTION_BRANDING) {
        await createMutation.mutateAsync({
          targetType: target.type,
          targetExternalId: target.externalId,
          offerId: null,
          associationType: "excluded_branding",
        });
      } else {
        await createMutation.mutateAsync({
          targetType: target.type,
          targetExternalId: target.externalId,
          offerId: value,
          associationType: "manual",
        });
      }
      // Optimistic removal: hide this row immediately.
      setSavedKeys((prev) => new Set(prev).add(key));
    } catch {
      /* error surfaces via mutation.isError; row stays visible so user can retry */
    } finally {
      setSavingKeys((prev) => {
        const next = new Set(prev);
        next.delete(key);
        return next;
      });
    }
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

  const isSaving = createMutation.isPending || applyMutation.isPending;

  return (
    <SheetContent side="right" className="w-full sm:max-w-[560px] flex flex-col p-0">
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
            {savedCount > 0 ? (
              <>
                <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-500" aria-hidden="true" />
                <p className="text-sm font-medium">
                  ¡Listo! Todas las campañas ya están asociadas.
                </p>
                <p className="text-xs text-muted-foreground">
                  Asignaste {savedCount} campaña{savedCount === 1 ? "" : "s"} en esta sesión. Podés
                  cerrar este panel.
                </p>
              </>
            ) : (
              <>
                <p className="text-sm font-medium">No hay campañas sin asignar</p>
                <p className="text-xs text-muted-foreground">
                  Todas tus campañas activas ya están asociadas a una offer o marcadas como
                  branding. Si necesitás cambiar una, volvé a la tab Campañas y clickeá el badge de
                  esa fila.
                </p>
                {offers.length === 0 && (
                  <p className="text-[11px] text-amber-500 pt-1">
                    Además, no hay offers activas en tu Offer Studio.
                  </p>
                )}
              </>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            {effectiveTargets.map((target) => {
              const key = keyFor(target);
              const rowIsSaving = savingKeys.has(key);
              const currentValue = target.suggestedOfferId ?? OPTION_NONE;

              return (
                <div
                  key={key}
                  className={cn(
                    "rounded-lg border bg-card p-3 space-y-2 transition-opacity",
                    rowIsSaving && "opacity-60",
                  )}
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
                          {target.type === "ad_set" ? "Ad set" : "Campaña"}
                        </span>
                      </div>
                    </div>
                    {target.suggestedOfferId && (
                      <span
                        className={cn(
                          "shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium",
                          target.suggestedConfidence === "high"
                            ? "bg-emerald-500/10 text-emerald-400"
                            : "bg-blue-500/10 text-blue-400",
                        )}
                      >
                        Sugerido · {target.suggestedConfidence ?? "media"}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <Select
                      value={currentValue}
                      onValueChange={(v) => void handleSelect(target, v as PendingChoice)}
                      disabled={rowIsSaving}
                    >
                      <SelectTrigger className="h-8 text-xs flex-1">
                        <SelectValue placeholder="Elegir offer..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value={OPTION_NONE}>No asignar todavía</SelectItem>
                        <SelectItem value={OPTION_BRANDING}>
                          Marcar como Branding (sin offer)
                        </SelectItem>
                        {offers.map((o) => {
                          const isSuggested = o.id === target.suggestedOfferId;
                          return (
                            <SelectItem key={o.id} value={o.id}>
                              <span className="flex items-center gap-1.5">
                                <span aria-hidden="true">{archetypeEmoji(o.archetype)}</span>
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
                    {rowIsSaving && (
                      <Loader2
                        className="h-4 w-4 animate-spin text-muted-foreground"
                        aria-label="Guardando..."
                      />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer — simpler now that saves are instant */}
      <div className="border-t px-6 py-3 flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          {savedCount > 0 ? (
            <span className="inline-flex items-center gap-1.5">
              <CheckCircle2 className="h-3 w-3 text-emerald-500" aria-hidden="true" />
              {savedCount} asignada{savedCount === 1 ? "" : "s"} en esta sesión
            </span>
          ) : (
            "Cada selección se guarda automáticamente"
          )}
        </p>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => onOpenChange(false)}
          disabled={isSaving}
        >
          Cerrar
        </Button>
      </div>
    </SheetContent>
  );
}
