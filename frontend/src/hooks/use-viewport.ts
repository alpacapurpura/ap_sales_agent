"use client";

import { useState, useLayoutEffect } from "react";

/** Breakpoint thresholds (px) — matches Tailwind defaults */
const MOBILE_MAX = 767; // < 768 → mobile
const TABLET_MAX = 1023; // 768-1023 → tablet
// ≥ 1024 → desktop

export interface ViewportState {
  /** True when viewport width < 768px */
  isMobile: boolean;
  /** True when viewport width 768-1023px */
  isTablet: boolean;
  /** True when viewport width >= 1024px */
  isDesktop: boolean;
  /**
   * Raw viewport width in pixels.
   * `null` on initial SSR render (before any effect fires).
   */
  width: number | null;
}

const SSR_INITIAL: ViewportState = {
  isMobile: false,
  isTablet: false,
  isDesktop: false,
  width: null,
};

function computeState(width: number): ViewportState {
  return {
    isMobile: width <= MOBILE_MAX,
    isTablet: width > MOBILE_MAX && width <= TABLET_MAX,
    isDesktop: width > TABLET_MAX,
    width,
  };
}

/**
 * Reads viewport width synchronously; returns SSR_INITIAL when `window` is unavailable.
 * Used as the lazy `useState` initialiser to avoid an extra render on mount.
 */
function getInitialState(): ViewportState {
  if (typeof window === "undefined" || !window.matchMedia) {
    return SSR_INITIAL;
  }
  return computeState(window.innerWidth);
}

/**
 * SSR-safe matchMedia wrapper that tracks viewport breakpoints.
 *
 * Returns `{ isMobile, isTablet, isDesktop, width }`.
 * `width` is `null` on initial render (before hydration) to avoid
 * server/client mismatch.
 *
 * Breakpoints: mobile < 768, tablet 768-1023, desktop >= 1024.
 *
 * Initial state is read synchronously via lazy `useState` initialiser.
 * Change listeners subscribe via `useLayoutEffect` for break-point transitions.
 */
export function useViewport(): ViewportState {
  // Lazy initialiser reads the DOM synchronously on first render (client only).
  // On SSR the function returns SSR_INITIAL, so no server/client mismatch occurs.
  const [state, setState] = useState<ViewportState>(getInitialState);

  useLayoutEffect(() => {
    // Guard: SSR / environments without matchMedia (also handles JSDOM in tests)
    if (typeof window === "undefined" || !window.matchMedia) {
      return;
    }

    // Listen on mobile breakpoint boundary
    const mobileQuery = window.matchMedia(`(max-width: ${MOBILE_MAX}px)`);
    // Listen on tablet/desktop boundary
    const desktopQuery = window.matchMedia(`(min-width: ${TABLET_MAX + 1}px)`);

    function handleChange() {
      setState(computeState(window.innerWidth));
    }

    mobileQuery.addEventListener("change", handleChange);
    desktopQuery.addEventListener("change", handleChange);

    return () => {
      mobileQuery.removeEventListener("change", handleChange);
      desktopQuery.removeEventListener("change", handleChange);
    };
  }, []);

  return state;
}
