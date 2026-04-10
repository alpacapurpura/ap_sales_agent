import { useAuth } from '@clerk/nextjs';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { fetchClient } from '@/lib/http-client';
import { config } from '@/lib/config';
import { camelizeKeys, snakeifyKeys } from '@/lib/case-conversion';
import type {
  AdCampaignTemplate,
  Association,
  AssociationCreatePayload,
  AssociationSuggestion,
  AssociationsFilters,
  MetaHealthCheck,
  MetricsByOffer,
  OfferSummary,
} from '../types/offer-association';
import type { MetaAdsPeriod } from '../types/metrics';

const API_URL = config.api.baseUrl;

// Shared case-conversion helpers live in @/lib/case-conversion.

function authHeaders(token: string): Record<string, string> {
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
}

// ---------------------------------------------------------------------------
// Plain fetch functions (exported for testing)
// ---------------------------------------------------------------------------

export async function fetchAssociations(
  token: string,
  filters?: AssociationsFilters,
): Promise<Association[]> {
  const params = new URLSearchParams();
  if (filters?.targetType) params.set('target_type', filters.targetType);
  if (filters?.offerId) params.set('offer_id', filters.offerId);
  const qs = params.toString();
  const url = `${API_URL}/api/v1/advertising/associations${qs ? `?${qs}` : ''}`;
  const res = await fetchClient(url, { headers: authHeaders(token) });
  if (!res.ok) throw new Error(`fetchAssociations failed: ${res.status}`);
  const json: unknown = await res.json();
  return camelizeKeys<Association[]>(json);
}

export async function createAssociation(
  token: string,
  payload: AssociationCreatePayload,
): Promise<Association> {
  const url = `${API_URL}/api/v1/advertising/associations`;
  const res = await fetchClient(url, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(snakeifyKeys(payload)),
  });
  if (!res.ok) throw new Error(`createAssociation failed: ${res.status}`);
  const json: unknown = await res.json();
  return camelizeKeys<Association>(json);
}

export async function deleteAssociation(
  token: string,
  associationId: string,
): Promise<void> {
  const url = `${API_URL}/api/v1/advertising/associations/${associationId}`;
  const res = await fetchClient(url, {
    method: 'DELETE',
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error(`deleteAssociation failed: ${res.status}`);
}

export async function autoDetectSuggestions(
  token: string,
): Promise<AssociationSuggestion[]> {
  const url = `${API_URL}/api/v1/advertising/associations/auto-detect`;
  const res = await fetchClient(url, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error(`autoDetectSuggestions failed: ${res.status}`);
  const json: unknown = await res.json();
  return camelizeKeys<AssociationSuggestion[]>(json);
}

export async function applySuggestions(
  token: string,
  suggestions: AssociationSuggestion[],
): Promise<Association[]> {
  const url = `${API_URL}/api/v1/advertising/associations/apply-suggestions`;
  const body = suggestions.map(s => ({
    target_type: s.targetType,
    target_external_id: s.targetExternalId,
    offer_id: s.suggestedOfferId,
    association_type: s.associationType,
    confidence: s.confidence,
  }));
  const res = await fetchClient(url, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`applySuggestions failed: ${res.status}`);
  const json: unknown = await res.json();
  return camelizeKeys<Association[]>(json);
}

export async function fetchMetaHealthCheck(
  token: string,
): Promise<MetaHealthCheck> {
  const url = `${API_URL}/api/v1/advertising/health-check?provider=meta`;
  const res = await fetchClient(url, { headers: authHeaders(token) });
  if (!res.ok) throw new Error(`fetchMetaHealthCheck failed: ${res.status}`);
  const json: unknown = await res.json();
  return camelizeKeys<MetaHealthCheck>(json);
}

export async function fetchMetricsByOffer(
  token: string,
  period: MetaAdsPeriod = '30d',
): Promise<MetricsByOffer> {
  const url = `${API_URL}/api/v1/advertising/metrics-by-offer?period=${period}`;
  const res = await fetchClient(url, { headers: authHeaders(token) });
  if (!res.ok) throw new Error(`fetchMetricsByOffer failed: ${res.status}`);
  const json: unknown = await res.json();
  return camelizeKeys<MetricsByOffer>(json);
}

export async function fetchOffersForAssignment(
  token: string,
): Promise<OfferSummary[]> {
  const url = `${API_URL}/api/v1/advertising/offers`;
  const res = await fetchClient(url, { headers: authHeaders(token) });
  if (!res.ok) throw new Error(`fetchOffersForAssignment failed: ${res.status}`);
  const json: unknown = await res.json();
  return camelizeKeys<OfferSummary[]>(json);
}

export async function fetchCampaignTemplateForOffer(
  token: string,
  offerId: string,
): Promise<AdCampaignTemplate | null> {
  const url = `${API_URL}/api/v1/advertising/campaign-templates/suggest?offer_id=${offerId}`;
  const res = await fetchClient(url, { headers: authHeaders(token) });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`fetchCampaignTemplateForOffer failed: ${res.status}`);
  const json: unknown = await res.json();
  return camelizeKeys<AdCampaignTemplate>(json);
}

// ---------------------------------------------------------------------------
// React Query hooks
// ---------------------------------------------------------------------------

export function useAssociations(filters?: AssociationsFilters) {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ['advertising', 'associations', filters ?? {}],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return fetchAssociations(token, filters);
    },
    staleTime: 2 * 60 * 1000,
  });
}

export function useCreateAssociation() {
  const { getToken } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: AssociationCreatePayload) => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return createAssociation(token, payload);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['advertising', 'associations'] });
      qc.invalidateQueries({ queryKey: ['advertising', 'health-check'] });
      qc.invalidateQueries({ queryKey: ['advertising', 'metrics-by-offer'] });
      qc.invalidateQueries({ queryKey: ['advertising', 'campaigns-with-offers'] });
    },
  });
}

export function useDeleteAssociation() {
  const { getToken } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (associationId: string) => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return deleteAssociation(token, associationId);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['advertising', 'associations'] });
      qc.invalidateQueries({ queryKey: ['advertising', 'health-check'] });
      qc.invalidateQueries({ queryKey: ['advertising', 'metrics-by-offer'] });
    },
  });
}

export function useAutoDetectSuggestions() {
  const { getToken } = useAuth();
  return useMutation({
    mutationFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return autoDetectSuggestions(token);
    },
  });
}

export function useApplySuggestions() {
  const { getToken } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (suggestions: AssociationSuggestion[]) => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return applySuggestions(token, suggestions);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['advertising', 'associations'] });
      qc.invalidateQueries({ queryKey: ['advertising', 'health-check'] });
      qc.invalidateQueries({ queryKey: ['advertising', 'metrics-by-offer'] });
    },
  });
}

export function useMetaHealthCheck(enabled = true) {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ['advertising', 'health-check', 'meta'],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return fetchMetaHealthCheck(token);
    },
    enabled,
    staleTime: 2 * 60 * 1000,
  });
}

export function useMetricsByOffer(
  period: MetaAdsPeriod = '30d',
  enabled = true,
) {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ['advertising', 'metrics-by-offer', period],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return fetchMetricsByOffer(token, period);
    },
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}

export function useOffersForAssignment(enabled = true) {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ['advertising', 'offers-for-assignment'],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return fetchOffersForAssignment(token);
    },
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}

export function useCampaignTemplateForOffer(
  offerId: string | null | undefined,
) {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ['advertising', 'campaign-template', offerId],
    queryFn: async () => {
      if (!offerId) return null;
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return fetchCampaignTemplateForOffer(token, offerId);
    },
    enabled: !!offerId,
    staleTime: 10 * 60 * 1000,
  });
}
