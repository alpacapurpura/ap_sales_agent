"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { useParams } from "next/navigation";
import { useNavigation } from "@/components/shared/navigation";
import { offerApi } from "@/features/offer-studio/api";
import { Offer, OfferValueLevel, OfferType, OfferStatus } from "@/features/offer-studio/types";
import { OfferCard } from "./offer-card";
import { AddOfferCard } from "./add-offer-card";
import { LeadMagnetStreamCard } from "./lead-magnet-stream-card";
import { EmptyLevelSlot } from "./empty-level-slot";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AlertCircle, Plus, Loader2, Lightbulb, Rocket, TrendingUp, Gem, Building, Building2, SearchX, X } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

import { OfferLegend } from "./offer-legend";

import { OfferLadderLayout } from "./offer-ladder-layout";

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

import { getOffersByLevel, OFFER_TYPE_METADATA } from "@/features/offer-studio/types/offer-metadata";

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

  // Dialog State
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedLevel, setSelectedLevel] = useState<OfferValueLevel | null>(null);
  const [selectedType, setSelectedType] = useState<OfferType | null>(null);
  const [newOfferName, setNewOfferName] = useState("");
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

  // Handle external trigger for creation (defaulting to N0 if no specific level is selected)
  useEffect(() => {
    if (externalCreateTrigger) {
      handleOpenCreate(OfferValueLevel.N0);
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
        
        // Advanced Filtering: Label & Delivery Model
        // Safe access to metadata with fallback
        const metadata = OFFER_TYPE_METADATA[offer.type];
        const typeLabel = metadata?.label?.toLowerCase() || "";
        const matchesLabel = typeLabel.includes(lowerQuery);
        
        const delivery = (offer.delivery_model || "").toLowerCase();
        const matchesDelivery = delivery.includes(lowerQuery);

        if (!matchesName && !matchesLabel && !matchesDelivery) {
          return; // Skip this offer
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

  const handleOpenCreate = (level: OfferValueLevel) => {
    setSelectedLevel(level);
    setSelectedType(null); // Reset selection
    setNewOfferName("");
    setIsDialogOpen(true);
  };

  const handleCreateOffer = async () => {
    if (!newOfferName.trim() || !selectedLevel) return;
    
    // Validate that a type is selected if we have options (which we always should now)
    // But for safety, fallback to default if logic fails, though UI should prevent it.
    
    setCreating(true);
    try {
      const token = await getToken();
      if (!token) throw new Error("No authenticated");

      // Default types map (Fallback only)
      const DEFAULT_TYPES: Record<string, OfferType> = {
        [OfferValueLevel.N0]: OfferType.FREE_RESOURCE,
        [OfferValueLevel.N1]: OfferType.TRIPWIRE_OFFER,
        [OfferValueLevel.N2]: OfferType.HYBRID_MENTORSHIP,
        [OfferValueLevel.N3]: OfferType.VIP_DAY_STRATEGY,
        [OfferValueLevel.N4]: OfferType.PRODUCTIZED_SERVICE,
        [OfferValueLevel.N5]: OfferType.MASTERMIND_NETWORK,
        [OfferValueLevel.N6]: OfferType.CORPORATE_TRAINING,
      };
      
      const typeToUse = selectedType || DEFAULT_TYPES[selectedLevel] || OfferType.FREE_RESOURCE;

      const newOffer = await offerApi.createOffer({
        public_name: newOfferName,
        type: typeToUse,
        status: OfferStatus.DRAFT,
        requires_application: true,
      } as Parameters<typeof offerApi.createOffer>[0], token);
      
      if (newOffer.id) {
        setIsDialogOpen(false);
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
                   // This assumes parent component controls state via props, but we can't clear parent state easily here 
                   // unless we added a onClear prop. For now, let's trigger creation.
                   // Actually, better UX is just to offer creation.
                   handleOpenCreate(OfferValueLevel.N0);
                   setNewOfferName(searchQuery);
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
                             onClick={() => handleOpenCreate(level)}
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
                     onClick={() => handleOpenCreate(level)}
                 >
                      <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center group-hover:bg-primary/10 transition-colors">
                         <Plus className="h-4 w-4 text-muted-foreground group-hover:text-primary" />
                      </div>
                      <span className="text-sm font-medium text-muted-foreground group-hover:text-foreground">Crear Lead Magnet</span>
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
      />

      {/* Create Modal */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Crear Oferta {selectedLevel}</DialogTitle>
            <DialogDescription>
              Selecciona el tipo de oferta y define su nombre para comenzar.
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid gap-6 py-4">
             {/* Type Selection */}
             <div className="space-y-3">
               <Label className="text-base font-medium">1. Selecciona el Tipo de Oferta</Label>
               <ScrollArea className="h-[300px] rounded-md border bg-muted/10 p-4">
                 <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                   {selectedLevel && getOffersByLevel(selectedLevel).map((def) => (
                     <div 
                        key={def.type}
                        onClick={() => setSelectedType(def.type)}
                        className={cn(
                          "cursor-pointer rounded-xl border p-4 transition-all hover:shadow-md relative overflow-hidden bg-background",
                          selectedType === def.type 
                            ? "border-primary ring-1 ring-primary shadow-sm" 
                            : "border-border hover:border-primary/50"
                        )}
                     >
                        {selectedType === def.type && (
                          <div className="absolute top-0 right-0 w-3 h-3 bg-primary rounded-bl-lg" />
                        )}
                        <div className="flex items-start justify-between mb-3 gap-2">
                           <span className="font-semibold text-sm leading-tight">{def.label}</span>
                           <Badge variant="secondary" className="text-[10px] shrink-0 font-mono">{def.delivery}</Badge>
                        </div>
                        <p className="text-xs text-muted-foreground mb-2">{def.description}</p>
                        <p className="text-[10px] text-primary/80 font-medium italic">&quot;{def.hint}&quot;</p>
                     </div>
                   ))}
                 </div>
               </ScrollArea>
             </div>

            <div className="space-y-3">
              <Label htmlFor="name" className="text-base font-medium">2. Nombre de la Oferta</Label>
              <Input
                id="name"
                value={newOfferName}
                onChange={(e) => setNewOfferName(e.target.value)}
                placeholder="Ej. Mi Nuevo Producto..."
                className="h-11"
              />
            </div>
          </div>
          <DialogFooter>
            <Button onClick={handleCreateOffer} disabled={creating || !selectedType || !newOfferName.trim()} size="lg">
              {creating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Crear Oferta
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
