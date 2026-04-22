import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import { mapSlashCommand } from "../types/conversations";

import type { SlashCommand } from "../types/conversations";

const BASE = `${config.api.baseUrl}/api/v1/copilot`;

/**
 * Fetch available slash commands.
 * Falls back to empty array if backend endpoint returns 404
 * (stub phase — not yet implemented).
 */
export async function listSlashCommands(token: string): Promise<SlashCommand[]> {
  try {
    const response = await fetchClient(`${BASE}/commands`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (response.status === 404) {
      // Endpoint not yet available — return stub list
      return getStubSlashCommands();
    }

    if (!response.ok) {
      throw new Error(`listSlashCommands failed: ${response.status}`);
    }

    const data = (await response.json()) as Record<string, unknown>[];
    return data.map(mapSlashCommand);
  } catch {
    // Non-blocking fallback — slash commands are a UX enhancement
    return getStubSlashCommands();
  }
}

/** Stub slash commands for development / before backend endpoint is ready. */
function getStubSlashCommands(): SlashCommand[] {
  return [
    {
      name: "llena-identidad",
      description: "Completa la identidad de tu marca",
      skillId: "brand.identity.fill",
    },
    {
      name: "llena-oferta",
      description: "Completa la sección de tu oferta",
      skillId: "offer.fill",
    },
    {
      name: "llena-buyer-persona",
      description: "Completa el perfil de tu cliente ideal",
      skillId: "buyer_persona.fill",
    },
    {
      name: "audita-marca",
      description: "Analiza y audita tu identidad de marca",
      skillId: "brand.audit",
    },
    {
      name: "mejora-copy",
      description: "Mejora el copy de tus textos de ventas",
      skillId: "copy.improve",
    },
  ];
}
