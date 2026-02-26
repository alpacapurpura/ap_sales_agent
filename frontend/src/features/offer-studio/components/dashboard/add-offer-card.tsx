import { Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import { OfferValueLevel } from "@/features/offer-studio/types";

interface AddOfferCardProps {
  level: OfferValueLevel;
  onClick: () => void;
  className?: string;
  compact?: boolean;
}

export function AddOfferCard({ level, onClick, className, compact = false }: AddOfferCardProps) {
  return (
    <div 
      onClick={onClick}
      className={cn(
        "group w-full border-2 border-dashed border-muted-foreground/25 rounded-lg",
        "flex flex-col items-center justify-center gap-2",
        "cursor-pointer transition-all duration-200",
        "hover:border-primary/50 hover:bg-muted/50",
        compact ? "h-[80px]" : "h-[180px]",
        className
      )}
    >
      <div className={cn(
        "rounded-full bg-muted flex items-center justify-center group-hover:bg-primary/10 group-hover:text-primary transition-colors duration-200",
        compact ? "h-8 w-8" : "h-10 w-10"
      )}>
        <Plus className={cn("text-muted-foreground group-hover:text-primary transition-colors duration-200", compact ? "h-4 w-4" : "h-6 w-6")} />
      </div>
      {!compact && (
        <span className="text-sm font-medium text-muted-foreground group-hover:text-primary transition-colors duration-200">
          Añadir a {level}
        </span>
      )}
    </div>
  );
}
