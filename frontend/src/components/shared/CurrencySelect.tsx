"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCurrencyCatalog } from "@/hooks/use-currency-catalog";

interface CurrencySelectProps {
  value: string | undefined;
  onChange: (code: string) => void;
  disabled?: boolean;
  id?: string;
  className?: string;
}

/**
 * Picker for the curated currency catalog. Drop-in for forms — renders
 * the ISO code, symbol, and localized label so users with multiple
 * regional peso currencies (ARS, CLP, COP, MXN, UYU, all using ``$``)
 * can disambiguate at a glance.
 *
 * While the catalog is loading the trigger stays disabled with a
 * neutral placeholder so the form doesn't flicker.
 */
export function CurrencySelect({ value, onChange, disabled, id, className }: CurrencySelectProps) {
  const { data, isLoading } = useCurrencyCatalog();
  const currencies = data?.currencies ?? [];

  return (
    <Select value={value} onValueChange={onChange} disabled={disabled || isLoading}>
      <SelectTrigger id={id} className={className}>
        <SelectValue placeholder={isLoading ? "Cargando..." : "Moneda"} />
      </SelectTrigger>
      <SelectContent>
        {currencies.map((c) => (
          <SelectItem key={c.code} value={c.code}>
            <span className="font-mono text-xs mr-2">{c.code}</span>
            <span className="mr-2">{c.symbol}</span>
            <span className="text-muted-foreground">{c.label_es}</span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
