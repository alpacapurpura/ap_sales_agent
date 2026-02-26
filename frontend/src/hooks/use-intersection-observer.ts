import { useEffect, useRef, useState, type RefObject } from 'react';

interface UseIntersectionObserverProps extends IntersectionObserverInit {
  freezeOnceVisible?: boolean;
}

/**
 * A hook that tracks the visibility of an element using the Intersection Observer API.
 *
 * @param options IntersectionObserver options
 * @returns A tuple containing the ref to attach to the element and a boolean indicating visibility
 */
export function useIntersectionObserver({
  threshold = 0,
  root = null,
  rootMargin = '0%',
  freezeOnceVisible = false,
}: UseIntersectionObserverProps = {}): [RefObject<Element>, boolean] {
  const [entry, setEntry] = useState<IntersectionObserverEntry>();
  const [frozen, setFrozen] = useState(false);
  const node = useRef<Element>(null);

  const frozenState = frozen && freezeOnceVisible;

  useEffect(() => {
    // Ensure we have a node and support for IntersectionObserver
    if (
      !node.current ||
      frozenState ||
      typeof IntersectionObserver === 'undefined'
    ) {
      return;
    }

    const observerParams = { threshold, root, rootMargin };
    const observer = new IntersectionObserver(([entry]) => {
      setEntry(entry);
      if (entry.isIntersecting && freezeOnceVisible) {
        setFrozen(true);
      }
    }, observerParams);

    observer.observe(node.current);

    return () => {
      observer.disconnect();
    };
  }, [threshold, root, rootMargin, frozenState, freezeOnceVisible]);

  return [node, !!entry?.isIntersecting];
}
