/**
 * Legacy team editor — dialog-embedded, non-form-runtime. Used only by
 * offer-studio ``InstructorsSelector`` until Sprint 6 completes the
 * offer-studio editor migration to route-per-field form-runtime.
 *
 * Do not build new consumers on top of this. For team editing, prefer the
 * canonical route: ``/{tenantId}/brand-studio/team``.
 */
export { TeamManager } from "./TeamManager";
