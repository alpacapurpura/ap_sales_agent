"use client";

import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { PricingStructure } from "../../types";
import { formatMoney } from "@/lib/format-money";

interface EditionPricingOverrideProps {
  offerPricing: PricingStructure[];
  currency: string;
  value: PricingStructure[] | null;
  onChange: (pricing: PricingStructure[] | null) => void;
}

export function EditionPricingOverride({
  offerPricing,
  currency,
  value,
  onChange,
}: EditionPricingOverrideProps) {
  const isOverride = value !== null;

  const handleToggle = (checked: boolean) => {
    if (checked) {
      onChange(offerPricing.map((p) => ({ ...p })));
    } else {
      onChange(null);
    }
  };

  const handleAmountChange = (index: number, amount: number) => {
    if (!value) return;
    const updated = [...value];
    updated[index] = { ...updated[index], total_amount: amount };
    onChange(updated);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Label className="text-sm font-medium">Precio especial para esta edición</Label>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">
            {isOverride ? "Override activo" : "Usa precio base"}
          </span>
          <Switch checked={isOverride} onCheckedChange={handleToggle} />
        </div>
      </div>

      {!isOverride && (
        <p className="text-xs text-muted-foreground">
          Precio heredado de la oferta:{" "}
          {offerPricing.map((p) => formatMoney(p.total_amount, currency)).join(" / ")}
        </p>
      )}

      {isOverride && value && (
        <div className="space-y-3 rounded-lg border p-4 bg-amber-500/5 border-amber-500/20">
          <p className="text-xs font-medium text-amber-500">
            Precio especial activado — esta edición usa precios diferentes.
          </p>
          {value.map((plan, idx) => (
            <div key={idx} className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground w-24 truncate">
                {plan.label || `Plan ${idx + 1}`}
              </span>
              <div className="relative flex-1">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-xs">
                  {currency}
                </span>
                <Input
                  type="number"
                  value={plan.total_amount}
                  onChange={(e) => handleAmountChange(idx, parseFloat(e.target.value) || 0)}
                  className="pl-12"
                />
              </div>
              {offerPricing[idx] && plan.total_amount < offerPricing[idx].total_amount && (
                <span className="text-xs text-green-500 whitespace-nowrap">
                  -{Math.round(((offerPricing[idx].total_amount - plan.total_amount) / offerPricing[idx].total_amount) * 100)}%
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
