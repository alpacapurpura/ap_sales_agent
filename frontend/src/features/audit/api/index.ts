import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

export const API_BASE = `${config.api.baseUrl}/api/v1/admin`;

export async function clearLeadHistory(token: string, leadId: string) {
  const res = await fetchClient(`${API_BASE}/audit/leads/${leadId}/history`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to clear history");
  return res.json();
}
