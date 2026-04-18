/**
 * Offer-studio action registry bootstrap.
 *
 * Imported by ``schemas/index.ts`` (side-effect) so every page that reads
 * a schema also gets the registry populated before the form-runtime
 * attempts to render ``custom`` fields.
 *
 * Each Phase E section port replaces the placeholder for its action key
 * with the real implementation and removes the entry from
 * ``PLACEHOLDER_ACTIONS`` — the arch test
 * ``test-no-unregistered-placeholder-actions`` will surface any action
 * key referenced by a schema but no longer registered.
 */

import { registerAction } from "@/lib/form-runtime/actions/registry";

import { createPlaceholderAction, PLACEHOLDER_ACTIONS } from "./placeholders";

for (const { key, label } of PLACEHOLDER_ACTIONS) {
  registerAction(key, createPlaceholderAction(key, label));
}
