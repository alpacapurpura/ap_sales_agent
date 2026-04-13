import { registerPreview } from "@/features/copilot/config/interview-preview-registry";
import { BrandPreviewSummary } from "./brand-preview-summary";
import { BrandPreviewSections } from "./brand-preview-sections";

/**
 * Register the brand domain preview in the PreviewRegistry.
 * This must be called (imported) before rendering an InterviewSplitView
 * with domain="brand". Typically imported in the brand interview page.
 */
registerPreview("brand", {
  summaryComponent: BrandPreviewSummary,
  sectionsComponent: BrandPreviewSections,
  emptyStateMessage: "Aún no hay datos de marca. Responde las preguntas para construir tu perfil.",
});
