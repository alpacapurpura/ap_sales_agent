/**
 * Copilot types — unified exports from store and domain
 *
 * This module re-exports copilot types following FSD convention.
 * Domain types (FocusEntity, InterviewProgress) are sourced from the store,
 * which is the canonical location for Zustand state interface definitions.
 */

// ── Store domain types ──
export type {
  CopilotMessage,
  CopilotStatus,
  FocusEntity,
  InterviewProgress,
  MessageRole,
  ProcedureStepStatus,
  ActiveProcedure,
  ProposalUpdate,
  SelectedField,
  SidebarState,
  UIAction,
} from "../store/copilot-store";
