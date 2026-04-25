"use client";

import { usePathname } from "next/navigation";
import { useRouter as useTopLoaderRouter } from "nextjs-toploader/app";
import {
  createContext,
  useCallback,
  useContext,
  useState,
  useTransition,
  type ReactNode,
} from "react";

interface NavigationContextType {
  isNavigating: boolean;
  navigate: (href: string) => void;
  navigateReplace: (href: string) => void;
  pendingHref: string | null;
  /**
   * Wrap an async operation so the same NavigationOverlay that covers
   * route transitions also covers cross-route async flows (entity
   * creation, multi-step orchestrations). The overlay engages on the
   * leading edge and releases on settle, regardless of fn outcome.
   */
  runWithOverlay: <T>(fn: () => Promise<T>) => Promise<T>;
}

const NavigationContext = createContext<NavigationContextType | null>(null);

/**
 *
 */
export function NavigationProvider({ children }: { children: ReactNode }) {
  const router = useTopLoaderRouter();
  const pathname = usePathname();
  const [isPending, startTransition] = useTransition();
  const [pendingHref, setPendingHref] = useState<string | null>(null);
  const [overlayDepth, setOverlayDepth] = useState(0);

  const navigate = useCallback(
    (href: string) => {
      if (isPending) return;
      if (href === pathname) return;
      setPendingHref(href);
      startTransition(() => {
        router.push(href);
      });
    },
    [isPending, pathname, router],
  );

  const navigateReplace = useCallback(
    (href: string) => {
      if (isPending) return;
      if (href === pathname) return;
      setPendingHref(href);
      startTransition(() => {
        router.replace(href);
      });
    },
    [isPending, pathname, router],
  );

  const runWithOverlay = useCallback(async <T,>(fn: () => Promise<T>): Promise<T> => {
    setOverlayDepth((d) => d + 1);
    try {
      return await fn();
    } finally {
      setOverlayDepth((d) => Math.max(0, d - 1));
    }
  }, []);

  const isNavigating = isPending || overlayDepth > 0;

  return (
    <NavigationContext.Provider
      value={{
        isNavigating,
        navigate,
        navigateReplace,
        pendingHref: isPending ? pendingHref : null,
        runWithOverlay,
      }}
    >
      {children}
    </NavigationContext.Provider>
  );
}

/**
 *
 */
export function useNavigation() {
  const ctx = useContext(NavigationContext);
  if (!ctx) {
    throw new Error("useNavigation must be used within NavigationProvider");
  }
  return ctx;
}
