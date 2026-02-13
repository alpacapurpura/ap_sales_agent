"use client";

import { useEffect, useState } from "react";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useAuth } from "@clerk/nextjs";
import { OfferSchema, 
  OfferFormValues, 
  OfferStatus, 
  FinancialCapacity,
  AccessDuration,
  OfferType
} from "../types/schema";
import { offerApi } from "@/lib/api/offer";
import { avatarApi, Avatar } from "@/lib/api/avatar";
import { Button } from "@/components/ui/button";
import { OFFER_TYPE_METADATA } from "../types/offer-metadata";
import { ACCESS_DURATION_METADATA } from "../types/enum-metadata";
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Save, ArrowLeft, Plus, Trash2, DollarSign, Target, Sparkles, CreditCard, Star, ShieldCheck, Clock } from "lucide-react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { 
  GuaranteeType, 
  OnboardingMechanism,
} from "../types";
import { PaymentPlanType } from "../types/schema";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { CurrencySelector } from "@/components/ui/currency-selector";
import { CURRENCIES } from "@/lib/constants/currencies";
import { eventTypesApi, EventType } from "@/lib/api/event-types";
import { PolymorphicFactory } from "./ui/polymorphic-factory";
import { RichSelect } from "@/components/ui/rich-select";
import { ValueStackStep } from "./steps/value-stack-step";
import { ResourcesStep } from "./steps/resources-step";
import { OfferContextPanel, OfferPhase, getOfferValidationStatus } from "./ui/offer-context-panel";
import { OfferGallerySection } from "./offer-gallery-section";
import { InstructorsSelector } from "./forms/instructors-selector";
import { cn } from "@/lib/utils";
import { Play, Pause, Archive, RotateCcw } from "lucide-react";
import { OfferPsychologyCard } from "./cards/offer-psychology-card";

export function OfferEditor({ offerId }: { offerId: string }) {
  const { getToken } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [generatingPsychology, setGeneratingPsychology] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ALLOWED_CURRENCY_CODES = ["USD", "PEN", "COP", "ARS", "MXN", "CLP"];
  const LATAM_CURRENCIES = CURRENCIES.filter(c => ALLOWED_CURRENCY_CODES.includes(c.code));

  const [avatars, setAvatars] = useState<Avatar[]>([]);
  const [appointmentTypes, setAppointmentTypes] = useState<EventType[]>([]);
  const [activePhase, setActivePhase] = useState<OfferPhase>('context');

  const form = useForm<OfferFormValues>({
    resolver: zodResolver(OfferSchema) as any,
    defaultValues: {
      status: OfferStatus.DRAFT,
      requires_application: false,
      min_financial_capacity: FinancialCapacity.LOW,
      specific_details: undefined,
      pricing_options: [],
      target_avatar_match: [],
      marketing_pain_points: [],
      marketing_desires: [],
      prerequisites: [],
      includes_offers: [],
      deliverables: [],
    } as any,
    mode: "onChange",
  });
  
  const { fields: pricingFields, append: addPricing, remove: removePricing, update: updatePricing } = useFieldArray({
    control: form.control,
    name: "pricing_options",
  });

  const setPricingDefault = (index: number) => {
      // Logic: Set selected to true, all others to false
      pricingFields.forEach((field, i) => {
          const currentData = form.getValues(`pricing_options.${i}`);
          updatePricing(i, {
              ...currentData,
              is_default: i === index
          });
      });
  };

  useEffect(() => {
    const fetchOffer = async () => {
      if (!offerId || offerId === 'undefined') {
          console.error("Invalid Offer ID provided to editor");
          setError("ID de oferta no válido proporcionado");
          setLoading(false);
          return; 
      }
      try {
        const token = await getToken();
        if (!token) return;
        const data = await offerApi.getOffer(offerId, token);
        
        const formData = {
           ...data,
           public_name: data.name,
           pricing_options: data.pricing || [],
           // Ensure metadata fields are mapped back to form if they exist
           onboarding_action: data.metadata_info?.onboarding_action || data.onboarding_action,
           onboarding_url: data.metadata_info?.onboarding_url || data.onboarding_url,
           calendar_type_id: data.metadata_info?.calendar_type_id || data.calendar_type_id,
           checkout_page_url: data.metadata_info?.checkout_page_url || data.checkout_page_url,
           vsl_link: data.metadata_info?.vsl_link || data.vsl_link
        };
        form.reset(formData as unknown as OfferFormValues);
      } catch (error) {
        console.error("Failed to load offer", error);
        setError("Error al cargar la oferta. Por favor, intente nuevamente.");
      } finally {
        setLoading(false);
      }
    };
    fetchOffer();
  }, [offerId, getToken, form]);

  useEffect(() => {
    const fetchAvatars = async () => {
      try {
        const token = await getToken();
        if (!token) return;
        const data = await avatarApi.listAvatars(token);
        setAvatars(data);
      } catch (error) {
        console.error("Failed to load avatars", error);
      }
    };
    fetchAvatars();
  }, [getToken]);

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

  const saveOffer = async (data: OfferFormValues, statusOverride?: OfferStatus) => {
    setSaving(true);
    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      
      const payload = { ...data };
      if (statusOverride) {
          payload.status = statusOverride;
      }

      // Adapter for Backend Compatibility
      // 1. Map pricing_options (Frontend) -> pricing (Backend)
      (payload as any).pricing = data.pricing_options;

      // FIX: Remove metadata_info to prevent overwriting partial updates (like pains/desires)
      // with stale data from the initial fetch.
      delete (payload as any).metadata_info;

      await offerApi.saveOffer(offerId, payload as any, token);
      
      if (statusOverride) {
          form.setValue("status", statusOverride);
          toast.success(`Estado actualizado a ${statusOverride}`);
      } else {
          toast.success("Oferta guardada correctamente");
      }
    } catch (error) {
      console.error("Failed to save offer", error);
      toast.error("Error al guardar la oferta");
    } finally {
      setSaving(false);
    }
  };

  const onSubmit = async (data: OfferFormValues) => {
      await saveOffer(data);
  };

  const handleStatusChange = async (newStatus: OfferStatus) => {
      const currentValues = form.getValues();
      
      // Validation Logic for Activation
      if (newStatus === OfferStatus.ACTIVE) {
          const validation = getOfferValidationStatus(currentValues);
          if (!validation.isValid) {
              toast.error(`No se puede activar: Faltan ${validation.missingItems.length} requisitos.`);
              return;
          }
      }
      
      await saveOffer(currentValues, newStatus);
  };

  const onInvalid = (errors: any) => {
    console.error("Form validation errors:", JSON.stringify(errors, null, 2));
    toast.error("Por favor corrige los errores en el formulario antes de guardar.");
    
    // Optional: Auto-switch phase based on error location to help user find it
    const errorKeys = Object.keys(errors);
    if (errorKeys.some(k => ['public_name', 'type', 'avatar_id', 'marketing_pain_points', 'marketing_desires'].includes(k))) {
        setActivePhase('context');
    } else if (errorKeys.some(k => ['headline_promise', 'primary_outcome', 'time_to_value', 'specific_details', 'deliverables'].includes(k))) {
        setActivePhase('solution');
    } else if (errorKeys.some(k => ['onboarding_action', 'pricing_options', 'guarantee_type'].includes(k))) {
        setActivePhase('deal');
    }
  };

  const handleGeneratePsychology = async () => {
    const avatarId = form.getValues("avatar_id");
    const currentPains = form.getValues("marketing_pain_points") || [];
    const currentDesires = form.getValues("marketing_desires") || [];
    const offerName = form.getValues("public_name") || "Oferta sin nombre";
    const offerDesc = form.getValues("headline_promise");

    if (!avatarId) return;
    setGeneratingPsychology(true);

    try {
        const token = await getToken();
        if (!token) return;

        const result = await offerApi.generatePsychology({
            avatar_id: avatarId,
            offer_name: offerName,
            offer_description: offerDesc,
            current_pains: currentPains,
            current_desires: currentDesires
        }, token);

        // Replace with AI suggestions
        form.setValue("marketing_pain_points", result.pains as any);
        form.setValue("marketing_desires", result.desires as any);
        
        toast.success("Psicología generada con IA exitosamente");
    } catch (e) {
        toast.error("Error generando psicología con IA");
        console.error(e);
    } finally {
        setGeneratingPsychology(false);
    }
  };

  if (loading) {
    return <div className="flex h-96 items-center justify-center"><Loader2 className="animate-spin h-8 w-8 text-primary" /></div>;
  }

  if (error) {
      return (
          <div className="flex flex-col items-center justify-center h-96 gap-4">
              <div className="text-destructive font-medium">{error}</div>
              <div className="flex gap-4">
                <Link href="/offer-studio">
                  <Button variant="outline"><ArrowLeft className="mr-2 h-4 w-4" /> Volver</Button>
                </Link>
              </div>
          </div>
      );
  }

  const offerTypeOptions = Object.values(OFFER_TYPE_METADATA).map(meta => ({
      value: meta.type,
      label: meta.label,
      description: meta.hint
  }));

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
  
  const currentStatus = form.watch("status");

  return (
    <div className="flex flex-col h-[calc(100vh-9rem)] md:h-[calc(100vh-6rem)] min-h-[500px] overflow-hidden rounded-xl border shadow-sm bg-background">
      {/* Header Fijo */}
      <div className="flex items-center justify-between px-6 py-4 border-b bg-background z-10">
        <div className="flex items-center gap-4">
          <Link href="/offer-studio">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight">{form.watch("public_name") || "Nueva Oferta"}</h1>
                {currentStatus === OfferStatus.ACTIVE && <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />}
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span className="uppercase tracking-wider font-medium">{OFFER_TYPE_METADATA[form.watch("type")]?.label || form.watch("type")}</span>
                <span>•</span>
                <span className={cn(
                    "uppercase font-bold px-1.5 py-0.5 rounded text-[10px]",
                    currentStatus === OfferStatus.ACTIVE ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300" :
                    currentStatus === OfferStatus.PAUSED ? "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300" :
                    currentStatus === OfferStatus.ARCHIVED ? "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300" :
                    "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                )}>
                    {currentStatus}
                </span>
            </div>
          </div>
        </div>
        
        {/* Action Bar */}
        <div className="flex items-center gap-2">
            <Link href={`/editor/${offerId}`} target="_blank">
                <Button variant="outline" size="sm" className="cursor-pointer gap-2 border-purple-200 text-purple-700 hover:bg-purple-50">
                    <Sparkles className="h-4 w-4" /> Landing Page
                </Button>
            </Link>

            {/* Common Save (Secondary if Draft) */}
            <Button onClick={form.handleSubmit(onSubmit, onInvalid)} disabled={saving} variant="outline" size="sm" className="cursor-pointer">
              {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
              {currentStatus === OfferStatus.DRAFT ? "Guardar Borrador" : "Guardar Cambios"}
            </Button>

            {/* Status Transitions */}
            {currentStatus === OfferStatus.DRAFT && (
                <Button onClick={() => handleStatusChange(OfferStatus.ACTIVE)} disabled={saving} size="sm" className="cursor-pointer bg-emerald-600 hover:bg-emerald-700">
                    <Play className="mr-2 h-4 w-4" /> Publicar
                </Button>
            )}

            {currentStatus === OfferStatus.ACTIVE && (
                <Button onClick={() => handleStatusChange(OfferStatus.PAUSED)} disabled={saving} variant="secondary" size="sm" className="cursor-pointer text-amber-600 bg-amber-100 hover:bg-amber-200">
                    <Pause className="mr-2 h-4 w-4" /> Pausar
                </Button>
            )}

            {currentStatus === OfferStatus.PAUSED && (
                <>
                    <Button onClick={() => handleStatusChange(OfferStatus.ACTIVE)} disabled={saving} size="sm" className="cursor-pointer bg-emerald-600 hover:bg-emerald-700">
                        <Play className="mr-2 h-4 w-4" /> Reanudar
                    </Button>
                    <Button onClick={() => handleStatusChange(OfferStatus.ARCHIVED)} disabled={saving} variant="ghost" size="sm" className="cursor-pointer text-destructive hover:bg-destructive/10">
                        <Archive className="mr-2 h-4 w-4" /> Archivar
                    </Button>
                </>
            )}

             {currentStatus === OfferStatus.ARCHIVED && (
                <Button onClick={() => handleStatusChange(OfferStatus.DRAFT)} disabled={saving} variant="outline" size="sm" className="cursor-pointer">
                    <RotateCcw className="mr-2 h-4 w-4" /> Restaurar a Borrador
                </Button>
            )}
        </div>
      </div>

      <div className="flex-1 grid grid-cols-12 overflow-hidden">
          {/* LEFT PANEL: NARRATIVE FORM */}
          <div className="col-span-12 lg:col-span-7 xl:col-span-8 h-full overflow-y-auto p-6 lg:p-10 pb-32 scroll-smooth bg-slate-50/50 dark:bg-slate-950/20">
             <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit, onInvalid)} className="max-w-3xl mx-auto space-y-12">
                    
                    {/* PHASE 1: CONTEXT (Identity & Psychology) */}
                    <section 
                        id="phase-context" 
                        onFocusCapture={() => setActivePhase('context')}
                        className={cn("space-y-6 transition-opacity duration-300", activePhase !== 'context' && "opacity-60 hover:opacity-100")}
                    >
                        <div className="flex items-center gap-3 mb-4 border-b pb-2">
                            <div className="h-8 w-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold">1</div>
                            <h2 className="text-xl font-semibold">El Contexto</h2>
                            <span className="text-sm text-muted-foreground ml-auto">Estrategia & Identidad</span>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-4">
                                <FormField control={form.control} name="public_name" render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Nombre Público</FormLabel>
                                        <FormControl><Input {...field} className="bg-background" /></FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )} />
                                <FormField control={form.control} name="type" render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Tipo de Oferta</FormLabel>
                                        <RichSelect 
                                            options={offerTypeOptions} 
                                            value={field.value} 
                                            onValueChange={field.onChange} 
                                            disabled={true}
                                        />
                                        <FormMessage />
                                    </FormItem>
                                )} />
                            </div>

                            {/* Avatar Selector directly in context */}
                            <FormField control={form.control} name="avatar_id" render={({ field }) => (
                                <FormItem className="md:col-span-1">
                                    <FormLabel className="flex items-center gap-2">
                                        <Target className="w-4 h-4 text-primary" /> Avatar Match
                                    </FormLabel>
                                    <RichSelect 
                                        options={avatars.map(a => ({ 
                                            value: a.id, 
                                            label: a.name, 
                                            description: a.icp_description ? a.icp_description.substring(0, 60) + "..." : "Sin descripción" 
                                        }))} 
                                        value={field.value || undefined} 
                                        onValueChange={field.onChange} 
                                        placeholder="Selecciona Avatar..."
                                    />
                                    <FormDescription className="text-xs">
                                        ¿A quién le vendes? Define la psicología de la oferta.
                                    </FormDescription>
                                    <FormMessage />
                                </FormItem>
                            )} />
                        </div>

                        {/* Psychology Section */}
                        <OfferPsychologyCard 
                            control={form.control}
                            onGenerate={handleGeneratePsychology}
                            avatarSelected={!!form.watch("avatar_id")}
                            isGenerating={generatingPsychology}
                        />
                    </section>

                    {/* PHASE 2: SOLUTION (Promise & Delivery) */}
                    <section 
                        id="phase-solution" 
                        onFocusCapture={() => setActivePhase('solution')}
                        className={cn("space-y-6 transition-opacity duration-300", activePhase !== 'solution' && "opacity-60 hover:opacity-100")}
                    >
                         <div className="flex items-center gap-3 mb-4 border-b pb-2">
                            <div className="h-8 w-8 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center text-amber-600 dark:text-amber-400 font-bold">2</div>
                            <h2 className="text-xl font-semibold">La Solución</h2>
                            <span className="text-sm text-muted-foreground ml-auto">Promesa & Vehículo</span>
                        </div>

                        <Card className="border-amber-200/50 dark:border-amber-800/30 bg-amber-50/30 dark:bg-amber-950/10">
                            <CardContent className="pt-6 space-y-4">
                                <FormField control={form.control} name="headline_promise" render={({ field }) => (
                                    <FormItem>
                                        <FormLabel className="flex items-center gap-2 text-amber-700 dark:text-amber-400">
                                            <Sparkles className="w-4 h-4" /> La Gran Promesa (Headline)
                                        </FormLabel>
                                        <FormControl>
                                            <Textarea 
                                                className="text-lg font-medium resize-none bg-background min-h-[100px]" 
                                                placeholder="Te ayudo a lograr [Resultado] en [Tiempo] sin [Dolor]..." 
                                                {...field} 
                                            />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )} />
                                <div className="grid grid-cols-2 gap-4">
                                    <FormField control={form.control} name="primary_outcome" render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Resultado Tangible</FormLabel>
                                            <FormControl><Input placeholder="Ej. $10k/mes" {...field} className="bg-background" /></FormControl>
                                        </FormItem>
                                    )} />
                                    <FormField control={form.control} name="time_to_value" render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>Tiempo al Valor</FormLabel>
                                            <FormControl><Input placeholder="Ej. 90 días" {...field} className="bg-background" /></FormControl>
                                        </FormItem>
                                    )} />
                                </div>
                                {/* Access Duration Row */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                                    <FormField control={form.control} name="access_duration" render={({ field }) => (
                                        <FormItem>
                                            <FormLabel className="flex items-center gap-2">
                                                <Clock className="w-4 h-4" /> Duración del Acceso
                                            </FormLabel>
                                            <RichSelect 
                                                options={Object.entries(ACCESS_DURATION_METADATA).map(([k, v]) => ({ value: k, label: v.label, description: v.description }))}
                                                value={field.value || undefined}
                                                onValueChange={field.onChange}
                                                placeholder="Selecciona duración..."
                                            />
                                            <FormMessage />
                                        </FormItem>
                                    )} />
                                    
                                    {(form.watch("access_duration") === AccessDuration.LIMITED_TIME_ACCESS || form.watch("access_duration") === AccessDuration.HYBRID_ACCESS) && (
                                        <div className="animate-in fade-in slide-in-from-left-2">
                                             <FormField control={form.control} name="access_duration_text" render={({ field }) => (
                                                <FormItem>
                                                    <FormLabel>Tiempo Específico</FormLabel>
                                                    <FormControl><Input placeholder="Ej. 1 Año, 6 Meses..." {...field} value={field.value || ""} className="bg-background" /></FormControl>
                                                    <FormMessage />
                                                </FormItem>
                                            )} />
                                        </div>
                                    )}
                                </div>
                            </CardContent>
                        </Card>

                        {/* Polymorphic Form Container */}
                        <div className="space-y-4">
                            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Configuración del Vehículo</h3>
                            {form.watch("type") ? (
                                <PolymorphicFactory type={form.watch("type")} form={form} />
                            ) : (
                                <Card>
                                    <CardContent className="pt-6">
                                        <div className="text-center py-8 text-muted-foreground">Selecciona un tipo de oferta arriba.</div>
                                    </CardContent>
                                </Card>
                            )}
                        </div>

                        {/* Mentors / Instructors (Conditionally Rendered) */}
                        {[
                            OfferType.HYBRID_MENTORSHIP, 
                            OfferType.COHORT_BASED_COURSE, 
                            OfferType.GROUP_COACHING_PROGRAM, 
                            OfferType.ONE_ON_ONE_PRIVATE_MENTORING,
                            OfferType.MASTERMIND_NETWORK,
                            OfferType.VIP_DAY_STRATEGY,
                            OfferType.CORPORATE_TRAINING,
                            OfferType.KEYNOTE_SPEAKING
                        ].includes(form.watch("type")) && (
                            <div className="space-y-4">
                                <InstructorsSelector 
                                    selectedInstructorIds={(form.watch("instructors") || []) as string[]}
                                    onUpdate={(ids) => form.setValue("instructors", ids, { shouldDirty: true, shouldValidate: true })}
                                />
                            </div>
                        )}

                        {/* Value Stack (Conditionally Rendered) */}
                        {![
                            OfferType.HYBRID_MENTORSHIP, 
                            OfferType.COHORT_BASED_COURSE, 
                            OfferType.GROUP_COACHING_PROGRAM, 
                            OfferType.FREE_WEBINAR_CHALLENGE
                        ].includes(form.watch("type")) && (
                            <div className="space-y-4">
                                <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Stack de Valor</h3>
                                <ValueStackStep form={form} />
                            </div>
                        )}

                        {/* Agent Resources */}
                        <div className="space-y-4">
                             <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Recursos del Agente</h3>
                             <ResourcesStep form={form} />
                        </div>

                        {/* Offer Gallery */}
                        <div className="space-y-4">
                             <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Galería Visual</h3>
                             <Card>
                                <CardContent className="pt-6">
                                    <OfferGallerySection offerId={offerId} />
                                </CardContent>
                             </Card>
                        </div>
                    </section>

                    {/* PHASE 3: DEAL (Economics & Closing) */}
                    <section 
                        id="phase-deal" 
                        onFocusCapture={() => setActivePhase('deal')}
                        className={cn("space-y-6 transition-opacity duration-300", activePhase !== 'deal' && "opacity-60 hover:opacity-100")}
                    >
                         <div className="flex items-center gap-3 mb-4 border-b pb-2">
                            <div className="h-8 w-8 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center text-emerald-600 dark:text-emerald-400 font-bold">3</div>
                            <h2 className="text-xl font-semibold">El Trato</h2>
                            <span className="text-sm text-muted-foreground ml-auto">Economía & Cierre</span>
                        </div>

                        {/* STACK VERTICAL: CLOSING FIRST, THEN PRICING */}
                        <div className="space-y-8">
                             {/* 1. CLOSING MECHANISM (SPLIT CARDS) */}
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

                             {/* 2. PRICING STRATEGY (SHOPIFY STYLE) */}
                             <Card className="overflow-hidden border-slate-200 dark:border-slate-800">
                                <CardHeader className="pb-4 border-b bg-slate-50 dark:bg-slate-900/50 flex flex-row items-center justify-between">
                                    <div>
                                        <CardTitle className="text-base flex items-center gap-2">
                                            <CreditCard className="w-4 h-4 text-primary"/> 
                                            Estrategia de Precios
                                        </CardTitle>
                                        <CardDescription>Configura tus planes de pago, suscripciones o precios únicos.</CardDescription>
                                    </div>
                                    <div className="flex items-center gap-3">
                                         <FormField control={form.control} name="currency" render={({ field }) => (
                                            <FormItem className="space-y-0">
                                                <FormControl>
                                                    <CurrencySelector 
                                                        value={field.value} 
                                                        onValueChange={field.onChange} 
                                                        currencies={LATAM_CURRENCIES}
                                                        className="w-[140px] h-8 text-xs"
                                                    />
                                                </FormControl>
                                            </FormItem>
                                        )} />
                                        <Button type="button" size="sm" onClick={() => addPricing({ 
                                            label: "Nuevo Precio", 
                                            plan_type: PaymentPlanType.PAY_IN_FULL,
                                            total_amount: 0, 
                                            deposit_required: 0, 
                                            number_of_installments: 1, 
                                            installment_amount: 0, 
                                            is_default: false 
                                        })}>
                                            <Plus className="h-4 w-4 mr-2"/> Agregar Opción
                                        </Button>
                                    </div>
                                </CardHeader>
                                <CardContent className="p-0 bg-slate-50/30 dark:bg-slate-950/30">
                                    {pricingFields.length === 0 ? (
                                        <div className="text-center py-12 text-muted-foreground">
                                            <DollarSign className="w-10 h-10 mx-auto mb-3 opacity-20" />
                                            <p>No hay precios definidos.</p>
                                            <p className="text-xs">Agrega una opción de pago para comenzar.</p>
                                        </div>
                                    ) : (
                                        <div className="divide-y">
                                            {pricingFields.map((field, index) => {
                                                // Watch values for reactive UI inside the map
                                                const planType = form.watch(`pricing_options.${index}.plan_type`);
                                                const totalAmount = form.watch(`pricing_options.${index}.total_amount`) || 0;
                                                const deposit = form.watch(`pricing_options.${index}.deposit_required`) || 0;
                                                const installments = form.watch(`pricing_options.${index}.number_of_installments`) || 1;
                                                const isDefault = form.watch(`pricing_options.${index}.is_default`);
                                                
                                                // Calculate installment amount dynamically
                                                const calculatedInstallment = installments > 0 ? (totalAmount - deposit) / installments : 0;
                                                const currency = form.watch("currency") || "USD";

                                                return (
                                                    <div key={field.id} className={cn(
                                                        "p-6 bg-background group hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors border-l-4",
                                                        isDefault ? "border-l-yellow-400 bg-yellow-50/10" : "border-l-transparent"
                                                    )}>
                                                        <div className="flex items-start justify-between mb-6">
                                                            <div className="flex items-center gap-4 flex-1">
                                                                <div className={cn(
                                                                    "h-10 w-10 rounded-full flex items-center justify-center font-bold text-sm transition-all",
                                                                    isDefault ? "bg-yellow-100 text-yellow-600 ring-2 ring-yellow-400 ring-offset-2" : "bg-primary/10 text-primary"
                                                                )}>
                                                                    {index + 1}
                                                                </div>
                                                                <div className="space-y-1 flex-1">
                                                                    <div className="flex items-center gap-2">
                                                                        <Input 
                                                                            className="h-8 text-lg font-semibold border-none p-0 focus-visible:ring-0 bg-transparent placeholder:text-muted-foreground/50 w-full max-w-[300px]" 
                                                                            {...form.register(`pricing_options.${index}.label`)} 
                                                                            placeholder="Nombre del Plan (Ej. Pago Único)" 
                                                                        />
                                                                        {isDefault && (
                                                                            <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100 text-[10px] uppercase font-bold tracking-wider">
                                                                                Popular
                                                                            </Badge>
                                                                        )}
                                                                    </div>
                                                                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                                                        <Badge variant="outline" className="text-[10px] uppercase font-normal">
                                                                            {planType === PaymentPlanType.PAY_IN_FULL ? "Pago Único" : 
                                                                             planType === PaymentPlanType.INTERNAL_SPLIT_PAY ? "Financiado" : "Suscripción"}
                                                                        </Badge>
                                                                        {planType === PaymentPlanType.INTERNAL_SPLIT_PAY && (
                                                                            <span>• {installments} cuotas de {currency} {calculatedInstallment.toFixed(2)}</span>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            </div>
                                                            
                                                            {/* Right Actions & Summary */}
                                                            <div className="flex items-start gap-4">
                                                                <div className="text-right mr-2 hidden md:block">
                                                                    <div className="text-lg font-bold text-slate-900 dark:text-slate-100">
                                                                        {currency} {totalAmount.toLocaleString()}
                                                                    </div>
                                                                    <div className="text-xs text-muted-foreground">
                                                                        Total a Pagar
                                                                    </div>
                                                                </div>

                                                                <div className="flex items-center gap-1">
                                                                    <Button 
                                                                        type="button" 
                                                                        variant="ghost" 
                                                                        size="icon" 
                                                                        className={cn("h-8 w-8 hover:text-yellow-500", isDefault ? "text-yellow-500" : "text-muted-foreground")} 
                                                                        onClick={() => setPricingDefault(index)}
                                                                        title="Marcar como opción recomendada"
                                                                    >
                                                                        <Star className={cn("h-4 w-4", isDefault && "fill-current")} />
                                                                    </Button>
                                                                    <Button type="button" variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive" onClick={() => removePricing(index)}>
                                                                        <Trash2 className="h-4 w-4"/>
                                                                    </Button>
                                                                </div>
                                                            </div>
                                                        </div>

                                                        {/* SMART EDITOR */}
                                                        <div className="pl-11">
                                                            <Tabs 
                                                                defaultValue={planType || PaymentPlanType.PAY_IN_FULL} 
                                                                onValueChange={(val) => form.setValue(`pricing_options.${index}.plan_type`, val as PaymentPlanType)}
                                                                className="w-full"
                                                            >
                                                                <TabsList className="mb-4 w-full justify-start h-auto p-1 bg-muted/50">
                                                                    <TabsTrigger value={PaymentPlanType.PAY_IN_FULL} className="text-xs">Pago Único</TabsTrigger>
                                                                    <TabsTrigger value={PaymentPlanType.INTERNAL_SPLIT_PAY} className="text-xs">Plan de Pagos</TabsTrigger>
                                                                    <TabsTrigger value={PaymentPlanType.SUBSCRIPTION_RECURRING} className="text-xs">Suscripción</TabsTrigger>
                                                                </TabsList>

                                                                <TabsContent value={PaymentPlanType.PAY_IN_FULL} className="mt-0 space-y-4">
                                                                    <div className="grid grid-cols-2 gap-4">
                                                                        <FormField
                                                                            control={form.control}
                                                                            name={`pricing_options.${index}.total_amount`}
                                                                            render={({ field }) => (
                                                                                <FormItem>
                                                                                    <FormLabel className="text-xs">Monto Total</FormLabel>
                                                                                    <div className="relative">
                                                                                        <DollarSign className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                                                                                        <FormControl>
                                                                                            <Input 
                                                                                                type="number" 
                                                                                                className="pl-8" 
                                                                                                {...field}
                                                                                                onChange={e => field.onChange(e.target.valueAsNumber)}
                                                                                            />
                                                                                        </FormControl>
                                                                                    </div>
                                                                                    <FormMessage />
                                                                                </FormItem>
                                                                            )}
                                                                        />
                                                                        <FormField
                                                                            control={form.control}
                                                                            name={`pricing_options.${index}.savings_claim`}
                                                                            render={({ field }) => (
                                                                                <FormItem>
                                                                                    <FormLabel className="text-xs">Texto de Ahorro (Opcional)</FormLabel>
                                                                                    <FormControl>
                                                                                        <Input placeholder="Ej. Ahorra $200 vs Plan" {...field} value={field.value || ""} />
                                                                                    </FormControl>
                                                                                    <FormMessage />
                                                                                </FormItem>
                                                                            )}
                                                                        />
                                                                    </div>
                                                                </TabsContent>

                                                                <TabsContent value={PaymentPlanType.INTERNAL_SPLIT_PAY} className="mt-0 space-y-4">
                                                                    <div className="grid grid-cols-3 gap-4">
                                                                        <FormField
                                                                            control={form.control}
                                                                            name={`pricing_options.${index}.total_amount`}
                                                                            render={({ field }) => (
                                                                                <FormItem>
                                                                                    <FormLabel className="text-xs">Monto Total del Plan</FormLabel>
                                                                                    <div className="relative">
                                                                                        <DollarSign className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                                                                                        <FormControl>
                                                                                            <Input 
                                                                                                type="number" 
                                                                                                className="pl-8" 
                                                                                                {...field}
                                                                                                onChange={e => field.onChange(e.target.valueAsNumber)}
                                                                                            />
                                                                                        </FormControl>
                                                                                    </div>
                                                                                    <FormMessage />
                                                                                </FormItem>
                                                                            )}
                                                                        />
                                                                         <FormField
                                                                            control={form.control}
                                                                            name={`pricing_options.${index}.deposit_required`}
                                                                            render={({ field }) => (
                                                                                <FormItem>
                                                                                    <FormLabel className="text-xs">Pago Inicial (Depósito)</FormLabel>
                                                                                    <div className="relative">
                                                                                        <DollarSign className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                                                                                        <FormControl>
                                                                                            <Input 
                                                                                                type="number" 
                                                                                                className="pl-8" 
                                                                                                {...field}
                                                                                                onChange={e => field.onChange(e.target.valueAsNumber)}
                                                                                            />
                                                                                        </FormControl>
                                                                                    </div>
                                                                                    <FormMessage />
                                                                                </FormItem>
                                                                            )}
                                                                        />
                                                                         <FormField
                                                                            control={form.control}
                                                                            name={`pricing_options.${index}.number_of_installments`}
                                                                            render={({ field }) => (
                                                                                <FormItem>
                                                                                    <FormLabel className="text-xs">N° de Cuotas</FormLabel>
                                                                                    <FormControl>
                                                                                        <Input 
                                                                                            type="number" 
                                                                                            {...field}
                                                                                            onChange={e => field.onChange(e.target.valueAsNumber)}
                                                                                        />
                                                                                    </FormControl>
                                                                                    <FormMessage />
                                                                                </FormItem>
                                                                            )}
                                                                        />
                                                                    </div>
                                                                    
                                                                    {/* Calculation Preview */}
                                                                    <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg flex items-center justify-between text-sm text-blue-700 dark:text-blue-300">
                                                                        <span className="font-medium">Resumen para el Cliente:</span>
                                                                        <span>
                                                                            Hoy paga <strong>${deposit}</strong> + {installments} cuotas de <strong>${calculatedInstallment.toFixed(2)}</strong>
                                                                        </span>
                                                                    </div>
                                                                </TabsContent>

                                                                <TabsContent value={PaymentPlanType.SUBSCRIPTION_RECURRING} className="mt-0">
                                                                    <div className="flex items-center gap-4">
                                                                         <FormField
                                                                            control={form.control}
                                                                            name={`pricing_options.${index}.total_amount`}
                                                                            render={({ field }) => (
                                                                                <FormItem className="flex-1">
                                                                                    <FormLabel className="text-xs">Monto por Período</FormLabel>
                                                                                    <div className="relative">
                                                                                        <DollarSign className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                                                                                        <FormControl>
                                                                                            <Input 
                                                                                                type="number" 
                                                                                                className="pl-8" 
                                                                                                {...field}
                                                                                                onChange={e => field.onChange(e.target.valueAsNumber)}
                                                                                            />
                                                                                        </FormControl>
                                                                                    </div>
                                                                                    <FormMessage />
                                                                                </FormItem>
                                                                            )}
                                                                        />
                                                                        <div className="flex-1 text-xs text-muted-foreground pt-6">
                                                                            La configuración de recurrencia se maneja en el procesador de pagos (Stripe). Aquí solo defines el precio visual.
                                                                        </div>
                                                                    </div>
                                                                </TabsContent>
                                                            </Tabs>
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    )}
                                </CardContent>
                             </Card>
                        </div>
                    </section>

                </form>
             </Form>
          </div>

          {/* RIGHT PANEL: CONTEXT & ASSISTANT */}
          <div className="col-span-0 lg:col-span-5 xl:col-span-4 hidden lg:block border-l bg-background h-full overflow-hidden">
             <OfferContextPanel 
                phase={activePhase}
                formValues={form.watch()}
                avatars={avatars}
                isDirty={form.formState.isDirty}
                onSave={async () => {
                    await saveOffer(form.getValues());
                }}
                onFieldChange={(field, value) => {
                    form.setValue(field as any, value, { shouldDirty: true, shouldValidate: true });
                }}
             />
          </div>
      </div>
    </div>
  );
}
