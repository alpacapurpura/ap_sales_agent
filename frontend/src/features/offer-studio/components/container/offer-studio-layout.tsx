import React, { useState } from "react";
import { Offer } from "@/features/offer-studio/types";
import { OfferNavRail } from "../navigation/OfferNavRail";
import { Button } from "@/components/ui/button";
import { Eye, Edit3, Save, ExternalLink, Globe, Wand2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { useParams } from "next/navigation";

interface OfferStudioLayoutProps {
  offer: Offer;
  onUpdate: (offer: Offer) => void;
  children: React.ReactNode;
  activeSection: string;
  onNavigate: (sectionId: string) => void;
  isSaving?: boolean;
  onSmartFill?: () => void;
}

export function OfferStudioLayout({
  offer,
  onUpdate,
  children,
  activeSection,
  onNavigate,
  isSaving = false,
  onSmartFill
}: OfferStudioLayoutProps) {
  const [mode, setMode] = useState<"edit" | "preview">("edit");
  const params = useParams();
  const tenantId = params?.tenantId as string;

  const handleOpenLanding = () => {
    window.open(`/${tenantId}/editor/${offer.id}`, "_blank", "noopener");
  };

  return (
    <div className="flex flex-col h-screen bg-background overflow-hidden">
      {/* Header - Fixed Top Bar */}
      <header className="h-16 border-b flex items-center justify-between px-6 bg-background/80 backdrop-blur-sm sticky top-0 z-50 w-full flex-none">
         <div className="flex items-center gap-3">
            <h1 className="font-bold text-lg truncate max-w-[300px] text-foreground">{offer.name}</h1>
            <Badge variant="outline" className="uppercase text-[10px] tracking-wider font-semibold">
              {offer.status}
            </Badge>
            {offer.archetype && (
              <Badge variant="secondary" className="text-[10px] tracking-wider font-semibold capitalize">
                {offer.archetype}{offer.format_hint ? ` - ${offer.format_hint}` : ""}
              </Badge>
            )}
            {!offer.archetype && (
              <Badge variant="secondary" className="uppercase text-[10px] tracking-wider font-semibold">
                {offer.value_level}
              </Badge>
            )}
         </div>
         
         <div className="flex items-center gap-3">
            <div className="flex items-center bg-muted/50 rounded-lg p-1 border">
               <Button 
                  variant={mode === "edit" ? "secondary" : "ghost"} 
                  size="sm" 
                  className="h-8 text-xs font-medium"
                  onClick={() => setMode("edit")}
               >
                  <Edit3 className="h-3.5 w-3.5 mr-1.5" />
                  Editor
               </Button>
               <Button
                  variant={mode === "preview" ? "secondary" : "ghost"}
                  size="sm"
                  className="h-8 text-xs font-medium"
                  onClick={() => setMode("preview")}
               >
                  <Eye className="h-3.5 w-3.5 mr-1.5" />
                  Vista Previa
               </Button>
            </div>

            <Button
               variant="outline"
               size="sm"
               className="h-8 text-xs font-medium gap-1.5"
               onClick={handleOpenLanding}
            >
               <Globe className="h-3.5 w-3.5" />
               Landing Page
            </Button>

            {onSmartFill && (
                <Button
                    variant="outline"
                    size="sm"
                    className="h-8 text-xs font-medium gap-1.5"
                    onClick={onSmartFill}
                >
                    <Wand2 className="h-3.5 w-3.5" />
                    Completar con IA
                </Button>
            )}

            <div className="h-6 w-px bg-border mx-1" />

            <Button 
              size="sm" 
              onClick={() => onUpdate(offer)} 
              disabled={isSaving}
              className="font-medium"
            >
               {isSaving ? (
                  <>Guardando...</>
               ) : (
                  <>
                      <Save className="h-4 w-4 mr-2" />
                      Guardar
                  </>
               )}
            </Button>
         </div>
      </header>

      {/* Main Layout: Sidebar + Content */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Left Rail */}
        <OfferNavRail 
          offer={offer} 
          activeSection={activeSection} 
          onNavigate={onNavigate}
          className="flex-none z-20 h-full border-r bg-muted/10"
        />

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto scroll-smooth relative" id="offer-editor-main">
           {mode === "edit" ? (
             <div className="min-h-full pb-20">
                <div className="max-w-5xl mx-auto p-8">
                    {children}
                </div>
             </div>
           ) : (
             <div className="min-h-full w-full bg-slate-50 dark:bg-slate-950">
                <OfferLivePreview offer={offer} />
             </div>
           )}
        </main>
      </div>
    </div>
  );
}

/**
 * Componente de vista previa en vivo.
 * Renderiza cómo se verá la oferta para el cliente final.
 */
function OfferLivePreview({ offer }: { offer: Offer }) {
  return (
    <div className="min-h-full flex flex-col items-center justify-center p-8">
        <div className="max-w-md text-center space-y-6">
            <div className="mx-auto h-20 w-20 bg-primary/5 rounded-2xl flex items-center justify-center border border-primary/10">
                <Eye className="h-10 w-10 text-primary" />
            </div>
            
            <div className="space-y-2">
                <h3 className="text-2xl font-semibold tracking-tight">Vista Previa de &quot;{offer.name}&quot;</h3>
                <p className="text-muted-foreground">
                    La previsualización en tiempo real se está generando basada en la configuración de 
                    <span className="font-medium text-foreground mx-1">{offer.archetype}</span>.
                </p>
            </div>

            <div className="p-4 bg-yellow-50 dark:bg-yellow-900/10 border border-yellow-200 dark:border-yellow-900/30 rounded-lg text-sm text-yellow-800 dark:text-yellow-200">
                <p>
                    <strong>Nota:</strong> Esta vista simulará la experiencia de compra y el contenido entregable.
                    Configura las secciones en el editor para ver cambios aquí.
                </p>
            </div>

            <Button variant="outline" className="gap-2">
                <ExternalLink className="h-4 w-4" />
                Abrir en nueva pestaña
            </Button>
        </div>
    </div>
  );
}
