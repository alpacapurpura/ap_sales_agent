import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

export interface SyncChannelResult {
  status: string;
  run_id: string;
  provider: string;
  channel_slug: string;
}

export interface SyncChannelError {
  detail: string;
  remaining_minutes?: number;
}

export async function syncChannel(
  token: string,
  channelSlug: string,
): Promise<SyncChannelResult> {
  const res = await fetchClient(
    `${API_URL}/api/v1/analytics/metrics/attraction/refresh/${channelSlug}`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    },
  );

  if (res.status === 429) {
    const errData = (await res.json().catch(() => ({}))) as { detail?: string; remaining_minutes?: number };
    const err: SyncChannelError = {
      detail: errData.detail ?? "Rate limited",
      remaining_minutes: errData.remaining_minutes,
    };
    throw err;
  }

  if (!res.ok) {
    const errData = (await res.json().catch(() => ({}))) as { detail?: string };
    throw { detail: errData.detail ?? `Sync failed (${res.status})` } as SyncChannelError;
  }

  return res.json() as Promise<SyncChannelResult>;
}
