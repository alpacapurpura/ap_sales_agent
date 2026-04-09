"use client";

import { memo } from "react";
import { Offer, OfferArchetype, OfferDeliveryModel, OfferStatus, OfferValueLevel } from "@/features/offer-studio/types";
import { ARCHETYPE_METADATA } from "@/features/offer-studio/config/archetype-metadata";
import { HighlightedText } from "@/components/ui/highlighted-text";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  MoreHorizontal,
  Users,
  CreditCard,
  Clock,
  Package,
  Zap,
  Gem,
  Building2,
  Sparkles,
  ExternalLink
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useParams } from "next/navigation";
import { useNavigation } from "@/components/shared/navigation";
import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";

interface OfferCardProps {
  offer: Offer;
  searchQuery?: string;
  compact?: boolean;
  className?: string;
  onArchive?: (offerId: string) => void;
}

const DELIVERY_COLORS = {
  [OfferDeliveryModel.DIY]: "border-emerald-500",
  [OfferDeliveryModel.DWY]: "border-blue-500",
  [OfferDeliveryModel.DFY]: "border-purple-600",
  [OfferDeliveryModel.HYBRID]: "border-yellow-500",
};

const STATUS_CONFIG = {
  [OfferStatus.ACTIVE]: { color: "bg-green-500", label: "Active" },
  [OfferStatus.PAUSED]: { color: "bg-amber-500", label: "Paused" },
  [OfferStatus.WAITLIST]: { color: "bg-orange-500", label: "Waitlist" },
  [OfferStatus.SOLD_OUT]: { color: "bg-red-500", label: "Closed" },
  [OfferStatus.DRAFT]: { color: "bg-gray-400", label: "Draft" },
  [OfferStatus.ARCHIVED]: { color: "bg-gray-600", label: "Archived" },
};

const LEVEL_ICONS: Record<string, any> = {
  [OfferValueLevel.LEAD_MAGNET]: Package,
  [OfferValueLevel.ACTIVACION]: Zap,
  [OfferValueLevel.TRANSFORMACION]: Users,
  [OfferValueLevel.MAXIMIZACION]: Gem,
  [OfferValueLevel.CORPORATIVO]: Building2,
};

const DELIVERY_BADGES = {
  [OfferDeliveryModel.DIY]: { label: "DIY", color: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20" },
  [OfferDeliveryModel.DWY]: { label: "DWY", color: "bg-blue-500/10 text-blue-600 border-blue-500/20" },
  [OfferDeliveryModel.DFY]: { label: "DFY", color: "bg-purple-600/10 text-purple-600 border-purple-600/20" },
  [OfferDeliveryModel.HYBRID]: { label: "Hybrid", color: "bg-yellow-500/10 text-yellow-600 border-yellow-500/20" },
};

export const OfferCard = memo(function OfferCard({ offer, searchQuery = "", compact = false, className, onArchive }: OfferCardProps) {
  const { navigate, isNavigating } = useNavigation();
  const params = useParams();
  const tenantId = params?.tenantId as string;
  const { currency: tenantCurrency } = useTenantLocale();

  const borderColor = DELIVERY_COLORS[offer.delivery_model] || "border-gray-200";
  const badgeConfig = DELIVERY_BADGES[offer.delivery_model] || DELIVERY_BADGES[OfferDeliveryModel.DIY];
  const statusConfig = STATUS_CONFIG[offer.status] || STATUS_CONFIG[OfferStatus.DRAFT];
  const Icon = LEVEL_ICONS[offer.value_level] || Package;

  const archetypeMeta = offer.archetype ? ARCHETYPE_METADATA[offer.archetype as OfferArchetype] : null;
  const typeLabel = archetypeMeta
    ? (offer.format_hint ? `${archetypeMeta.label} - ${offer.format_hint}` : archetypeMeta.label)
    : "Oferta";

  // Calculate Price Display
  const priceDisplay = offer.pricing && offer.pricing.length > 0
    ? new Intl.NumberFormat('en-US', { style: 'currency', currency: offer.currency || tenantCurrency }).format(offer.pricing[0].total_amount)
    : "Free";

  const handleClick = (e: React.MouseEvent) => {
    // Prevent navigation if clicking inside dropdown or buttons
    if ((e.target as HTMLElement).closest('[role="menuitem"]') || (e.target as HTMLElement).closest('button')) {
      return;
    }
    navigate(`/${tenantId}/offer-studio/offer/${offer.id}`);
  };

  return (
    <Card 
      className={cn(
        "group relative w-full overflow-hidden transition-all duration-200 hover:shadow-md hover:scale-[1.01] cursor-pointer border-t-4 bg-background",
        isNavigating && "opacity-60 pointer-events-none",
        compact ? "h-auto min-h-[140px]" : "h-[180px]",
        borderColor,
        className
      )}
      onClick={handleClick}
    >
      <div className={cn("flex flex-col h-full justify-between", compact ? "p-3" : "p-4")}>
        {/* Header */}
        <div className="flex justify-between items-start">
          <div className={cn("rounded bg-muted flex items-center justify-center text-muted-foreground", compact ? "h-6 w-6" : "h-8 w-8")}>
             <Icon className={cn(compact ? "h-3 w-3" : "h-4 w-4")} />
          </div>
          
          <div className="flex items-center gap-2">
             <div 
               className={cn("w-2 h-2 rounded-full", statusConfig.color)} 
               title={statusConfig.label}
             />
             
             <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity -mr-2">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => navigate(`/${tenantId}/offer-studio/offer/${offer.id}`)}>
                  Editar
                </DropdownMenuItem>
                {offer.landing_page_config?.is_published && (
                    <DropdownMenuItem onClick={() => window.open(`/p/${offer.landing_page_config?.slug}`, '_blank')}>
                      <ExternalLink className="mr-2 h-4 w-4" />
                      Ver Landing Page
                    </DropdownMenuItem>
                )}
                <DropdownMenuItem>Duplicar</DropdownMenuItem>
                <DropdownMenuItem className="text-destructive" onClick={() => onArchive?.(offer.id)}>Archivar</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Body */}
        <div className="space-y-1">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="outline" className={cn("text-[10px] h-5 px-1.5 py-0 font-bold border", badgeConfig.color)}>
              <HighlightedText text={badgeConfig.label} query={searchQuery} />
            </Badge>
            <Badge variant="secondary" className="text-[10px] h-5 px-1.5 py-0 font-medium bg-muted text-muted-foreground border-transparent">
              <HighlightedText text={typeLabel} query={searchQuery} />
            </Badge>
          </div>
          <h3 className="font-semibold text-sm line-clamp-2 leading-tight" title={offer.name}>
             <HighlightedText text={offer.name} query={searchQuery} />
          </h3>
          <p className="text-lg font-bold text-foreground">
            {priceDisplay}
          </p>
        </div>

        {/* Footer KPIs */}
        <div className="flex items-center gap-3 text-xs text-muted-foreground mt-auto">
          <div className="flex items-center gap-1">
            <Users className="h-3 w-3" />
            <span>{offer.active_clients || 0}</span>
          </div>
          <div className="flex items-center gap-1">
            <CreditCard className="h-3 w-3" />
            <span>24</span> {/* Mock Sales count */}
          </div>
          {offer.time_to_value && (
            <div className="flex items-center gap-1" title="Time to Value">
                <Clock className="h-3 w-3" />
                <span className="truncate max-w-[60px]">{offer.time_to_value}</span>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
});
