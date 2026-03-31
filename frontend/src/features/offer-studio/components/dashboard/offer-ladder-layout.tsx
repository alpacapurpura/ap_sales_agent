import { Offer, OfferValueLevel } from "@/features/offer-studio/types";
import { OfferCard } from "./offer-card";
import { AddOfferCard } from "./add-offer-card";
import { Button } from "@/components/ui/button";
import { Plus, Zap, Users, Trophy, Building2 } from "lucide-react";

interface OfferLadderLayoutProps {
  groupedOffers: Record<string, Offer[]>;
  searchQuery: string;
  onCreate: (level: OfferValueLevel) => void;
  onArchive?: (offerId: string) => void;
}

export function OfferLadderLayout({ groupedOffers, searchQuery, onCreate, onArchive }: OfferLadderLayoutProps) {

  const renderLevelGroup = (level: OfferValueLevel) => {
    const offers = groupedOffers[level] || [];

    return (
      <div className="space-y-3">
        {offers.map(offer => (
          <OfferCard key={offer.id} offer={offer} searchQuery={searchQuery} compact onArchive={onArchive} />
        ))}
        <AddOfferCard level={level} onClick={() => onCreate(level)} compact />
      </div>
    );
  };

  return (
    <div className="space-y-12">

      {/* THE LADDER - 3 Columns Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">

        {/* COLUMN 1: Activacion */}
        <div className="rounded-xl border bg-card/50 p-4 shadow-sm h-full flex flex-col">
          <div className="mb-6 pb-4 border-b">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2 mb-1">
                <div className="p-2 rounded-md bg-blue-500/10 text-blue-500">
                  <Zap className="h-5 w-5" />
                </div>
                <h3 className="font-semibold text-lg">Activacion</h3>
              </div>
              <Button
                variant="outline"
                size="icon"
                className="h-7 w-7 rounded-md border border-border"
                onClick={() => onCreate(OfferValueLevel.ACTIVACION)}
                title="Crear oferta en Activacion"
              >
                <Plus className="h-3.5 w-3.5" />
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">Primera compra, bajo riesgo. Convierte leads en clientes.</p>
          </div>

          <div className="flex-1">
            {renderLevelGroup(OfferValueLevel.ACTIVACION)}
          </div>
        </div>

        {/* COLUMN 2: Transformacion */}
        <div className="rounded-xl border bg-card/50 p-4 shadow-sm h-full flex flex-col relative overflow-hidden">
           <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-violet-500 to-fuchsia-500 opacity-80" />

          <div className="mb-6 pb-4 border-b">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2 mb-1">
                <div className="p-2 rounded-md bg-violet-500/10 text-violet-500">
                  <Users className="h-5 w-5" />
                </div>
                <h3 className="font-semibold text-lg">Transformacion</h3>
              </div>
              <Button
                variant="outline"
                size="icon"
                className="h-7 w-7 rounded-md border border-border"
                onClick={() => onCreate(OfferValueLevel.TRANSFORMACION)}
                title="Crear oferta en Transformacion"
              >
                <Plus className="h-3.5 w-3.5" />
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">Oferta principal, transformacion real. Core offer escalable.</p>
          </div>

          <div className="flex-1">
            {renderLevelGroup(OfferValueLevel.TRANSFORMACION)}
          </div>
        </div>

        {/* COLUMN 3: Maximizacion */}
        <div className="rounded-xl border bg-card/50 p-4 shadow-sm h-full flex flex-col">
          <div className="mb-6 pb-4 border-b">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2 mb-1">
                <div className="p-2 rounded-md bg-amber-500/10 text-amber-500">
                  <Trophy className="h-5 w-5" />
                </div>
                <h3 className="font-semibold text-lg">Maximizacion</h3>
              </div>
              <Button
                variant="outline"
                size="icon"
                className="h-7 w-7 rounded-md border border-border"
                onClick={() => onCreate(OfferValueLevel.MAXIMIZACION)}
                title="Crear oferta en Maximizacion"
              >
                <Plus className="h-3.5 w-3.5" />
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">Premium, alto contacto, maximo LTV.</p>
          </div>

          <div className="flex-1">
            {renderLevelGroup(OfferValueLevel.MAXIMIZACION)}
          </div>
        </div>

      </div>

      {/* CORPORATE ROW */}
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
                    onClick={() => onCreate(OfferValueLevel.CORPORATIVO)}
                >
                    <Plus className="mr-2 h-3 w-3" /> Anadir Servicio B2B
                </Button>
            </div>

            <div className="flex-1 w-full">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {groupedOffers[OfferValueLevel.CORPORATIVO]?.map(offer => (
                        <OfferCard key={offer.id} offer={offer} searchQuery={searchQuery} compact onArchive={onArchive} className="bg-slate-800 border-slate-700 text-slate-100 hover:bg-slate-700 transition-colors" />
                    ))}
                     {(!groupedOffers[OfferValueLevel.CORPORATIVO] || groupedOffers[OfferValueLevel.CORPORATIVO].length === 0) && (
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
