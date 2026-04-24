"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { AlertCircle, Plus, SearchX } from "lucide-react";
import { useParams } from "next/navigation";
import { useState, useEffect, useMemo, useCallback } from "react";

import { useNavigation } from "@/components/shared/navigation";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useGuidedEntityCreation } from "@/features/copilot/hooks/use-guided-entity-creation";
import { offerApi } from "@/features/offer-studio/api";
import { useArchiveOffer } from "@/features/offer-studio/hooks/use-offer";
import { useValueLevelMetadata } from "@/features/offer-studio/hooks/use-value-level-catalog";
import { resolveIconByName } from "@/features/offer-studio/lib/icon-name-resolver";
import { OfferValueLevel } from "@/features/offer-studio/types";
import { computeLadderCompleteness } from "@/features/offer-studio/utils/ladder-completeness";

import { CreateOfferWizard } from "../legacy-wizard/CreateOfferWizard";

import { LeadMagnetStreamCard } from "./LeadMagnetStreamCard";
import { OfferLadderLayout } from "./OfferLadderLayout";

import type { WizardResult } from "../legacy-wizard/CreateOfferWizard";
import type { Offer } from "@/features/offer-studio/types";
import type { OfferFormValues } from "@/features/offer-studio/types/schema";

/**
 * Map the wizard payload to the strict `ProductCreate` DTO shape.
 *
 * `value_level` (not `offer_value_level`) is the DTO key — sending the wrong
 * key made FastAPI discard the field and `_normalize_ladder_position`
 * defaulted to ACTIVACION, dumping every paid offer into "Primera Compra".
 * See backend/src/modules/offer/api/dto/products.py:113.
 *
 * The `pricing_options` cast narrows the loose wizard interface to the
 * Zod-resolved OfferFormValues shape — the runtime values are already
 * fully-populated PricingStructure records.
 */
function toOfferCreatePayload(wizardData: WizardResult): {
  public_name: string;
  archetype: WizardResult["archetype"];
  preset_id: WizardResult["preset_id"];
  conditional_answers: WizardResult["conditional_answers"];
  format_hint: WizardResult["format_hint"];
  is_lead_magnet: WizardResult["is_lead_magnet"];
  has_editions: WizardResult["has_editions"];
  headline_promise: WizardResult["headline_promise"];
  status: WizardResult["status"];
  delivery_model: WizardResult["delivery_model"];
  value_level: WizardResult["value_level"];
  specific_details: WizardResult["specific_details"];
  currency: WizardResult["currency"];
  pricing_options: OfferFormValues["pricing_options"];
} {
  return {
    public_name: wizardData.name,
    archetype: wizardData.archetype,
    preset_id: wizardData.preset_id,
    conditional_answers: wizardData.conditional_answers,
    format_hint: wizardData.format_hint,
    is_lead_magnet: wizardData.is_lead_magnet,
    has_editions: wizardData.has_editions,
    headline_promise: wizardData.headline_promise,
    status: wizardData.status,
    delivery_model: wizardData.delivery_model,
    value_level: wizardData.value_level,
    specific_details: wizardData.specific_details,
    currency: wizardData.currency,
    pricing_options: wizardData.pricing_options as OfferFormValues["pricing_options"],
  };
}

interface OfferStudioDashboardProps {
  searchQuery?: string;
  externalCreateTrigger?: boolean;
  onCreateTriggerHandled?: () => void;
  onLadderComputed?: (data: {
    filledGroups: Set<OfferValueLevel>;
    score: string;
    percentage: number;
  }) => void;
}

/**
 *
 */
export function OfferStudioDashboard({
  searchQuery = "",
  externalCreateTrigger = false,
  onCreateTriggerHandled,
  onLadderComputed,
}: OfferStudioDashboardProps) {
  const { getToken } = useAuth();
  const { navigate } = useNavigation();
  const params = useParams();
  const tenantId = params?.tenantId as string;

  const {
    data: offers = [],
    isLoading: loading,
    error: queryError,
    refetch: fetchOffers,
  } = useQuery({
    queryKey: ["offers"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return offerApi.listOffers(token);
    },
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  const error = queryError ? "No se pudieron cargar las ofertas." : null;

  // Wizard State
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [creatingManual, setCreatingManual] = useState(false);

  const { create: createOfferWithGuided, creating: creatingGuided } = useGuidedEntityCreation<
    { id: string },
    WizardResult
  >({
    domain: "offer",
    tenantId,
    createEntity: async (wizardData) => {
      const token = await getToken();
      if (!token) throw new Error("No authenticated");
      const newOffer = await offerApi.createOffer(toOfferCreatePayload(wizardData), token);
      if (!newOffer.id) throw new Error("Backend devolvió oferta sin id");
      return { id: newOffer.id };
    },
    onNavigate: navigate,
  });

  const creating = creatingManual || creatingGuided;
  // Rung preselected by the click context. Header "Nueva Oferta" passes
  // undefined (full 6-step flow); each column's "+" passes its level so
  // the wizard skips the pick-rung step.
  const [presetValueLevel, setPresetValueLevel] = useState<OfferValueLevel | undefined>(undefined);

  // Handle external trigger for creation (header "Nueva Oferta" button).
  useEffect(() => {
    if (externalCreateTrigger) {
      setPresetValueLevel(undefined);
      setIsWizardOpen(true);
      if (onCreateTriggerHandled) {
        onCreateTriggerHandled();
      }
    }
  }, [externalCreateTrigger, onCreateTriggerHandled]);

  const offersByLevel = useMemo(() => {
    const grouped: Record<string, Offer[]> = {};
    const lowerQuery = searchQuery.toLowerCase().trim();
    let matches = 0;

    offers.forEach((offer) => {
      // 1. Filter logic
      if (lowerQuery) {
        const name = (offer.name || "").toLowerCase();
        const matchesName = name.includes(lowerQuery);

        // Advanced Filtering: Archetype, Format Hint & Delivery Model
        const archetypeLabel = (offer.archetype || "").toLowerCase();
        const formatLabel = (offer.format_hint || "").toLowerCase();
        const matchesArchetype =
          archetypeLabel.includes(lowerQuery) || formatLabel.includes(lowerQuery);

        const delivery = (offer.delivery_model || "").toLowerCase();
        const matchesDelivery = delivery.includes(lowerQuery);

        if (!matchesName && !matchesDelivery && !matchesArchetype) {
          return;
        }
      }

      matches++; // Count matches (or all if no query)

      // The adapter always resolves a concrete value_level, so this branch
      // only triggers for pathological data. Fall back to is_lead_magnet
      // rather than silently dumping unclassified offers into LEAD_MAGNET.
      const level =
        offer.value_level ||
        (offer.is_lead_magnet ? OfferValueLevel.LEAD_MAGNET : OfferValueLevel.ACTIVACION);
      if (!grouped[level]) grouped[level] = [];
      grouped[level].push(offer);
    });

    return { grouped, totalMatches: matches };
  }, [offers, searchQuery]);

  const { grouped: groupedOffers, totalMatches } = offersByLevel;

  const ladderCompleteness = useMemo(() => computeLadderCompleteness(offers), [offers]);

  useEffect(() => {
    if (onLadderComputed) {
      onLadderComputed(ladderCompleteness);
    }
  }, [ladderCompleteness, onLadderComputed]);

  const archiveOfferMutation = useArchiveOffer();

  const handleArchiveOffer = useCallback(
    (offerId: string) => {
      archiveOfferMutation.mutate(offerId);
    },
    [archiveOfferMutation],
  );

  const handleOpenCreate = useCallback((level?: OfferValueLevel) => {
    setPresetValueLevel(level);
    setIsWizardOpen(true);
  }, []);

  const handleCreateOffer = async (wizardData: WizardResult) => {
    setCreatingManual(true);
    try {
      const token = await getToken();
      if (!token) throw new Error("No authenticated");

      const newOffer = await offerApi.createOffer(toOfferCreatePayload(wizardData), token);

      if (newOffer.id) {
        setIsWizardOpen(false);
        navigate(`/${tenantId}/offer-studio/offer/${newOffer.id}`);
      }
    } catch (err) {
      console.error("Error creating offer:", err);
    } finally {
      setCreatingManual(false);
    }
  };

  // IA path: delegates create + openPanel + guided prompt + navigate to the
  // shared `useGuidedEntityCreation` hook. Same contract as buyer-persona.
  const handleCreateOfferWithIA = async (wizardData: WizardResult) => {
    setIsWizardOpen(false);
    await createOfferWithGuided(wizardData);
  };

  if (loading) {
    return (
      <div className="space-y-8">
        {[1, 2, 3].map((i) => (
          <div key={i} className="space-y-4">
            <Skeleton className="h-8 w-48" />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[1, 2, 3].map((j) => (
                <Skeleton key={j} className="h-[180px] w-full" />
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription className="flex items-center gap-4">
          {error}
          <Button variant="outline" size="sm" onClick={() => fetchOffers()}>
            Reintentar
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-8 pb-20">
      {/* Empty State for No Matches */}
      {searchQuery && totalMatches === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-center animate-in fade-in-50">
          <div className="h-20 w-20 bg-muted rounded-full flex items-center justify-center mb-6">
            <SearchX className="h-10 w-10 text-muted-foreground" />
          </div>
          <h3 className="text-xl font-semibold tracking-tight mb-2">
            No encontramos ofertas para &quot;{searchQuery}&quot;
          </h3>
          <p className="text-muted-foreground max-w-md mb-8">
            Intenta con otro término o crea una nueva oferta con este nombre.
          </p>
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              onClick={() => {
                handleOpenCreate();
              }}
            >
              <Plus className="mr-2 h-4 w-4" />
              Crear &quot;{searchQuery}&quot;
            </Button>
          </div>
        </div>
      )}

      {/* --- LEVEL 0: LEAD MAGNET STREAM (Horizontal) --- */}
      <LeadMagnetStream
        offers={groupedOffers[OfferValueLevel.LEAD_MAGNET] || []}
        searchQuery={searchQuery}
        onCreate={() => handleOpenCreate(OfferValueLevel.LEAD_MAGNET)}
        onArchive={handleArchiveOffer}
        onNavigate={(offerId) => navigate(`/${tenantId}/offer-studio/offer/${offerId}`)}
      />

      {/* --- LADDER LAYOUT (L1 - L6) --- */}
      <OfferLadderLayout
        groupedOffers={groupedOffers}
        searchQuery={searchQuery}
        onCreate={handleOpenCreate}
        onArchive={handleArchiveOffer}
      />

      {/* Create Wizard */}
      <CreateOfferWizard
        open={isWizardOpen}
        onOpenChange={setIsWizardOpen}
        onCreateOffer={handleCreateOffer}
        onCreateWithIA={handleCreateOfferWithIA}
        creating={creating}
        presetValueLevel={presetValueLevel}
      />
    </div>
  );
}

interface LeadMagnetStreamProps {
  readonly offers: readonly Offer[];
  readonly searchQuery: string;
  readonly onCreate: () => void;
  readonly onArchive: (offerId: string) => void;
  readonly onNavigate: (offerId: string) => void;
}

/** Horizontal "top of funnel" stream rendered above the 4-column ladder.
 *  Title, description and icon come from the ValueLevel catalog so the
 *  dashboard stays in lockstep with the domain SSoT. */
function LeadMagnetStream({
  offers,
  searchQuery,
  onCreate,
  onArchive,
  onNavigate,
}: LeadMagnetStreamProps) {
  const metadata = useValueLevelMetadata(OfferValueLevel.LEAD_MAGNET);
  const count = offers.length;

  if (searchQuery && count === 0) return null;

  const title = metadata?.label_es ?? "Lead Magnets";
  const description =
    metadata?.description_es ?? "Recursos gratuitos para convertir tráfico frío en leads.";
  const Icon = resolveIconByName(metadata?.icon_name);

  return (
    <section
      className="space-y-4 py-6 px-4 -mx-4 border-y border-dashed border-border/60 rounded-lg"
      style={{
        background: "linear-gradient(135deg, hsl(var(--muted) / 0.3), hsl(var(--primary) / 0.05))",
      }}
    >
      <div className="flex items-start gap-4 pl-2 border-l-4 border-primary/70">
        <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
          {/* eslint-disable-next-line react-hooks/static-components -- Icon is a stable reference resolved from the ValueLevel catalog, not a component created during render. */}
          <Icon className="h-6 w-6 text-primary" />
        </div>
        <div className="space-y-1 flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold tracking-tight text-foreground">{title}</h3>
            <Badge variant="secondary" className="bg-primary/10 text-primary hover:bg-primary/20">
              {count} Magnets
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              className="ml-auto h-6 text-xs text-muted-foreground hover:text-foreground"
              onClick={onCreate}
            >
              <Plus className="mr-1 h-3 w-3" /> Nuevo Magnet
            </Button>
          </div>
          <p className="text-sm text-muted-foreground/90 max-w-3xl">{description}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 px-2 py-1">
        {offers.map((offer) => (
          <LeadMagnetStreamCard
            key={offer.id}
            offer={offer}
            onClick={() => onNavigate(offer.id)}
            onArchive={onArchive}
          />
        ))}
        <div
          className="h-[80px] border-2 border-dashed border-muted-foreground/20 rounded-lg flex items-center justify-center gap-2 cursor-pointer hover:bg-muted/50 hover:border-primary/40 transition-colors group"
          onClick={onCreate}
        >
          <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center group-hover:bg-primary/10 transition-colors">
            <Plus className="h-4 w-4 text-muted-foreground group-hover:text-primary" />
          </div>
          <span className="text-sm font-medium text-muted-foreground group-hover:text-foreground">
            Crear Oferta
          </span>
        </div>
      </div>
    </section>
  );
}
