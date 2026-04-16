import {
  Target,
  Fingerprint,
  Brain,
  Star,
  BookOpen,
  Package,
  Briefcase,
  Calendar,
  RefreshCw,
  Users,
  Layers,
  Library,
  Image,
  DollarSign,
  CheckCircle,
  Rocket,
} from "lucide-react";

// Preview Imports
import { EditionsSection } from "../components/editions/EditionsSection";
import { ClosingForm } from "../components/editor/sections/closing/ClosingForm";
import { ClosingPreview } from "../components/editor/sections/closing/ClosingPreview";
import { IdentityForm } from "../components/editor/sections/identity/IdentityForm";
import { IdentityPreview } from "../components/editor/sections/identity/IdentityPreview";
import { StrategyPreview } from "../components/editor/sections/strategy/StrategyPreview";
import { PricingPreview } from "../components/editor/sections/pricing/PricingPreview";
import { InstructorsPreview } from "../components/editor/sections/instructors/InstructorsPreview";
import { ValueStackForm } from "../components/editor/sections/value-stack/ValueStackForm";
import { ValueStackPreview } from "../components/editor/sections/value-stack/ValueStackPreview";
import { ResourcesPreview } from "../components/editor/sections/resources/ResourcesPreview";
import { GalleryPreview } from "../components/editor/sections/visuals/GalleryPreview";

// Form Imports
import { StrategyForm } from "../components/editor/sections/strategy/StrategyForm";
import { PricingForm } from "../components/editor/sections/pricing/PricingForm";
import { PsychologyForm } from "../components/editor/sections/psychology/PsychologyForm";
import { PromiseForm } from "../components/editor/sections/promise/PromiseForm";
import { InstructorsForm } from "../components/editor/sections/instructors/InstructorsForm";
import { InstructorsManager } from "../components/editor/sections/instructors/InstructorsManager";
import { ResourcesForm } from "../components/editor/sections/resources/ResourcesForm";
import { ResourcesManager } from "../components/editor/sections/resources/ResourcesManager";
import { GalleryForm } from "../components/editor/sections/visuals/GalleryForm";
import { GalleryManager } from "../components/editor/sections/visuals/GalleryManager";
import { ProgramDetailsForm } from "../components/editor/sections/program-details/ProgramForm";
import { ProductDetailsForm } from "../components/editor/sections/product-details/ProductForm";
import { ServiceDetailsForm } from "../components/editor/sections/service-details/ServiceForm";
import { EventDetailsForm } from "../components/editor/sections/event-details/EventForm";
import { SubscriptionDetailsForm } from "../components/editor/sections/subscription-details/SubscriptionForm";

// Placeholder for missing forms/previews if any
import { PlaceholderForm } from "../components/editor/sections/common/PlaceholderForm";
import { PlaceholderPreview } from "../components/editor/sections/common/PlaceholderPreview";
import { OfferArchetype } from "../types";

import type { SectionProps } from "../types/section";
import type { LucideIcon } from "lucide-react";
import type { ComponentType } from "react";

// Plugin registry: each section has distinct prop types (StrategyFormProps, IdentityFormProps, etc.)
// with no common base interface. TypeScript function parameter contravariance makes it impossible
// to assign specific-props components to a generic type without `any`.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type PluginComponent = ComponentType<any>;

export interface OfferBuilderSectionConfig {
  id: string;
  title: string;
  component: PluginComponent;
  icon: LucideIcon;
  previewComponent: PluginComponent;
  formComponent: PluginComponent;
}

export const SECTION_REGISTRY: Record<string, OfferBuilderSectionConfig> = {
  strategy: {
    id: "strategy",
    title: "Estrategia & Avatar",
    component: StrategyForm,
    icon: Target,
    previewComponent: StrategyPreview,
    formComponent: StrategyForm,
  },
  identity: {
    id: "identity",
    title: "Identidad de Oferta",
    component: IdentityForm,
    icon: Fingerprint,
    previewComponent: IdentityPreview,
    formComponent: IdentityForm,
  },
  psychology: {
    id: "psychology",
    title: "Psicología & IA",
    component: PsychologyForm,
    icon: Brain,
    previewComponent: PlaceholderPreview, // Could implement PsychologyPreview
    formComponent: PsychologyForm,
  },
  promise: {
    id: "promise",
    title: "Promesa & Resultado",
    component: PromiseForm,
    icon: Star,
    previewComponent: PlaceholderPreview, // Could implement PromisePreview
    formComponent: PromiseForm,
  },
  program_details: {
    id: "program_details",
    title: "Detalles del Programa",
    component: ProgramDetailsForm,
    icon: BookOpen,
    previewComponent: PlaceholderPreview,
    formComponent: ProgramDetailsForm,
  },
  product_details: {
    id: "product_details",
    title: "Detalles del Producto",
    component: ProductDetailsForm,
    icon: Package,
    previewComponent: PlaceholderPreview,
    formComponent: ProductDetailsForm,
  },
  service_details: {
    id: "service_details",
    title: "Detalles del Servicio",
    component: ServiceDetailsForm,
    icon: Briefcase,
    previewComponent: PlaceholderPreview,
    formComponent: ServiceDetailsForm,
  },
  event_details: {
    id: "event_details",
    title: "Detalles del Evento",
    component: EventDetailsForm,
    icon: Calendar,
    previewComponent: PlaceholderPreview,
    formComponent: EventDetailsForm,
  },
  subscription_details: {
    id: "subscription_details",
    title: "Detalles de Suscripción",
    component: SubscriptionDetailsForm,
    icon: RefreshCw,
    previewComponent: PlaceholderPreview,
    formComponent: SubscriptionDetailsForm,
  },
  instructors: {
    id: "instructors",
    title: "Instructores",
    component: InstructorsForm,
    icon: Users,
    previewComponent: InstructorsPreview,
    formComponent: InstructorsManager,
  },
  value_stack: {
    id: "value_stack",
    title: "Stack de Valor",
    component: ValueStackForm,
    icon: Layers,
    previewComponent: ValueStackPreview,
    formComponent: ValueStackForm,
  },
  resources: {
    id: "resources",
    title: "Recursos",
    component: ResourcesForm,
    icon: Library,
    previewComponent: ResourcesPreview,
    formComponent: ResourcesManager,
  },
  gallery: {
    id: "gallery",
    title: "Galería Visual",
    component: GalleryForm,
    icon: Image,
    previewComponent: GalleryPreview,
    formComponent: GalleryManager,
  },
  pricing: {
    id: "pricing",
    title: "Precios",
    component: PricingForm,
    icon: DollarSign,
    previewComponent: PricingPreview,
    formComponent: PricingForm,
  },
  closing: {
    id: "closing",
    title: "Cierre & Garantía",
    component: ClosingForm,
    icon: CheckCircle,
    previewComponent: ClosingPreview,
    formComponent: ClosingForm,
  },
  editions: {
    id: "editions",
    title: "Ediciones",
    component: EditionsSection,
    icon: Rocket,
    previewComponent: PlaceholderPreview,
    formComponent: EditionsSection,
  },
};

// --- ARCHETYPE-BASED CONFIG (new, preferred) ---
export const ARCHETYPE_BUILDER_CONFIG: Record<OfferArchetype, string[]> = {
  [OfferArchetype.PRODUCTO]: [
    "identity",
    "strategy",
    "psychology",
    "promise",
    "product_details",
    "value_stack",
    "resources",
    "gallery",
    "pricing",
    "closing",
  ],
  [OfferArchetype.PROGRAMA]: [
    "identity",
    "strategy",
    "psychology",
    "promise",
    "program_details",
    "instructors",
    "value_stack",
    "resources",
    "gallery",
    "pricing",
    "editions",
    "closing",
  ],
  [OfferArchetype.SERVICIO]: [
    "identity",
    "strategy",
    "psychology",
    "promise",
    "service_details",
    "instructors",
    "value_stack",
    "resources",
    "gallery",
    "pricing",
    "editions",
    "closing",
  ],
  [OfferArchetype.MEMBRESIA]: [
    "identity",
    "strategy",
    "psychology",
    "promise",
    "subscription_details",
    "value_stack",
    "resources",
    "gallery",
    "pricing",
    "closing",
  ],
  [OfferArchetype.EXPERIENCIA]: [
    "identity",
    "strategy",
    "psychology",
    "promise",
    "event_details",
    "instructors",
    "value_stack",
    "resources",
    "gallery",
    "pricing",
    "editions",
    "closing",
  ],
};

/**
 * Get sections for an offer based on archetype and wizard-driven flags.
 *
 * Editions section visibility:
 * - PRODUCTO / MEMBRESIA: never shown (archetype doesn't support editions).
 * - PROGRAMA / SERVICIO / EXPERIENCIA: shown unless `has_editions === false`.
 *   When the field is undefined (legacy offers), we default to showing the
 *   section to preserve existing UX.
 */
export function getSectionsForOffer(offer: {
  archetype?: OfferArchetype | string;
  has_editions?: boolean | null;
}): string[] {
  const archetype =
    offer.archetype && ARCHETYPE_BUILDER_CONFIG[offer.archetype as OfferArchetype]
      ? (offer.archetype as OfferArchetype)
      : OfferArchetype.PRODUCTO;
  const sections = ARCHETYPE_BUILDER_CONFIG[archetype];

  if (offer.has_editions === false) {
    return sections.filter((id) => id !== "editions");
  }
  return sections;
}
