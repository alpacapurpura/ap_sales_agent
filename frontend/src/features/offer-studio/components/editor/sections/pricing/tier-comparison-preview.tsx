import { PricingStructure } from "../../../../types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface TierComparisonPreviewProps {
  tiers: PricingStructure[];
  currency: string;
}

export function TierComparisonPreview({ tiers, currency }: TierComparisonPreviewProps) {
  if (!tiers || tiers.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-8">
        No hay tiers configurados.
      </p>
    );
  }

  return (
    <div className={cn(
      "grid gap-4",
      tiers.length === 1 && "grid-cols-1 max-w-sm mx-auto",
      tiers.length === 2 && "grid-cols-1 md:grid-cols-2",
      tiers.length >= 3 && "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
    )}>
      {tiers.map((tier, i) => (
        <div
          key={i}
          className={cn(
            "relative rounded-xl border-2 p-6 space-y-4 text-center",
            tier.is_highlighted
              ? "border-primary bg-primary/5 shadow-lg scale-[1.02]"
              : "border-border bg-background"
          )}
        >
          {tier.is_highlighted && (
            <Badge className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground text-[10px]">
              Mas Popular
            </Badge>
          )}

          <h4 className="font-bold text-lg">{tier.label}</h4>

          <div className="flex items-baseline justify-center gap-1">
            <span className="text-3xl font-black">
              {new Intl.NumberFormat("en-US", { style: "currency", currency }).format(tier.total_amount)}
            </span>
            <span className="text-sm text-muted-foreground">/ mes</span>
          </div>

          {tier.benefits && tier.benefits.length > 0 && (
            <ul className="space-y-2 text-left">
              {tier.benefits.filter(Boolean).map((benefit, bi) => (
                <li key={bi} className="flex items-start gap-2 text-sm">
                  <Check className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                  <span>{benefit}</span>
                </li>
              ))}
            </ul>
          )}

          <Button
            variant={tier.is_highlighted ? "default" : "outline"}
            className="w-full"
            disabled
          >
            {tier.cta_text || "Comenzar"}
          </Button>
        </div>
      ))}
    </div>
  );
}
