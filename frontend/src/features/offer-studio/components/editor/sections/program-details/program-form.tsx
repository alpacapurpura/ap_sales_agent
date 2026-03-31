"use client";

import { UseFormReturn } from "react-hook-form";
import { SectionFormWrapper } from "../common/section-form-wrapper";
import { OfferSchema, OfferFormValues } from "../../../../types/schema";
import { ProgramStructure, LiveInteractionType, CommunityPlatform } from "../../../../types";
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Checkbox } from "@/components/ui/checkbox";
import { RichSelect } from "@/components/ui/rich-select";
import { SmartDateTimePicker } from "@/components/ui/smart-datetime-picker";
import { TimezoneSelect } from "@/components/ui/timezone-select";
import { 
  PROGRAM_STRUCTURE_METADATA, 
  LIVE_INTERACTION_METADATA, 
  COMMUNITY_PLATFORM_METADATA, 
  getEnumOptions 
} from "../../../../types/enum-metadata";
import { SessionScheduleBuilder } from "./session-schedule-builder";
import { CurriculumBuilder } from "./curriculum-builder";
import { CalendarIcon, Clock, Sparkles, Shield, ShieldCheck } from "lucide-react";
import { format, parseISO } from "date-fns";
import { cn } from "@/lib/utils";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

const ProgramDetailsSchema = OfferSchema.pick({
  specific_details: true
});

type ProgramDetailsFormValues = Pick<OfferFormValues, "specific_details">;

export interface ProgramDetailsFormProps {
  defaultValues: Partial<OfferFormValues>;
  onSave: (data: Partial<OfferFormValues>) => Promise<void>;
  form?: any;
}

// MAPPING: Smart Suggestions based on Structure
const STRUCTURE_INTERACTION_RECOMMENDATIONS: Record<string, LiveInteractionType[]> = {
  [ProgramStructure.FIXED_COHORT]: [
    LiveInteractionType.WORKSHOPS,
    LiveInteractionType.HOT_SEATS,
    LiveInteractionType.GROUP_Q_AND_A,
    LiveInteractionType.ONE_ON_ONE_CHECKINS
  ],
  [ProgramStructure.ROLLING_ADMISSION]: [
    LiveInteractionType.GROUP_Q_AND_A,
    LiveInteractionType.NONE,
    LiveInteractionType.WORKSHOPS,
    LiveInteractionType.ONE_ON_ONE_CHECKINS
  ],
  [ProgramStructure.CHALLENGE]: [
    LiveInteractionType.WORKSHOPS,
    LiveInteractionType.GROUP_Q_AND_A,
    LiveInteractionType.HOT_SEATS
  ],
  [ProgramStructure.MEMBERSHIP]: [
    LiveInteractionType.GROUP_Q_AND_A,
    LiveInteractionType.WORKSHOPS,
    LiveInteractionType.NONE
  ]
};

function ProgramDetailsContent({ form }: { form: UseFormReturn<OfferFormValues> }) {
  const timezone = form.watch("specific_details.timezone") || "UTC";
  const structureType = form.watch("specific_details.structure_type") as ProgramStructure;
  const isCohortOrChallenge = structureType === ProgramStructure.FIXED_COHORT || structureType === ProgramStructure.CHALLENGE;

  // Filter Logic
  const allInteractionOptions = getEnumOptions(LIVE_INTERACTION_METADATA);
  const recommendedTypes = structureType ? STRUCTURE_INTERACTION_RECOMMENDATIONS[structureType] : [];
  
  const filteredInteractionOptions = structureType 
    ? allInteractionOptions.filter(opt => recommendedTypes.includes(opt.value as LiveInteractionType))
    : allInteractionOptions;

  return (
    <div className="space-y-8">
      {/* 1. Diseño del Programa (Unified Structure & Dynamics) */}
      <Card className="border-indigo-100 dark:border-indigo-900/50 shadow-sm">
        <CardHeader className="bg-indigo-50/50 dark:bg-indigo-950/20 border-b pb-4">
            <CardTitle className="flex items-center gap-2 text-indigo-900 dark:text-indigo-300">
                <Sparkles className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
                Diseño del Programa
            </CardTitle>
            <CardDescription>
                Configura la estructura, duración y experiencia de entrega de tu programa.
            </CardDescription>
        </CardHeader>
        <CardContent className="space-y-8 pt-6">
            {/* ROW 1: Structure Type & Gatekeeping */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <FormField
                    control={form.control}
                    name="specific_details.structure_type"
                    render={({ field }) => (
                    <FormItem>
                        <FormLabel>Tipo de Estructura</FormLabel>
                        <RichSelect 
                        options={getEnumOptions(PROGRAM_STRUCTURE_METADATA)}
                        value={field.value as string}
                        onValueChange={(val) => {
                            field.onChange(val);
                            // Reset interaction if not valid? No, let user decide.
                        }}
                        placeholder="Selecciona estructura..."
                        />
                        <FormDescription className="text-xs">
                            Define el ritmo: Cohorte (Fecha Fija), Evergreen (Rolling) o Reto.
                        </FormDescription>
                        <FormMessage />
                    </FormItem>
                    )}
                />

                <FormField
                    control={form.control}
                    name="specific_details.is_application_required"
                    render={({ field }) => (
                    <FormItem>
                        <div className={cn(
                        "rounded-lg border p-3 transition-all duration-300 h-full flex flex-col justify-center",
                        field.value 
                            ? "bg-indigo-50 dark:bg-indigo-950/40 border-indigo-200 dark:border-indigo-800" 
                            : "bg-muted/10 border-muted/20"
                        )}>
                        <div className="flex flex-row items-center justify-between gap-4">
                            <div className="space-y-0.5">
                                <div className="flex items-center gap-2">
                                    {field.value 
                                    ? <ShieldCheck className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                                    : <Shield className="h-4 w-4 text-muted-foreground" />
                                    }
                                    <FormLabel className={cn("text-sm font-semibold cursor-pointer", field.value ? "text-indigo-900 dark:text-indigo-300" : "text-muted-foreground")}>
                                    Requiere Aplicación
                                    </FormLabel>
                                </div>
                                <p className={cn("text-[10px]", field.value ? "text-indigo-700/80 dark:text-indigo-400/80" : "text-muted-foreground")}>
                                    Filtra alumnos antes del pago (High Ticket).
                                </p>
                            </div>
                            <FormControl>
                            <Switch
                                checked={field.value as boolean}
                                onCheckedChange={field.onChange}
                                className={cn(field.value && "data-[state=checked]:bg-indigo-600")}
                            />
                            </FormControl>
                        </div>
                        </div>
                    </FormItem>
                    )}
                />
            </div>

            {/* ROW 2: Dynamics (Filtered) & Duration */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 items-start">
                <FormField
                    control={form.control}
                    name="specific_details.duration_weeks"
                    render={({ field }) => (
                    <FormItem>
                        <FormLabel>
                            {structureType === ProgramStructure.CHALLENGE ? "Duración (Días)" : "Duración (Semanas)"}
                        </FormLabel>
                        <FormControl>
                            <div className="relative">
                                <Input 
                                    type="number" 
                                    {...field} 
                                    onChange={e => field.onChange(parseInt(e.target.value))} 
                                    value={field.value as number || 0} 
                                    className="pl-9"
                                />
                                <Clock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                            </div>
                        </FormControl>
                        <FormMessage />
                    </FormItem>
                    )}
                />

                <FormField
                    control={form.control}
                    name="specific_details.interaction_type"
                    render={({ field }) => (
                    <FormItem className="lg:col-span-1">
                        <FormLabel>Dinámica de Interacción</FormLabel>
                        <RichSelect 
                            options={filteredInteractionOptions}
                            value={field.value as string}
                            onValueChange={field.onChange}
                            placeholder={structureType ? "Selecciona dinámica..." : "Primero elige estructura"}
                            disabled={!structureType}
                        />
                        <FormMessage />
                    </FormItem>
                    )}
                />

                <FormField
                    control={form.control}
                    name="specific_details.community_platform"
                    render={({ field }) => (
                    <FormItem>
                        <FormLabel>Plataforma de Comunidad</FormLabel>
                        <RichSelect 
                            options={getEnumOptions(COMMUNITY_PLATFORM_METADATA)}
                            value={field.value as string}
                            onValueChange={field.onChange}
                            placeholder="¿Dónde interactúan?"
                        />
                        <FormMessage />
                    </FormItem>
                    )}
                />
            </div>

            {/* ROW 3: Schedule Builder */}
            <div className="pt-4 border-t border-dashed">
                <SessionScheduleBuilder form={form} />
            </div>
        </CardContent>
      </Card>

      {/* 2. CURRICULUM (Nuevo: Estructura Educativa) */}
      <div className="pt-2">
         <CurriculumBuilder form={form} />
      </div>

      {/* 3. Calendario de Lanzamiento (Solo Cohortes/Challenges) */}
      {isCohortOrChallenge && (
        <Card className="border-l-4 border-l-primary/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
                <CalendarIcon className="h-5 w-5 text-primary" />
                Calendario de Lanzamiento
            </CardTitle>
            <CardDescription>
                Configura las fechas clave para tu cohorte o reto.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <FormField
              control={form.control}
              name="specific_details.timezone"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Zona Horaria del Programa</FormLabel>
                  <TimezoneSelect 
                    value={field.value as string} 
                    onValueChange={field.onChange} 
                  />
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Columna Izquierda: Inicio y Cierre */}
              <div className="space-y-6">
                <div className="space-y-2">
                    <Label>Fecha y Hora de Inicio (Kick-off)</Label>
                    <div className="flex gap-2">
                        {/* Date Picker Custom Implementation since SmartDateTimePicker combines them */}
                        <FormField
                            control={form.control}
                            name="specific_details.start_date"
                            render={({ field }) => (
                                <FormItem className="flex-1">
                                    <Popover>
                                        <PopoverTrigger asChild>
                                            <FormControl>
                                                <Button
                                                    variant={"outline"}
                                                    className={cn(
                                                        "w-full pl-3 text-left font-normal",
                                                        !field.value && "text-muted-foreground"
                                                    )}
                                                >
                                                    {field.value ? (
                                                        format(parseISO(field.value as string), "PPP")
                                                    ) : (
                                                        <span>Seleccionar fecha</span>
                                                    )}
                                                    <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                                                </Button>
                                            </FormControl>
                                        </PopoverTrigger>
                                        <PopoverContent className="w-auto p-0" align="start">
                                            <Calendar
                                                mode="single"
                                                selected={field.value ? parseISO(field.value as string) : undefined}
                                                onSelect={(date) => {
                                                    if (!date) return;
                                                    // Preserve time if exists, or set default
                                                    const current = field.value ? parseISO(field.value as string) : new Date();
                                                    date.setHours(current.getHours(), current.getMinutes());
                                                    field.onChange(date.toISOString());
                                                }}
                                                initialFocus
                                            />
                                        </PopoverContent>
                                    </Popover>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        {/* Time Picker */}
                        <FormField
                            control={form.control}
                            name="specific_details.start_date"
                            render={({ field }) => {
                                const dateVal = field.value ? parseISO(field.value as string) : null;
                                const timeStr = dateVal ? format(dateVal, "HH:mm") : "";
                                return (
                                    <FormItem className="w-32">
                                        <FormControl>
                                            <Input 
                                                type="time" 
                                                value={timeStr}
                                                onChange={(e) => {
                                                    if (!field.value) return; // Must select date first
                                                    const [hours, minutes] = e.target.value.split(':').map(Number);
                                                    const newDate = parseISO(field.value as string);
                                                    newDate.setHours(hours || 0);
                                                    newDate.setMinutes(minutes || 0);
                                                    field.onChange(newDate.toISOString());
                                                }}
                                            />
                                        </FormControl>
                                    </FormItem>
                                )
                            }}
                        />
                    </div>
                    <p className="text-[0.8rem] text-muted-foreground">La hora es opcional (se asume 00:00 si no se define).</p>
                </div>

                <FormField
                    control={form.control}
                    name="specific_details.registration_end_date"
                    render={({ field }) => (
                        <FormItem className="space-y-3 rounded-md border p-3 bg-background">
                            <div className="flex flex-row items-start space-x-3 space-y-0">
                                <FormControl>
                                    <Checkbox
                                        checked={!!field.value}
                                        onCheckedChange={(checked) => {
                                            if (checked) {
                                                // Default to start date if available, or today
                                                const startDate = form.getValues("specific_details.start_date");
                                                field.onChange(startDate || new Date().toISOString());
                                            } else {
                                                field.onChange(null);
                                            }
                                        }}
                                    />
                                </FormControl>
                                <div className="space-y-1 leading-none">
                                    <FormLabel>
                                        Definir fecha de Cierre de Inscripciones
                                    </FormLabel>
                                    <FormDescription>
                                        Si no se activa, se asume que cierran al iniciar el programa.
                                    </FormDescription>
                                </div>
                            </div>
                            {field.value && (
                                <SmartDateTimePicker 
                                    value={field.value as string} 
                                    onChange={field.onChange} 
                                    timezone={timezone}
                                />
                            )}
                        </FormItem>
                    )}
                />
              </div>

              {/* Columna Derecha: Fin */}
              <div className="space-y-6">
                <div className="space-y-2">
                    <Label>Fecha de Fin (Graduación)</Label>
                    <FormField
                        control={form.control}
                        name="specific_details.end_date"
                        render={({ field }) => (
                            <FormItem>
                                <Popover>
                                    <PopoverTrigger asChild>
                                        <FormControl>
                                            <Button
                                                variant={"outline"}
                                                className={cn(
                                                    "w-full pl-3 text-left font-normal",
                                                    !field.value && "text-muted-foreground"
                                                )}
                                            >
                                                {field.value ? (
                                                    format(parseISO(field.value as string), "PPP")
                                                ) : (
                                                    <span>Seleccionar fecha de fin</span>
                                                )}
                                                <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                                            </Button>
                                        </FormControl>
                                    </PopoverTrigger>
                                    <PopoverContent className="w-auto p-0" align="start">
                                        <Calendar
                                            mode="single"
                                            selected={field.value ? parseISO(field.value as string) : undefined}
                                            onSelect={(date) => {
                                                if (date) {
                                                    // Set end of day usually? Or keep same time? User said "no time".
                                                    // Let's set it to 23:59:59 of that day to be inclusive
                                                    date.setHours(23, 59, 59);
                                                    field.onChange(date.toISOString());
                                                } else {
                                                    field.onChange(null);
                                                }
                                            }}
                                            initialFocus
                                        />
                                    </PopoverContent>
                                </Popover>
                                <FormMessage />
                            </FormItem>
                        )}
                    />
                    
                    <FormField
                        control={form.control}
                        name="specific_details.is_end_date_estimated"
                        render={({ field }) => (
                            <FormItem className="flex flex-row items-start space-x-3 space-y-0 mt-2">
                                <FormControl>
                                    <Checkbox
                                        checked={field.value as boolean}
                                        onCheckedChange={field.onChange}
                                    />
                                </FormControl>
                                <div className="space-y-1 leading-none">
                                    <FormLabel className="font-normal text-muted-foreground">
                                        Esta fecha es estimada
                                    </FormLabel>
                                </div>
                            </FormItem>
                        )}
                    />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export function ProgramDetailsForm({ defaultValues: propValues, onSave }: ProgramDetailsFormProps) {
  const defaultValues: ProgramDetailsFormValues = {
    specific_details: propValues?.specific_details || {}
  };

  const handleSave = async (data: ProgramDetailsFormValues) => {
    await onSave(data);
  };

  return (
    <SectionFormWrapper<ProgramDetailsFormValues>
      schema={ProgramDetailsSchema}
      defaultValues={defaultValues}
      onSubmit={handleSave}
    >
      {(form) => (
        <ProgramDetailsContent form={form as unknown as UseFormReturn<OfferFormValues>} />
      )}
    </SectionFormWrapper>
  );
}
