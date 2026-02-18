"use client";

import { UseFormReturn } from "react-hook-form";
import { OfferFormValues } from "../../types/schema";
import { EventLocationType } from "../../types";
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { RichSelect } from "@/components/ui/rich-select";
import { SmartDateTimePicker } from "@/components/ui/smart-datetime-picker";
import { TimezoneSelect } from "@/components/ui/timezone-select";
import { 
  EVENT_LOCATION_METADATA, 
  ACCOMMODATION_METADATA, 
  getEnumOptions 
} from "../../types/enum-metadata";
import { Card, CardContent } from "@/components/ui/card";

export function EventDetailsForm({ form }: { form: UseFormReturn<OfferFormValues> }) {
  const timezone = form.watch("specific_details.timezone") || "UTC";

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="space-y-6">
          <h3 className="text-lg font-medium">Logística del Evento</h3>
          
          <FormField
            control={form.control}
        name="specific_details.timezone"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Zona Horaria</FormLabel>
            <TimezoneSelect 
              value={field.value as string} 
              onValueChange={field.onChange} 
            />
            <FormMessage />
          </FormItem>
        )}
      />

      <div className="grid grid-cols-2 gap-4">
        <FormField
          control={form.control}
          name="specific_details.start_date"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Fecha Inicio</FormLabel>
              <SmartDateTimePicker 
                value={field.value as string} 
                onChange={field.onChange} 
                timezone={timezone}
              />
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={form.control}
          name="specific_details.end_date"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Fecha Fin</FormLabel>
               <SmartDateTimePicker 
                value={field.value as string} 
                onChange={field.onChange} 
                timezone={timezone}
              />
              <FormMessage />
            </FormItem>
          )}
        />
      </div>

      <FormField
        control={form.control}
        name="specific_details.location_type"
        render={({ field }) => (
          <FormItem>
            <FormLabel>Tipo de Ubicación</FormLabel>
            <RichSelect 
              options={getEnumOptions(EVENT_LOCATION_METADATA)}
              value={field.value as string}
              onValueChange={field.onChange}
            />
            <FormMessage />
          </FormItem>
        )}
      />

      {(form.watch("specific_details.location_type") === EventLocationType.IN_PERSON_LOCAL || 
        form.watch("specific_details.location_type") === EventLocationType.DESTINATION_RETREAT) && (
        <div className="border p-4 rounded-md space-y-4">
          <h4 className="font-medium text-sm text-muted-foreground">Detalles Físicos</h4>
          <FormField
            control={form.control}
            name="specific_details.venue_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Nombre del Lugar (Venue)</FormLabel>
                <FormControl>
                  <Input placeholder="Ej. Hotel Xcaret" {...field} value={field.value as string || ""} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="specific_details.venue_address"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Dirección</FormLabel>
                <FormControl>
                  <Input placeholder="Calle 123..." {...field} value={field.value as string || ""} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>
      )}
      
      {form.watch("specific_details.location_type") === EventLocationType.DESTINATION_RETREAT && (
          <div className="border p-4 rounded-md space-y-4 bg-muted/20">
             <h4 className="font-medium text-sm text-muted-foreground">Logística de Retiro</h4>
             <FormField
                control={form.control}
                name="specific_details.accommodation_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Alojamiento Incluido</FormLabel>
                    <RichSelect 
                      options={getEnumOptions(ACCOMMODATION_METADATA)}
                      value={field.value as string}
                      onValueChange={field.onChange}
                    />
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="specific_details.is_transfer_included"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3 shadow-sm">
                    <div className="space-y-0.5">
                      <FormLabel>Transporte Incluido</FormLabel>
                    </div>
                    <FormControl>
                      <Switch
                        checked={field.value as boolean}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
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
