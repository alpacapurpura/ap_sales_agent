import { create } from "zustand";

import type { ModelTier } from "../types/conversations";
import type { FormRuntimeBridge } from "@/lib/form-runtime/copilot";

// ── Types ───────────────────────────────────────────────────────────

export type MessageRole = "user" | "assistant";

export interface ProposalUpdate {
  field_id: string;
  new_value: string;
  reason?: string;
}

export interface ProcedureStepStatus {
  id: string;
  label: string;
  status: "completed" | "current" | "pending";
  routeHint?: string;
}

export interface ActiveProcedure {
  id: string;
  name: string;
  steps: ProcedureStepStatus[];
  currentStepIndex: number;
}

export interface UIAction {
  type:
    | "navigate"
    | "scroll_to_field"
    | "open_form"
    | "proposal"
    | "procedure_progress"
    | "metric_summary"
    | "comparison"
    | "checklist"
    | "multi_option"
    | "alternatives_card"
    | "clarify_card"
    | "checkpoint_card"
    | "interview_complete"
    | "preview_update";
  route?: string;
  page_label?: string;
  section_id?: string;
  field_id?: string;
  form_id?: string;
  prefill_data?: Record<string, unknown>;
  updates?: ProposalUpdate[];
  // Procedure progress fields
  procedure_id?: string;
  procedure_name?: string;
  steps?: ProcedureStepStatus[];
  current_step_index?: number;
  // Generative UI fields (Phase 3)
  metrics?: { label: string; value: string; trend?: "up" | "down" | "flat"; delta?: string }[];
  columns?: string[];
  rows?: Record<string, string>[];
  recommended?: string;
  items?: { label: string; done: boolean; route?: string }[];
  options?: { id: string; title: string; content: string }[];
  // Interview card fields
  field_path?: string;
  question?: string;
  alternatives?: {
    id: string;
    title: string;
    description: string;
    recommended?: boolean;
    recommendation_reason?: string;
  }[];
  allow_custom?: boolean;
  clarify_items?: { field_path: string; issue: string; options: string[] }[];
  block_id?: string;
  block_label?: string;
  summary?: Record<string, string>;
  health_score?: number;
  blocks_progress?: { completed: number; total: number };
  card_status?: "pending" | "resolved" | "confirmed" | "revising";
  redirect?: string;
  delta?: Record<string, unknown>;
}

export interface SelectedField {
  fieldId: string;
  fieldLabel: string;
  fieldValue: string;
}

export interface CopilotMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: number;
  /** Tool call metadata (for displaying tool execution feedback) */
  toolCalls?: {
    tool: string;
    args?: Record<string, unknown>;
    result?: string;
  }[];
  /** UI actions attached to this message (e.g. navigation cards) */
  uiActions?: UIAction[];
}

export type CopilotStatus = "idle" | "thinking" | "streaming" | "done";

/**
 * Sidebar has three visible states:
 * - ``collapsed``: only the 60px rail is visible
 * - ``rail``: chat panel (380px) + rail (60px)
 * - ``full``: history panel (280px) + chat panel (400px) + rail (60px)
 *
 * Persisted to localStorage as ``copilot.sidebarState``.
 */
export type SidebarState = "collapsed" | "rail" | "full";

/**
 * Active editing run. ``free`` = ambient copilot; ``interview`` = guided Q&A.
 */
export interface CopilotSession {
  /** Form-runtime section key, e.g. ``"brand.identity"`` or ``"offer.pricing"``. */
  sectionKey: string;
  /** Human label shown in the header (e.g. the brand or offer name). */
  label: string;
  /** Entity being edited (brand/offer/persona). Null = implicit tenant-level. */
  entityId: string | null;
  procedure: "free" | "interview";
  /** Backend conversation id for interview procedures; null for ``free``. */
  sessionId: string | null;
  progress?: {
    totalBlocks: number;
    blocksCompleted: string[];
    currentBlock?: string;
  };
  startedAt: Date;
  /** Field snapshot at session start — used for session-level undo. */
  snapshot: Record<string, unknown>;
}

export interface FocusedField {
  id: string;
  label: string;
  /** Dot-path into the section's value object (e.g. ``"identity.tagline"``). */
  path: string;
}

interface CopilotState {
  // Panel — sidebarState is the source of truth (3 states)
  sidebarState: SidebarState;
  setSidebarState: (state: SidebarState) => void;
  /** Cycles through: collapsed → rail → full → collapsed */
  cycleSidebarState: () => void;

  // Backward-compat: isOpen derived from sidebarState (true when not collapsed)
  isOpen: boolean;
  togglePanel: () => void;
  openPanel: () => void;
  closePanel: () => void;

  // Slash command overlay
  slashCommandOpen: boolean;
  setSlashCommandOpen: (open: boolean) => void;

  // Context-rot dismissed banners (per-conversation, in-memory only)
  dismissedRotBanners: Set<string>;
  dismissRotBanner: (convId: string) => void;

  // Last tier per message (updated by SSE tier_decision events)
  lastMessageTiers: Record<string, ModelTier>;
  setLastMessageTier: (msgId: string, tier: ModelTier) => void;

  // Conversation
  conversationId: string | null;
  messages: CopilotMessage[];
  status: CopilotStatus;

  // Actions
  setConversationId: (id: string) => void;
  addMessage: (msg: CopilotMessage) => void;
  appendToLastAssistant: (chunk: string) => void;
  addUIActionToLastAssistant: (action: UIAction) => void;
  updateUIActionStatus: (
    messageId: string,
    actionIndex: number,
    status: NonNullable<UIAction["card_status"]>,
  ) => void;
  setStatus: (status: CopilotStatus) => void;
  clearMessages: () => void;

  // Route awareness
  currentRoute: string | null;
  setCurrentRoute: (route: string) => void;

  // Pending UI actions queue (processed by navigator hook)
  pendingUIActions: UIAction[];
  enqueuUIAction: (action: UIAction) => void;
  dequeuUIAction: () => UIAction | undefined;

  // Active procedure (set by procedure_progress UIAction)
  activeProcedure: ActiveProcedure | null;
  setActiveProcedure: (proc: ActiveProcedure) => void;
  clearActiveProcedure: () => void;

  // Selected fields context (chat "add to context" affordance)
  selectedFields: SelectedField[];
  addSelectedField: (field: SelectedField) => void;
  removeSelectedField: (fieldId: string) => void;
  updateFieldValue: (fieldId: string, value: string) => void;
  clearSelectedFields: () => void;

  // Unified active session (free edit or guided interview)
  session: CopilotSession | null;
  setSession: (session: CopilotSession) => void;
  updateSession: (patch: Partial<CopilotSession>) => void;
  clearSession: () => void;

  // Currently focused field inside the active section
  focusedField: FocusedField | null;
  setFocusedField: (field: FocusedField) => void;
  clearFocusedField: () => void;

  // Bridge to the mounted form-runtime section
  activeBridge: FormRuntimeBridge | null;
  connectBridge: (bridge: FormRuntimeBridge) => void;
  disconnectBridge: (bridge: FormRuntimeBridge) => void;
}

// ── Constants ────────────────────────────────────────────────────────

/** Maximum number of messages kept in memory. Oldest are trimmed when exceeded. */
export const MAX_MESSAGES = 100;

/** localStorage key for persisting sidebar state */
const SIDEBAR_STATE_KEY = "copilot.sidebarState";

// ── Helpers ──────────────────────────────────────────────────────────

/** Compute isOpen from sidebarState */
function deriveIsOpen(sidebarState: SidebarState): boolean {
  return sidebarState !== "collapsed";
}

/** Cycle order: collapsed → rail → full → collapsed */
function cycleState(current: SidebarState): SidebarState {
  if (current === "collapsed") return "rail";
  if (current === "rail") return "full";
  return "collapsed";
}

/** Persist sidebar state to localStorage (client-side only) */
function persistSidebarState(state: SidebarState): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(SIDEBAR_STATE_KEY, state);
  }
}

/** Load persisted sidebar state from localStorage */
function loadPersistedSidebarState(): SidebarState {
  if (typeof window === "undefined") return "rail";
  const saved = localStorage.getItem(SIDEBAR_STATE_KEY);
  if (saved === "rail" || saved === "full") return saved;
  return "rail";
}

/**
 * Append a message to the list and enforce the MAX_MESSAGES limit.
 * Returns a new array with at most MAX_MESSAGES entries (oldest trimmed).
 */
function appendWithLimit(messages: CopilotMessage[], msg: CopilotMessage): CopilotMessage[] {
  const next = [...messages, msg];
  return next.length > MAX_MESSAGES ? next.slice(next.length - MAX_MESSAGES) : next;
}

// ── Store ───────────────────────────────────────────────────────────

export const useCopilotStore = create<CopilotState>((set, get) => ({
  // Panel — sidebarState as source of truth; isOpen kept in sync
  // Default to "rail" on client (will be overwritten from localStorage in CopilotSidebar mount)
  sidebarState: "collapsed",
  isOpen: false,

  setSidebarState: (state) => {
    persistSidebarState(state);
    set({ sidebarState: state, isOpen: deriveIsOpen(state) });
  },

  cycleSidebarState: () =>
    set((s) => {
      const next = cycleState(s.sidebarState);
      persistSidebarState(next);
      return { sidebarState: next, isOpen: deriveIsOpen(next) };
    }),

  togglePanel: () =>
    set((s) => {
      // Backward-compat: toggle between collapsed and rail
      const next: SidebarState = s.sidebarState === "collapsed" ? "rail" : "collapsed";
      persistSidebarState(next);
      return { sidebarState: next, isOpen: deriveIsOpen(next) };
    }),
  openPanel: () => {
    persistSidebarState("rail");
    set({ sidebarState: "rail", isOpen: true });
  },
  closePanel: () => {
    persistSidebarState("collapsed");
    set({ sidebarState: "collapsed", isOpen: false });
  },

  // Slash command overlay
  slashCommandOpen: false,
  setSlashCommandOpen: (open) => set({ slashCommandOpen: open }),

  // Context-rot dismissed banners
  dismissedRotBanners: new Set<string>(),
  dismissRotBanner: (convId) =>
    set((s) => {
      const next = new Set(s.dismissedRotBanners);
      next.add(convId);
      return { dismissedRotBanners: next };
    }),

  // Last tier per message
  lastMessageTiers: {},
  setLastMessageTier: (msgId, tier) =>
    set((s) => ({
      lastMessageTiers: { ...s.lastMessageTiers, [msgId]: tier },
    })),

  // Conversation
  conversationId: null,
  messages: [],
  status: "idle",

  setConversationId: (id) => set({ conversationId: id }),

  addMessage: (msg) => set((s) => ({ messages: appendWithLimit(s.messages, msg) })),

  appendToLastAssistant: (chunk) =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last?.role === "assistant") {
        msgs[msgs.length - 1] = { ...last, content: last.content + chunk };
      }
      return { messages: msgs };
    }),

  addUIActionToLastAssistant: (action) =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last?.role === "assistant") {
        const existing = last.uiActions ?? [];
        msgs[msgs.length - 1] = { ...last, uiActions: [...existing, action] };
      }
      return { messages: msgs };
    }),

  updateUIActionStatus: (messageId, actionIndex, status) =>
    set((s) => {
      const msgs = [...s.messages];
      const msgIdx = msgs.findIndex((m) => m.id === messageId);
      if (msgIdx === -1) return s;
      const msg = msgs[msgIdx];
      if (!msg.uiActions?.[actionIndex]) return s;
      const actions = [...msg.uiActions];
      actions[actionIndex] = { ...actions[actionIndex], card_status: status };
      msgs[msgIdx] = { ...msg, uiActions: actions };
      return { messages: msgs };
    }),

  setStatus: (status) => set({ status }),

  clearMessages: () => set({ messages: [], conversationId: null, status: "idle" }),

  // Route
  currentRoute: null,
  setCurrentRoute: (route) => set({ currentRoute: route }),

  // UI action queue
  pendingUIActions: [],
  enqueuUIAction: (action) => set((s) => ({ pendingUIActions: [...s.pendingUIActions, action] })),
  dequeuUIAction: () => {
    const actions = get().pendingUIActions;
    if (actions.length === 0) return undefined;
    const [first, ...rest] = actions;
    set({ pendingUIActions: rest });
    return first;
  },

  // Active procedure
  activeProcedure: null,
  setActiveProcedure: (proc) => set({ activeProcedure: proc }),
  clearActiveProcedure: () => set({ activeProcedure: null }),

  // Selected fields context
  selectedFields: [],
  addSelectedField: (field) =>
    set((s) => {
      if (s.selectedFields.some((f) => f.fieldId === field.fieldId)) {
        return s;
      }
      return { selectedFields: [...s.selectedFields, field] };
    }),
  removeSelectedField: (fieldId) =>
    set((s) => ({
      selectedFields: s.selectedFields.filter((f) => f.fieldId !== fieldId),
    })),
  updateFieldValue: (fieldId, value) =>
    set((s) => ({
      selectedFields: s.selectedFields.map((f) =>
        f.fieldId === fieldId ? { ...f, fieldValue: value } : f,
      ),
    })),
  clearSelectedFields: () => set({ selectedFields: [] }),

  // Active session
  session: null,
  setSession: (session) => set({ session }),
  updateSession: (patch) => set((s) => (s.session ? { session: { ...s.session, ...patch } } : s)),
  clearSession: () => set({ session: null, focusedField: null }),

  // Focused field
  focusedField: null,
  setFocusedField: (field) => set({ focusedField: field }),
  clearFocusedField: () => set({ focusedField: null }),

  // Active bridge
  activeBridge: null,
  connectBridge: (bridge) => set({ activeBridge: bridge }),
  disconnectBridge: (bridge) =>
    set((s) => (s.activeBridge === bridge ? { activeBridge: null } : s)),
}));

// Export helper for mounting to restore persisted state
export { loadPersistedSidebarState };
