"use client";

import { Check, Sparkles } from "lucide-react";
import React from "react";
import { useFormContext } from "react-hook-form";

import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";

import type { OfferFormValues } from "../../../../types/schema";

interface ValueStackPreviewProps {
  data?: Partial<OfferFormValues>;
}

export const ValueStackPreview = ({ data: propsData }: ValueStackPreviewProps) => {
  const { currency: tenantCurrency } = useTenantLocale();
  const form = useFormContext<OfferFormValues>();
  const data = propsData || (form ? form.watch() : null);

  if (!data?.deliverables?.length) return null;

  const { deliverables, currency } = data;
  const currencyCode = currency || tenantCurrency;
  const totalValue = deliverables.reduce(
    (sum, item) => sum + (Number(item.value_stack_price) || 0),
    0,
  );

  return (
    <div className="w-full">
      <div className="mb-6 text-center p-4 rounded-xl bg-primary/5 border border-primary/10">
        <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1 flex items-center justify-center gap-1">
          <Sparkles className="w-3 h-3 text-primary" /> Valor Total
        </div>
        <div className="text-3xl font-black tracking-tighter text-primary">
          {totalValue.toLocaleString()}{" "}
          <span className="text-sm font-bold text-muted-foreground/70 align-top mt-1 inline-block">
            {currencyCode}
          </span>
        </div>
      </div>

      <div className="space-y-3">
        {deliverables.map((item, idx) => (
          <div key={idx} className="flex items-start gap-3 group">
            <div className="mt-1 shrink-0">
              <div className="w-5 h-5 rounded-full bg-green-500/10 flex items-center justify-center">
                <Check className="w-3 h-3 text-green-600 dark:text-green-400" />
              </div>
            </div>
            <div className="flex-1 min-w-0 border-b border-dashed border-border/60 pb-3 group-last:border-0 group-last:pb-0">
              <div className="flex justify-between items-start gap-4">
                <div>
                  <p className="text-sm font-medium leading-snug">{item.name}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-muted text-muted-foreground capitalize">
                      {item.format}
                    </span>
                    {parseInt(item.quantity) > 1 && (
                      <span className="text-[10px] text-muted-foreground">x{item.quantity}</span>
                    )}
                  </div>
                </div>
                <div className="text-sm font-semibold text-muted-foreground/80 tabular-nums">
                  {Number(item.value_stack_price).toLocaleString()}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
