import { ComponentType } from 'react';
import { SectionProps } from '../types/section';
import { OfferArchetype } from '../types';
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
  LucideIcon
} from 'lucide-react';

// Preview Imports
import { PlaceholderPreview } from '../components/editor/sections/common/placeholder-preview';
import { StrategyPreview } from '../components/editor/sections/strategy/strategy-preview';
import { IdentityPreview } from '../components/editor/sections/identity/identity-preview';
import { PricingPreview } from '../components/editor/sections/pricing/pricing-preview';
import { InstructorsPreview } from '../components/editor/sections/instructors/instructors-preview';
import { ValueStackPreview } from '../components/editor/sections/value-stack/value-stack-preview';
import { ResourcesPreview } from '../components/editor/sections/resources/resources-preview';
import { GalleryPreview } from '../components/editor/sections/visuals/gallery-preview';
import { ClosingPreview } from '../components/editor/sections/closing/closing-preview';

// Form Imports
import { StrategyForm } from '../components/editor/sections/strategy/strategy-form';
import { IdentityForm } from '../components/editor/sections/identity/identity-form';
import { PricingForm } from '../components/editor/sections/pricing/pricing-form';
import { PsychologyForm } from '../components/editor/sections/psychology/psychology-form';
import { PromiseForm } from '../components/editor/sections/promise/promise-form';
import { ClosingForm } from '../components/editor/sections/closing/closing-form';
import { InstructorsForm } from '../components/editor/sections/instructors/instructors-form';
import { InstructorsManager } from '../components/editor/sections/instructors/instructors-manager';
import { ValueStackForm } from '../components/editor/sections/value-stack/value-stack-form';
import { ResourcesForm } from '../components/editor/sections/resources/resources-form';
import { ResourcesManager } from '../components/editor/sections/resources/resources-manager';
import { GalleryForm } from '../components/editor/sections/visuals/gallery-form';
import { GalleryManager } from '../components/editor/sections/visuals/gallery-manager';
import { ProgramDetailsForm } from '../components/editor/sections/program-details/program-form';
import { ProductDetailsForm } from '../components/editor/sections/product-details/product-form';
import { ServiceDetailsForm } from '../components/editor/sections/service-details/service-form';
import { EventDetailsForm } from '../components/editor/sections/event-details/event-form';
import { SubscriptionDetailsForm } from '../components/editor/sections/subscription-details/subscription-form';
import { EditionsSection } from '../components/editions/EditionsSection';

// Placeholder for missing forms/previews if any
import { PlaceholderForm } from '../components/editor/sections/common/placeholder-form';

export interface OfferBuilderSectionConfig {
  id: string;
  title: string;
  component: ComponentType<SectionProps | any>; 
  icon: LucideIcon;
  previewComponent: ComponentType<any>;
  formComponent: ComponentType<any>;
}

export const SECTION_REGISTRY: Record<string, OfferBuilderSectionConfig> = {
  strategy: {
    id: 'strategy',
    title: 'Estrategia & Avatar',
    component: StrategyForm,
    icon: Target,
    previewComponent: StrategyPreview,
    formComponent: StrategyForm
  },
  identity: {
    id: 'identity',
    title: 'Identidad de Oferta',
    component: IdentityForm,
    icon: Fingerprint,
    previewComponent: IdentityPreview,
    formComponent: IdentityForm
  },
  psychology: {
    id: 'psychology',
    title: 'Psicología & IA',
    component: PsychologyForm,
    icon: Brain,
    previewComponent: PlaceholderPreview, // Could implement PsychologyPreview
    formComponent: PsychologyForm
  },
  promise: {
    id: 'promise',
    title: 'Promesa & Resultado',
    component: PromiseForm,
    icon: Star,
    previewComponent: PlaceholderPreview, // Could implement PromisePreview
    formComponent: PromiseForm
  },
  program_details: {
    id: 'program_details',
    title: 'Detalles del Programa',
    component: ProgramDetailsForm,
    icon: BookOpen,
    previewComponent: PlaceholderPreview,
    formComponent: ProgramDetailsForm
  },
  product_details: {
    id: 'product_details',
    title: 'Detalles del Producto',
    component: ProductDetailsForm,
    icon: Package,
    previewComponent: PlaceholderPreview,
    formComponent: ProductDetailsForm
  },
  service_details: {
    id: 'service_details',
    title: 'Detalles del Servicio',
    component: ServiceDetailsForm,
    icon: Briefcase,
    previewComponent: PlaceholderPreview,
    formComponent: ServiceDetailsForm
  },
  event_details: {
    id: 'event_details',
    title: 'Detalles del Evento',
    component: EventDetailsForm,
    icon: Calendar,
    previewComponent: PlaceholderPreview,
    formComponent: EventDetailsForm
  },
  subscription_details: {
    id: 'subscription_details',
    title: 'Detalles de Suscripción',
    component: SubscriptionDetailsForm,
    icon: RefreshCw,
    previewComponent: PlaceholderPreview,
    formComponent: SubscriptionDetailsForm
  },
  instructors: {
    id: 'instructors',
    title: 'Instructores',
    component: InstructorsForm,
    icon: Users,
    previewComponent: InstructorsPreview,
    formComponent: InstructorsManager
  },
  value_stack: {
    id: 'value_stack',
    title: 'Stack de Valor',
    component: ValueStackForm,
    icon: Layers,
    previewComponent: ValueStackPreview,
    formComponent: ValueStackForm
  },
  resources: {
    id: 'resources',
    title: 'Recursos',
    component: ResourcesForm,
    icon: Library,
    previewComponent: ResourcesPreview,
    formComponent: ResourcesManager
  },
  gallery: {
    id: 'gallery',
    title: 'Galería Visual',
    component: GalleryForm,
    icon: Image,
    previewComponent: GalleryPreview,
    formComponent: GalleryManager
  },
  pricing: {
    id: 'pricing',
    title: 'Precios',
    component: PricingForm,
    icon: DollarSign,
    previewComponent: PricingPreview,
    formComponent: PricingForm
  },
  closing: {
    id: 'closing',
    title: 'Cierre & Garantía',
    component: ClosingForm,
    icon: CheckCircle,
    previewComponent: ClosingPreview,
    formComponent: ClosingForm
  },
  editions: {
    id: 'editions',
    title: 'Ediciones',
    component: EditionsSection,
    icon: Rocket,
    previewComponent: PlaceholderPreview,
    formComponent: EditionsSection,
  }
};

// --- ARCHETYPE-BASED CONFIG (new, preferred) ---
export const ARCHETYPE_BUILDER_CONFIG: Record<OfferArchetype, string[]> = {
  [OfferArchetype.PRODUCTO]: ['identity', 'strategy', 'psychology', 'promise', 'product_details', 'value_stack', 'resources', 'gallery', 'pricing', 'closing'],
  [OfferArchetype.PROGRAMA]: ['identity', 'strategy', 'psychology', 'promise', 'program_details', 'instructors', 'value_stack', 'resources', 'gallery', 'pricing', 'editions', 'closing'],
  [OfferArchetype.SERVICIO]: ['identity', 'strategy', 'psychology', 'promise', 'service_details', 'instructors', 'value_stack', 'resources', 'gallery', 'pricing', 'editions', 'closing'],
  [OfferArchetype.MEMBRESIA]: ['identity', 'strategy', 'psychology', 'promise', 'subscription_details', 'value_stack', 'resources', 'gallery', 'pricing', 'closing'],
  [OfferArchetype.EXPERIENCIA]: ['identity', 'strategy', 'psychology', 'promise', 'event_details', 'instructors', 'value_stack', 'resources', 'gallery', 'pricing', 'editions', 'closing'],
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
