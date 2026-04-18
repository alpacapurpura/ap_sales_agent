import { Plus, Zap, Users, Trophy, Building2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useValueLevelMetadata } from "@/features/offer-studio/hooks/use-value-level-catalog";
import { OfferValueLevel } from "@/features/offer-studio/types";

import { AddOfferCard } from "./AddOfferCard";
import { OfferCatalogCard } from "./OfferCatalogCard";

import type { Offer } from "@/features/offer-studio/types";
import type { LucideIcon } from "lucide-react";

interface OfferLadderLayoutProps {
  groupedOffers: Record<string, Offer[]>;
  searchQuery: string;
  onCreate: (level: OfferValueLevel) => void;
  onArchive?: (offerId: string) => void;
}

// Presentation tokens kept locally — the catalog owns language (label +
// description) while the dashboard owns the column aesthetics (accent
// color per rung + which Lucide glyph sits next to the title).
interface ColumnTokens {
  icon: LucideIcon;
  iconBg: string;
  iconFg: string;
}

const COLUMN_TOKENS: Record<OfferValueLevel, ColumnTokens> = {
  [OfferValueLevel.LEAD_MAGNET]: { icon: Zap, iconBg: "bg-primary/10", iconFg: "text-primary" },
  [OfferValueLevel.ACTIVACION]: {
    icon: Zap,
    iconBg: "bg-blue-500/10",
    iconFg: "text-blue-500",
  },
  [OfferValueLevel.TRANSFORMACION]: {
    icon: Users,
    iconBg: "bg-violet-500/10",
    iconFg: "text-violet-500",
  },
  [OfferValueLevel.MAXIMIZACION]: {
    icon: Trophy,
    iconBg: "bg-amber-500/10",
    iconFg: "text-amber-500",
  },
  [OfferValueLevel.CORPORATIVO]: {
    icon: Building2,
    iconBg: "bg-slate-700/40",
    iconFg: "text-slate-300",
  },
};

/**
 *
 */
export function OfferLadderLayout({
  groupedOffers,
  searchQuery,
  onCreate,
  onArchive,
}: OfferLadderLayoutProps) {
  const renderLevelGroup = (level: OfferValueLevel) => {
    const offers = groupedOffers[level] || [];

    return (
      <div className="space-y-3">
        {offers.map((offer) => (
          <OfferCatalogCard
            key={offer.id}
            offer={offer}
            searchQuery={searchQuery}
            compact
            onArchive={onArchive}
          />
        ))}
        <AddOfferCard level={level} onClick={() => onCreate(level)} compact />
      </div>
    );
  };

  return (
    <div className="space-y-12">
      {/* THE LADDER - 3 Columns Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        <LadderColumn
          level={OfferValueLevel.ACTIVACION}
          onCreate={onCreate}
          renderOffers={renderLevelGroup}
        />
        <LadderColumn
          level={OfferValueLevel.TRANSFORMACION}
          onCreate={onCreate}
          renderOffers={renderLevelGroup}
          withGradientAccent
        />
        <LadderColumn
          level={OfferValueLevel.MAXIMIZACION}
          onCreate={onCreate}
          renderOffers={renderLevelGroup}
        />
      </div>

      {/* CORPORATE ROW */}
      <CorporateRow
        offers={groupedOffers[OfferValueLevel.CORPORATIVO] || []}
        searchQuery={searchQuery}
        onCreate={() => onCreate(OfferValueLevel.CORPORATIVO)}
        onArchive={onArchive}
      />
    </div>
  );
}

interface LadderColumnProps {
  level: OfferValueLevel;
  onCreate: (level: OfferValueLevel) => void;
  renderOffers: (level: OfferValueLevel) => React.ReactNode;
  withGradientAccent?: boolean;
}

/** One column of the 3-column ladder. Reads label + description from the
 *  ValueLevel catalog; keeps local icon + color tokens for visual rhythm. */
function LadderColumn({
  level,
  onCreate,
  renderOffers,
  withGradientAccent = false,
}: LadderColumnProps) {
  const metadata = useValueLevelMetadata(level);
  const tokens = COLUMN_TOKENS[level];
  const Icon = tokens.icon;
  const label = metadata?.label_es ?? "";
  const description = metadata?.description_es ?? "";

  return (
    <div className="rounded-xl border bg-card/50 p-4 shadow-sm h-full flex flex-col relative overflow-hidden">
      {withGradientAccent && (
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-violet-500 to-fuchsia-500 opacity-80" />
      )}
      <div className="mb-6 pb-4 border-b">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2 mb-1">
            <div className={`p-2 rounded-md ${tokens.iconBg} ${tokens.iconFg}`}>
              <Icon className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-lg">{label}</h3>
          </div>
          <Button
            variant="outline"
            size="icon"
            className="h-7 w-7 rounded-md border border-border"
            onClick={() => onCreate(level)}
            title={`Crear oferta en ${label}`}
          >
            <Plus className="h-3.5 w-3.5" />
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
      <div className="flex-1">{renderOffers(level)}</div>
    </div>
  );
}

interface CorporateRowProps {
  offers: Offer[];
  searchQuery: string;
  onCreate: () => void;
  onArchive?: (offerId: string) => void;
}

/** CORPORATIVO rung stays visually distinct (dark theme) — label and
 *  description still come from the catalog. */
function CorporateRow({ offers, searchQuery, onCreate, onArchive }: CorporateRowProps) {
  const metadata = useValueLevelMetadata(OfferValueLevel.CORPORATIVO);
  const label = metadata?.label_es ?? "Venta Corporativa";
  const description = metadata?.description_es ?? "Soluciones B2B para empresas.";

  return (
    <div className="rounded-xl border bg-slate-900 text-slate-50 p-6 shadow-md">
      <div className="flex flex-col md:flex-row gap-8 items-start">
        <div className="md:w-1/4 space-y-2">
          <div className="flex items-center gap-2 mb-2">
            <Building2 className="h-6 w-6 text-slate-300" />
            <h3 className="font-semibold text-xl">{label}</h3>
          </div>
          <p className="text-sm text-slate-400">{description}</p>
          <Button variant="secondary" size="sm" className="w-full mt-4" onClick={onCreate}>
            <Plus className="mr-2 h-3 w-3" /> Añadir Servicio B2B
          </Button>
        </div>

        <div className="flex-1 w-full">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {offers.map((offer) => (
              <OfferCatalogCard
                key={offer.id}
                offer={offer}
                searchQuery={searchQuery}
                compact
                onArchive={onArchive}
                className="bg-slate-800 border-slate-700 text-slate-100 hover:bg-slate-700 transition-colors"
              />
            ))}
            {offers.length === 0 && (
              <div className="col-span-full py-8 text-center border border-dashed border-slate-700 rounded-lg text-slate-500 text-sm">
                No hay servicios corporativos activos.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
