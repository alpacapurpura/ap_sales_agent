/**
 * Register the offer domain preview in the PreviewRegistry.
 * Delegates to the full implementation in previews/.
 *
 * This must be imported (side-effect) before rendering an InterviewSplitView
 * with domain="offer". Typically imported in the offer interview page.
 */
import "./previews/register-offer-preview";
