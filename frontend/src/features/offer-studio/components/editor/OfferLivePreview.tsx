import { Edit3, Eye, AlertCircle } from "lucide-react";
import { useMemo, useCallback } from "react";
import { useWatch } from "react-hook-form";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { SECTION_REGISTRY, getSectionsForOffer } from "../../config/offer-builder-config";
import { GuaranteeType } from "../../types";

import { OfferSectionWrapper } from "./OfferSectionWrapper";
import { IdentityPreview } from "./sections/identity/IdentityPreview";
import type { OfferFormValues } from "../../types/schema";

import type { UseFormReturn } from "react-hook-form";

interface OfferLivePreviewProps {
  form: UseFormReturn<OfferFormValues>;
  onEdit: (sectionId: string) => void;
}

const SECTION_METADATA: Record<string, { quote: string; action: string }> = {
  identity: {
    quote: "Tu oferta necesita un nombre que resuene con tu audiencia.",
    action: "Definir Identidad",
  },
  strategy: {
    quote: "¿A quién ayudas y cómo transformas su vida?",
    action: "Definir Estrategia",
  },
  psychology: {
    quote: "Conecta con las emociones profundas de tu cliente ideal y anticipa sus objeciones.",
    action: "Configurar Psicología",
  },
  promise: {
    quote: "Una promesa audaz es el corazón de una oferta irresistible.",
    action: "Crear Promesa",
  },
  pricing: {
    quote: "El precio es solo un número; el valor es lo que perciben.",
    action: "Establecer Precios",
  },
  closing: {
    quote: "Elimina el riesgo y dales una razón para actuar ahora.",
    action: "Definir Cierre",
  },
  instructors: {
    quote: "La autoridad genera confianza. Presenta a los expertos.",
    action: "Añadir Instructores",
  },
  value_stack: {
    quote: "Muestra todo lo que reciben. Aumenta el valor percibido.",
    action: "Construir Stack",
  },
  resources: {
    quote: "Herramientas que facilitan el éxito de tu cliente.",
    action: "Subir Recursos",
  },
  gallery: {
    quote: "Una imagen vale más que mil palabras.",
    action: "Gestionar Galería",
  },
  program_details: {
    quote: "La estructura da seguridad. Define el camino.",
    action: "Detallar Programa",
  },
  product_details: {
    quote: "Especificaciones claras para productos tangibles.",
    action: "Detallar Producto",
  },
  service_details: {
    quote: "Define el alcance y la metodología de tu servicio.",
    action: "Detallar Servicio",
  },
  event_details: {
    quote: "Crea una experiencia inolvidable. Logística y agenda.",
    action: "Detallar Evento",
  },
};

const DEFAULT_METADATA = {
  quote: "La claridad genera confianza. Especifica qué recibirán.",
  action: "Detallar Entregable",
};

export function OfferLivePreview({ form, onEdit }: OfferLivePreviewProps) {
  // Use useWatch for specific fields to avoid re-rendering the entire component on every keystroke
  // However, since this is a "Live Preview", we might want updates.
  // Optimization: Memoize the sections calculation and the empty check function.
  const formValues = form.watch();
  const currentArchetype = formValues.archetype;

  // Helper to check if a section is empty using current watched values
  const isSectionEmpty = useCallback(
    (sectionId: string) => {
      switch (sectionId) {
        case "identity":
          return !formValues.public_name;
        case "strategy":
          return (
            (!formValues.target_avatar_match || formValues.target_avatar_match.length === 0) &&
            (!formValues.marketing_pain_points || formValues.marketing_pain_points.length === 0)
          );
        case "psychology":
          return (
            (!formValues.marketing_pain_points || formValues.marketing_pain_points.length === 0) &&
            (!formValues.marketing_desires || formValues.marketing_desires.length === 0) &&
            (!formValues.objections || formValues.objections.length === 0)
          );
        case "promise":
          return !formValues.headline_promise;
        case "pricing":
          return !formValues.pricing_options || formValues.pricing_options.length === 0;
        case "closing":
          return formValues.guarantee_type === GuaranteeType.NONE && !formValues.guarantee_terms;
        case "instructors":
          return !formValues.instructors || formValues.instructors.length === 0;
        case "value_stack":
          return !formValues.deliverables || formValues.deliverables.length === 0;
        case "resources":
          const resourceAssets = formValues.assets?.filter((a) =>
            ["PDF", "TXT", "URL", "AUDIO"].includes(a.type),
          );
          return !resourceAssets || resourceAssets.length === 0;
        case "gallery":
          const mediaAssets = formValues.assets?.filter((a) => ["IMAGE", "VIDEO"].includes(a.type));
          return !mediaAssets || mediaAssets.length === 0;
        case "product_details":
        case "service_details":
        case "program_details":
        case "event_details":
        case "subscription_details":
          return (
            !formValues.specific_details || Object.keys(formValues.specific_details).length === 0
          );
        default:
          return false;
      }
    },
    [formValues],
  );

  const sections = useMemo(() => {
    return getSectionsForOffer({ archetype: currentArchetype });
  }, [currentArchetype]);

  // Filter out identity to render it separately as a header
  const sectionsWithoutIdentity = useMemo(
    () => sections.filter((id) => id !== "identity"),
    [sections],
  );

  if (!sections || sections.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-12 text-center">
        <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
        <h3 className="text-lg font-medium">No hay secciones configuradas</h3>
        <p className="text-muted-foreground mt-2">
          Selecciona un tipo de oferta para ver las secciones disponibles.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8 p-8 max-w-5xl mx-auto pb-32">
      {/* Identity Header (Rendered Outside the List) */}
      {sections.includes("identity") && (
        <div className="mb-8">
          <IdentityPreview onEdit={() => onEdit("identity")} data={formValues} />
        </div>
      )}

      <div className="space-y-12">
        {sectionsWithoutIdentity.map((sectionId, index) => {
          const config = SECTION_REGISTRY[sectionId];
          if (!config) return null;

          const PreviewComponent = config.previewComponent;
          const Icon = config.icon;
          const isEmpty = isSectionEmpty(sectionId);
          const metadata = SECTION_METADATA[sectionId] || DEFAULT_METADATA;

          return (
            <OfferSectionWrapper
              key={sectionId}
              id={sectionId}
              title={`${config.title}`}
              icon={Icon}
              isEmpty={isEmpty}
              quote={metadata.quote}
              actionLabel={metadata.action}
              onEdit={() => onEdit(sectionId)}
            >
              {/* Remove wrapper div to keep it clean */}
              <PreviewComponent
                form={form}
                data={formValues}
                title={config.title}
                sectionId={sectionId}
              />
            </OfferSectionWrapper>
          );
        })}
      </div>
    </div>
  );
}
