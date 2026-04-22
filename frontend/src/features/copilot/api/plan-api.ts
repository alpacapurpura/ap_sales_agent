import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import type { PlanApproveResponse, PlanRejectResponse } from "../types/conversations";

const BASE = `${config.api.baseUrl}/api/v1/copilot`;

/**
 * Approve a proposed plan.
 * Note: stub endpoint — plan execution is S5 scope (see UI-SPEC §15).
 */
export async function approvePlan(token: string, messageId: string): Promise<PlanApproveResponse> {
  const response = await fetchClient(`${BASE}/plan/${messageId}/approve`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`approvePlan failed: ${response.status}`);
  }

  return { status: "approved" };
}

/**
 * Reject a proposed plan.
 * Note: stub endpoint — plan execution is S5 scope (see UI-SPEC §15).
 */
export async function rejectPlan(token: string, messageId: string): Promise<PlanRejectResponse> {
  const response = await fetchClient(`${BASE}/plan/${messageId}/reject`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`rejectPlan failed: ${response.status}`);
  }

  return { status: "rejected" };
}
