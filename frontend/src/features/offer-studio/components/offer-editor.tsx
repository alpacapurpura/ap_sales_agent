"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useAuth } from "@clerk/nextjs";
import { OfferSchema, OfferFormValues } from "../types/schema";
import { offerApi } from "@/lib/api/offer";
import { Button } from "@/components/ui/button";
import { Form } from "@/components/ui/form";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, Save, ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  OfferType, 
  DeliveryModel, 
  GuaranteeType, 
  ProgramType, 
  DeliverableFormat 
} from "../types/index";

// Steps
import { IdentityStep } from "./steps/identity-step";
import { SpecificDetailsStep } from "./steps/specific-details-step";
import { PromiseStep } from "./steps/promise-step";
import { ValueStackStep } from "./steps/value-stack-step";
import { PricingStep } from "./steps/pricing-step";
import { RulesStep } from "./steps/rules-step";

// Test Data for Development
const TEST_OFFER_DATA: OfferFormValues = {
  internal_sku: "TEST-001",
  public_name: "Programa de Prueba (High Ticket)",
  type: OfferType.COHORT_PROGRAM,
  delivery_model: DeliveryModel.DWY,
  headline_promise: "Transforma tu negocio en 90 días con nuestro sistema probado de ventas automatizadas.",
  target_avatar_match: ["Emprendedores Digitales", "Coaches", "Consultores"],
  primary_outcome: "Sistema de ventas instalado y generando leads cualificados.",
  time_to_value: "14 días para primeras ventas",
  requires_application: true,
  min_financial_capacity: "$2000 USD/mes disponible para inversión",
  prerequisites: ["Tener una oferta validada", "Web básica"],
  pricing_options: [
    {
      label: "Pago Único",
      total_amount: 2997,
      deposit_required: 500,
      number_of_installments: 1,
      installment_amount: 0,
      is_default: true,
      savings_claim: "Ahorra $500 vs Plan de Pagos"
    },
    {
      label: "Plan de Pagos",
      total_amount: 3500,
      deposit_required: 500,
      number_of_installments: 3,
      installment_amount: 1000,
      is_default: false
    }
  ],
  currency: "USD",
  guarantee_type: GuaranteeType.CONDITIONAL_ACTION_BASED,
  guarantee_terms: "Si implementas todo y no recuperas tu inversión, trabajamos contigo gratis hasta que lo logres.",
  includes_offers: [],
  deliverables: [
    {
      name: "Sesiones Grupales Semanales",
      format: DeliverableFormat.LIVE_CALL,
      quantity: "12",
      value_stack_price: 1997
    },
    {
      name: "Portal de Contenidos",
      format: DeliverableFormat.RECORDED_CONTENT,
      quantity: "Acceso de por vida",
      value_stack_price: 997
    }
  ],
  status: "DRAFT",
  specific_details: {
    program_type: ProgramType.COHORT_BASED,
    duration_weeks: 12,
    syllabus_modules: { "1": "Fundamentos", "2": "Estrategia", "3": "Implementación" },
    calls_per_week: 2,
    call_schedule_details: "Martes y Jueves 10 AM EST",
    are_calls_recorded: true,
    one_on_one_sessions: 3,
    includes_certification: true
  }
};

export function OfferEditor({ offerId }: { offerId: string }) {
  const { getToken } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("identity");

  const form = useForm<OfferFormValues>({
    resolver: zodResolver(OfferSchema) as any,
    defaultValues: {
      specific_details: undefined,
      pricing_options: [],
      target_avatar_match: [],
      prerequisites: [],
      includes_offers: [],
      deliverables: [],
    } as any,
    mode: "onChange",
  });

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
        
        // Cast API response to Form Values (ensure types match)
        form.reset(data as unknown as OfferFormValues);
      } catch (error) {
        console.error("Failed to load offer", error);
        setError("Error al cargar la oferta. Por favor, intente nuevamente.");
      } finally {
        setLoading(false);
      }
    };
    fetchOffer();
  }, [offerId, getToken, form]);

  const onSubmit = async (data: OfferFormValues) => {
    setSaving(true);
    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      
      await offerApi.saveOffer(offerId, data as any, token);
      // Optional: Show toast success
    } catch (error) {
      console.error("Failed to save offer", error);
      // Optional: Show toast error
    } finally {
      setSaving(false);
    }
  };

  const loadTestData = () => {
    form.reset(TEST_OFFER_DATA);
    setError(null);
    setLoading(false);
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
                  <Button variant="outline">
                      <ArrowLeft className="mr-2 h-4 w-4" /> Volver al Dashboard
                  </Button>
                </Link>
                <Button variant="secondary" onClick={loadTestData}>
                   🛠️ Cargar Datos de Prueba (Dev)
                </Button>
              </div>
          </div>
      );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/offer-studio">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">{form.watch("public_name") || "Editar Oferta"}</h1>
            <p className="text-sm text-muted-foreground">{form.watch("type")}</p>
          </div>
        </div>
        <Button onClick={form.handleSubmit(onSubmit)} disabled={saving}>
          {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
          Guardar Cambios
        </Button>
      </div>

      {/* Main Content */}
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="w-full justify-start overflow-x-auto">
              <TabsTrigger value="identity">Identidad</TabsTrigger>
              <TabsTrigger value="details">Detalles Específicos</TabsTrigger>
              <TabsTrigger value="promise">Promesa</TabsTrigger>
              <TabsTrigger value="stack">Value Stack</TabsTrigger>
              <TabsTrigger value="pricing">Economía</TabsTrigger>
              <TabsTrigger value="rules">Reglas</TabsTrigger>
            </TabsList>

            <div className="mt-6">
              <Card>
                <CardContent className="pt-6">
                  <TabsContent value="identity" className="mt-0">
                    <div className="space-y-6">
                        <IdentityStep form={form} />
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="details" className="mt-0">
                    <SpecificDetailsStep form={form} />
                  </TabsContent>

                  <TabsContent value="promise" className="mt-0">
                    <div className="space-y-6">
                        <PromiseStep form={form} />
                    </div>
                  </TabsContent>

                  <TabsContent value="stack" className="mt-0">
                    <ValueStackStep form={form} />
                  </TabsContent>

                  <TabsContent value="pricing" className="mt-0">
                    <PricingStep form={form} />
                  </TabsContent>

                  <TabsContent value="rules" className="mt-0">
                    <RulesStep form={form} />
                  </TabsContent>
                </CardContent>
              </Card>
            </div>
          </Tabs>
        </form>
      </Form>
    </div>
  );
}
