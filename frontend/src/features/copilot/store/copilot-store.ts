import { create } from "zustand";

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
  type: "navigate" | "scroll_to_field" | "open_form" | "proposal" | "procedure_progress"
       | "metric_summary" | "comparison" | "checklist" | "multi_option";
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
  metrics?: Array<{ label: string; value: string; trend?: "up" | "down" | "flat"; delta?: string }>;
  columns?: string[];
  rows?: Array<Record<string, string>>;
  recommended?: string;
  items?: Array<{ label: string; done: boolean; route?: string }>;
  options?: Array<{ id: string; title: string; content: string }>;
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
  toolCalls?: Array<{
    tool: string;
    args?: Record<string, unknown>;
    result?: string;
  }>;
  /** UI actions attached to this message (e.g. navigation cards) */
  uiActions?: UIAction[];
}

export type CopilotStatus = "idle" | "thinking" | "streaming" | "done";

interface CopilotState {
  // Panel UI
  isOpen: boolean;
  togglePanel: () => void;
  openPanel: () => void;
  closePanel: () => void;

  // Conversation
  conversationId: string | null;
  messages: CopilotMessage[];
  status: CopilotStatus;

  // Actions
  setConversationId: (id: string) => void;
  addMessage: (msg: CopilotMessage) => void;
  appendToLastAssistant: (chunk: string) => void;
  addUIActionToLastAssistant: (action: UIAction) => void;
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

  // Selected fields context (for WithCopilot wrapper)
  selectedFields: SelectedField[];
  addSelectedField: (field: SelectedField) => void;
  removeSelectedField: (fieldId: string) => void;
  updateFieldValue: (fieldId: string, value: string) => void;
  clearSelectedFields: () => void;

  // Interview mode
  interviewMode: boolean;
  interviewSessionId: string | null;
  interviewPreviewData: Record<string, unknown> | null;
  setInterviewMode: (active: boolean, sessionId?: string) => void;
  updateInterviewPreview: (delta: Record<string, unknown>) => void;
  clearInterview: () => void;
}

// ── Store ───────────────────────────────────────────────────────────

export const useCopilotStore = create<CopilotState>((set, get) => ({
  // Panel
  isOpen: false,
  togglePanel: () => set((s) => ({ isOpen: !s.isOpen })),
  openPanel: () => set({ isOpen: true }),
  closePanel: () => set({ isOpen: false }),

  // Conversation
  conversationId: null,
  messages: [],
  status: "idle",

  setConversationId: (id) => set({ conversationId: id }),

  addMessage: (msg) =>
    set((s) => ({ messages: [...s.messages, msg] })),

  appendToLastAssistant: (chunk) =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === "assistant") {
        msgs[msgs.length - 1] = { ...last, content: last.content + chunk };
      }
      return { messages: msgs };
    }),

  addUIActionToLastAssistant: (action) =>
    set((s) => {
      const msgs = [...s.messages];
      const last = msgs[msgs.length - 1];
      if (last && last.role === "assistant") {
        const existing = last.uiActions ?? [];
        msgs[msgs.length - 1] = { ...last, uiActions: [...existing, action] };
      }
      return { messages: msgs };
    }),

  setStatus: (status) => set({ status }),

  clearMessages: () => set({ messages: [], conversationId: null, status: "idle" }),

  // Route
  currentRoute: null,
  setCurrentRoute: (route) => set({ currentRoute: route }),

  // UI action queue
  pendingUIActions: [],
  enqueuUIAction: (action) =>
    set((s) => ({ pendingUIActions: [...s.pendingUIActions, action] })),
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
      // Avoid duplicates
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
        f.fieldId === fieldId ? { ...f, fieldValue: value } : f
      ),
    })),
  clearSelectedFields: () => set({ selectedFields: [] }),

  // Interview mode
  interviewMode: false,
  interviewSessionId: null,
  interviewPreviewData: null,

  setInterviewMode: (active, sessionId) =>
    set({ interviewMode: active, interviewSessionId: sessionId ?? null }),

  updateInterviewPreview: (delta) =>
    set((state) => ({
      interviewPreviewData: { ...(state.interviewPreviewData ?? {}), ...delta },
    })),

  clearInterview: () =>
    set({ interviewMode: false, interviewSessionId: null, interviewPreviewData: null }),
}));
