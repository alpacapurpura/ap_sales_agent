import { fetchClient } from '@/lib/http-client';
import { config } from '@/lib/config';

const API_URL = config.api.baseUrl;

export async function promoteToEvangelist(token: string, customerId: string): Promise<any> {
  const res = await fetchClient(`${API_URL}/api/v1/crm/referrals/promote`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ customer_id: customerId }),
  });
  if (!res.ok) throw new Error('Failed to promote');
  return res.json();
}

export async function createNpsSurvey(token: string, payload: { customer_id?: string; offer_id?: string; delivery_channel?: string }): Promise<any> {
  const res = await fetchClient(`${API_URL}/api/v1/crm/nps/surveys`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to create survey');
  return res.json();
}
