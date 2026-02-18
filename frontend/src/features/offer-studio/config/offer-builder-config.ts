import { ComponentType } from 'react';
import { SectionProps } from '../types/section';
import { OfferType } from '../types';

// Section Imports
import { StrategySection } from '../components/sections/StrategySection';
import { IdentitySection } from '../components/sections/IdentitySection';
import { PsychologySection } from '../components/sections/PsychologySection';
import { PromiseSection } from '../components/sections/PromiseSection';
import { ProgramDetailsSection } from '../components/sections/ProgramDetailsSection';
import { ProductDetailsSection } from '../components/sections/ProductDetailsSection';
import { ServiceDetailsSection } from '../components/sections/ServiceDetailsSection';
import { EventDetailsSection } from '../components/sections/EventDetailsSection';
import { SubscriptionDetailsSection } from '../components/sections/SubscriptionDetailsSection';
import { PricingSection } from '../components/sections/PricingSection';
import { ClosingSection } from '../components/sections/ClosingSection';
import { InstructorsSection } from '../components/sections/InstructorsSection';
import { ValueStackSection } from '../components/sections/ValueStackSection';
import { ResourcesSection } from '../components/sections/ResourcesSection';
import { GallerySection } from '../components/sections/GallerySection';

export interface OfferBuilderSectionConfig {
  id: string;
  title: string;
  component: ComponentType<SectionProps | any>; // Using any to accommodate IdentityStep for now
}

export type OfferBuilderConfig = Partial<Record<OfferType, string[]>>;

export const SECTION_REGISTRY: Record<string, OfferBuilderSectionConfig> = {
  strategy: {
    id: 'strategy',
    title: 'Estrategia & Avatar',
    component: StrategySection
  },
  identity: {
    id: 'identity',
    title: 'Identidad de Oferta',
    component: IdentitySection
  },
  psychology: {
    id: 'psychology',
    title: 'Psicología & IA',
    component: PsychologySection
  },
  promise: {
    id: 'promise',
    title: 'Promesa & Resultado',
    component: PromiseSection
  },
  program_details: {
    id: 'program_details',
    title: 'Detalles del Programa',
    component: ProgramDetailsSection
  },
  product_details: {
    id: 'product_details',
    title: 'Detalles del Producto',
    component: ProductDetailsSection
  },
  service_details: {
    id: 'service_details',
    title: 'Detalles del Servicio',
    component: ServiceDetailsSection
  },
  event_details: {
    id: 'event_details',
    title: 'Detalles del Evento',
    component: EventDetailsSection
  },
  subscription_details: {
    id: 'subscription_details',
    title: 'Detalles de Suscripción',
    component: SubscriptionDetailsSection
  },
  instructors: {
    id: 'instructors',
    title: 'Instructores',
    component: InstructorsSection
  },
  value_stack: {
    id: 'value_stack',
    title: 'Stack de Valor',
    component: ValueStackSection
  },
  resources: {
    id: 'resources',
    title: 'Recursos',
    component: ResourcesSection
  },
  gallery: {
    id: 'gallery',
    title: 'Galería Visual',
    component: GallerySection
  },
  pricing: {
    id: 'pricing',
    title: 'Precios',
    component: PricingSection
  },
  closing: {
    id: 'closing',
    title: 'Cierre & Garantía',
    component: ClosingSection
  }
};

export const OFFER_BUILDER_CONFIG: OfferBuilderConfig = {
    // Default configurations for common offer types
    [OfferType.GROUP_COACHING_PROGRAM]: ['strategy', 'identity', 'psychology', 'promise', 'program_details', 'instructors', 'value_stack', 'resources', 'gallery', 'pricing', 'closing'],
    [OfferType.HYBRID_MENTORSHIP]: ['strategy', 'identity', 'psychology', 'promise', 'program_details', 'instructors', 'value_stack', 'resources', 'gallery', 'pricing', 'closing'],
    [OfferType.COHORT_BASED_COURSE]: ['strategy', 'identity', 'psychology', 'promise', 'program_details', 'instructors', 'value_stack', 'resources', 'gallery', 'pricing', 'closing'],
    
    // Product types
    [OfferType.FREE_RESOURCE]: ['strategy', 'identity', 'promise', 'product_details', 'resources', 'gallery', 'pricing', 'closing'],
    [OfferType.TRIPWIRE_OFFER]: ['strategy', 'identity', 'psychology', 'promise', 'product_details', 'value_stack', 'resources', 'gallery', 'pricing', 'closing'],
    [OfferType.SELF_PACED_COURSE]: ['strategy', 'identity', 'psychology', 'promise', 'product_details', 'value_stack', 'resources', 'gallery', 'pricing', 'closing'],
    
    // Service types
    [OfferType.VIP_DAY_STRATEGY]: ['strategy', 'identity', 'psychology', 'promise', 'service_details', 'instructors', 'gallery', 'pricing', 'closing'],
    [OfferType.ONE_ON_ONE_PRIVATE_MENTORING]: ['strategy', 'identity', 'psychology', 'promise', 'service_details', 'instructors', 'gallery', 'pricing', 'closing'],
    
    // Event types
    [OfferType.LUXURY_RETREAT]: ['strategy', 'identity', 'psychology', 'promise', 'event_details', 'instructors', 'gallery', 'pricing', 'closing'],
    [OfferType.MASTERMIND_NETWORK]: ['strategy', 'identity', 'psychology', 'promise', 'subscription_details', 'instructors', 'gallery', 'pricing', 'closing'],
    [OfferType.CORPORATE_TRAINING]: ['strategy', 'identity', 'psychology', 'promise', 'service_details', 'gallery', 'pricing', 'closing'],
};
