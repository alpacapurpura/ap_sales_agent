import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import type {
  Enrollment,
  EnrollmentFilters,
  EnrollmentListResponse,
  PromoteWaitlistResponse,
} from "../types/enrollment";

const BASE = `${config.api.baseUrl}/api/v1/sales-agent/enrollments`;

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

function buildQuery(filters: EnrollmentFilters): string {
  const params = new URLSearchParams();
  if (filters.offer_id) params.set("offer_id", filters.offer_id);
  if (filters.edition_id) params.set("edition_id", filters.edition_id);
  if (filters.status) params.set("status", filters.status);
  if (filters.contact_id) params.set("contact_id", filters.contact_id);
  return params.toString();
}

export const enrollmentsApi = {
  list: async (filters: EnrollmentFilters, token: string): Promise<EnrollmentListResponse> => {
    const qs = buildQuery(filters);
    const url = qs ? `${BASE}?${qs}` : BASE;
    const res = await fetchClient(url, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return json<EnrollmentListResponse>(res);
  },

  listWaitlist: async (offerId: string, token: string): Promise<EnrollmentListResponse> => {
    const res = await fetchClient(`${BASE}/waitlist?offer_id=${offerId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return json<EnrollmentListResponse>(res);
  },

  getByConversation: async (conversationId: string, token: string): Promise<Enrollment | null> => {
    const res = await fetchClient(`${BASE}/by-conversation/${conversationId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return json<Enrollment | null>(res);
  },

  markPaid: async (
    enrollmentId: string,
    token: string,
    provider = "manual",
    transactionId?: string,
  ): Promise<Enrollment> => {
    const res = await fetchClient(`${BASE}/${enrollmentId}/mark-paid`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ provider, transaction_id: transactionId ?? null }),
    });
    return json<Enrollment>(res);
  },

  promoteWaitlist: async (
    enrollmentIds: string[],
    targetEditionId: string,
    token: string,
  ): Promise<PromoteWaitlistResponse> => {
    const res = await fetchClient(`${BASE}/promote-waitlist`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        enrollment_ids: enrollmentIds,
        target_edition_id: targetEditionId,
      }),
    });
    return json<PromoteWaitlistResponse>(res);
  },
};
