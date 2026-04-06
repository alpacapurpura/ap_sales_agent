'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

interface UseIntersectionObserverOptions {
  /** Extra margin around root to pre-fetch before element is visible. Default: '0px' */
  rootMargin?: string;
  /** Visibility threshold (0-1). Default: 0 */
  threshold?: number;
}

/**
 * Tracks whether a DOM element is (or has ever been) visible in the viewport.
 *
 * **Once-mode:** After `isVisible` becomes `true`, it stays `true` even if the
 * element scrolls out of view. This prevents re-fetching data for groups that
 * have already loaded.
 *
 * Usage:
 * ```tsx
 * const { ref, isVisible } = useIntersectionObserver({ rootMargin: '200px' });
 * return <div ref={ref}>{isVisible && <ExpensiveComponent />}</div>;
 * ```
 */
export function useIntersectionObserver(options?: UseIntersectionObserverOptions) {
  const [isVisible, setIsVisible] = useState(false);
  const observerRef = useRef<IntersectionObserver | null>(null);
  const elementRef = useRef<Element | null>(null);
  const seenRef = useRef(false);

  // Create observer once
  useEffect(() => {
    observerRef.current = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting && !seenRef.current) {
            seenRef.current = true;
            setIsVisible(true);
          }
        }
      },
      {
        rootMargin: options?.rootMargin ?? '0px',
        threshold: options?.threshold ?? 0,
      },
    );

    // If element was already attached, observe it
    if (elementRef.current) {
      observerRef.current.observe(elementRef.current);
    }

    return () => {
      observerRef.current?.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [options?.rootMargin, options?.threshold]);

  // Ref callback — attach/detach element
  const ref = useCallback((node: Element | null) => {
    // Unobserve previous element
    if (elementRef.current && observerRef.current) {
      observerRef.current.unobserve(elementRef.current);
    }

    elementRef.current = node;

    // Observe new element
    if (node && observerRef.current) {
      observerRef.current.observe(node);
    }
  }, []);

  return { ref, isVisible };
}
