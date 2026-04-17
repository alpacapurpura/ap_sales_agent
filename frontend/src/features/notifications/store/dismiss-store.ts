import { create } from "zustand";
import { persist } from "zustand/middleware";

interface DismissState {
  dismissedIds: Record<string, number>;
  dismiss: (id: string) => void;
  isDismissed: (id: string) => boolean;
  clearExpired: (ttlMs: number) => void;
}

export const useDismissStore = create<DismissState>()(
  persist(
    (set, get) => ({
      dismissedIds: {},
      dismiss: (id) => set((s) => ({ dismissedIds: { ...s.dismissedIds, [id]: Date.now() } })),
      isDismissed: (id) => Boolean(get().dismissedIds[id]),
      clearExpired: (ttlMs) => {
        const now = Date.now();
        const next: Record<string, number> = {};
        for (const [id, ts] of Object.entries(get().dismissedIds)) {
          if (now - ts < ttlMs) next[id] = ts;
        }
        set({ dismissedIds: next });
      },
    }),
    { name: "notifications-dismiss" },
  ),
);
