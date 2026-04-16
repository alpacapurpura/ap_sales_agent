/**
 * ARCH TEST: Component files must be PascalCase.
 *
 * Rule: every .tsx file under any components/ directory or components/shared/ must have
 * a PascalCase basename (e.g. MyWidget.tsx, not my-widget.tsx).
 *
 * Ratchet pattern: KNOWN_KEBAB_COMPONENTS is frozen at 2026-04-15 violations.
 * This set MUST only shrink — never add new entries.
 * To fix: git mv old.tsx New.tsx, update all imports, run tsc --noEmit.
 */
import { describe, it, expect } from "vitest";
import * as path from "path";
import {
  FEATURES_DIR,
  SHARED_COMPONENTS_DIR,
  walkFiles,
  relPath,
  isPascalCase,
  isTestFile,
} from "./helpers";

// ── Ratchet allowlist ─────────────────────────────────────────────────────────
// These 187 entries existed on 2026-04-15. Fix them in Phase 2 and remove.
const KNOWN_KEBAB_COMPONENTS = new Set([
  // admin (1)
  "features/admin/components/tenants-list.tsx",
  // audit (6)
  "features/audit/components/chat-timeline.tsx",
  "features/audit/components/context-panel.tsx",
  "features/audit/components/node-details-panel.tsx",
  "features/audit/components/node-icons.tsx",
  "features/audit/components/trace-inspector.tsx",
  "features/audit/components/user-list.tsx",
  // brand (26)
  "features/brand/components/empty-state/brand-empty-state.tsx",
  "features/brand/components/forms/edit-sheet-manager.tsx",
  "features/brand/components/interview/brand-preview-sections.tsx",
  "features/brand/components/interview/brand-preview-summary.tsx",
  "features/brand/components/interview/previews/persona-preview-sections.tsx",
  "features/brand/components/interview/previews/persona-preview-summary.tsx",
  "features/brand/components/layout/brand-section-shell.tsx",
  "features/brand/components/layout/section-header.tsx",
  "features/brand/components/legal/legal-form.tsx",
  "features/brand/components/legal/legal-manager.tsx",
  "features/brand/components/navigation/section-nav-rail.tsx",
  "features/brand/components/onboarding/onboarding-wizard.tsx",
  "features/brand/components/onboarding/step-documents.tsx",
  "features/brand/components/onboarding/step-gap-review.tsx",
  "features/brand/components/onboarding/step-processing.tsx",
  "features/brand/components/onboarding/step-source-picker.tsx",
  "features/brand/components/onboarding/step-website.tsx",
  "features/brand/components/onboarding/wizard-progress-bar.tsx",
  "features/brand/components/smart-fill/smart-fill-dialog.tsx",
  "features/brand/components/tabs/brand-studio-tabs.tsx",
  "features/brand/components/views/avatar-edit-view.tsx",
  "features/brand/components/views/esencia-view.tsx",
  "features/brand/components/views/estrategia-view.tsx",
  "features/brand/components/views/identidad-creativa-view.tsx",
  "features/brand/components/views/persona-detail-view.tsx",
  "features/brand/components/views/publico-view.tsx",
  // closer-studio (13)
  "features/closer-studio/components/closer-layout.tsx",
  "features/closer-studio/components/frozen/frozen-card.tsx",
  "features/closer-studio/components/frozen/frozen-list.tsx",
  "features/closer-studio/components/inbox/contact-sidebar.tsx",
  "features/closer-studio/components/inbox/conversation-item.tsx",
  "features/closer-studio/components/inbox/conversation-list.tsx",
  "features/closer-studio/components/inbox/conversation-thread.tsx",
  "features/closer-studio/components/inbox/inbox-view.tsx",
  "features/closer-studio/components/inbox/message-bubble.tsx",
  "features/closer-studio/components/inbox/message-input.tsx",
  "features/closer-studio/components/pipeline/pipeline-board.tsx",
  "features/closer-studio/components/pipeline/pipeline-card.tsx",
  "features/closer-studio/components/pipeline/pipeline-column.tsx",
  // connections (16)
  "features/connections/components/connection-card.tsx",
  "features/connections/components/connection-detail-layout.tsx",
  "features/connections/components/connections-hub.tsx",
  "features/connections/components/gmail-view.tsx",
  "features/connections/components/google-analytics-view.tsx",
  "features/connections/components/google-calendar-view.tsx",
  "features/connections/components/google-workspace-view.tsx",
  "features/connections/components/mailerlite-view.tsx",
  "features/connections/components/manychat-view.tsx",
  "features/connections/components/meta-view.tsx",
  "features/connections/components/oauth-callback-handler.tsx",
  "features/connections/components/property-picker.tsx",
  "features/connections/components/shopify-view.tsx",
  "features/connections/components/telegram-view.tsx",
  "features/connections/components/whatsapp-view.tsx",
  "features/connections/components/youtube-view.tsx",
  // copilot (16)
  "features/copilot/components/cards/alternatives-card.tsx",
  "features/copilot/components/cards/checkpoint-card.tsx",
  "features/copilot/components/cards/clarify-card.tsx",
  "features/copilot/components/cards/interview-complete-card.tsx",
  "features/copilot/components/copilot-header.tsx",
  "features/copilot/components/copilot-input.tsx",
  "features/copilot/components/copilot-preview-pane.tsx",
  "features/copilot/components/copilot-sidebar.tsx",
  "features/copilot/components/copilot-status-bar.tsx",
  "features/copilot/components/focus-bar.tsx",
  "features/copilot/components/focus-mode-button.tsx",
  "features/copilot/components/shared/attachment-button.tsx",
  "features/copilot/components/shared/document-chip.tsx",
  "features/copilot/components/shared/interview-mode-button.tsx",
  "features/copilot/components/shared/section-chat-trigger.tsx",
  "features/copilot/components/shared/voice-button.tsx",
  // growth-studio (2)
  "features/growth-studio/components/connection-health-banner.tsx",
  "features/growth-studio/components/sync-progress-dialog.tsx",
  // offer-studio (75)
  "features/offer-studio/components/assets/asset-card.tsx",
  "features/offer-studio/components/assets/asset-generation-wizard-dialog.tsx",
  "features/offer-studio/components/assets/asset-toolbar.tsx",
  "features/offer-studio/components/assets/assets-view.tsx",
  "features/offer-studio/components/campaigns/campaigns-view.tsx",
  "features/offer-studio/components/container/auto-save-indicator.tsx",
  "features/offer-studio/components/container/generate-landing-confirm-dialog.tsx",
  "features/offer-studio/components/container/landing-action-button.tsx",
  "features/offer-studio/components/container/landing-kebab-menu.tsx",
  "features/offer-studio/components/container/offer-progress-bar.tsx",
  "features/offer-studio/components/container/offer-shell-header-row1.tsx",
  "features/offer-studio/components/container/offer-shell-header-row2.tsx",
  "features/offer-studio/components/container/offer-shell.tsx",
  "features/offer-studio/components/container/offer-status-change-modal.tsx",
  "features/offer-studio/components/container/offer-status-switcher.tsx",
  "features/offer-studio/components/container/offer-tab-bar.tsx",
  "features/offer-studio/components/dashboard/add-offer-card.tsx",
  "features/offer-studio/components/dashboard/ladder-progress-bar.tsx",
  "features/offer-studio/components/dashboard/lead-magnet-stream-card.tsx",
  "features/offer-studio/components/dashboard/offer-card.tsx",
  "features/offer-studio/components/dashboard/offer-ladder-layout.tsx",
  "features/offer-studio/components/dashboard/offer-legend.tsx",
  "features/offer-studio/components/dashboard/offer-studio-dashboard.tsx",
  "features/offer-studio/components/editor/components/ai-assist-button.tsx",
  "features/offer-studio/components/editor/components/cards/offer-objections-card.tsx",
  "features/offer-studio/components/editor/components/cards/offer-psychology-card.tsx",
  "features/offer-studio/components/editor/components/offer-gallery-section.tsx",
  "features/offer-studio/components/editor/offer-edit-sheet-manager.tsx",
  "features/offer-studio/components/editor/offer-editor-content.tsx",
  "features/offer-studio/components/editor/offer-live-preview.tsx",
  "features/offer-studio/components/editor/offer-section-wrapper.tsx",
  "features/offer-studio/components/editor/offer-section/offer-section.tsx",
  "features/offer-studio/components/editor/sections/closing/closing-form.tsx",
  "features/offer-studio/components/editor/sections/closing/closing-preview.tsx",
  "features/offer-studio/components/editor/sections/common/editions-opt-in.tsx",
  "features/offer-studio/components/editor/sections/common/placeholder-form.tsx",
  "features/offer-studio/components/editor/sections/common/placeholder-preview.tsx",
  "features/offer-studio/components/editor/sections/common/section-form-wrapper.tsx",
  "features/offer-studio/components/editor/sections/event-details/event-form.tsx",
  "features/offer-studio/components/editor/sections/identity/identity-form.tsx",
  "features/offer-studio/components/editor/sections/identity/identity-preview.tsx",
  "features/offer-studio/components/editor/sections/instructors/instructors-form.tsx",
  "features/offer-studio/components/editor/sections/instructors/instructors-manager.tsx",
  "features/offer-studio/components/editor/sections/instructors/instructors-preview.tsx",
  "features/offer-studio/components/editor/sections/instructors/instructors-selector.tsx",
  "features/offer-studio/components/editor/sections/pricing/pricing-form.tsx",
  "features/offer-studio/components/editor/sections/pricing/pricing-preview.tsx",
  "features/offer-studio/components/editor/sections/pricing/tier-comparison-builder.tsx",
  "features/offer-studio/components/editor/sections/product-details/product-form.tsx",
  "features/offer-studio/components/editor/sections/program-details/curriculum-builder.tsx",
  "features/offer-studio/components/editor/sections/program-details/import-curriculum-dialog.tsx",
  "features/offer-studio/components/editor/sections/program-details/program-form.tsx",
  "features/offer-studio/components/editor/sections/program-details/session-schedule-builder.tsx",
  "features/offer-studio/components/editor/sections/promise/promise-form.tsx",
  "features/offer-studio/components/editor/sections/psychology/psychology-form.tsx",
  "features/offer-studio/components/editor/sections/resources/resources-form.tsx",
  "features/offer-studio/components/editor/sections/resources/resources-manager.tsx",
  "features/offer-studio/components/editor/sections/resources/resources-preview.tsx",
  "features/offer-studio/components/editor/sections/service-details/service-form.tsx",
  "features/offer-studio/components/editor/sections/strategy/strategy-form.tsx",
  "features/offer-studio/components/editor/sections/strategy/strategy-preview.tsx",
  "features/offer-studio/components/editor/sections/subscription-details/subscription-form.tsx",
  "features/offer-studio/components/editor/sections/value-stack/value-stack-form.tsx",
  "features/offer-studio/components/editor/sections/value-stack/value-stack-preview.tsx",
  "features/offer-studio/components/editor/sections/visuals/gallery-form.tsx",
  "features/offer-studio/components/editor/sections/visuals/gallery-manager.tsx",
  "features/offer-studio/components/editor/sections/visuals/gallery-preview.tsx",
  "features/offer-studio/components/editor/ui/offer-context-panel.tsx",
  "features/offer-studio/components/editor/ui/offers-multi-select.tsx",
  "features/offer-studio/components/interview/previews/offer-preview-sections.tsx",
  "features/offer-studio/components/interview/previews/offer-preview-summary.tsx",
  "features/offer-studio/components/knowledge/knowledge-view.tsx",
  "features/offer-studio/components/landing/components/blocks/hero/hero.tsx",
  "features/offer-studio/components/landing/components/editor/landing-editor.tsx",
  "features/offer-studio/components/landing/utils/puck.config.tsx",
  // sales (16)
  "features/sales/components/availability-view.tsx",
  "features/sales/components/dashboard/activity-feed-widget.tsx",
  "features/sales/components/dashboard/calendar-widget.tsx",
  "features/sales/components/dashboard/conversion-command-center.tsx",
  "features/sales/components/dashboard/lanes/agenda-lane.tsx",
  "features/sales/components/dashboard/lanes/opportunity-lane.tsx",
  "features/sales/components/dashboard/lanes/sales-lane.tsx",
  "features/sales/components/event-type-form.tsx",
  "features/sales/components/event-type-view.tsx",
  "features/sales/components/generate-link-modal.tsx",
  "features/sales/components/overlay/appointment-sheet.tsx",
  "features/sales/components/overlay/availability-modal.tsx",
  "features/sales/components/overlay/payment-gateway-config.tsx",
  "features/sales/components/overlay/sales-inbox-sheet.tsx",
  "features/sales/components/sales-dashboard.tsx",
  "features/sales/components/views/sales-mock-view.tsx",
  // settings (7)
  "features/settings/components/ai-keys-form.tsx",
  "features/settings/components/general-settings-form.tsx",
  "features/settings/components/payment-settings-view.tsx",
  "features/settings/components/profile-view.tsx",
  "features/settings/components/scheduling-settings-view.tsx",
  "features/settings/components/team-view.tsx",
  "features/settings/components/webhook-view.tsx",
  // components/shared (9)
  "components/shared/development-tools.tsx",
  "components/shared/error-boundary.tsx",
  "components/shared/layout/app-sidebar.tsx",
  "components/shared/layout/sidebar-context.tsx",
  "components/shared/layout/tenant-switcher.tsx",
  "components/shared/mode-toggle.tsx",
  "components/shared/navigation/nav-link.tsx",
  "components/shared/navigation/navigation-context.tsx",
  "components/shared/navigation/navigation-overlay.tsx",
]);

// ─────────────────────────────────────────────────────────────────────────────

const COMPONENTS_SEGMENT = path.sep + "components" + path.sep;

describe("Architecture: Component naming", () => {
  it("every .tsx file under components/ must be PascalCase", () => {
    const featureFiles = walkFiles(FEATURES_DIR)
      .filter((f) => f.includes(COMPONENTS_SEGMENT) && f.endsWith(".tsx"))
      .filter((f) => !isTestFile(f));

    const sharedFiles = walkFiles(SHARED_COMPONENTS_DIR)
      .filter((f) => f.endsWith(".tsx"))
      .filter((f) => !isTestFile(f));

    const violations: string[] = [];

    for (const file of [...featureFiles, ...sharedFiles]) {
      const basename = path.basename(file, ".tsx");
      if (!isPascalCase(basename)) {
        violations.push(relPath(file));
      }
    }

    const newViolations = violations.filter((v) => !KNOWN_KEBAB_COMPONENTS.has(v));
    const alreadyFixed = [...KNOWN_KEBAB_COMPONENTS].filter((v) => !violations.includes(v));

    if (alreadyFixed.length > 0) {
      console.info(
        `[arch] Allowlist can shrink: ${alreadyFixed.length} entries already fixed:\n  ${alreadyFixed.join("\n  ")}`,
      );
    }

    expect(
      newViolations,
      `NEW component naming violations (rename to PascalCase and update imports):\n${newViolations.join("\n")}`,
    ).toEqual([]);
  });
});
