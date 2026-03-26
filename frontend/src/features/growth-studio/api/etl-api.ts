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
