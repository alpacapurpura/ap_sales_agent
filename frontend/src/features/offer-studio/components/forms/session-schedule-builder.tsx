"use client";

import { UseFormReturn, useFieldArray } from "react-hook-form";
import { OfferFormValues } from "../../types/schema";
import { FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Trash2, Plus, Clock, Calendar } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";

const DAYS_OF_WEEK = [
  "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"
];

export function SessionScheduleBuilder({ form }: { form: UseFormReturn<OfferFormValues> }) {
  // @ts-ignore - RHF path inference limitation with union types
  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "specific_details.schedule",
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <Label className="text-base font-semibold">Horario de Sesiones</Label>
          <p className="text-sm text-muted-foreground">Define la estructura semanal de tu programa (ej. Mentorías, Q&A).</p>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => append({ title: "", day_of_week: "Lunes", time: "19:00", duration_minutes: 60 })}
        >
          <Plus className="mr-2 h-4 w-4" />
          Agregar Sesión
        </Button>
      </div>

      <div className="space-y-3">
        {fields.map((field, index) => (
          <Card key={field.id} className="bg-muted/30">
            <CardContent className="p-4 space-y-4">
              {/* Row 1: Title (Full Width) */}
              <FormField
                control={form.control}
                // @ts-ignore
                name={`specific_details.schedule.${index}.title`}
                render={({ field }) => (
                  <FormItem className="w-full">
                    <FormLabel className="text-xs">Título de la Sesión</FormLabel>
                    <FormControl>
                      <Input placeholder="Ej. Mentoria Grupal de Q&A" {...field} className="bg-background font-medium" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Row 2: Metadata (Grid) */}
              <div className="grid grid-cols-2 md:grid-cols-12 gap-4 items-end">
                <div className="col-span-2 md:col-span-5">
                    <FormField
                        control={form.control}
                        // @ts-ignore
                        name={`specific_details.schedule.${index}.day_of_week`}
                        render={({ field }) => (
                        <FormItem>
                            <FormLabel className="text-xs">Día</FormLabel>
                            <Select onValueChange={field.onChange} defaultValue={field.value}>
                            <FormControl>
                                <SelectTrigger className="bg-background">
                                <SelectValue placeholder="Día" />
                                </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                                {DAYS_OF_WEEK.map((day) => (
                                <SelectItem key={day} value={day}>{day}</SelectItem>
                                ))}
                            </SelectContent>
                            </Select>
                            <FormMessage />
                        </FormItem>
                        )}
                    />
                </div>

                <div className="col-span-1 md:col-span-3">
                    <FormField
                    control={form.control}
                    // @ts-ignore
                    name={`specific_details.schedule.${index}.time`}
                    render={({ field }) => (
                        <FormItem>
                        <FormLabel className="text-xs">Hora</FormLabel>
                        <div className="relative">
                            <Input type="time" {...field} className="bg-background pl-8" />
                            <Clock className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                        </div>
                        <FormMessage />
                        </FormItem>
                    )}
                    />
                </div>

                <div className="col-span-1 md:col-span-3">
                    <FormField
                    control={form.control}
                    // @ts-ignore
                    name={`specific_details.schedule.${index}.duration_minutes`}
                    render={({ field }) => (
                        <FormItem>
                        <FormLabel className="text-xs">Duración (min)</FormLabel>
                        <FormControl>
                            <Input 
                            type="number" 
                            {...field} 
                            onChange={e => field.onChange(parseInt(e.target.value))} 
                            className="bg-background" 
                            />
                        </FormControl>
                        <FormMessage />
                        </FormItem>
                    )}
                    />
                </div>

                <div className="col-span-2 md:col-span-1 flex justify-end md:justify-center pb-1">
                    <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="text-muted-foreground hover:text-destructive h-8 w-8"
                        onClick={() => remove(index)}
                    >
                        <Trash2 className="h-4 w-4" />
                    </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      
      {fields.length === 0 && (
         <div className="text-center p-8 border border-dashed rounded-lg bg-muted/10">
            <Calendar className="mx-auto h-10 w-10 text-muted-foreground/50 mb-3" />
            <h3 className="text-sm font-medium">No hay sesiones configuradas</h3>
            <p className="text-xs text-muted-foreground mt-1 mb-4">Agrega las sesiones recurrentes para que tus alumnos se organicen.</p>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => append({ title: "Sesión de Bienvenida", day_of_week: "Lunes", time: "19:00", duration_minutes: 60 })}
            >
              Crear primera sesión
            </Button>
         </div>
      )}
    </div>
  );
}
