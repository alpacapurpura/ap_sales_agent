import { fetchClient } from "@/lib/http-client";

export async function fetchOfferMetadata(token: string): Promise<Record<string, unknown>> {
  const res = await fetchClient("/products/metadata/hints", {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch metadata");
  return res.json();
}
