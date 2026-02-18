import { Offer, OfferValueLevel } from "@/features/offer-studio/types";
import { OfferCard } from "./offer-card";
import { AddOfferCard } from "./add-offer-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Plus, Users, Star, Briefcase, Zap, Trophy, Building2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface OfferLadderLayoutProps {
  groupedOffers: Record<string, Offer[]>;
  searchQuery: string;
  onCreate: (level: OfferValueLevel) => void;
}

export function OfferLadderLayout({ groupedOffers, searchQuery, onCreate }: OfferLadderLayoutProps) {
  
  // Helper to render a level section within a column
  const renderLevelGroup = (level: OfferValueLevel, title: string, icon: any, colorClass: string) => {
    const offers = groupedOffers[level] || [];
    const Icon = icon;
    
    return (
      <div className="space-y-3 mb-6 last:mb-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
            <Icon className={cn("h-4 w-4", colorClass)} />
            <span>{title}</span>
          </div>
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-6 w-6" 
            onClick={() => onCreate(level)}
            title={`Crear oferta en ${title}`}
          >
            <Plus className="h-3 w-3" />
          </Button>
        </div>
        
        <div className="space-y-3">
          {offers.map(offer => (
            <OfferCard key={offer.id} offer={offer} searchQuery={searchQuery} compact />
          ))}
          <AddOfferCard level={level} onClick={() => onCreate(level)} compact />
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-12">
      
      {/* THE LADDER (B2C) - 3 Columns Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        
        {/* COLUMN 1: DO IT YOURSELF (L1) */}
        <div className="rounded-xl border bg-card/50 p-4 shadow-sm h-full flex flex-col">
          <div className="mb-6 pb-4 border-b">
            <div className="flex items-center gap-2 mb-1">
              <div className="p-2 rounded-md bg-blue-500/10 text-blue-500">
                <Zap className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-lg">Iniciación (DIY)</h3>
            </div>
            <p className="text-xs text-muted-foreground">Productos digitales y cursos que el cliente consume por su cuenta.</p>
          </div>
          
          <div className="flex-1">
            {renderLevelGroup(OfferValueLevel.N1, "Nivel 1: Low Ticket", Zap, "text-blue-500")}
          </div>
        </div>

        {/* COLUMN 2: TRANSFORMATION (L2 + L3) */}
        <div className="rounded-xl border bg-card/50 p-4 shadow-sm h-full flex flex-col relative overflow-hidden">
           {/* Visual Emphasis for Core Zone */}
           <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-violet-500 to-fuchsia-500 opacity-80" />
           
          <div className="mb-6 pb-4 border-b">
            <div className="flex items-center gap-2 mb-1">
              <div className="p-2 rounded-md bg-violet-500/10 text-violet-500">
                <Users className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-lg">Transformación</h3>
            </div>
            <p className="text-xs text-muted-foreground">Programas con acompañamiento y mentoría (Grupal o 1:1).</p>
          </div>
          
          <div className="flex-1 space-y-6">
            {renderLevelGroup(OfferValueLevel.N2, "Nivel 2: Grupal / Híbrido", Users, "text-violet-500")}
            <div className="h-px bg-border/50" />
            {renderLevelGroup(OfferValueLevel.N3, "Nivel 3: Exclusivo 1 a 1", Star, "text-fuchsia-500")}
          </div>
        </div>

        {/* COLUMN 3: HIGH END (L4 + L5) */}
        <div className="rounded-xl border bg-card/50 p-4 shadow-sm h-full flex flex-col">
          <div className="mb-6 pb-4 border-b">
            <div className="flex items-center gap-2 mb-1">
              <div className="p-2 rounded-md bg-amber-500/10 text-amber-500">
                <Trophy className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-lg">Alta Gama</h3>
            </div>
            <p className="text-xs text-muted-foreground">Soluciones &quot;Done For You&quot; y experiencias de estatus.</p>
          </div>
          
          <div className="flex-1 space-y-6">
            {renderLevelGroup(OfferValueLevel.N4, "Nivel 4: Servicios DFY", Briefcase, "text-amber-600")}
            <div className="h-px bg-border/50" />
            {renderLevelGroup(OfferValueLevel.N5, "Nivel 5: Mastermind / Legacy", Trophy, "text-amber-500")}
          </div>
        </div>

      </div>

      {/* CORPORATE ROW (L6) */}
      <div className="rounded-xl border bg-slate-900 text-slate-50 p-6 shadow-md">
        <div className="flex flex-col md:flex-row gap-8 items-start">
            <div className="md:w-1/4 space-y-2">
                <div className="flex items-center gap-2 mb-2">
                    <Building2 className="h-6 w-6 text-slate-300" />
                    <h3 className="font-semibold text-xl">Corporativo</h3>
                </div>
                <p className="text-sm text-slate-400">
                    Soluciones B2B para empresas y grandes organizaciones.
                </p>
                <Button 
                    variant="secondary" 
                    size="sm" 
                    className="w-full mt-4"
                    onClick={() => onCreate(OfferValueLevel.N6)}
                >
                    <Plus className="mr-2 h-3 w-3" /> Añadir Servicio B2B
                </Button>
            </div>

            <div className="flex-1 w-full">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {groupedOffers[OfferValueLevel.N6]?.map(offer => (
                        <OfferCard key={offer.id} offer={offer} searchQuery={searchQuery} compact className="bg-slate-800 border-slate-700 text-slate-100 hover:bg-slate-700 transition-colors" />
                    ))}
                     {(!groupedOffers[OfferValueLevel.N6] || groupedOffers[OfferValueLevel.N6].length === 0) && (
                        <div className="col-span-full py-8 text-center border border-dashed border-slate-700 rounded-lg text-slate-500 text-sm">
                            No hay servicios corporativos activos.
                        </div>
                    )}
                </div>
            </div>
        </div>
      </div>

    </div>
  );
}
