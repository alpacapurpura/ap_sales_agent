import { fetchClient } from '@/lib/http-client';
import { config } from '@/lib/config';

const API_URL = config.api.baseUrl;

export async function triggerInitialLoad(token: string, provider: string, days: number = 30): Promise<{
  status: string;
  total_days: number;
  loaded_days: number;
  skipped_days: number;
}> {
  const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/${provider}/initial-load?days=${days}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Initial load failed (${res.status})`);
  }
  return res.json();
}

export async function getInitialLoadStatus(token: string, provider: string): Promise<{
  status: string;
  total_days?: number;
  completed_days?: number;
}> {
  const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/${provider}/initial-load/status`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return { status: 'idle' };
  return res.json();
}

// ─── Sync All Sources ─────────────────────────────────────────────────────────

export interface SyncProviderResult {
  provider: string;
  status: 'ok' | 'skipped_cooldown' | 'failed';
  loaded?: number;
  skipped?: number;
  total?: number;
  remaining_minutes?: number;
  error?: string;
}

export interface SyncAllResponse {
  status: string;
  providers_synced: number;
  providers_skipped_cooldown: number;
  providers_failed: number;
  total_loaded: number;
  total_skipped: number;
  details: SyncProviderResult[];
}

export async function triggerSyncAll(token: string, days: number = 30): Promise<SyncAllResponse> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 120_000);
  try {
    const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/sync?days=${days}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      signal: controller.signal,
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Sync failed (${res.status})`);
    }
    return res.json();
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new Error('Sincronizacion agotada (>2 min). Intenta de nuevo.');
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}
