/**
 * Compatibility re-export. The canonical hook now lives at
 * `@/lib/form-runtime/hooks/use-auto-save` so form-runtime consumers can
 * share the same autosave state machine. Offer-studio keeps this shim so
 * existing imports do not break during the brand-studio migration.
 *
 * Sprint 5 deletes this shim once offer-studio imports are rewired.
 */
export {
  useAutoSave,
  type AutoSaveState,
  type UseAutoSaveOptions,
  type UseAutoSaveResult,
} from "@/lib/form-runtime/hooks/use-auto-save";
