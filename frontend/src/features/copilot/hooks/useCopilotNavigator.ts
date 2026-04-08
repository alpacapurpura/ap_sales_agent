"use client";

import { useCallback, useEffect } from "react";
import { useParams } from "next/navigation";
import { useNavigation } from "@/components/shared/navigation";
import { useCopilotStore, type UIAction } from "../store/copilot-store";

export type { UIAction };

/**
 * Executes UI actions received from the copilot backend via SSE.
 * Also processes the pending action queue from the store.
 */
export function useCopilotNavigator() {
  const { navigate } = useNavigation();
  const params = useParams();
  const tenantId = params?.tenantId as string | undefined;
  const pendingUIActions = useCopilotStore((s) => s.pendingUIActions);

  const executeAction = useCallback(
    (action: UIAction) => {
      switch (action.type) {
        case "navigate": {
          if (!action.route) break;
          // Replace {tenantId} placeholder with actual tenant
          const route = tenantId
            ? action.route.replace(/{tenantId}/g, tenantId)
            : action.route;
          navigate(route);

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
    [navigate, tenantId]
  );

  // Process pending actions — read queue from store directly to avoid
  // unstable array reference in deps causing effect churn.
  const pendingLength = pendingUIActions.length;
  useEffect(() => {
    if (pendingLength === 0) return;
    const action = useCopilotStore.getState().dequeuUIAction();
    if (action) {
      executeAction(action);
    }
  }, [pendingLength, executeAction]);

  return { executeAction };
}
