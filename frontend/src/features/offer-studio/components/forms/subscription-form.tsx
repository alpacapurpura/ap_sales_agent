"use client";

import { UseFormReturn } from "react-hook-form";
import { OfferFormValues } from "../../types/schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { RichSelect } from "@/components/ui/rich-select";
import { BILLING_FREQUENCY_METADATA, getEnumOptions } from "../../types/enum-metadata";
import { Card, CardContent } from "@/components/ui/card";

export function SubscriptionDetailsForm({ form }: { form: UseFormReturn<OfferFormValues> }) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="space-y-6">
          <h3 className="text-lg font-medium">Configuración de Membresía</h3>
          
          <div className="grid grid-cols-2 gap-4">
        <FormField
          control={form.control}
          name="specific_details.billing_cycle"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Ciclo de Facturación</FormLabel>
              <RichSelect 
                options={getEnumOptions(BILLING_FREQUENCY_METADATA)}
                value={field.value as string}
                onValueChange={field.onChange}
              />
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={form.control}
          name="specific_details.trial_period_days"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Días de Prueba (Trial)</FormLabel>
              <FormControl>
                <Input type="number" {...field} onChange={e => field.onChange(parseInt(e.target.value))} value={field.value as number || 0} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      <FormField
        control={form.control}
        name="specific_details.tier_name"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Nombre del Nivel (Tier)</FormLabel>
            <FormControl>
              <Input placeholder="Ej. Pro, Gold, Elite" {...field} value={field.value as string || ""} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        control={form.control}
        name="specific_details.cancellation_policy"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Política de Cancelación</FormLabel>
             <FormControl>
              <Input placeholder="Ej. Cancelar en cualquier momento" {...field} value={field.value as string || ""} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
        />
        </div>
      </CardContent>
    </Card>
  );
}
