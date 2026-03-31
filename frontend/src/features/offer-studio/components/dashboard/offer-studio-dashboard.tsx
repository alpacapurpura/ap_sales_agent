"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { useParams } from "next/navigation";
import { useNavigation } from "@/components/shared/navigation";
import { offerApi } from "@/features/offer-studio/api";
import { Offer, OfferArchetype, OfferValueLevel, OfferStatus } from "@/features/offer-studio/types";
import { OfferCard } from "./offer-card";
import { AddOfferCard } from "./add-offer-card";
import { LeadMagnetStreamCard } from "./lead-magnet-stream-card";
import { EmptyLevelSlot } from "./empty-level-slot";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AlertCircle, Plus, Lightbulb, Rocket, TrendingUp, Gem, Building2, SearchX } from "lucide-react";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

import { OfferLegend } from "./offer-legend";
import { OfferLadderLayout } from "./offer-ladder-layout";
import { LadderProgressBar } from "./ladder-progress-bar";
import { CreateOfferWizard, WizardResult } from "../wizard/CreateOfferWizard";
import { computeLadderCompleteness } from "@/features/offer-studio/utils/ladder-completeness";

// Helper to sort levels correctly
const LEVEL_ORDER = [
  OfferValueLevel.LEAD_MAGNET,
  OfferValueLevel.ACTIVACION,
  OfferValueLevel.TRANSFORMACION,
  OfferValueLevel.MAXIMIZACION,
  OfferValueLevel.CORPORATIVO,
];

const LEVEL_RICH_INFO: Record<string, { title: string; description: string; icon: any }> = {
  [OfferValueLevel.LEAD_MAGNET]: {
    title: "Lead Magnets",
    description: "Recursos gratuitos para convertir trafico frio en leads. Ej: Ebooks, Webinars, Plantillas.",
    icon: Lightbulb
  },
  [OfferValueLevel.ACTIVACION]: {
    title: "Activacion",
    description: "Primera compra, bajo riesgo. Ej: Tripwires, Cursos Auto-dirigidos, Mini-cursos.",
    icon: Rocket
  },
  [OfferValueLevel.TRANSFORMACION]: {
    title: "Transformacion",
    description: "Oferta principal — transformacion real. Ej: Mentorias, Cohortes, Bootcamps.",
    icon: TrendingUp
  },
  [OfferValueLevel.MAXIMIZACION]: {
    title: "Maximizacion",
    description: "Premium, alto contacto. Ej: VIP Days, Mentorias 1:1, Masterminds.",
    icon: Gem
  },
  [OfferValueLevel.CORPORATIVO]: {
    title: "Corporativo",
    description: "Ventas B2B a grandes empresas. Ej: Capacitaciones corporativas, Patrocinios.",
    icon: Building2
  }
};

interface OfferStudioDashboardProps {
  searchQuery?: string;
  externalCreateTrigger?: boolean;
  onCreateTriggerHandled?: () => void;
}

export function OfferStudioDashboard({ 
  searchQuery = "", 
  externalCreateTrigger = false, 
  onCreateTriggerHandled 
}: OfferStudioDashboardProps) {
  const { getToken } = useAuth();
  const { navigate } = useNavigation();
  const params = useParams();
  const tenantId = params?.tenantId as string;
  
  const [offers, setOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Wizard State
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [creating, setCreating] = useState(false);

  const fetchOffers = useCallback(async () => {
    try {
      setLoading(true);
      const token = await getToken();
      if (!token) return;
      
      const data = await offerApi.listOffers(token);
      setOffers(data);
      setError(null);
    } catch (err) {
      console.error("Error fetching offers:", err);
      setError("No se pudieron cargar las ofertas.");
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    fetchOffers();
  }, [fetchOffers]);

  // Handle external trigger for creation
  useEffect(() => {
    if (externalCreateTrigger) {
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

    offers.forEach(offer => {
      // 1. Filter logic
      if (lowerQuery) {
        const name = (offer.name || "").toLowerCase();
        const matchesName = name.includes(lowerQuery);
        
        // Advanced Filtering: Archetype, Format Hint & Delivery Model
        const archetypeLabel = (offer.archetype || "").toLowerCase();
        const formatLabel = (offer.format_hint || "").toLowerCase();
        const matchesArchetype = archetypeLabel.includes(lowerQuery) || formatLabel.includes(lowerQuery);

        const delivery = (offer.delivery_model || "").toLowerCase();
        const matchesDelivery = delivery.includes(lowerQuery);

        if (!matchesName && !matchesDelivery && !matchesArchetype) {
          return;
        }
      }

      matches++; // Count matches (or all if no query)

      let level = offer.value_level;
      level = level || OfferValueLevel.LEAD_MAGNET;
      if (!grouped[level]) grouped[level] = [];
      grouped[level].push(offer);
    });
    
    return { grouped, totalMatches: matches };
  }, [offers, searchQuery]);

  const { grouped: groupedOffers, totalMatches } = offersByLevel;

  const ladderCompleteness = useMemo(() => computeLadderCompleteness(offers), [offers]);

  const handleArchiveOffer = useCallback(async (offerId: string) => {
    try {
      const token = await getToken();
      if (!token) return;
      await offerApi.saveOffer(offerId, { status: "archived" } as any, token);
      await fetchOffers();
    } catch (err) {
      console.error("Error archiving offer:", err);
    }
  }, [getToken, fetchOffers]);

  const handleOpenCreate = (_level?: OfferValueLevel) => {
    setIsWizardOpen(true);
  };

  const handleCreateOffer = async (wizardData: WizardResult) => {
    setCreating(true);
    try {
      const token = await getToken();
      if (!token) throw new Error("No authenticated");

      const newOffer = await offerApi.createOffer({
        public_name: wizardData.name,
        archetype: wizardData.archetype,
        format_hint: wizardData.format_hint,
        is_lead_magnet: wizardData.is_lead_magnet,
        headline_promise: wizardData.headline_promise,
        status: wizardData.status,
        delivery_model: wizardData.delivery_model,
        offer_value_level: wizardData.value_level,
        specific_details: wizardData.specific_details,
      } as any, token);

      if (newOffer.id) {
        setIsWizardOpen(false);
        navigate(`/${tenantId}/offer-studio/offer/${newOffer.id}`);
      }
    } catch (err) {
      console.error("Error creating offer:", err);
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-8">
        {[1, 2, 3].map((i) => (
          <div key={i} className="space-y-4">
             <Skeleton className="h-8 w-48" />
             <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
               {[1, 2, 3].map((j) => <Skeleton key={j} className="h-[180px] w-full" />)}
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
          <Button variant="outline" size="sm" onClick={fetchOffers}>Reintentar</Button>
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-10 pb-20">
      {/* Global Legend - Always Visible */}
      <OfferLegend />

      {/* Ladder Progress Bar */}
      {!searchQuery && (
        <LadderProgressBar
          filledGroups={ladderCompleteness.filledGroups}
          score={ladderCompleteness.score}
          percentage={ladderCompleteness.percentage}
        />
      )}
      
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
      {(() => {
        const level = OfferValueLevel.LEAD_MAGNET;
        const levelOffers = groupedOffers[level] || [];
        const count = levelOffers.length;
        const info = LEVEL_RICH_INFO[level];
        const Icon = info.icon;

        if (searchQuery && count === 0) return null;

        return (
          <section className="space-y-4 py-6 px-4 -mx-4 bg-muted/30 border-y border-dashed border-border/60">
             <div className="flex items-start gap-4 pl-2 border-l-4 border-primary/70">
                 <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                     <Icon className="h-6 w-6 text-primary" />
                 </div>
                 <div className="space-y-1 flex-1">
                     <div className="flex items-center gap-2">
                         <h3 className="text-lg font-semibold tracking-tight text-foreground">{info.title}</h3>
                         <Badge variant="secondary" className="bg-primary/10 text-primary hover:bg-primary/20">{count} Magnets</Badge>
                          <Button
                             variant="ghost"
                             size="sm"
                             className="ml-auto h-6 text-xs text-muted-foreground hover:text-foreground"
                             onClick={() => handleOpenCreate()}
                         >
                             <Plus className="mr-1 h-3 w-3" /> Nuevo Magnet
                         </Button>
                     </div>
                     <p className="text-sm text-muted-foreground/90 max-w-3xl">{info.description}</p>
                 </div>
             </div>

             <ScrollArea className="w-full whitespace-nowrap rounded-md pb-2">
               <div className="grid grid-rows-2 grid-flow-col gap-3 w-max px-2 py-1">
                 {levelOffers.map((offer) => (
                   <div key={offer.id} className="w-[280px]">
                     <LeadMagnetStreamCard offer={offer} onClick={() => navigate(`/${tenantId}/offer-studio/offer/${offer.id}`)} />
                   </div>
                 ))}
                 
                 {/* Add Button Slot in the Grid */}
                 <div 
                     className="w-[280px] h-[72px] border-2 border-dashed border-muted-foreground/20 rounded-lg flex items-center justify-center gap-2 cursor-pointer hover:bg-muted/50 hover:border-primary/40 transition-colors group"
                     onClick={() => handleOpenCreate()}
                 >
                      <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center group-hover:bg-primary/10 transition-colors">
                         <Plus className="h-4 w-4 text-muted-foreground group-hover:text-primary" />
                      </div>
                      <span className="text-sm font-medium text-muted-foreground group-hover:text-foreground">Crear Oferta</span>
                 </div>
               </div>
               <ScrollBar orientation="horizontal" />
             </ScrollArea>
          </section>
        );
      })()}

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
        creating={creating}
      />
    </div>
  );
}
