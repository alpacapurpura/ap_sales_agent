import { registerPreview } from "@/features/copilot/config/interview-preview-registry";
import { OfferPreviewSummary } from "./offer-preview-summary";
import { OfferPreviewSections } from "./offer-preview-sections";

/**
 * Register the offer domain preview in the PreviewRegistry.
 * This must be called (imported) before rendering an InterviewSplitView
 * with domain="offer". Typically imported in the offer interview page.
 */
registerPreview("offer", {
  summaryComponent: OfferPreviewSummary,
  sectionsComponent: OfferPreviewSections,
  emptyStateMessage:
    "Comienza la entrevista para dise\u00f1ar tu oferta",
});
