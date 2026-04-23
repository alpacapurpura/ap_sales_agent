"use client";

import { useCopilotStore, type UIAction } from "../store/copilot-store";

const SECTION_KEY_BY_DOMAIN: Record<string, string> = {
  brand: "brand.root",
  buyer_persona: "brand.buyer-persona",
  offer: "offer.root",
};

const DOMAIN_LABEL: Record<string, string> = {
  brand: "Brand Studio",
  buyer_persona: "Buyer Persona",
  offer: "Offer Studio",
};

/**
 * Route a UIAction received from the SSE stream to the appropriate store
 * operation. Extracted from useCopilotChat to keep that hook focused on
 * the send/stream lifecycle.
 *
 * Session-aware actions (``guided_started`` / ``guided_block_advanced`` /
 * ``guided_completed`` / ``guided_ended``) set or clear the active
 * ``CopilotSession`` so the header + progress chip stay in sync with the
 * backend-driven flow. Legacy ``preview_update`` / ``interview_complete``
 * are ignored or mapped to their guided equivalents.
 */
export function handleUIAction(action: UIAction): void {
  const store = useCopilotStore.getState();

  switch (action.type) {
    // Legacy preview pane removed (Sprint 4a) — preview deltas ignored.
    case "preview_update":
      return;

    // Guided: started — set the session so the header + progress chip render.
    case "guided_started": {
      store.addUIActionToLastAssistant(action);
      const domain = action.domain ?? "brand";
      store.setSession({
        sectionKey: SECTION_KEY_BY_DOMAIN[domain] ?? `${domain}.root`,
        label: DOMAIN_LABEL[domain] ?? domain,
        entityId: action.entity_id ?? null,
        procedure: "guided",
        domain,
        progress: {
          totalBlocks: action.total_blocks ?? 0,
          blocksCompleted: [],
          currentBlock: action.current_block
            ? { id: action.current_block.id, label: action.current_block.label }
            : undefined,
        },
        startedAt: new Date(),
        snapshot: {},
      });
      return;
    }

    // Guided: block advanced — update progress while preserving session.
    case "guided_block_advanced": {
      store.addUIActionToLastAssistant(action);
      store.updateSession({
        progress: {
          totalBlocks: action.total_blocks ?? 0,
          blocksCompleted: action.completed_blocks ?? [],
          currentBlock: action.current_block
            ? { id: action.current_block.id, label: action.current_block.label }
            : undefined,
        },
      });
      return;
    }

    // Guided: completed or ended — clear the session, back to free chat.
    case "guided_completed":
    case "guided_ended":
      store.addUIActionToLastAssistant(action);
      store.clearSession();
      return;

    // Legacy interview_complete is treated as guided_completed.
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
