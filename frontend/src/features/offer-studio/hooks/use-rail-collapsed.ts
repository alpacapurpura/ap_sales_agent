import { useCallback, useEffect, useState } from "react";

const VARIANTS_RAIL_KEY = "nicolify.offer-studio.rail-collapsed";
const SECTIONS_RAIL_KEY = "nicolify.offer-studio.sections-rail-collapsed";

/**
 * Persisted collapsed state for any offer-studio rail.
 *
 * Uses `localStorage` so the preference follows the user across browser
 * sessions. Defaults to expanded. Handles SSR — during hydration the
 * default is returned so server and client markup match, then the stored
 * value rehydrates after mount.
 */
function makePersistedCollapsed(storageKey: string): () => readonly [boolean, () => void] {
  function readPersistedValue(): boolean {
    if (typeof window === "undefined") return false;
    try {
      return window.localStorage.getItem(storageKey) === "true";
    } catch {
      return false;
    }
  }

  return function usePersistedCollapsed() {
    const [collapsed, setCollapsed] = useState<boolean>(readPersistedValue);

    // Track changes in other tabs / windows.
    useEffect(() => {
      const onStorage = (event: StorageEvent) => {
        if (event.key === storageKey) setCollapsed(event.newValue === "true");
      };
      window.addEventListener("storage", onStorage);
      return () => window.removeEventListener("storage", onStorage);
    }, []);

    const toggle = useCallback(() => {
      setCollapsed((current) => {
        const next = !current;
        try {
          window.localStorage.setItem(storageKey, String(next));
        } catch {
          // ignore write errors — state still updates in memory
        }
        return next;
      });
    }, []);

    return [collapsed, toggle] as const;
  };
}

/** Persisted collapsed state for the Variants Rail. */
export const useRailCollapsed = makePersistedCollapsed(VARIANTS_RAIL_KEY);

/** Persisted collapsed state for the Sections Rail (Finder column 1). */
export const useSectionsRailCollapsed = makePersistedCollapsed(SECTIONS_RAIL_KEY);
