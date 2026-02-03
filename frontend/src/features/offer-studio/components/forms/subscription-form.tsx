"use client";

import { UseFormReturn } from "react-hook-form";
import { OfferFormValues } from "../../types/schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { BillingFrequency } from "../../types/index";

export function SubscriptionDetailsForm({ form }: { form: UseFormReturn<OfferFormValues> }) {
  return (
    <div className="space-y-6">
      <h3 className="text-lg font-medium">Configuración de Membresía</h3>
      
      <div className="grid grid-cols-2 gap-4">
        <FormField
          control={form.control}
          name="specific_details.billing_cycle"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Ciclo de Facturación</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value as string}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {Object.values(BillingFrequency).map((t) => (
                    <SelectItem key={t} value={t}>{t}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
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
        name="specific_details.platform_name"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Plataforma de Comunidad</FormLabel>
            <FormControl>
              <Input placeholder="Skool, Discord, Circle" {...field} value={field.value as string || ""} />
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
              <Input placeholder="Cancelar en cualquier momento..." {...field} value={field.value as string || ""} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      
       <FormField
        control={form.control}
        name="specific_details.save_offer_script"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Script de Retención (Save Offer)</FormLabel>
            <FormControl>
              <Input placeholder="Si te quedas, te regalo una auditoría..." {...field} value={field.value as string || ""} />
            </FormControl>
            <FormDescription>Lo que dirá el agente si intentan cancelar.</FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />
    </div>
  );
}
