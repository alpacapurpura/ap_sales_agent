"use client";

import { UseFormReturn } from "react-hook-form";
import { OfferFormValues } from "../../types/schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { ServiceCategory, InteractionMode, ServiceFrequency } from "../../types";
import { RichSelect } from "@/components/ui/rich-select";
import { 
  SERVICE_CATEGORY_METADATA, 
  SERVICE_FREQUENCY_METADATA, 
  INTERACTION_MODE_METADATA, 
  getEnumOptions 
} from "../../types/enum-metadata";
import { Card, CardContent } from "@/components/ui/card";

export function ServiceDetailsForm({ form }: { form: UseFormReturn<OfferFormValues> }) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="space-y-6">
          <h3 className="text-lg font-medium">Gestión de Servicio</h3>
          
          <div className="grid grid-cols-2 gap-4">
        <FormField
          control={form.control}
          name="specific_details.category"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Categoría</FormLabel>
              <RichSelect 
                options={getEnumOptions(SERVICE_CATEGORY_METADATA)}
                value={field.value as string}
                onValueChange={field.onChange}
              />
              <FormMessage />
            </FormItem>
          )}
        />
         <FormField
          control={form.control}
          name="specific_details.frequency_type"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Frecuencia</FormLabel>
              <RichSelect 
                options={getEnumOptions(SERVICE_FREQUENCY_METADATA)}
                value={field.value as string}
                onValueChange={field.onChange}
              />
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <FormField
          control={form.control}
          name="specific_details.interaction_mode"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Modo de Interacción</FormLabel>
              <RichSelect 
                options={getEnumOptions(INTERACTION_MODE_METADATA)}
                value={field.value as string}
                onValueChange={field.onChange}
              />
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="specific_details.booking_url"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Link de Agenda</FormLabel>
              <FormControl>
                <Input placeholder="https://calendly.com/..." {...field} value={field.value as string || ""} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      <FormField
        control={form.control}
        name="specific_details.deliverables_list"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Lista de Entregables (Scope)</FormLabel>
             <FormControl>
                <Input 
                  placeholder="Auditoría, 4 Embudos, Copy (Separados por coma)" 
                  value={(field.value as string[] || []).join(", ")}
                  onChange={(e) => field.onChange(e.target.value.split(",").map(s => s.trim()))}
                />
              </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
      
      {form.watch("specific_details.category") === ServiceCategory.DONE_FOR_YOU_AGENCY && (
         <div className="border p-4 rounded-md space-y-4 bg-muted/20">
            <h4 className="font-medium text-sm text-muted-foreground">Lógica de Agencia</h4>
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="specific_details.turnaround_time_days"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Días de Entrega (SLA)</FormLabel>
                    <FormControl>
                      <Input type="number" {...field} onChange={e => field.onChange(parseInt(e.target.value))} value={field.value as number || 0} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="specific_details.revision_rounds"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Rondas de Cambios</FormLabel>
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
              name="specific_details.onboarding_brief_url"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Link al Brief de Inicio</FormLabel>
                  <FormControl>
                    <Input placeholder="https://tally.so/..." {...field} value={field.value as string || ""} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
         </div>
      )}
        </div>
      </CardContent>
    </Card>
  );
}
