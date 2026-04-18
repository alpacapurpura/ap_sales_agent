/**
 * Typed fixtures for the archetype + section catalog API response.
 *
 * Used by every test that renders a hook or component depending on
 * ``useArchetypeCatalog``. Keeping a single fixture here prevents drift
 * between test mocks and the real backend contract — if the backend
 * ``test_archetypes_api`` adds a required field, TypeScript fails this
 * fixture first, surfacing the drift immediately.
 */

import { OfferArchetype } from "../../types";

import type {
  ArchetypeCapabilities,
  ArchetypeCatalogResponse,
  SectionMetadata,
} from "../../api/archetype-catalog-api";

const section = (
  key: SectionMetadata["key"],
  scope: SectionMetadata["scope"],
  label_es: string,
  icon_name: string,
): SectionMetadata => ({
  key,
  label_es,
  subtitle_es: `${label_es} — descripción de prueba`,
  help_text_es: `${label_es} — contexto ampliado de prueba para el copilot que describe qué, cómo y por qué.`,
  icon_name,
  scope,
  completion_weight: 0.5,
  required_to_publish: false,
});

const IDENTITY = section("identity", "offer_level", "Identidad de oferta", "Fingerprint");
const STRATEGY = section("strategy", "offer_level", "Estrategia y avatar", "Target");
const PSYCHOLOGY = section("psychology", "offer_level", "Psicología", "Brain");
const PROMISE = section("promise", "offer_level", "Promesa", "Star");
const VALUE_STACK = section("value_stack", "offer_level", "Stack de valor", "Layers");
const INSTRUCTORS = section("instructors", "offer_level", "Instructores", "Users");
const KNOWLEDGE = section("knowledge", "offer_level", "Conocimiento", "Database");
const CLOSING = section("closing", "offer_level", "Cierre", "CheckCircle");
const PRODUCT_DETAILS = section("product_details", "offer_level", "Producto", "Package");
const SUBSCRIPTION_DETAILS = section(
  "subscription_details",
  "offer_level",
  "Suscripción",
  "RefreshCw",
);
const GALLERY = section("gallery", "offer_level", "Galería", "Image");
const EVENT_DETAILS = section("event_details", "edition_level", "Evento", "Calendar");
const PRICING = section("pricing", "mixed", "Precios", "DollarSign");
const PROGRAM_DETAILS = section("program_details", "mixed", "Programa", "BookOpen");
const SERVICE_DETAILS = section("service_details", "mixed", "Servicio", "Briefcase");
const RESOURCES = section("resources", "mixed", "Recursos", "Library");
const FAQ = section("faq", "offer_level", "FAQ", "HelpCircle");
const TESTIMONIALS = section("testimonials", "offer_level", "Testimonios", "Quote");
const PORTFOLIO = section("portfolio", "offer_level", "Portfolio", "Trophy");
const METHODOLOGY = section("methodology", "offer_level", "Metodología", "Workflow");
const CREDENTIALS = section("credentials", "offer_level", "Credenciales", "Shield");
const LOCATION = section("location", "mixed", "Ubicación", "MapPin");
const PLATFORM_DETAILS = section("platform_details", "offer_level", "Plataforma", "Cpu");

export const MOCK_SECTION_CATALOG: readonly SectionMetadata[] = [
  IDENTITY,
  STRATEGY,
  PSYCHOLOGY,
  PROMISE,
  VALUE_STACK,
  INSTRUCTORS,
  KNOWLEDGE,
  CLOSING,
  PRODUCT_DETAILS,
  SUBSCRIPTION_DETAILS,
  GALLERY,
  EVENT_DETAILS,
  PRICING,
  PROGRAM_DETAILS,
  SERVICE_DETAILS,
  RESOURCES,
  FAQ,
  TESTIMONIALS,
  PORTFOLIO,
  METHODOLOGY,
  CREDENTIALS,
  LOCATION,
  PLATFORM_DETAILS,
];

const BASE_CAPABILITIES_DEFAULTS = {
  requires_start_date_on_publish: false,
  requires_end_date_on_publish: false,
  requires_location_on_publish: false,
  supports_capacity: false,
  supports_waitlist: false,
  default_delivery: "diy",
  default_fulfillment: "digital_download",
  examples_es: [] as readonly string[],
  editions_wizard_copy: null,
};

const EXPERIENCIA_ARCHETYPE: ArchetypeCapabilities = {
  ...BASE_CAPABILITIES_DEFAULTS,
  archetype: OfferArchetype.EXPERIENCIA,
  supports_editions: true,
  edition_structure: "single_date",
  edition_noun_es: "salida",
  edition_noun_plural_es: "salidas",
  requires_start_date_on_publish: true,
  requires_location_on_publish: true,
  supports_capacity: true,
  supports_waitlist: true,
  default_delivery: "dwy",
  default_fulfillment: "manual_provisioning",
  label_es: "Experiencia / Evento",
  subtitle_es: "Un momento único",
  icon_name: "Tent",
  examples_es: ["Retiro", "Taller"],
  editions_wizard_copy: {
    title: "¿Tendrá varias salidas?",
    description: "...",
    yes_label: "Sí",
    no_label: "No",
  },
  sections: [
    IDENTITY,
    STRATEGY,
    PSYCHOLOGY,
    PROMISE,
    EVENT_DETAILS,
    INSTRUCTORS,
    VALUE_STACK,
    RESOURCES,
    PRICING,
    CLOSING,
    KNOWLEDGE,
  ],
};

const PROGRAMA_ARCHETYPE: ArchetypeCapabilities = {
  ...BASE_CAPABILITIES_DEFAULTS,
  archetype: OfferArchetype.PROGRAMA,
  supports_editions: true,
  edition_structure: "cohort",
  edition_noun_es: "cohorte",
  edition_noun_plural_es: "cohortes",
  requires_start_date_on_publish: true,
  requires_end_date_on_publish: true,
  supports_capacity: true,
  supports_waitlist: true,
  default_delivery: "dwy",
  default_fulfillment: "lms_access",
  label_es: "Programa",
  subtitle_es: "Un proceso con inicio y fin",
  icon_name: "Map",
  examples_es: ["Bootcamp"],
  sections: [
    IDENTITY,
    STRATEGY,
    PSYCHOLOGY,
    PROMISE,
    PROGRAM_DETAILS,
    INSTRUCTORS,
    VALUE_STACK,
    RESOURCES,
    PRICING,
    CLOSING,
    KNOWLEDGE,
  ],
};

const SERVICIO_ARCHETYPE: ArchetypeCapabilities = {
  ...BASE_CAPABILITIES_DEFAULTS,
  archetype: OfferArchetype.SERVICIO,
  supports_editions: true,
  edition_structure: "recurring",
  edition_noun_es: "convocatoria",
  edition_noun_plural_es: "convocatorias",
  supports_capacity: true,
  default_delivery: "dfy",
  default_fulfillment: "manual_provisioning",
  label_es: "Servicio",
  subtitle_es: "Trabajo que hago con alguien",
  icon_name: "Wrench",
  examples_es: ["Consultoría"],
  sections: [
    IDENTITY,
    STRATEGY,
    PSYCHOLOGY,
    PROMISE,
    SERVICE_DETAILS,
    INSTRUCTORS,
    VALUE_STACK,
    RESOURCES,
    PRICING,
    CLOSING,
    KNOWLEDGE,
  ],
};

const PRODUCTO_ARCHETYPE: ArchetypeCapabilities = {
  ...BASE_CAPABILITIES_DEFAULTS,
  archetype: OfferArchetype.PRODUCTO,
  supports_editions: false,
  edition_structure: "none",
  edition_noun_es: "",
  edition_noun_plural_es: "",
  label_es: "Producto",
  subtitle_es: "Algo que creas",
  icon_name: "Package",
  examples_es: ["Ebook"],
  sections: [
    IDENTITY,
    STRATEGY,
    PSYCHOLOGY,
    PROMISE,
    PRODUCT_DETAILS,
    VALUE_STACK,
    RESOURCES,
    PRICING,
    CLOSING,
    KNOWLEDGE,
  ],
};

const MEMBRESIA_ARCHETYPE: ArchetypeCapabilities = {
  ...BASE_CAPABILITIES_DEFAULTS,
  archetype: OfferArchetype.MEMBRESIA,
  supports_editions: false,
  edition_structure: "none",
  edition_noun_es: "",
  edition_noun_plural_es: "",
  default_fulfillment: "lms_access",
  label_es: "Membresía",
  subtitle_es: "Acceso por suscripción",
  icon_name: "RefreshCw",
  examples_es: ["Club"],
  sections: [
    IDENTITY,
    STRATEGY,
    PSYCHOLOGY,
    PROMISE,
    SUBSCRIPTION_DETAILS,
    VALUE_STACK,
    RESOURCES,
    PRICING,
    CLOSING,
    KNOWLEDGE,
  ],
};

export const MOCK_ARCHETYPE_CATALOG_RESPONSE: ArchetypeCatalogResponse = {
  version: "test-2026-04-18",
  archetypes: [
    EXPERIENCIA_ARCHETYPE,
    PROGRAMA_ARCHETYPE,
    SERVICIO_ARCHETYPE,
    PRODUCTO_ARCHETYPE,
    MEMBRESIA_ARCHETYPE,
  ],
  section_catalog: MOCK_SECTION_CATALOG,
};
