import { UseFormReturn } from "react-hook-form";
import { OfferFormValues } from "../../types/schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { OfferType, DeliveryModel } from "../../types/index";

interface StepProps {
  form: UseFormReturn<OfferFormValues>;
}

export function IdentityStep({ form }: StepProps) {
  return (
    <>
      <div className="grid grid-cols-2 gap-4">
        <FormField
          control={form.control}
          name="internal_sku"
          render={({ field }) => (
            <FormItem>
              <FormLabel>SKU Interno</FormLabel>
              <FormControl>
                <Input placeholder="MASTERMIND_Q1_2026" {...field} />
              </FormControl>
              <FormDescription>Identificador único para el sistema.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={form.control}
          name="public_name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Nombre Público</FormLabel>
              <FormControl>
                <Input placeholder="Agency Accelerator 3.0" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <FormField
          control={form.control}
          name="type"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Tipo de Oferta</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecciona un tipo" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {Object.values(OfferType).map((type) => (
                    <SelectItem key={type} value={type}>
                      {type.replace("_", " ")}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormDescription>Define la naturaleza logística.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="delivery_model"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Modelo de Entrega</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecciona modelo" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {Object.values(DeliveryModel).map((model) => (
                    <SelectItem key={model} value={model}>
                      {model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormDescription>Justifica el precio (DIY vs DFY).</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
      </div>
    </>
  );
}
