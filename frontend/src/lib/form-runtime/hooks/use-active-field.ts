"use client";

import { usePathname, useSearchParams } from "next/navigation";
import { useCallback, useSyncExternalStore } from "react";

/**
 * Active-field URL state.
 *
 * Owns the single source of truth for "which field is selected right now"
 * across form-runtime surfaces (FieldList, FieldDetail, EditableField,
 * copilot bridge). The active field lives in the ``?field=`` query
 * parameter so focus changes do not trigger a full server-side route
 * transition — path navigation is reserved for section changes.
 *
 * **Write discipline (enforced by callers, not the hook):**
 *
 *   ``setActiveField`` must only be invoked in response to an explicit
 *   user selection gesture — a click on a field row, a focus on the
 *   input itself, a keyboard shortcut that resolves to "select field X".
 *   Blur events, ``useEffect`` fallbacks, and "normalise to first field"
 *   shims must never call it. The URL is a pull target; rendering
 *   defaults (e.g. "no query → highlight first") live purely in the
 *   consumer's render path. Violating this invariant causes stray
 *   clicks to silently wipe the user's selection (see
 *   ``EditableField``'s doc comment for the historical regression).
 *
 * Why query-param over path segment:
 *
 *  - Changing a query param via ``history.replaceState`` is a pure
 *    client-side update. No RSC payload fetch, no component remount.
 *  - Deep-linking still works: ``/editor/identity?field=frase-titular``
 *    is a valid bookmark-able URL.
 *  - Cross-page deep-links from copilot (``navigate_to_page`` with a
 *    field id) fall out naturally.
 *
 * The shallow-update pattern (history.replaceState + CustomEvent) is
 * required because ``router.replace()`` in App Router still triggers an
 * RSC roundtrip on some Next.js versions. ``useSyncExternalStore``
 * subscribes to both the custom event (our own mutator) and the native
 * ``popstate`` event (browser back/forward) so the active field stays
 * correct through every URL transition.
 */
const FIELD_QUERY_KEY = "field";
const FIELD_CHANGE_EVENT = "form-runtime:active-field-change";

export interface UseActiveFieldResult {
  activeFieldId: string | null;
  setActiveField: (fieldId: string | null) => void;
  /** Build the href for a given field id. ``null`` ⇒ section-level URL. */
  getFieldHref: (fieldId: string | null) => string;
}

function subscribe(onStoreChange: () => void): () => void {
  window.addEventListener(FIELD_CHANGE_EVENT, onStoreChange);
  window.addEventListener("popstate", onStoreChange);
  return () => {
    window.removeEventListener(FIELD_CHANGE_EVENT, onStoreChange);
    window.removeEventListener("popstate", onStoreChange);
  };
}

function getClientSnapshot(): string | null {
  return new URLSearchParams(window.location.search).get(FIELD_QUERY_KEY);
}

/**
 * Read + update the ``?field=`` query parameter without re-rendering the
 * server component tree. Consumers (FieldList, EditableField) call
 * ``setActiveField`` to switch the active field; subscribers
 * (FieldDetail, FieldContextPanel, bridge effect) re-read ``activeFieldId``
 * on every change via ``useSyncExternalStore``.
 */
export function useActiveField(): UseActiveFieldResult {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const serverSnapshot = searchParams.get(FIELD_QUERY_KEY);

  const activeFieldId = useSyncExternalStore(subscribe, getClientSnapshot, () => serverSnapshot);

  const buildHref = useCallback(
    (fieldId: string | null) => {
      const params = new URLSearchParams(searchParams);
      if (fieldId) {
        params.set(FIELD_QUERY_KEY, fieldId);
      } else {
        params.delete(FIELD_QUERY_KEY);
      }
      const qs = params.toString();
      return qs ? `${pathname}?${qs}` : pathname;
    },
    [pathname, searchParams],
  );

  const setActiveField = useCallback(
    (fieldId: string | null) => {
      const href = buildHref(fieldId);
      // Shallow URL update — no RSC fetch, no scroll reset.
      window.history.replaceState(null, "", href);
      window.dispatchEvent(new CustomEvent<string | null>(FIELD_CHANGE_EVENT, { detail: fieldId }));
    },
    [buildHref],
  );

  return { activeFieldId, setActiveField, getFieldHref: buildHref };
}
