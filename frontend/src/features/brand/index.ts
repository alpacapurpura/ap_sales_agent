// Context & Hooks
export { BrandStudioProvider, useBrandStudio } from "./context/brand-studio-context";
export { useBrandSettings } from "./hooks/use-brand-settings";

// Config
export { BRAND_SECTIONS, BRAND_SECTION_ORDER, buildSectionNavItems } from "./config/sections";
export type { BrandSectionId, BrandSectionConfig } from "./config/sections";

// Types (re-export)
export type * from "./types";
export type { EditMode } from "./types/edit-mode";

// Validation
export type { StatusResult, ValidationStatus } from "./utils/brand-validation";
