/**
 * Shell mutex store — tenant-namespaced zustand store for tracking
 * which panel (app-sidebar | copilot) is active.
 *
 * AD4: Factory pattern with tenant-namespaced localStorage key.
 * Each tenant gets an isolated store keyed `shell-mutex-${tenantId}`.
 *
 * Phase 1: Store created with actions wired. Mutex policy activation
 * happens in T-4 (useShellMutex effects activate mutex enforcement).
 */
import { createStore } from "zustand/vanilla";

export type ActivePanel = "app-sidebar" | "copilot" | null;

export interface ShellMutexState {
  /** Currently active (open) panel. null means both are in their natural state. */
  activePanel: ActivePanel;
}

export interface ShellMutexActions {
  /** Open the specified panel. Does not automatically close the other. */
  openPanel: (panel: Exclude<ActivePanel, null>) => void;
  /** Close the currently active panel. */
  closePanel: () => void;
  /**
   * Toggle the specified panel:
   * - If the panel is already active → close it (set null)
   * - Otherwise → open it
   */
  togglePanel: (panel: Exclude<ActivePanel, null>) => void;
}

export type ShellMutexStore = ShellMutexState & ShellMutexActions;

/**
 * Factory that creates a tenant-namespaced shell mutex store.
 *
 * Using vanilla zustand store (not React `create`) so the same factory can be
 * called per tenant in a React context via `useMemo` inside `useShellMutex`.
 */
export function createShellMutexStore(tenantId: string) {
  const storageKey = `shell-mutex-${tenantId}`;

  // Attempt to restore persisted state
  function loadPersistedPanel(): ActivePanel {
    if (typeof localStorage === "undefined") return null;
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw === "app-sidebar" || raw === "copilot") return raw;
      return null;
    } catch {
      return null;
    }
  }

  function persistPanel(panel: ActivePanel): void {
    if (typeof localStorage === "undefined") return;
    try {
      if (panel === null) {
        localStorage.removeItem(storageKey);
      } else {
        localStorage.setItem(storageKey, panel);
      }
    } catch {
      // localStorage unavailable (private mode, quota exceeded) — silently skip
    }
  }

  return createStore<ShellMutexStore>((set) => ({
    activePanel: loadPersistedPanel(),

    openPanel: (panel) => {
      set({ activePanel: panel });
      persistPanel(panel);
    },

    closePanel: () => {
      set({ activePanel: null });
      persistPanel(null);
    },

    togglePanel: (panel) => {
      set((prev) => {
        const next: ActivePanel = prev.activePanel === panel ? null : panel;
        persistPanel(next);
        return { activePanel: next };
      });
    },
  }));
}

export type ShellMutexStoreInstance = ReturnType<typeof createShellMutexStore>;
