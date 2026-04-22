import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

// ── Types ────────────────────────────────────────────────────────────
export interface MutationJournalEntry {
  id: string;
  domain: string;
  fieldPath: string;
  appliedAt: string;
  revertedAt: string | null;
}

export interface MutationJournalResponse {
  entries: MutationJournalEntry[];
  activeCount: number;
}

// ── API ──────────────────────────────────────────────────────────────

/**
 * Fetch the mutation journal for a conversation.
 *
 * Endpoint path is TBD per UI-SPEC §15 (back-end wiring lands in a follow-up
 * sprint). Until then, the server returns 404 and this function maps it to an
 * empty journal so the UI can treat it as "nothing to undo yet".
 */
export async function fetchMutationJournal(
  token: string,
  conversationId: string,
): Promise<MutationJournalResponse> {
  const response = await fetchClient(
    `${config.api.baseUrl}/api/v1/copilot/conversations/${conversationId}/mutations`,
    { headers: { Authorization: `Bearer ${token}` } },
  );

  if (response.status === 404) {
    return { entries: [], activeCount: 0 };
  }

  if (!response.ok) {
    throw new Error(`fetchMutationJournal failed: ${response.status}`);
  }

  const data = (await response.json()) as Record<string, unknown>;
  const entries = (data.entries as MutationJournalEntry[]) ?? [];
  return {
    entries,
    activeCount: entries.filter((e) => e.revertedAt === null).length,
  };
}
