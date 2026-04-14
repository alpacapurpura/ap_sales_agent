"use client";

import { UseFormReturn, useFieldArray } from "react-hook-form";
import { OfferFormValues } from "../../../../types/schema";
import { PaymentPlanType } from "../../../../types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FormField, FormItem, FormLabel, FormControl } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Plus, Trash2, Star, DollarSign } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";

interface TierComparisonBuilderProps {
  form: UseFormReturn<OfferFormValues>;
}

export function TierComparisonBuilder({ form }: TierComparisonBuilderProps) {
  const { currency: tenantCurrency } = useTenantLocale();
  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "pricing_options",
  });

  const addTier = () => {
    append({
      label: `Tier ${fields.length + 1}`,
      plan_type: PaymentPlanType.SUBSCRIPTION,
      total_amount: 0,
      deposit_required: 0,
      number_of_installments: 1,
      installment_amount: 0,
      is_default: false,
      savings_claim: null,
      benefits: [],
      is_highlighted: false,
      cta_text: null,
    });
  };

  const currency = form.watch("currency") || tenantCurrency;

  return (
    <Card className="overflow-hidden border-slate-200 dark:border-slate-800">
      <CardHeader className="pb-4 border-b bg-slate-50 dark:bg-slate-900/50 flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-base flex items-center gap-2">
            <Star className="w-4 h-4 text-primary" />
            Tiers de Membresia
          </CardTitle>
          <p className="text-sm text-muted-foreground mt-1">
            Configura los niveles de tu membresia con beneficios diferenciados.
          </p>
        </div>
        <Button type="button" size="sm" onClick={addTier}>
          <Plus className="h-4 w-4 mr-2" /> Agregar Tier
        </Button>
      </CardHeader>
      <CardContent className="p-6">
        {fields.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            <DollarSign className="w-10 h-10 mx-auto mb-3 opacity-20" />
            <p>No hay tiers definidos.</p>
            <p className="text-xs">
              Agrega un tier para comenzar a construir tu tabla comparativa.
            </p>
          </div>
        ) : (
          <div
            className={cn(
              "grid gap-6",
              fields.length === 1 && "grid-cols-1 max-w-md mx-auto",
              fields.length === 2 && "grid-cols-1 md:grid-cols-2",
              fields.length >= 3 && "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
            )}
          >
            {fields.map((field, index) => {
              const isHighlighted = form.watch(`pricing_options.${index}.is_highlighted`);
              const benefits = form.watch(`pricing_options.${index}.benefits`) || [];

              return (
                <div
                  key={field.id}
                  className={cn(
                    "relative rounded-xl border-2 p-5 space-y-4 transition-all",
                    isHighlighted
                      ? "border-primary bg-primary/5 shadow-md"
                      : "border-border bg-background",
                  )}
                >
                  {isHighlighted && (
                    <Badge className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground text-[10px]">
                      Mas Popular
                    </Badge>
                  )}

                  {/* Header */}
                  <div className="flex items-start justify-between">
                    <FormField
                      control={form.control}
                      name={`pricing_options.${index}.label`}
                      render={({ field: f }) => (
                        <FormItem className="flex-1">
                          <FormControl>
                            <Input
                              className="text-lg font-bold border-none p-0 h-auto focus-visible:ring-0 bg-transparent"
                              placeholder="Nombre del Tier"
                              {...f}
                            />
                          </FormControl>
                        </FormItem>
                      )}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-muted-foreground hover:text-destructive"
                      onClick={() => remove(index)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>

                  {/* Price */}
                  <FormField
                    control={form.control}
                    name={`pricing_options.${index}.total_amount`}
                    render={({ field: f }) => (
                      <FormItem>
                        <div className="flex items-baseline gap-1">
                          <span className="text-sm text-muted-foreground">{currency}</span>
                          <FormControl>
                            <Input
                              type="number"
                              className="text-3xl font-black border-none p-0 h-auto focus-visible:ring-0 bg-transparent w-32"
                              {...f}
                              onChange={(e) => f.onChange(e.target.valueAsNumber)}
                            />
                          </FormControl>
                          <span className="text-sm text-muted-foreground">/ mes</span>
                        </div>
                      </FormItem>
                    )}
                  />

                  {/* Highlighted toggle */}
                  <FormField
                    control={form.control}
                    name={`pricing_options.${index}.is_highlighted`}
                    render={({ field: f }) => (
                      <FormItem className="flex items-center gap-2">
                        <FormControl>
                          <Switch checked={f.value} onCheckedChange={f.onChange} />
                        </FormControl>
                        <FormLabel className="text-xs text-muted-foreground !mt-0">
                          Marcar como &ldquo;Mas Popular&rdquo;
                        </FormLabel>
                      </FormItem>
                    )}
                  />

                  {/* Benefits */}
                  <div className="space-y-2">
                    <FormLabel className="text-xs font-medium">Beneficios</FormLabel>
                    {benefits.map((_: string, bi: number) => (
                      <div key={bi} className="flex items-center gap-2">
                        <Input
                          className="h-8 text-sm"
                          value={benefits[bi]}
                          onChange={(e) => {
                            const updated = [...benefits];
                            updated[bi] = e.target.value;
                            form.setValue(`pricing_options.${index}.benefits`, updated);
                          }}
                          placeholder="Beneficio..."
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 shrink-0"
                          onClick={() => {
                            const updated = benefits.filter((_: string, i: number) => i !== bi);
                            form.setValue(`pricing_options.${index}.benefits`, updated);
                          }}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    ))}
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="w-full h-7 text-xs"
                      onClick={() => {
                        form.setValue(`pricing_options.${index}.benefits`, [...benefits, ""]);
                      }}
                    >
                      <Plus className="h-3 w-3 mr-1" /> Agregar Beneficio
                    </Button>
                  </div>

                  {/* CTA text */}
                  <FormField
                    control={form.control}
                    name={`pricing_options.${index}.cta_text`}
                    render={({ field: f }) => (
                      <FormItem>
                        <FormLabel className="text-xs">Texto del CTA</FormLabel>
                        <FormControl>
                          <Input
                            className="h-8 text-sm"
                            placeholder="Ej. Comenzar Ahora"
                            {...f}
                            value={f.value || ""}
                          />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
