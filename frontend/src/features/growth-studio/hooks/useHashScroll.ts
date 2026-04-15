"use client";

import { useEffect, useRef } from "react";

interface UseHashScrollOptions {
  /** Pixel offset from top to account for sticky headers/tab bars. Default: 100 */
  offset?: number;
  /** Delay in ms before scrolling to allow tab content to render. Default: 300 */
  delay?: number;
}

function scrollToHash(hash: string, offset: number) {
  const el = document.getElementById(hash) ?? document.querySelector(`[data-section="${hash}"]`);
  if (!el) return;

  const y = el.getBoundingClientRect().top + window.scrollY - offset;
  window.scrollTo({ top: y, behavior: "smooth" });

  el.classList.add("copilot-highlight");
  setTimeout(() => el.classList.remove("copilot-highlight"), 3000);
}

/**
 * Scrolls to an element matching the URL hash on mount and on hash changes.
 * Applies the `copilot-highlight` animation (defined in globals.css).
 */
export function useHashScroll(opts?: UseHashScrollOptions) {
  const offset = opts?.offset ?? 100;
  const delay = opts?.delay ?? 300;

  // Capture initial values so the mount effect does not re-run on option changes.
  // Subsequent hash changes are handled by the hashchange listener below.
  const initialOffsetRef = useRef(offset);
  const initialDelayRef = useRef(delay);

  // Scroll on mount if hash is present
  useEffect(() => {
    const hash = window.location.hash.slice(1);
    if (!hash) return;

    const timer = setTimeout(
      () => scrollToHash(hash, initialOffsetRef.current),
      initialDelayRef.current,
    );
    return () => clearTimeout(timer);
  }, []);

  // Listen for subsequent hash changes
  useEffect(() => {
    function onHashChange() {
      const hash = window.location.hash.slice(1);
      if (hash) scrollToHash(hash, offset);
    }

    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, [offset]);
}
