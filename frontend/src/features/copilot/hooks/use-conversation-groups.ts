"use client";

import type { ConversationSummary } from "../types/conversations";

export interface ConversationGroup {
  label: string;
  items: ConversationSummary[];
}

/** Computes date-group boundaries relative to now */
function getGroupBoundaries() {
  const now = new Date();

  const todayStart = new Date(now);
  todayStart.setHours(0, 0, 0, 0);

  const yesterdayStart = new Date(todayStart);
  yesterdayStart.setDate(yesterdayStart.getDate() - 1);

  const sevenDaysStart = new Date(todayStart);
  sevenDaysStart.setDate(sevenDaysStart.getDate() - 7);

  return { todayStart, yesterdayStart, sevenDaysStart };
}

/**
 * Groups conversations by date relative to now.
 * Returns only non-empty groups in display order.
 */
export function useConversationGroups(items: ConversationSummary[]): ConversationGroup[] {
  const { todayStart, yesterdayStart, sevenDaysStart } = getGroupBoundaries();

  const groups: ConversationGroup[] = [
    { label: "Hoy", items: [] },
    { label: "Ayer", items: [] },
    { label: "Últimos 7 días", items: [] },
    { label: "Anterior", items: [] },
  ];

  for (const item of items) {
    const updatedAt = new Date(item.updatedAt);

    if (updatedAt >= todayStart) {
      groups[0].items.push(item);
    } else if (updatedAt >= yesterdayStart) {
      groups[1].items.push(item);
    } else if (updatedAt >= sevenDaysStart) {
      groups[2].items.push(item);
    } else {
      groups[3].items.push(item);
    }
  }

  // Return only groups with items
  return groups.filter((g) => g.items.length > 0);
}
