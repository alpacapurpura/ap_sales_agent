"use client";

import { useCallback, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useCopilotStore, type UIAction } from "../store/copilot-store";

export type { UIAction };

/**
 * Executes UI actions received from the copilot backend via SSE.
 * Also processes the pending action queue from the store.
 */
export function useCopilotNavigator() {
  const router = useRouter();
  const params = useParams();
  const tenantId = params?.tenantId as string | undefined;
  const pendingUIActions = useCopilotStore((s) => s.pendingUIActions);
  const dequeuUIAction = useCopilotStore((s) => s.dequeuUIAction);

  const executeAction = useCallback(
    (action: UIAction) => {
      switch (action.type) {
        case "navigate": {
          if (!action.route) break;
          // Replace {tenantId} placeholder with actual tenant
          const route = tenantId
            ? action.route.replace(/{tenantId}/g, tenantId)
            : action.route;
          router.push(route);

          // If a section_id is provided, scroll to it after navigation
          if (action.section_id) {
            setTimeout(() => {
              const el =
                document.getElementById(action.section_id!) ??
                document.querySelector(
                  `[data-section="${action.section_id}"]`
                );
              if (el) {
                el.scrollIntoView({ behavior: "smooth", block: "center" });
                el.classList.add("copilot-highlight");
                setTimeout(
                  () => el.classList.remove("copilot-highlight"),
                  3000
                );
              }
            }, 800);
          }
          break;
        }

        case "scroll_to_field": {
          if (!action.field_id) break;
          const el =
            document.getElementById(action.field_id) ??
            document.querySelector(
              `[data-field-id="${action.field_id}"]`
            ) ??
            document.querySelector(`[name="${action.field_id}"]`);
          if (el) {
            el.scrollIntoView({ behavior: "smooth", block: "center" });
            el.classList.add("copilot-highlight");
            setTimeout(() => el.classList.remove("copilot-highlight"), 3000);
          }
          break;
        }

        case "open_form": {
          window.dispatchEvent(
            new CustomEvent("copilot:open-form", {
              detail: {
                formId: action.form_id,
                prefillData: action.prefill_data,
              },
            })
          );
          break;
        }
      }
    },
    [router, tenantId]
  );

  // Process pending actions from the queue
  useEffect(() => {
    if (pendingUIActions.length === 0) return;
    const action = dequeuUIAction();
    if (action) {
      executeAction(action);
    }
  }, [pendingUIActions, dequeuUIAction, executeAction]);

  return { executeAction };
}
