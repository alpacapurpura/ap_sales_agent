"use client";

import { UseFormReturn, useFieldArray } from "react-hook-form";
import { SectionFormWrapper } from "../common/section-form-wrapper";
import { OfferSchema, OfferFormValues } from "../../../../types/schema";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CreditCard, Plus, Trash2, DollarSign, Star } from "lucide-react";
import { CurrencySelector } from "@/components/ui/currency-selector";
import { CURRENCIES } from "@/lib/constants/currencies";
import { PaymentPlanType } from "../../../../types";
import { cn } from "@/lib/utils";

const PricingSchema = OfferSchema.pick({
  pricing_options: true,
  currency: true
});

type PricingFormValues = Pick<OfferFormValues, "pricing_options" | "currency">;

export interface PricingFormProps {
  defaultValues: Partial<OfferFormValues>;
  onSave: (data: Partial<OfferFormValues>) => Promise<void>;
  form?: any;
}

function PricingContent({ form }: { form: UseFormReturn<OfferFormValues> }) {
  const { fields: pricingFields, append: addPricing, remove: removePricing, update: updatePricing } = useFieldArray({
    control: form.control,
    name: "pricing_options",
  });

  const ALLOWED_CURRENCY_CODES = ["USD", "PEN", "COP", "ARS", "MXN", "CLP"];
  const LATAM_CURRENCIES = CURRENCIES.filter(c => ALLOWED_CURRENCY_CODES.includes(c.code));

  const setPricingDefault = (index: number) => {
      // Logic: Set selected to true, all others to false
      pricingFields.forEach((field, i) => {
          const currentData = form.getValues(`pricing_options.${i}`);
          updatePricing(i, {
              ...currentData,
              is_default: i === index
          });
      });
  };

  return (
    <Card className="overflow-hidden border-slate-200 dark:border-slate-800">
        <CardHeader className="pb-4 border-b bg-slate-50 dark:bg-slate-900/50 flex flex-row items-center justify-between">
            <div>
                <CardTitle className="text-base flex items-center gap-2">
                    <CreditCard className="w-4 h-4 text-primary"/> 
                    Estrategia de Precios
                </CardTitle>
                <CardDescription>Configura tus planes de pago, suscripciones o precios únicos.</CardDescription>
            </div>
            <div className="flex items-center gap-3">
                    <FormField control={form.control} name="currency" render={({ field }) => (
                    <FormItem className="space-y-0">
                        <FormControl>
                            <CurrencySelector 
                                value={field.value} 
                                onValueChange={field.onChange} 
                                currencies={LATAM_CURRENCIES}
                                className="w-[140px] h-8 text-xs"
                            />
                        </FormControl>
                    </FormItem>
                )} />
                <Button type="button" size="sm" onClick={() => addPricing({ 
                    label: "Nuevo Precio", 
                    plan_type: PaymentPlanType.ONE_TIME,
                    total_amount: 0, 
                    deposit_required: 0, 
                    number_of_installments: 1, 
                    installment_amount: 0, 
                    is_default: false 
                })}>
                    <Plus className="h-4 w-4 mr-2"/> Agregar Opción
                </Button>
            </div>
        </CardHeader>
        <CardContent className="p-0 bg-slate-50/30 dark:bg-slate-950/30">
            {pricingFields.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                    <DollarSign className="w-10 h-10 mx-auto mb-3 opacity-20" />
                    <p>No hay precios definidos.</p>
                    <p className="text-xs">Agrega una opción de pago para comenzar.</p>
                </div>
            ) : (
                <div className="divide-y">
                    {pricingFields.map((field, index) => {
                        // Watch values for reactive UI inside the map
                        const planType = form.watch(`pricing_options.${index}.plan_type`);
                        const totalAmount = form.watch(`pricing_options.${index}.total_amount`) || 0;
                        const deposit = form.watch(`pricing_options.${index}.deposit_required`) || 0;
                        const installments = form.watch(`pricing_options.${index}.number_of_installments`) || 1;
                        const isDefault = form.watch(`pricing_options.${index}.is_default`);
                        
                        // Calculate installment amount dynamically
                        const calculatedInstallment = installments > 0 ? (totalAmount - deposit) / installments : 0;
                        const currency = form.watch("currency") || "USD";

                        return (
                            <div key={field.id} className={cn(
                                "p-6 bg-background group hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors border-l-4",
                                isDefault ? "border-l-yellow-400 bg-yellow-50/10" : "border-l-transparent"
                            )}>
                                <div className="flex items-start justify-between mb-6">
                                    <div className="flex items-center gap-4 flex-1">
                                        <div className={cn(
                                            "h-10 w-10 rounded-full flex items-center justify-center font-bold text-sm transition-all",
                                            isDefault ? "bg-yellow-100 text-yellow-600 ring-2 ring-yellow-400 ring-offset-2" : "bg-primary/10 text-primary"
                                        )}>
                                            {index + 1}
                                        </div>
                                        <div className="space-y-1 flex-1">
                                            <div className="flex items-center gap-2">
                                                <Input 
                                                    className="h-8 text-lg font-semibold border-none p-0 focus-visible:ring-0 bg-transparent placeholder:text-muted-foreground/50 w-full max-w-[300px]" 
                                                    {...form.register(`pricing_options.${index}.label`)} 
                                                    placeholder="Nombre del Plan (Ej. Pago Único)" 
                                                />
                                                {isDefault && (
                                                    <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100 text-[10px] uppercase font-bold tracking-wider">
                                                        Popular
                                                    </Badge>
                                                )}
                                            </div>
                                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                                <Badge variant="outline" className="text-[10px] uppercase font-normal">
                                                    {planType === PaymentPlanType.ONE_TIME ? "Pago Único" : 
                                                        planType === PaymentPlanType.PAYMENT_PLAN ? "Financiado" : "Suscripción"}
                                                </Badge>
                                                {planType === PaymentPlanType.PAYMENT_PLAN && (
                                                    <span>• {installments} cuotas de {currency} {calculatedInstallment.toFixed(2)}</span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                    
                                    {/* Right Actions & Summary */}
                                    <div className="flex items-start gap-4">
                                        <div className="text-right mr-2 hidden md:block">
                                            <div className="text-lg font-bold text-slate-900 dark:text-slate-100">
                                                {currency} {totalAmount.toLocaleString()}
                                            </div>
                                            <div className="text-xs text-muted-foreground">
                                                Total a Pagar
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-1">
                                            <Button 
                                                type="button" 
                                                variant="ghost" 
                                                size="icon" 
                                                className={cn("h-8 w-8 hover:text-yellow-500", isDefault ? "text-yellow-500" : "text-muted-foreground")} 
                                                onClick={() => setPricingDefault(index)}
                                                title="Marcar como opción recomendada"
                                            >
                                                <Star className={cn("h-4 w-4", isDefault && "fill-current")} />
                                            </Button>
                                            <Button type="button" variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive" onClick={() => removePricing(index)}>
                                                <Trash2 className="h-4 w-4"/>
                                            </Button>
                                        </div>
                                    </div>
                                </div>

                                {/* SMART EDITOR */}
                                <div className="pl-11">
                                    <Tabs 
                                        defaultValue={planType || PaymentPlanType.ONE_TIME} 
                                        onValueChange={(val) => form.setValue(`pricing_options.${index}.plan_type`, val as PaymentPlanType)}
                                        className="w-full"
                                    >
                                        <TabsList className="mb-4 w-full justify-start h-auto p-1 bg-muted/50">
                                            <TabsTrigger value={PaymentPlanType.ONE_TIME} className="text-xs">Pago Único</TabsTrigger>
                                            <TabsTrigger value={PaymentPlanType.PAYMENT_PLAN} className="text-xs">Plan de Pagos</TabsTrigger>
                                            <TabsTrigger value={PaymentPlanType.SUBSCRIPTION} className="text-xs">Suscripción</TabsTrigger>
                                        </TabsList>

                                        <TabsContent value={PaymentPlanType.ONE_TIME} className="mt-0 space-y-4">
                                            <div className="grid grid-cols-2 gap-4">
                                                <FormField
                                                    control={form.control}
                                                    name={`pricing_options.${index}.total_amount`}
                                                    render={({ field }) => (
                                                        <FormItem>
                                                            <FormLabel className="text-xs">Monto Total</FormLabel>
                                                            <div className="relative">
                                                                <DollarSign className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                                                                <FormControl>
                                                                    <Input 
                                                                        type="number" 
                                                                        className="pl-8" 
                                                                        {...field}
                                                                        onChange={e => field.onChange(e.target.valueAsNumber)}
                                                                    />
                                                                </FormControl>
                                                            </div>
                                                            <FormMessage />
                                                        </FormItem>
                                                    )}
                                                />
                                                <FormField
                                                    control={form.control}
                                                    name={`pricing_options.${index}.savings_claim`}
                                                    render={({ field }) => (
                                                        <FormItem>
                                                            <FormLabel className="text-xs">Texto de Ahorro (Opcional)</FormLabel>
                                                            <FormControl>
                                                                <Input placeholder="Ej. Ahorra $200 vs Plan" {...field} value={field.value || ""} />
                                                            </FormControl>
                                                            <FormMessage />
                                                        </FormItem>
                                                    )}
                                                />
                                            </div>
                                        </TabsContent>

                                        <TabsContent value={PaymentPlanType.PAYMENT_PLAN} className="mt-0 space-y-4">
                                            <div className="grid grid-cols-3 gap-4">
                                                <FormField
                                                    control={form.control}
                                                    name={`pricing_options.${index}.total_amount`}
                                                    render={({ field }) => (
                                                        <FormItem>
                                                            <FormLabel className="text-xs">Monto Total del Plan</FormLabel>
                                                            <div className="relative">
                                                                <DollarSign className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                                                                <FormControl>
                                                                    <Input 
                                                                        type="number" 
                                                                        className="pl-8" 
                                                                        {...field}
                                                                        onChange={e => field.onChange(e.target.valueAsNumber)}
                                                                    />
                                                                </FormControl>
                                                            </div>
                                                            <FormMessage />
                                                        </FormItem>
                                                    )}
                                                />
                                                    <FormField
                                                    control={form.control}
                                                    name={`pricing_options.${index}.deposit_required`}
                                                    render={({ field }) => (
                                                        <FormItem>
                                                            <FormLabel className="text-xs">Pago Inicial (Depósito)</FormLabel>
                                                            <div className="relative">
                                                                <DollarSign className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                                                                <FormControl>
                                                                    <Input 
                                                                        type="number" 
                                                                        className="pl-8" 
                                                                        {...field}
                                                                        onChange={e => field.onChange(e.target.valueAsNumber)}
                                                                    />
                                                                </FormControl>
                                                            </div>
                                                            <FormMessage />
                                                        </FormItem>
                                                    )}
                                                />
                                                    <FormField
                                                    control={form.control}
                                                    name={`pricing_options.${index}.number_of_installments`}
                                                    render={({ field }) => (
                                                        <FormItem>
                                                            <FormLabel className="text-xs">N° de Cuotas</FormLabel>
                                                            <FormControl>
                                                                <Input 
                                                                    type="number" 
                                                                    {...field}
                                                                    onChange={e => field.onChange(e.target.valueAsNumber)}
                                                                />
                                                            </FormControl>
                                                            <FormMessage />
                                                        </FormItem>
                                                    )}
                                                />
                                            </div>
                                            
                                            {/* Calculation Preview */}
                                            <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg flex items-center justify-between text-sm text-blue-700 dark:text-blue-300">
                                                <span className="font-medium">Resumen para el Cliente:</span>
                                                <span>
                                                    Hoy paga <strong>${deposit}</strong> + {installments} cuotas de <strong>${calculatedInstallment.toFixed(2)}</strong>
                                                </span>
                                            </div>
                                        </TabsContent>

                                        <TabsContent value={PaymentPlanType.SUBSCRIPTION} className="mt-0">
                                            <div className="flex items-center gap-4">
                                                    <FormField
                                                    control={form.control}
                                                    name={`pricing_options.${index}.total_amount`}
                                                    render={({ field }) => (
                                                        <FormItem className="flex-1">
                                                            <FormLabel className="text-xs">Monto por Período</FormLabel>
                                                            <div className="relative">
                                                                <DollarSign className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                                                                <FormControl>
                                                                    <Input 
                                                                        type="number" 
                                                                        className="pl-8" 
                                                                        {...field}
                                                                        onChange={e => field.onChange(e.target.valueAsNumber)}
                                                                    />
                                                                </FormControl>
                                                            </div>
                                                            <FormMessage />
                                                        </FormItem>
                                                    )}
                                                />
                                                <div className="flex-1 text-xs text-muted-foreground pt-6">
                                                    La configuración de recurrencia se maneja en el procesador de pagos (Stripe). Aquí solo defines el precio visual.
                                                </div>
                                            </div>
                                        </TabsContent>
                                    </Tabs>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </CardContent>
    </Card>
  );
}

export function PricingForm({ defaultValues: propValues, onSave }: PricingFormProps) {
  const defaultValues: PricingFormValues = {
    pricing_options: propValues?.pricing_options || [],
    currency: propValues?.currency || "USD"
  };

  const handleSave = async (data: PricingFormValues) => {
    await onSave(data);
  };

  return (
    <SectionFormWrapper<PricingFormValues>
      schema={PricingSchema}
      defaultValues={defaultValues}
      onSubmit={handleSave}
    >
      {(form) => (
        <PricingContent form={form as unknown as UseFormReturn<OfferFormValues>} />
      )}
    </SectionFormWrapper>
  );
}
