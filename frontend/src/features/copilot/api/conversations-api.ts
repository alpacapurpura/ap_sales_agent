import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import {
  mapConversationDetail,
  mapConversationListResponse,
  mapConversationSummary,
  mapRevertResponse,
} from "../types/conversations";

import type {
  ConversationDetail,
  ConversationListResponse,
  ConversationSummary,
  PatchConversationRequest,
  RevertRequest,
  RevertResponse,
} from "../types/conversations";

const BASE = `${config.api.baseUrl}/api/v1/copilot`;

interface ListConversationsParams {
  limit?: number;
  cursor?: string;
  includeArchived?: boolean;
}

/**
 * List conversations for the current user (paginated).
 * fetchClient auto-injects X-Tenant-ID.
 */
export async function listConversations(
  token: string,
  params: ListConversationsParams = {},
): Promise<ConversationListResponse> {
  const { limit = 6, cursor, includeArchived = false } = params;

  const qs = new URLSearchParams();
  qs.set("limit", String(limit));
  if (cursor) qs.set("cursor", cursor);
  if (includeArchived) qs.set("include_archived", "true");

  const response = await fetchClient(`${BASE}/conversations?${qs.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) {
    throw new Error(`listConversations failed: ${response.status}`);
  }

  const data = (await response.json()) as Record<string, unknown>;
  return mapConversationListResponse(data);
}

/**
 * Fetch a single conversation with its decoded message history.
 * Used to hydrate the chat panel when the user selects a historical
 * conversation from the sidebar.
 */
export async function getConversation(token: string, id: string): Promise<ConversationDetail> {
  const response = await fetchClient(`${BASE}/conversations/${id}`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) {
    throw new Error(`getConversation failed: ${response.status}`);
  }

  const data = (await response.json()) as Record<string, unknown>;
  return mapConversationDetail(data);
}

/**
 * Create a new conversation for the current user.
 */
export async function createConversation(token: string): Promise<ConversationSummary> {
  const response = await fetchClient(`${BASE}/conversations`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`createConversation failed: ${response.status}`);
  }

  const data = (await response.json()) as Record<string, unknown>;
  return mapConversationSummary(data);
}

/**
 * Patch a conversation (rename or archive/unarchive).
 */
export async function patchConversation(
  token: string,
  id: string,
  body: PatchConversationRequest,
): Promise<ConversationSummary> {
  const response = await fetchClient(`${BASE}/conversations/${id}`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`patchConversation failed: ${response.status}`);
  }

  const data = (await response.json()) as Record<string, unknown>;
  return mapConversationSummary(data);
}

/**
 * Delete (soft-archive) a conversation.
 */
export async function deleteConversation(token: string, id: string): Promise<void> {
  const response = await fetchClient(`${BASE}/conversations/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok && response.status !== 204) {
    throw new Error(`deleteConversation failed: ${response.status}`);
  }
}

/**
 * Revert mutations applied in a conversation.
 * Omit mutation_ids to revert all active mutations.
 */
export async function revertMutations(
  token: string,
  id: string,
  body: RevertRequest = {},
): Promise<RevertResponse> {
  const response = await fetchClient(`${BASE}/conversations/${id}/revert`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body.mutationIds !== undefined ? { mutation_ids: body.mutationIds } : {}),
  });

  if (!response.ok) {
    throw new Error(`revertMutations failed: ${response.status}`);
  }

  const data = (await response.json()) as Record<string, unknown>;
  return mapRevertResponse(data);
}
