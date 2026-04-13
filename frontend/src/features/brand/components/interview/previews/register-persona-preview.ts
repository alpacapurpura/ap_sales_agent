import { registerPreview } from "@/features/copilot/config/interview-preview-registry";
import { PersonaPreviewSummary } from "./persona-preview-summary";
import { PersonaPreviewSections } from "./persona-preview-sections";

/**
 * Register the buyer_persona domain preview in the PreviewRegistry.
 * This must be imported (side-effect) before rendering an InterviewSplitView
 * with domain="buyer_persona". Typically imported in the persona interview page.
 */
registerPreview("buyer_persona", {
  summaryComponent: PersonaPreviewSummary,
  sectionsComponent: PersonaPreviewSections,
  emptyStateMessage:
    "Comienza la entrevista para construir tu buyer persona",
});
