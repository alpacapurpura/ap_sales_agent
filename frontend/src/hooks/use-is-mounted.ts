"use client";

import { useSyncExternalStore } from "react";

/**
 * Returns `true` only after the first client-side mount.
 *
 * Why this exists
 * ---------------
 * On the server (RSC pre-render of a Client Component) and on the very
 * first client paint (before React commits the first effect), browser-only
 * state is unavailable. Anything that depends on browser-only data —
 * Clerk's auth SDK loading, third-party widgets that paint extra DOM,
 * React Query's optimistic `fetchStatus='fetching'` flag — produces
 * different output on the server vs. the first client paint, and React
 * reports it as a hydration mismatch.
 *
 * Gating render branches with `useIsMounted` keeps the server output and
 * the first-paint client output identical (`false`), then commits to
 * `true` once React has finished hydrating. The follow-up render is a
 * normal client update, not a hydration step, so no mismatch is reported.
 *
 * Implementation note
 * -------------------
 * Implemented with `useSyncExternalStore` instead of
 * `useState + useEffect`: React deliberately treats this hook as
 * hydration-safe — `getServerSnapshot` is used during SSR and during the
 * first client render, then `getSnapshot` takes over after hydration.
 * The `useState + useEffect` variant trips ``react-hooks/set-state-in-effect``
 * because it calls `setState` from inside an effect.
 *
 * Usage with React Query + Clerk:
 *
 *     const isMounted = useIsMounted();
 *     const { isLoaded, isSignedIn } = useAuth();
 *     useQuery({ ..., enabled: isMounted && isLoaded && isSignedIn });
 *
 * Usage with SDK widgets that paint browser-only DOM:
 *
 *     const isMounted = useIsMounted();
 *     return <div>{isMounted ? <SignIn /> : null}</div>;
 */
// Static mount-state store: nothing ever fires `onChange`, the snapshot
// flips from `false` (server / first hydration) to `true` (client) once
// React commits, courtesy of `useSyncExternalStore`'s built-in hydration
// handling.
const noop = () => undefined;
const subscribe = (): (() => void) => noop;
const getSnapshot = (): boolean => true;
const getServerSnapshot = (): boolean => false;

/** See module-level docs above. */
export function useIsMounted(): boolean {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
