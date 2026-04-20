import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import type { TenantDomain, DomainInstructions } from "../types";

const BASE = `${config.api.baseUrl}/api/v1/domains`;

/**
 *
 */
export async function listDomains(token: string): Promise<TenantDomain[]> {
  const res = await fetchClient(BASE, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Error obteniendo dominios");
  return res.json() as Promise<TenantDomain[]>;
}

/**
 *
 */
export async function createDomain(
  token: string,
  hostname: string,
  domainType: "platform" | "custom",
): Promise<TenantDomain> {
  const res = await fetchClient(BASE, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ hostname, domain_type: domainType }),
  });
  if (!res.ok) {
    const err: unknown = await res.json();
    throw err;
  }
  return res.json() as Promise<TenantDomain>;
}

/**
 *
 */
export async function deleteDomain(token: string, id: string): Promise<void> {
  const res = await fetchClient(`${BASE}/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Error eliminando dominio");
}

/**
 *
 */
export async function setPrimary(token: string, id: string): Promise<TenantDomain> {
  const res = await fetchClient(`${BASE}/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ is_primary: true }),
  });
  if (!res.ok) throw new Error("Error estableciendo dominio principal");
  return res.json() as Promise<TenantDomain>;
}

/**
 *
 */
export async function verifyDomain(token: string, id: string): Promise<TenantDomain> {
  const res = await fetchClient(`${BASE}/${id}/verify`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Error al verificar dominio");
  return res.json() as Promise<TenantDomain>;
}

/**
 *
 */
export async function getDomainInstructions(
  token: string,
  id: string,
): Promise<DomainInstructions> {
  const res = await fetchClient(`${BASE}/${id}/instructions`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Error obteniendo instrucciones del dominio");
  return res.json() as Promise<DomainInstructions>;
}
