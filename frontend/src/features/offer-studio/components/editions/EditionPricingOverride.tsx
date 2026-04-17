"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { formatMoney } from "@/lib/format-money";

import type { PricingStructure } from "../../types";

interface EditionPricingOverrideProps {
  /**
   * Base pricing options from the parent offer. May be undefined or empty
   * while the offer is still loading or was created without pricing yet —
   * the component must render a graceful empty state instead of crashing.
   */
  offerPricing: PricingStructure[] | undefined;
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
  const basePricing = offerPricing ?? [];
  const hasBasePricing = basePricing.length > 0;
  const isOverride = value !== null;
  const toggleDisabled = !hasBasePricing && !isOverride;

  const handleToggle = (checked: boolean) => {
    if (checked) {
      onChange(basePricing.map((p) => ({ ...p })));
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
          <Switch checked={isOverride} onCheckedChange={handleToggle} disabled={toggleDisabled} />
        </div>
      </div>

      {!isOverride && hasBasePricing && (
        <p className="text-xs text-muted-foreground">
          Precio heredado de la oferta:{" "}
          {basePricing.map((p) => formatMoney(p.total_amount, currency)).join(" / ")}
        </p>
      )}

      {!isOverride && !hasBasePricing && (
        <p className="text-xs text-amber-600">
          La oferta aún no tiene precio base configurado. Actívalo en la oferta o define un precio
          específico para esta edición.
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
              {basePricing[idx] && plan.total_amount < basePricing[idx].total_amount && (
                <span className="text-xs text-green-500 whitespace-nowrap">
                  -
                  {Math.round(
                    ((basePricing[idx].total_amount - plan.total_amount) /
                      basePricing[idx].total_amount) *
                      100,
                  )}
                  %
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
