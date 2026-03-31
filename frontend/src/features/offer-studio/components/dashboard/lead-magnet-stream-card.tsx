import { Offer, OfferArchetype, OfferStatus } from "@/features/offer-studio/types";
import { ARCHETYPE_METADATA } from "@/features/offer-studio/config/archetype-metadata";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  MoreHorizontal,
  Magnet,
  ExternalLink
} from "lucide-react";
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { useParams } from "next/navigation";
import { useNavigation } from "@/components/shared/navigation";

interface LeadMagnetStreamCardProps {
  offer: Offer;
  onClick?: () => void;
}

const ARCHETYPE_COLORS: Record<string, string> = {
  producto: "bg-blue-100 text-blue-700 border-r border-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800",
  programa: "bg-orange-100 text-orange-700 border-r border-orange-200 dark:bg-orange-900/30 dark:text-orange-400 dark:border-orange-800",
  servicio: "bg-violet-100 text-violet-700 border-r border-violet-200 dark:bg-violet-900/30 dark:text-violet-400 dark:border-violet-800",
  membresia: "bg-emerald-100 text-emerald-700 border-r border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-800",
  experiencia: "bg-amber-100 text-amber-700 border-r border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800",
  default: "bg-slate-100 text-slate-700 border-r border-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700"
};

export function LeadMagnetStreamCard({ offer, onClick }: LeadMagnetStreamCardProps) {
  const { navigate, isNavigating } = useNavigation();
  const params = useParams();
  const tenantId = params?.tenantId as string;

  const archetypeMeta = offer.archetype ? ARCHETYPE_METADATA[offer.archetype as OfferArchetype] : null;
  const Icon = archetypeMeta?.icon || Magnet;
  const colorClass = ARCHETYPE_COLORS[offer.archetype] || ARCHETYPE_COLORS.default;
  const typeLabel = archetypeMeta?.label || "Recurso";
  
  const handleClick = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('[role="menuitem"]') || (e.target as HTMLElement).closest('button')) {
      return;
    }
    if (onClick) onClick();
    else navigate(`/${tenantId}/offer-studio/offer/${offer.id}`);
  };

  return (
    <Card 
      className={cn(
        "group flex items-center h-[72px] w-[280px] overflow-hidden transition-all duration-200 hover:shadow-md cursor-pointer border bg-card hover:border-primary/30",
        isNavigating && "opacity-60 pointer-events-none"
      )}
      onClick={handleClick}
    >
      {/* Left Icon Area */}
      <div className={cn(
        "h-full w-[72px] flex items-center justify-center shrink-0 transition-colors",
        colorClass
      )}>
        <Icon className="h-6 w-6 opacity-90" />
      </div>

      {/* Content Area */}
      <div className="flex-1 px-3 py-2 min-w-0 flex flex-col justify-center h-full">
        <div className="flex items-center justify-between gap-2 mb-0.5">
           <Badge variant="secondary" className="text-[9px] h-4 px-1 rounded-sm font-normal bg-muted text-muted-foreground border-transparent truncate max-w-[120px]">
              {typeLabel}
           </Badge>
           
           {/* Status Dot */}
           <div 
             className={cn(
               "w-1.5 h-1.5 rounded-full shrink-0",
               offer.status === OfferStatus.ACTIVE ? "bg-emerald-500" : "bg-slate-300"
             )} 
             title={`Status: ${offer.status}`}
           />
        </div>
        
        <h4 className="font-semibold text-xs leading-tight line-clamp-2 text-foreground/90 group-hover:text-primary transition-colors" title={offer.name}>
          {offer.name}
        </h4>
      </div>

      {/* Hover Action */}
      <div className="w-8 h-full flex items-center justify-center border-l border-transparent group-hover:border-border/50 bg-transparent group-hover:bg-muted/10 transition-all opacity-0 group-hover:opacity-100">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-6 w-6">
                <MoreHorizontal className="h-3 w-3 text-muted-foreground" />
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
            </DropdownMenuContent>
          </DropdownMenu>
      </div>
    </Card>
  );
}
