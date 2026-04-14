"use client";

import { useCallback, useState } from "react";

/**
 * Storage + TTL for the 24h-ignore feature. Exported under `__` prefix so
 * tests can reference them without leaking them into the public API.
 */
export const __IGNORE_STORAGE_KEY = "meta-ads-ignored-notices-v1";
export const __IGNORE_TTL_MS = 24 * 60 * 60 * 1000;

type StoredEntry = [string, number];

function readEntries(): StoredEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(__IGNORE_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (entry): entry is StoredEntry =>
        Array.isArray(entry) &&
        entry.length === 2 &&
        typeof entry[0] === "string" &&
        typeof entry[1] === "number",
    );
  } catch {
    return [];
  }
}

function writeEntries(entries: StoredEntry[]): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(__IGNORE_STORAGE_KEY, JSON.stringify(entries));
  } catch {
    /* quota exceeded or other — silently ignore */
  }
}

function loadFreshIds(): Set<string> {
  const entries = readEntries();
  const now = Date.now();
  const fresh = entries.filter(([, ts]) => now - ts < __IGNORE_TTL_MS);
  // Rewrite storage if we purged anything so stale entries don't accumulate.
  if (fresh.length !== entries.length) {
    writeEntries(fresh);
  }
  return new Set(fresh.map(([id]) => id));
}

/**
 * React hook: track locally-ignored notice ids with a 24h TTL.
 *
 * Storage lives in `localStorage` under a versioned key; there is no backend.
 * A notice re-appears automatically after 24h or if its id changes (e.g. the
 * affected campaign is different).
 */
export function useIgnoredNotices() {
  const [ignored, setIgnored] = useState<Set<string>>(() => loadFreshIds());

  const ignore = useCallback((id: string) => {
    setIgnored((prev) => {
      if (prev.has(id)) return prev;
      const next = new Set(prev);
      next.add(id);

      // Persist: merge with whatever is currently in storage + new entry.
      const existing = readEntries().filter(([existingId]) => existingId !== id);
      existing.push([id, Date.now()]);
      writeEntries(existing);

      return next;
    });
  }, []);

  const isIgnored = useCallback((id: string) => ignored.has(id), [ignored]);

  return { ignored, ignore, isIgnored };
}
