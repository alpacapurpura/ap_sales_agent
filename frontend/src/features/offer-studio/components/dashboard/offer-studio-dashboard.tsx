"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { useParams } from "next/navigation";
import { useNavigation } from "@/components/shared/navigation";
import { offerApi } from "@/features/offer-studio/api";
import { Offer, OfferArchetype, OfferValueLevel, OfferType, OfferStatus } from "@/features/offer-studio/types";
import { OfferCard } from "./offer-card";
import { AddOfferCard } from "./add-offer-card";
import { LeadMagnetStreamCard } from "./lead-magnet-stream-card";
import { EmptyLevelSlot } from "./empty-level-slot";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AlertCircle, Plus, Lightbulb, Rocket, TrendingUp, Gem, Building, Building2, SearchX } from "lucide-react";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

import { OfferLegend } from "./offer-legend";
import { OfferLadderLayout } from "./offer-ladder-layout";
import { CreateOfferWizard, WizardResult } from "../wizard/CreateOfferWizard";

// Helper to sort levels correctly
const LEVEL_ORDER = [
  OfferValueLevel.N0,
  OfferValueLevel.N1,
  OfferValueLevel.N2,
  OfferValueLevel.N3,
  OfferValueLevel.N4,
  OfferValueLevel.N5,
  OfferValueLevel.N6,
];

const LEVEL_RICH_INFO: Record<string, { title: string; description: string; icon: any }> = {
  [OfferValueLevel.N0]: {
    title: "Adquisición (Nivel 0)",
    description: "Offers pensados en convertir tráfico frío en leads (Lead Magnets). Ej: Ebooks, Webinars gratuitos, Plantillas.",
    icon: Lightbulb
  },
  [OfferValueLevel.N1]: {
    title: "Activación (Nivel 1)",
    description: "Offers pensados en convertir leads en clientes con bajo riesgo. Ej: Tripwires, Cursos Auto-dirigidos, Newsletters pagas.",
    icon: Rocket
  },
  [OfferValueLevel.N2]: {
    title: "Escalabilidad (Nivel 2)",
    description: "Offers pensados para escalar y entregar resultados sin depender 100% de tu tiempo. Ej: Mentorías Híbridas, Cursos por Cohortes.",
    icon: TrendingUp
  },
  [OfferValueLevel.N3]: {
    title: "Profit Maximizer (Nivel 3)",
    description: "Offers High Ticket para clientes que buscan mayor velocidad y soporte. Ej: VIP Days, Mentorías 1:1, Auditorías.",
    icon: Gem
  },
  [OfferValueLevel.N4]: {
    title: "Delegación (Nivel 4)",
    description: "Servicios 'Done For You' donde ejecutas por el cliente. Ej: Retainers mensuales, Agencias de servicios.",
    icon: Building
  },
  [OfferValueLevel.N5]: {
    title: "Legado (Nivel 5)",
    description: "Experiencias exclusivas de alto estatus. Ej: Masterminds, Retiros de lujo.",
    icon: Building2
  },
  [OfferValueLevel.N6]: {
    title: "Corporativo (Nivel 6)",
    description: "Ventas B2B a grandes empresas. Ej: Capacitaciones corporativas, Patrocinios.",
    icon: Building2
  }
};

const TYPE_TO_LEVEL_MAP: Record<string, OfferValueLevel> = {
  [OfferType.FREE_RESOURCE]: OfferValueLevel.N0,
  [OfferType.COMMUNITY_LITE]: OfferValueLevel.N0,
  [OfferType.CONTENT_ASSET_PODCAST]: OfferValueLevel.N0,
  [OfferType.FREE_WEBINAR_CHALLENGE]: OfferValueLevel.N0,
  
  [OfferType.TRIPWIRE_OFFER]: OfferValueLevel.N1,
  [OfferType.SELF_PACED_COURSE]: OfferValueLevel.N1,
  [OfferType.PAID_NEWSLETTER_SUBSCRIPTION]: OfferValueLevel.N1,
  
  [OfferType.HYBRID_MENTORSHIP]: OfferValueLevel.N2,
  [OfferType.COHORT_BASED_COURSE]: OfferValueLevel.N2,
  [OfferType.GROUP_COACHING_PROGRAM]: OfferValueLevel.N2,
  
  [OfferType.VIP_DAY_STRATEGY]: OfferValueLevel.N3,
  [OfferType.ONE_ON_ONE_PRIVATE_MENTORING]: OfferValueLevel.N3,
  [OfferType.DEEP_DIVE_AUDIT]: OfferValueLevel.N3,
  
  [OfferType.PRODUCTIZED_SERVICE]: OfferValueLevel.N4,
  [OfferType.MONTHLY_RETAINER]: OfferValueLevel.N4,
  [OfferType.PERFORMANCE_REV_SHARE]: OfferValueLevel.N4,
  
  [OfferType.MASTERMIND_NETWORK]: OfferValueLevel.N5,
  [OfferType.LUXURY_RETREAT]: OfferValueLevel.N5,
  
  [OfferType.CORPORATE_TRAINING]: OfferValueLevel.N6,
  [OfferType.BRAND_SPONSORSHIP]: OfferValueLevel.N6,
  [OfferType.KEYNOTE_SPEAKING]: OfferValueLevel.N6,
};

import { OFFER_TYPE_METADATA } from "@/features/offer-studio/types/offer-metadata";

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
        
        // Advanced Filtering: Label, Archetype, Format Hint & Delivery Model
        const metadata = OFFER_TYPE_METADATA[offer.type];
        const typeLabel = metadata?.label?.toLowerCase() || "";
        const matchesLabel = typeLabel.includes(lowerQuery);

        const delivery = (offer.delivery_model || "").toLowerCase();
        const matchesDelivery = delivery.includes(lowerQuery);

        const archetypeLabel = (offer.archetype || "").toLowerCase();
        const formatLabel = (offer.format_hint || "").toLowerCase();
        const matchesArchetype = archetypeLabel.includes(lowerQuery) || formatLabel.includes(lowerQuery);

        if (!matchesName && !matchesLabel && !matchesDelivery && !matchesArchetype) {
          return;
        }
      }

      matches++; // Count matches (or all if no query)

      let level = offer.value_level;
      
      // Fallback logic...
      if ((!level || level === OfferValueLevel.N0) && offer.type && TYPE_TO_LEVEL_MAP[offer.type]) {
          const inferred = TYPE_TO_LEVEL_MAP[offer.type];
          if (inferred !== OfferValueLevel.N0) {
             level = inferred; 
          }
      }

      level = level || OfferValueLevel.N0;
      if (!grouped[level]) grouped[level] = [];
      grouped[level].push(offer);
    });
    
    return { grouped, totalMatches: matches };
  }, [offers, searchQuery]);

  const { grouped: groupedOffers, totalMatches } = offersByLevel;

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
        const level = OfferValueLevel.N0;
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
