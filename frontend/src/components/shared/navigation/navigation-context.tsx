"use client";

import {
  createContext,
  useCallback,
  useContext,
  useRef,
  useTransition,
  type ReactNode,
} from "react";
import { useRouter as useTopLoaderRouter } from "nextjs-toploader/app";
import { usePathname } from "next/navigation";

interface NavigationContextType {
  isNavigating: boolean;
  navigate: (href: string) => void;
  navigateReplace: (href: string) => void;
  pendingHref: string | null;
}

const NavigationContext = createContext<NavigationContextType | null>(null);

export function NavigationProvider({ children }: { children: ReactNode }) {
  const router = useTopLoaderRouter();
  const pathname = usePathname();
  const [isPending, startTransition] = useTransition();

  const pendingHrefRef = useRef<string | null>(null);

  const navigate = useCallback(
    (href: string) => {
      if (isPending) return;
      if (href === pathname) return;
      pendingHrefRef.current = href;
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
      pendingHrefRef.current = href;
      startTransition(() => {
        router.replace(href);
      });
    },
    [isPending, pathname, router],
  );

  return (
    <NavigationContext.Provider
      value={{
        isNavigating: isPending,
        navigate,
        navigateReplace,
        pendingHref: isPending ? pendingHrefRef.current : null,
      }}
    >
      {children}
    </NavigationContext.Provider>
  );
}

export function useNavigation() {
  const ctx = useContext(NavigationContext);
  if (!ctx) {
    throw new Error("useNavigation must be used within NavigationProvider");
  }
  return ctx;
}
