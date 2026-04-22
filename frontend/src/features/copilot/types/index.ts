/**
 * Copilot types — unified exports from store and domain.
 *
 * Domain types are sourced from the store, which is the canonical location
 * for Zustand state interface definitions.
 */

export type {
  ActiveProcedure,
  CopilotMessage,
  CopilotSession,
  CopilotStatus,
  FocusedField,
  MessageRole,
  ProcedureStepStatus,
  ProposalUpdate,
  SelectedField,
  SidebarState,
  UIAction,
} from "../store/copilot-store";

export type {
  ConversationListResponse,
  ConversationSummary,
  MutationAppliedEvent,
  ModelTier,
  PatchConversationRequest,
  PlanApproveResponse,
  PlanRejectResponse,
  PlanState,
  PlanStep,
  RevertFailure,
  RevertRequest,
  RevertResponse,
  SlashCommand,
  TierDecisionEvent,
} from "./conversations";

export {
  mapConversationListResponse,
  mapConversationSummary,
  mapRevertResponse,
  mapSlashCommand,
} from "./conversations";
