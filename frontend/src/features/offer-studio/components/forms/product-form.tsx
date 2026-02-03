"use client";

import { UseFormReturn } from "react-hook-form";
import { OfferFormValues } from "../../types/schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ProductFormat } from "../../types/index";

export function ProductDetailsForm({ form }: { form: UseFormReturn<OfferFormValues> }) {
  return (
    <div className="space-y-6">
      <h3 className="text-lg font-medium">Logística del Producto</h3>
      
      <div className="grid grid-cols-2 gap-4">
        <FormField
          control={form.control}
          name="specific_details.format"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Formato</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value as string}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecciona formato" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {Object.values(ProductFormat).map((t) => (
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
          name="specific_details.stock_quantity"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Stock Disponible</FormLabel>
              <FormControl>
                <Input type="number" {...field} onChange={e => field.onChange(parseInt(e.target.value))} value={field.value as number || 0} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
         <FormField
          control={form.control}
          name="specific_details.file_type"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Tipo de Archivo (Digital)</FormLabel>
              <FormControl>
                <Input placeholder="PDF, MP4, ZIP" {...field} value={field.value as string || ""} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={form.control}
          name="specific_details.access_link"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Link de Acceso/Descarga</FormLabel>
              <FormControl>
                <Input placeholder="https://..." {...field} value={field.value as string || ""} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

       <FormField
          control={form.control}
          name="specific_details.shipping_zones"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Zonas de Envío (Físico)</FormLabel>
              <FormControl>
                <Input 
                  placeholder="USA, MEX, LATAM (Separados por coma)" 
                  value={(field.value as string[] || []).join(", ")}
                  onChange={(e) => field.onChange(e.target.value.split(",").map(s => s.trim()))}
                />
              </FormControl>
              <FormDescription>Dejar vacío si es 100% digital.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
    </div>
  );
}
