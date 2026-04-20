"use client";

import { useCopilotStore, type UIAction } from "../store/copilot-store";

/**
 * Route a UIAction received from the SSE stream to the appropriate store
 * operation. Extracted from useCopilotChat to keep that hook focused on
 * the send/stream lifecycle.
 *
 * Session-aware actions (``interview_complete``) clear the active session
 * after surfacing the completion card. All other types attach as cards to
 * the last assistant message. The legacy ``preview_update`` action is
 * ignored — live preview died with the sidebar preview pane in Sprint 4a.
 */
export function handleUIAction(action: UIAction): void {
  const store = useCopilotStore.getState();

  switch (action.type) {
    // Legacy preview pane removed (Sprint 4a) — preview deltas ignored.
    case "preview_update":
      return;

    // Interview complete: attach card + clear active session
    case "interview_complete":
      store.addUIActionToLastAssistant(action);
      store.clearSession();
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
