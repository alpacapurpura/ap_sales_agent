"use client";

import { UseFormReturn } from "react-hook-form";
import { OfferFormValues } from "../../types/schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ServiceCapacity } from "../../types/index";

export function ServiceDetailsForm({ form }: { form: UseFormReturn<OfferFormValues> }) {
  return (
    <div className="space-y-6">
      <h3 className="text-lg font-medium">Gestión de Servicio</h3>
      
      <div className="grid grid-cols-2 gap-4">
        <FormField
          control={form.control}
          name="specific_details.capacity_status"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Estado de Capacidad</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value as string}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {Object.values(ServiceCapacity).map((t) => (
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
          name="specific_details.max_concurrent_clients"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Cupo Máximo</FormLabel>
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
        name="specific_details.onboarding_timeline"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Timeline de Onboarding</FormLabel>
            <FormControl>
              <Input placeholder="Kickoff call en 48h, primer entregable día 14" {...field} value={field.value as string || ""} />
            </FormControl>
            <FormDescription>Define las expectativas iniciales.</FormDescription>
            <FormMessage />
          </FormItem>
        )}
      />
      
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
    </div>
  );
}
