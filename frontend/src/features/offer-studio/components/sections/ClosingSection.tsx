"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { SectionProps } from "../../types/section";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { RichSelect } from "@/components/ui/rich-select";
import { Target, ShieldCheck } from "lucide-react";
import { OnboardingMechanism, GuaranteeType } from "../../types";
import { eventTypesApi, EventType } from "@/lib/api/event-types";

export function ClosingSection({ form }: SectionProps) {
  const { getToken } = useAuth();
  const [appointmentTypes, setAppointmentTypes] = useState<EventType[]>([]);

  useEffect(() => {
    const fetchEventTypes = async () => {
        try {
            const token = await getToken();
            if (!token) return;
            const data = await eventTypesApi.listEventTypes(token);
            setAppointmentTypes(data);
        } catch (error) {
            console.error("Failed to load event types", error);
        }
    };
    fetchEventTypes();
  }, [getToken]);

  const onboardingOptions = [
      { value: OnboardingMechanism.CHECKOUT_LINK, label: "Venta Directa (Checkout)", description: "Muestra un link de pago directo. Ideal para productos de bajo ticket." },
      { value: OnboardingMechanism.CALENDAR_BOOKING, label: "Agendar Cita (Consultiva)", description: "Muestra el calendario para agendar. Ideal para High Ticket." },
      { value: OnboardingMechanism.INTAKE_FORM, label: "Aplicación / Formulario", description: "Requiere llenar un formulario antes de comprar." },
      { value: OnboardingMechanism.COMMUNITY_INVITE, label: "Invitación a Comunidad", description: "Acceso directo a Discord/Skool/WhatsApp." },
  ];

  const guaranteeOptions = [
    { 
      value: GuaranteeType.UNCONDITIONAL_X_DAY, 
      label: "Incondicional (X Días)", 
      description: "Devolución total sin preguntas dentro del periodo." 
    },
    { 
      value: GuaranteeType.CONDITIONAL_ACTION_BASED, 
      label: "Condicional (Basada en Acción)", 
      description: "Reembolso solo si demuestran haber hecho el trabajo." 
    },
    { 
      value: GuaranteeType.EXCHANGE_ONLY, 
      label: "Solo Intercambio / Crédito", 
      description: "No se devuelve dinero, solo cambio por otro producto." 
    },
    { 
      value: GuaranteeType.NO_REFUNDS, 
      label: "Sin Reembolsos (Venta Final)", 
      description: "Estricto. Ideal para servicios ya consumidos o eventos." 
    }
  ];

  return (
    <div className="grid md:grid-cols-2 gap-6">
        {/* CARD A: ENTRY METHOD */}
        <Card className="border-emerald-100 dark:border-emerald-900/50 shadow-sm h-full">
            <CardHeader className="pb-3 border-b bg-emerald-50/50 dark:bg-emerald-950/20">
                <CardTitle className="text-base flex items-center gap-2">
                    <Target className="w-4 h-4 text-emerald-600"/> 
                    Método de Entrada
                </CardTitle>
                <CardDescription>¿Cómo compran o agendan?</CardDescription>
            </CardHeader>
            <CardContent className="pt-6 space-y-4">
                <FormField control={form.control} name="onboarding_action" render={({ field }) => (
                    <FormItem>
                        <RichSelect 
                            options={onboardingOptions}
                            value={field.value || undefined}
                            onValueChange={field.onChange}
                            placeholder="Selecciona método..."
                        />
                        <FormMessage />
                    </FormItem>
                )} />

                {form.watch("onboarding_action") === OnboardingMechanism.CHECKOUT_LINK && (
                    <div className="pt-2 animate-in fade-in slide-in-from-top-2">
                        <FormField control={form.control} name="checkout_page_url" render={({ field }) => (
                            <FormItem>
                                <FormLabel className="text-xs font-semibold text-muted-foreground uppercase">Link de Pago</FormLabel>
                                <FormControl><Input placeholder="https://stripe.com/..." {...field} value={field.value || ""} /></FormControl>
                            </FormItem>
                        )} />
                    </div>
                )}
                
                {form.watch("onboarding_action") === OnboardingMechanism.CALENDAR_BOOKING && (
                    <div className="pt-2 animate-in fade-in slide-in-from-top-2">
                        <FormField control={form.control} name="calendar_type_id" render={({ field }) => (
                            <FormItem>
                                <FormLabel className="text-xs font-semibold text-muted-foreground uppercase">Tipo de Cita</FormLabel>
                                <RichSelect 
                                    options={appointmentTypes.map(t => ({
                                        value: t.id,
                                        label: t.title,
                                        description: `${t.duration} min • /${t.slug}`
                                    }))}
                                    value={field.value || undefined}
                                    onValueChange={field.onChange}
                                    placeholder="Selecciona tipo de cita..."
                                />
                            </FormItem>
                        )} />
                    </div>
                )}
            </CardContent>
        </Card>

        {/* CARD B: RISK REVERSAL */}
        <Card className="border-emerald-100 dark:border-emerald-900/50 shadow-sm h-full">
            <CardHeader className="pb-3 border-b bg-emerald-50/50 dark:bg-emerald-950/20">
                <CardTitle className="text-base flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-600"/> 
                    Garantía
                </CardTitle>
                <CardDescription>Elimina el riesgo de compra.</CardDescription>
            </CardHeader>
            <CardContent className="pt-6 space-y-4">
                    <FormField control={form.control} name="guarantee_type" render={({ field }) => (
                    <FormItem>
                        <RichSelect 
                            options={guaranteeOptions}
                            value={field.value}
                            onValueChange={field.onChange}
                            placeholder="Selecciona nivel de riesgo..."
                        />
                        <FormMessage />
                    </FormItem>
                )} />

                {/* Conditional Inputs for Guarantee Terms */}
                {form.watch("guarantee_type") === GuaranteeType.UNCONDITIONAL_X_DAY && (
                    <div className="pt-2 animate-in fade-in slide-in-from-top-2">
                        <FormField control={form.control} name="guarantee_terms" render={({ field }) => (
                            <FormItem>
                                <FormLabel className="text-xs font-semibold text-muted-foreground uppercase">Días para Reembolso</FormLabel>
                                <FormControl>
                                    <div className="relative">
                                        <Input 
                                            type="number" 
                                            placeholder="30" 
                                            {...field} 
                                            value={field.value || ""} 
                                            className="pl-9"
                                        />
                                        <div className="absolute left-3 top-2.5 text-xs text-muted-foreground font-bold">#</div>
                                    </div>
                                </FormControl>
                                <FormDescription className="text-xs">
                                    El cliente tiene X días para pedir su dinero de vuelta.
                                </FormDescription>
                            </FormItem>
                        )} />
                    </div>
                )}

                {form.watch("guarantee_type") === GuaranteeType.CONDITIONAL_ACTION_BASED && (
                    <div className="pt-2 animate-in fade-in slide-in-from-top-2">
                        <FormField control={form.control} name="guarantee_terms" render={({ field }) => (
                            <FormItem>
                                <FormLabel className="text-xs font-semibold text-muted-foreground uppercase">Condiciones Requeridas</FormLabel>
                                <FormControl>
                                    <Textarea 
                                        placeholder="Ej. Haber completado el módulo 3 y asistido a 2 llamadas..." 
                                        {...field} 
                                        value={field.value || ""} 
                                        className="min-h-[80px] text-sm"
                                    />
                                </FormControl>
                            </FormItem>
                        )} />
                    </div>
                )}
            </CardContent>
        </Card>
    </div>
  );
}
