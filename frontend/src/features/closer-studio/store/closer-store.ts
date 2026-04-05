"use client";

import { create } from "zustand";
import type { ConversationFilters, HandlerMode, InputMode } from "../types";

interface CloserStudioState {
  // Selection
  selectedLeadId: string | null;
  setSelectedLeadId: (id: string | null) => void;

  // Filters
  filters: ConversationFilters;
  setFilter: <K extends keyof ConversationFilters>(key: K, value: ConversationFilters[K]) => void;
  resetFilters: () => void;

  // Input mode
  inputMode: InputMode;
  setInputMode: (mode: InputMode) => void;

  // Unread tracking (by lead)
  unreadByLead: Record<string, number>;
  incrementUnread: (leadId: string) => void;
  clearUnread: (leadId: string) => void;

  // WebSocket state
  wsConnected: boolean;
  setWsConnected: (connected: boolean) => void;

  // Sidebar
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

const DEFAULT_FILTERS: ConversationFilters = {
  temperature: null,
  handler_mode: null,
  channel: null,
  search: "",
};

export const useCloserStore = create<CloserStudioState>((set) => ({
  selectedLeadId: null,
  setSelectedLeadId: (id) => set({ selectedLeadId: id }),

  filters: { ...DEFAULT_FILTERS },
  setFilter: (key, value) =>
    set((state) => ({
      filters: { ...state.filters, [key]: value },
    })),
  resetFilters: () => set({ filters: { ...DEFAULT_FILTERS } }),

  inputMode: "direct",
  setInputMode: (mode) => set({ inputMode: mode }),

  unreadByLead: {},
  incrementUnread: (leadId) =>
    set((state) => ({
      unreadByLead: {
        ...state.unreadByLead,
        [leadId]: (state.unreadByLead[leadId] || 0) + 1,
      },
    })),
  clearUnread: (leadId) =>
    set((state) => {
      const next = { ...state.unreadByLead };
      delete next[leadId];
      return { unreadByLead: next };
    }),

  wsConnected: false,
  setWsConnected: (connected) => set({ wsConnected: connected }),

  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
}));
