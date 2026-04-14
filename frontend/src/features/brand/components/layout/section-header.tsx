import { Info } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface SectionHeaderProps {
  title: string;
  subtitle: string;
  tooltip?: string;
}

/**
 * Header for a section within a Brand Studio page.
 * Used to introduce each content block (e.g., "Origen", "Posicionamiento").
 */
export function SectionHeader({ title, subtitle, tooltip }: SectionHeaderProps) {
  return (
    <div className="border-b pb-4">
      <div className="flex items-center gap-2">
        <h2 className="text-2xl font-bold tracking-tight text-foreground/80">{title}</h2>
        {tooltip && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Info className="w-4 h-4 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent>
                <p>{tooltip}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>
      <p className="text-muted-foreground mt-1">{subtitle}</p>
    </div>
  );
}
