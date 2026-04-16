"use client";

import { useCopilotStore, type UIAction } from "../store/copilot-store";

/**
 * Route a UIAction received from the SSE stream to the appropriate store
 * operation. Extracted from useCopilotChat to keep that hook focused on
 * the send/stream lifecycle.
 *
 * Interview-specific actions get special handling (clear session, update
 * procedure stepper, etc.). All other types are attached as cards to the
 * last assistant message.
 */
export function handleUIAction(action: UIAction): void {
  const store = useCopilotStore.getState();

  switch (action.type) {
    // Silent: update preview data, don't show as card
    case "preview_update":
      if (action.delta) {
        store.updatePreviewData(action.delta);
      }
      return;

    // Interview complete: attach card + clear interview state
    case "interview_complete":
      store.addUIActionToLastAssistant(action);
      store.clearInterview();
      return;

    // Navigation: attach card + enqueue for router
    case "navigate":
      store.addUIActionToLastAssistant(action);
      store.enqueuUIAction(action);
      return;

    // Procedure progress: update store for stepper
    case "procedure_progress":
      store.addUIActionToLastAssistant(action);
      if (action.procedure_id && action.steps) {
        store.setActiveProcedure({
          id: action.procedure_id,
          name: action.procedure_name || action.procedure_id,
          steps: action.steps,
          currentStepIndex: action.current_step_index ?? 0,
        });
      }
      return;

    // All other types (proposal, alternatives_card, clarify_card, checkpoint_card, etc.)
    default:
      store.addUIActionToLastAssistant(action);
      return;
  }
}
