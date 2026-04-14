import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { LeadTemperature } from "../../types";

interface TemperatureBadgeProps {
  temperature: LeadTemperature;
  className?: string;
}

const variants: Record<LeadTemperature, string> = {
  cold: "bg-blue-100 text-blue-700 hover:bg-blue-200 border-blue-200",
  warm: "bg-orange-100 text-orange-700 hover:bg-orange-200 border-orange-200",
  hot: "bg-red-100 text-red-700 hover:bg-red-200 border-red-200",
};

const labels: Record<LeadTemperature, string> = {
  cold: "Frío",
  warm: "Tibio",
  hot: "Caliente",
};

export function TemperatureBadge({ temperature, className }: TemperatureBadgeProps) {
  return (
    <Badge
      variant="outline"
      className={cn("capitalize font-medium border", variants[temperature], className)}
    >
      {labels[temperature]}
    </Badge>
  );
}
