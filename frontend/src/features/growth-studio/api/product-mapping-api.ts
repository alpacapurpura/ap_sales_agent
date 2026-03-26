import { fetchClient } from '@/lib/http-client';
import { config } from '@/lib/config';

const API_URL = config.api.baseUrl;

// --- Product Mapping Types ---
export interface UnmatchedProduct {
  external_id: string;
  external_name: string | null;
  total_price: number | null;
  currency: string | null;
  event_count: number;
}

export interface SourceProduct {
  external_id: string;
  external_name: string | null;
  source: string;
  total_price: number;
  currency: string | null;
  event_count: number;
  is_mapped: boolean;
  offer_id: string | null;
  offer_name: string | null;
  mapping_id: string | null;
}

export interface ProductMapping {
  id: string;
  tenant_id: string;
  offer_id: string;
  source: string;
  external_id: string;
  external_name: string | null;
  metadata_info: Record<string, unknown>;
}

export interface CreateProductMappingResult {
  id: string;
  tenant_id: string;
  offer_id: string;
  source: string;
  external_id: string;
  external_name: string | null;
  metadata_info: Record<string, unknown>;
  sales_created: number;
}

export async function getUnmatchedProducts(token: string, source: string = 'shopify'): Promise<UnmatchedProduct[]> {
  const res = await fetchClient(`${API_URL}/api/v1/offer/product-mappings/unmatched?source=${source}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return [];
  return res.json();
}

export async function getSourceProducts(token: string, source: string = 'shopify'): Promise<SourceProduct[]> {
  const res = await fetchClient(`${API_URL}/api/v1/offer/product-mappings/source-products?source=${source}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return [];
  return res.json();
}

export async function getProductMappings(token: string, source: string = 'shopify'): Promise<ProductMapping[]> {
  const res = await fetchClient(`${API_URL}/api/v1/offer/product-mappings?source=${source}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return [];
  return res.json();
}

export async function createProductMapping(token: string, payload: { offer_id: string; source: string; external_id: string; external_name?: string }): Promise<CreateProductMappingResult> {
  const res = await fetchClient(`${API_URL}/api/v1/offer/product-mappings`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to create mapping');
  }
  return res.json();
}

export async function deleteProductMapping(token: string, mappingId: string): Promise<void> {
  const res = await fetchClient(`${API_URL}/api/v1/offer/product-mappings/${mappingId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Failed to delete mapping');
}
