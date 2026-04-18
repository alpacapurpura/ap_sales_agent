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
  Database,
} from "lucide-react";

import { ClosingForm } from "../components/editor/sections/closing/ClosingForm";
import { ClosingPreview } from "../components/editor/sections/closing/ClosingPreview";
import { PlaceholderPreview } from "../components/editor/sections/common/PlaceholderPreview";
import { EventDetailsForm } from "../components/editor/sections/event-details/EventForm";
import { IdentityForm } from "../components/editor/sections/identity/IdentityForm";
import { IdentityPreview } from "../components/editor/sections/identity/IdentityPreview";
import { InstructorsForm } from "../components/editor/sections/instructors/InstructorsForm";
import { InstructorsManager } from "../components/editor/sections/instructors/InstructorsManager";
import { InstructorsPreview } from "../components/editor/sections/instructors/InstructorsPreview";
import { PricingForm } from "../components/editor/sections/pricing/PricingForm";
import { PricingPreview } from "../components/editor/sections/pricing/PricingPreview";
import { ProductDetailsForm } from "../components/editor/sections/product-details/ProductForm";
import { ProgramDetailsForm } from "../components/editor/sections/program-details/ProgramForm";
import { PromiseForm } from "../components/editor/sections/promise/PromiseForm";
import { PsychologyForm } from "../components/editor/sections/psychology/PsychologyForm";
import { ResourcesForm } from "../components/editor/sections/resources/ResourcesForm";
import { ResourcesManager } from "../components/editor/sections/resources/ResourcesManager";
import { ResourcesPreview } from "../components/editor/sections/resources/ResourcesPreview";
import { ServiceDetailsForm } from "../components/editor/sections/service-details/ServiceForm";
import { StrategyForm } from "../components/editor/sections/strategy/StrategyForm";
import { StrategyPreview } from "../components/editor/sections/strategy/StrategyPreview";
import { SubscriptionDetailsForm } from "../components/editor/sections/subscription-details/SubscriptionForm";
import { ValueStackForm } from "../components/editor/sections/value-stack/ValueStackForm";
import { ValueStackPreview } from "../components/editor/sections/value-stack/ValueStackPreview";
import { GalleryForm } from "../components/editor/sections/visuals/GalleryForm";
import { GalleryManager } from "../components/editor/sections/visuals/GalleryManager";
import { GalleryPreview } from "../components/editor/sections/visuals/GalleryPreview";
import { KnowledgeView } from "../components/knowledge/KnowledgeView";

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
  knowledge: {
    id: "knowledge",
    title: "Conocimiento",
    component: KnowledgeView,
    icon: Database,
    previewComponent: PlaceholderPreview,
    formComponent: KnowledgeView,
  },
};

// --- Section ordering note ---
//
// Per-archetype section ordering lives in the BACKEND section catalog as
// the single source of truth (see ``backend/src/modules/offer/domain/
// section_catalog.py`` + ``archetype_catalog.py``). Frontend consumers
// read it via the React Query hooks in
// ``hooks/use-sections-for-archetype.ts`` and
// ``hooks/use-visible-sections.ts``.
//
// The frontend arch test ``test-no-catalog-duplicates`` rejects any attempt
// to reintroduce a per-archetype section-ordering map or legacy resolver
// here — duplicating the catalog breaks the guarantee that a backend
// deploy with a catalog version bump suffices to change section sets.
