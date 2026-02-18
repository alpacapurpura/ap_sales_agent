"use client";

import { useState, useEffect } from "react";
import { useForm, FieldErrors } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { OfferSchema, OfferFormValues } from "../types/schema";
import { OfferStatus } from "../types";
import { useOffer } from "../hooks/use-offer";
import { Button } from "@/components/ui/button";
import { Form } from "@/components/ui/form";
import { Loader2, Save, ArrowLeft, Eye, LayoutTemplate } from "lucide-react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { SECTION_REGISTRY, OFFER_BUILDER_CONFIG } from "../config/offer-builder-config";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { Separator } from "@/components/ui/separator";

export function DynamicOfferEditor({ offerId }: { offerId: string }) {
  const router = useRouter();
  const params = useParams();
  const tenantId = params?.tenantId as string;

  const { formValues, loading, saving, error, saveOffer } = useOffer(offerId);
  const [activeSection, setActiveSection] = useState<string | null>(null);

  const form = useForm<OfferFormValues>({
    resolver: zodResolver(OfferSchema),
    defaultValues: {
      status: OfferStatus.DRAFT,
      requires_application: false,
      pricing_options: [],
      marketing_pain_points: [],
      marketing_desires: [],
      prerequisites: [],
      includes_offers: [],
      deliverables: [],
    },
    mode: "onChange",
  });

  useEffect(() => {
    if (formValues) {
      form.reset(formValues);
    }
  }, [formValues, form]);

  const onSubmit = async (data: OfferFormValues) => {
      await saveOffer(data);
  };

  const onInvalid = (errors: FieldErrors<OfferFormValues>) => {
    console.error("Form validation errors:", JSON.stringify(errors, null, 2));
    toast.error("Por favor corrige los errores en el formulario antes de guardar.");
  };

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(`section-${sectionId}`);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        setActiveSection(sectionId);
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
                <Link href={`/${tenantId}/offer-studio`}>
                  <Button variant="outline"><ArrowLeft className="mr-2 h-4 w-4" /> Volver</Button>
                </Link>
              </div>
          </div>
      );
  }

  const currentType = form.watch("type");
  const sectionsToRender = currentType && OFFER_BUILDER_CONFIG[currentType] 
    ? OFFER_BUILDER_CONFIG[currentType]!
    : ['strategy']; // Default if type is not selected

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] overflow-hidden bg-background">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b bg-background z-10">
        <div className="flex items-center gap-4">
          <Link href={`/${tenantId}/offer-studio`}>
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-xl font-bold tracking-tight">{form.watch("public_name") || "Nueva Oferta"}</h1>
            <div className="text-xs text-muted-foreground flex items-center gap-2">
                <span className="uppercase tracking-wider">{currentType || "Sin Tipo"}</span>
                {form.formState.isDirty && <span className="text-amber-500">• Cambios sin guardar</span>}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
            <Link href={`/${tenantId}/editor/${offerId}`} target="_blank">
                <Button variant="outline" size="sm" className="gap-2">
                    <Eye className="h-4 w-4" /> Preview
                </Button>
            </Link>
            <Button onClick={form.handleSubmit(onSubmit, onInvalid)} disabled={saving} size="sm">
              {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
              Guardar
            </Button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar Navigation */}
        <aside className="w-64 border-r bg-muted/10 hidden md:block flex-shrink-0">
            <ScrollArea className="h-full">
                <div className="p-4 space-y-4">
                    <div className="font-semibold text-sm px-2 flex items-center gap-2 text-muted-foreground">
                        <LayoutTemplate className="w-4 h-4" />
                        Secciones
                    </div>
                    <nav className="space-y-1">
                        {sectionsToRender.map((sectionId) => {
                            const config = SECTION_REGISTRY[sectionId];
                            if (!config) return null;
                            
                            const isActive = activeSection === sectionId;
                            
                            return (
                                <button
                                    key={sectionId}
                                    onClick={() => scrollToSection(sectionId)}
                                    className={cn(
                                        "w-full text-left px-3 py-2 text-sm rounded-md transition-colors",
                                        isActive 
                                            ? "bg-primary/10 text-primary font-medium" 
                                            : "text-muted-foreground hover:bg-muted hover:text-foreground"
                                    )}
                                >
                                    {config.title}
                                </button>
                            );
                        })}
                    </nav>
                </div>
            </ScrollArea>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto bg-slate-50/50 dark:bg-slate-950/20 scroll-smooth">
             <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit, onInvalid)} className="max-w-4xl mx-auto p-6 lg:p-10 space-y-12 pb-32">
                    {sectionsToRender.map((sectionId, index) => {
                        const config = SECTION_REGISTRY[sectionId];
                        if (!config) {
                            return <div key={sectionId} className="text-red-500">Sección no encontrada: {sectionId}</div>;
                        }

                        const Component = config.component;
                        
                        return (
                            <section 
                                key={sectionId} 
                                id={`section-${sectionId}`}
                                className="scroll-mt-6"
                                onMouseEnter={() => setActiveSection(sectionId)}
                            >
                                <div className="flex items-center gap-4 mb-6">
                                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border bg-background text-sm font-semibold text-muted-foreground shadow-sm">
                                        {index + 1}
                                    </div>
                                    <div className="flex-1">
                                        <h2 className="text-lg font-semibold tracking-tight">{config.title}</h2>
                                        <Separator className="mt-2" />
                                    </div>
                                </div>
                                
                                <div className="pl-0 md:pl-12">
                                    <Component form={form} />
                                </div>
                            </section>
                        );
                    })}

                    {sectionsToRender.length === 0 && (
                        <div className="text-center py-20 text-muted-foreground">
                            No hay secciones configuradas para este tipo de oferta.
                        </div>
                    )}
                </form>
            </Form>
        </main>
      </div>
    </div>
  );
}
