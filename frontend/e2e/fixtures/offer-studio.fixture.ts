import { type Page } from '@playwright/test';
import { test as base, expect } from './auth.fixture';

import type { ArchetypeCatalogResponse, SectionKey, SectionScope } from '../../src/features/offer-studio/api/archetype-catalog-api';
import {
  OfferArchetype,
  OfferValueLevel,
  OfferDeliveryModel,
  OfferStatus,
  EditionStatus,
  EditionVisibility,
} from '../../src/features/offer-studio/types';
import type { LaunchEdition } from '../../src/features/offer-studio/types';
import type { Offer } from '../../src/features/offer-studio/types';

// ---------------------------------------------------------------------------
// Shared mock payloads
// ---------------------------------------------------------------------------

const MOCK_OFFER_ID = 'mock-offer-id-001';
const MOCK_EDITION_ID_1 = 'mock-edition-id-001';
const MOCK_EDITION_ID_2 = 'mock-edition-id-002';
const MOCK_EDITION_ID_3 = 'mock-edition-id-003';

type SharedSectionMetadata = {
  key: SectionKey;
  label_es: string;
  subtitle_es: string;
  help_text_es: string;
  icon_name: string;
  scope: SectionScope;
  completion_weight: number;
  required_to_publish: boolean;
  kind: 'singleton' | 'collection';
};

/** Minimal archetype catalog — covers PROGRAMA, MEMBRESIA, PRODUCTO archetypes. */
function buildArchetypeCatalog(): ArchetypeCatalogResponse {
  const sharedSections: SharedSectionMetadata[] = [
    {
      key: 'identity' satisfies SectionKey,
      label_es: 'Identidad',
      subtitle_es: 'Nombre y SKU de tu oferta.',
      help_text_es: 'La identidad define cómo se llama tu oferta y cómo la reconoces tú y tu equipo.',
      icon_name: 'Tag',
      scope: 'offer_level' satisfies SectionScope,
      completion_weight: 0.8,
      required_to_publish: true,
      kind: 'singleton',
    },
    {
      key: 'promise' satisfies SectionKey,
      label_es: 'Promesa',
      subtitle_es: 'La transformación que prometes.',
      help_text_es: 'Define el resultado específico que obtendrá el cliente al completar tu programa.',
      icon_name: 'Sparkles',
      scope: 'offer_level' satisfies SectionScope,
      completion_weight: 1.0,
      required_to_publish: true,
      kind: 'singleton',
    },
    {
      key: 'pricing' satisfies SectionKey,
      label_es: 'Precio',
      subtitle_es: 'Estructura de precios y planes.',
      help_text_es: 'Configura el precio base, los planes de pago y cualquier descuento especial.',
      icon_name: 'DollarSign',
      scope: 'mixed' satisfies SectionScope,
      completion_weight: 1.0,
      required_to_publish: true,
      kind: 'singleton',
    },
    {
      key: 'closing' satisfies SectionKey,
      label_es: 'Cierre',
      subtitle_es: 'CTA y urgencia.',
      help_text_es: 'Define cómo cierras la venta: llamada a la acción, escasez y urgencia.',
      icon_name: 'Zap',
      scope: 'offer_level' satisfies SectionScope,
      completion_weight: 0.7,
      required_to_publish: false,
      kind: 'singleton',
    },
  ];

  return {
    version: '2.0.0',
    archetypes: [
      {
        archetype: OfferArchetype.PROGRAMA,
        supports_editions: true,
        edition_noun_es: 'cohorte',
        edition_noun_plural_es: 'cohortes',
        requires_start_date_on_publish: true,
        requires_end_date_on_publish: false,
        requires_location_on_publish: false,
        supports_capacity: true,
        supports_waitlist: true,
        default_delivery: 'dwy',
        default_fulfillment: 'lms_access',
        default_variant_structure: 'temporal_cohort',
        supported_variant_structures: ['temporal_cohort', 'recurring_intake'],
        allow_single_variant: false,
        label_es: 'Programa',
        subtitle_es: 'Formación estructurada con un grupo de alumnos.',
        icon_name: 'BookOpen',
        examples_es: ['Bootcamp de Marketing Digital', 'Mentorship 1:1'],
        editions_wizard_copy: {
          title: '¿Tu programa tiene cohortes?',
          description: 'Las cohortes permiten organizar grupos de alumnos que empiezan y terminan juntos.',
          yes_label: 'Sí, crea cohortes',
          no_label: 'No, acceso continuo',
        },
        sections: sharedSections,
      },
      {
        archetype: OfferArchetype.MEMBRESIA,
        supports_editions: true,
        edition_noun_es: 'plan',
        edition_noun_plural_es: 'planes',
        requires_start_date_on_publish: false,
        requires_end_date_on_publish: false,
        requires_location_on_publish: false,
        supports_capacity: false,
        supports_waitlist: false,
        default_delivery: 'diy',
        default_fulfillment: 'lms_access',
        default_variant_structure: 'tier',
        supported_variant_structures: ['tier'],
        allow_single_variant: false,
        label_es: 'Membresía',
        subtitle_es: 'Acceso recurrente con planes diferenciados.',
        icon_name: 'Layers',
        examples_es: ['Comunidad Premium', 'Club de Lectores'],
        editions_wizard_copy: {
          title: '¿Tu membresía tiene niveles?',
          description: 'Los planes permiten ofrecer diferentes niveles de acceso a tu comunidad.',
          yes_label: 'Sí, con planes',
          no_label: 'No, acceso único',
        },
        sections: sharedSections,
      },
      {
        archetype: OfferArchetype.PRODUCTO,
        supports_editions: true,
        edition_noun_es: 'variante',
        edition_noun_plural_es: 'variantes',
        requires_start_date_on_publish: false,
        requires_end_date_on_publish: false,
        requires_location_on_publish: false,
        supports_capacity: true,
        supports_waitlist: false,
        default_delivery: 'diy',
        default_fulfillment: 'digital_download',
        default_variant_structure: 'sku_variant',
        supported_variant_structures: ['sku_variant'],
        allow_single_variant: true,
        label_es: 'Producto',
        subtitle_es: 'Producto digital o físico.',
        icon_name: 'Package',
        examples_es: ['Ebook de Productividad', 'Plantillas Notion'],
        editions_wizard_copy: null,
        sections: sharedSections,
      },
    ],
    section_catalog: sharedSections,
  };
}

/** Minimal preset catalog — one preset per common archetype. */
function buildPresetCatalog() {
  return {
    version: '1.0.0',
    presets: [
      {
        preset_id: 'programa_mentoria',
        label_es: 'Mentoría 1:1',
        description_es: 'Servicio de mentoría personalizada con sesiones individuales.',
        archetype: 'programa',
        business_types: ['coach'],
        base_sections: ['identity', 'promise', 'pricing'],
        conditional_questions: [
          {
            id: 'q1',
            question_es: '¿Cuántas sesiones incluye?',
            options_es: ['4 sesiones', '8 sesiones', '12 sesiones'],
          },
        ],
        flags: [],
      },
    ],
  };
}

/** Minimal variant structure catalog. */
function buildVariantStructureCatalog() {
  return {
    version: '1.0.0',
    structures: [
      { key: 'temporal_cohort', label_es: 'Cohortes', noun_es: 'cohorte', noun_plural_es: 'cohortes' },
      { key: 'tier', label_es: 'Planes', noun_es: 'plan', noun_plural_es: 'planes' },
      { key: 'sku_variant', label_es: 'Variantes', noun_es: 'variante', noun_plural_es: 'variantes' },
      { key: 'regional', label_es: 'Regiones', noun_es: 'región', noun_plural_es: 'regiones' },
      { key: 'modality', label_es: 'Modalidades', noun_es: 'modalidad', noun_plural_es: 'modalidades' },
      { key: 'language', label_es: 'Idiomas', noun_es: 'idioma', noun_plural_es: 'idiomas' },
      { key: 'temporal_single_date', label_es: 'Salidas', noun_es: 'salida', noun_plural_es: 'salidas' },
      { key: 'recurring_intake', label_es: 'Convocatorias', noun_es: 'convocatoria', noun_plural_es: 'convocatorias' },
    ],
  };
}

/** Minimal section catalog (standalone endpoint). */
function buildSectionCatalog() {
  return buildArchetypeCatalog().section_catalog;
}

// ---------------------------------------------------------------------------
// Edition factory helpers
// ---------------------------------------------------------------------------

function buildEditionBase(overrides: Partial<LaunchEdition> = {}): LaunchEdition {
  return {
    id: MOCK_EDITION_ID_1,
    offer_id: MOCK_OFFER_ID,
    edition_name: 'Edición 1',
    edition_number: 1,
    variant_structure: 'temporal_cohort',
    structure_data: {},
    sort_rank: 1,
    start_date: '2026-06-01T00:00:00Z',
    end_date: '2026-08-31T00:00:00Z',
    registration_start: null,
    registration_end: null,
    timezone: 'America/Lima',
    pricing_override: null,
    pricing_tiers: [],
    active_tier: null,
    effective_pricing: [
      { label: 'Precio base', plan_type: 'one_time', total_amount: 1500, currency: 'USD' },
    ],
    currency: 'USD',
    capacity: 30,
    enrollment_count: 12,
    status: EditionStatus.UPCOMING,
    visibility: EditionVisibility.PUBLIC,
    is_placeholder: false,
    location_override: null,
    notes: null,
    cloned_from_edition_id: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

function buildOfferBase(overrides: Partial<Offer> = {}): Offer {
  return {
    id: MOCK_OFFER_ID,
    name: 'Oferta de prueba',
    public_name: 'Oferta de prueba',
    archetype: OfferArchetype.PROGRAMA,
    value_level: OfferValueLevel.TRANSFORMACION,
    delivery_model: OfferDeliveryModel.DWY,
    status: OfferStatus.ACTIVE,
    ...overrides,
  };
}

// ---------------------------------------------------------------------------
// Exported factory functions (one per variant_structure)
// ---------------------------------------------------------------------------

/**
 * Offer with 3 TEMPORAL_COHORT editions — typical live program.
 * archetype.allow_single_variant = false → VariantRail must render.
 */
export function buildTemporalCohortOffer() {
  const offer = buildOfferBase({ archetype: OfferArchetype.PROGRAMA });
  const editions: LaunchEdition[] = [
    buildEditionBase({
      id: MOCK_EDITION_ID_1,
      edition_name: 'Cohorte 1',
      edition_number: 1,
      variant_structure: 'temporal_cohort',
    }),
    buildEditionBase({
      id: MOCK_EDITION_ID_2,
      edition_name: 'Cohorte 2',
      edition_number: 2,
      variant_structure: 'temporal_cohort',
      start_date: '2026-09-01T00:00:00Z',
    }),
    buildEditionBase({
      id: MOCK_EDITION_ID_3,
      edition_name: 'Cohorte 3',
      edition_number: 3,
      variant_structure: 'temporal_cohort',
      status: EditionStatus.DRAFT,
      start_date: null,
    }),
  ];
  return { offer, editions };
}

/**
 * Offer with 2 TIER editions — membership with plans.
 */
export function buildTierOffer() {
  const offer = buildOfferBase({
    id: 'mock-tier-offer-001',
    name: 'Membresía Planes',
    archetype: OfferArchetype.MEMBRESIA,
  });
  const editions: LaunchEdition[] = [
    buildEditionBase({
      id: 'tier-ed-001',
      offer_id: offer.id,
      edition_name: 'Plan Básico',
      variant_structure: 'tier',
      structure_data: { price_amount: 29, price_currency: 'USD', features: ['Acceso al foro'] },
    }),
    buildEditionBase({
      id: 'tier-ed-002',
      offer_id: offer.id,
      edition_name: 'Plan Premium',
      variant_structure: 'tier',
      structure_data: {
        price_amount: 99,
        price_currency: 'USD',
        features: ['Acceso al foro', 'Sesiones grupales mensuales'],
      },
    }),
  ];
  return { offer, editions };
}

/**
 * Offer with 2 SKU_VARIANT editions — physical/digital product with variants.
 */
export function buildSkuVariantOffer() {
  const offer = buildOfferBase({
    id: 'mock-sku-offer-001',
    name: 'Pack de Templates',
    archetype: OfferArchetype.PRODUCTO,
  });
  const editions: LaunchEdition[] = [
    buildEditionBase({
      id: 'sku-ed-001',
      offer_id: offer.id,
      edition_name: 'Pack Básico',
      variant_structure: 'sku_variant',
      structure_data: { sku_code: 'TMPL-BASE', attributes: { tipo: 'Básico' } },
    }),
    buildEditionBase({
      id: 'sku-ed-002',
      offer_id: offer.id,
      edition_name: 'Pack Completo',
      variant_structure: 'sku_variant',
      structure_data: { sku_code: 'TMPL-FULL', attributes: { tipo: 'Completo' } },
    }),
  ];
  return { offer, editions };
}

/**
 * Offer with 2 REGIONAL editions.
 */
export function buildRegionalOffer() {
  const offer = buildOfferBase({
    id: 'mock-regional-offer-001',
    name: 'Consultoría Regional',
    archetype: OfferArchetype.SERVICIO,
  });
  const editions: LaunchEdition[] = [
    buildEditionBase({
      id: 'reg-ed-001',
      offer_id: offer.id,
      edition_name: 'México',
      variant_structure: 'regional',
      structure_data: { country_codes: ['MX'], currency: 'MXN' },
      currency: 'MXN',
    }),
    buildEditionBase({
      id: 'reg-ed-002',
      offer_id: offer.id,
      edition_name: 'Colombia',
      variant_structure: 'regional',
      structure_data: { country_codes: ['CO'], currency: 'COP' },
      currency: 'COP',
    }),
  ];
  return { offer, editions };
}

/**
 * Offer with 2 MODALITY editions.
 */
export function buildModalityOffer() {
  const offer = buildOfferBase({
    id: 'mock-modality-offer-001',
    name: 'Taller Presencial / Online',
    archetype: OfferArchetype.EXPERIENCIA,
  });
  const editions: LaunchEdition[] = [
    buildEditionBase({
      id: 'mod-ed-001',
      offer_id: offer.id,
      edition_name: 'Modalidad Online',
      variant_structure: 'modality',
      structure_data: { mode: 'virtual' },
    }),
    buildEditionBase({
      id: 'mod-ed-002',
      offer_id: offer.id,
      edition_name: 'Modalidad Presencial',
      variant_structure: 'modality',
      structure_data: { mode: 'physical_local' },
    }),
  ];
  return { offer, editions };
}

/**
 * Offer with 2 LANGUAGE editions.
 */
export function buildLanguageOffer() {
  const offer = buildOfferBase({
    id: 'mock-language-offer-001',
    name: 'Curso Multilenguaje',
    archetype: OfferArchetype.PROGRAMA,
  });
  const editions: LaunchEdition[] = [
    buildEditionBase({
      id: 'lang-ed-001',
      offer_id: offer.id,
      edition_name: 'Español',
      variant_structure: 'language',
      structure_data: { locale: 'es' },
    }),
    buildEditionBase({
      id: 'lang-ed-002',
      offer_id: offer.id,
      edition_name: 'Inglés',
      variant_structure: 'language',
      structure_data: { locale: 'en' },
    }),
  ];
  return { offer, editions };
}

/**
 * Lead-magnet offer: archetype.allow_single_variant = true + exactly 1 edition.
 * No VariantRail should render.
 */
export function buildLeadMagnetOffer() {
  const offer = buildOfferBase({
    id: 'mock-lead-magnet-001',
    name: 'Guía Gratuita',
    archetype: OfferArchetype.PRODUCTO,
    is_lead_magnet: true,
    value_level: OfferValueLevel.LEAD_MAGNET,
  });
  const editions: LaunchEdition[] = [
    buildEditionBase({
      id: 'lm-ed-001',
      offer_id: offer.id,
      edition_name: 'Edición única',
      variant_structure: 'sku_variant',
      is_placeholder: false,
    }),
  ];
  return { offer, editions };
}

// ---------------------------------------------------------------------------
// Route mock setup
// ---------------------------------------------------------------------------

/** Register all offer-studio API mocks on the given Playwright page. */
export async function setupOfferStudioMocks(
  page: Page,
  offer: Offer,
  editions: LaunchEdition[],
): Promise<void> {
  // Offer list and detail
  await page.route('**/api/v1/offer/products**', async (route) => {
    const url = route.request().url();
    if (url.match(/\/products\/[^/]+\/editions/)) {
      await route.fulfill({ json: editions, status: 200 });
    } else if (url.match(/\/products\/[^/]+$/)) {
      await route.fulfill({ json: offer, status: 200 });
    } else {
      await route.fulfill({ json: [offer], status: 200 });
    }
  });

  // Archetype catalog
  await page.route('**/api/v1/offer/archetypes/catalog**', async (route) => {
    await route.fulfill({ json: buildArchetypeCatalog(), status: 200 });
  });

  // Type preset catalog
  await page.route('**/api/v1/offer/type-presets/catalog**', async (route) => {
    await route.fulfill({ json: buildPresetCatalog(), status: 200 });
  });

  // Variant structure catalog
  await page.route('**/api/v1/offer/variant-structures/catalog**', async (route) => {
    await route.fulfill({ json: buildVariantStructureCatalog(), status: 200 });
  });

  // Section catalog
  await page.route('**/api/v1/offer/sections/catalog**', async (route) => {
    await route.fulfill({ json: buildSectionCatalog(), status: 200 });
  });

  // Value level catalog
  await page.route('**/api/v1/offer/value-levels/catalog**', async (route) => {
    await route.fulfill({
      json: {
        version: '1.0.0',
        levels: [
          { key: 'lead_magnet', label_es: 'Lead Magnet', is_free: true },
          { key: 'activacion', label_es: 'Activación', is_free: false },
          { key: 'transformacion', label_es: 'Transformación', is_free: false },
        ],
      },
      status: 200,
    });
  });

  // Counts endpoint
  await page.route(`**/api/v1/offer/products/${offer.id}/counts**`, async (route) => {
    await route.fulfill({
      json: { assets: 0, campaigns: 0, editions: editions.length },
      status: 200,
    });
  });

  // Copilot nudge (suppress noise)
  await page.route('**/api/v1/copilot/nudge-context**', async (route) => {
    await route.fulfill({ json: { nudges: [] }, status: 200 });
  });
}

// ---------------------------------------------------------------------------
// Typed Playwright test fixture
// ---------------------------------------------------------------------------

export interface OfferStudioFixtures {
  /** The currently-mocked offer payload (changes per test via factory functions). */
  mockOffer: { offer: Offer; editions: LaunchEdition[] };
}

export const test = base.extend<OfferStudioFixtures>({
  mockOffer: async ({ page }, use) => {
    // Default fixture: TEMPORAL_COHORT offer with 3 editions.
    const payload = buildTemporalCohortOffer();
    await setupOfferStudioMocks(page, payload.offer, payload.editions);
    await use(payload);
  },
});

export { expect };
