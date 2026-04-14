"use client";

import { useCallback } from "react";
import { useRouter, usePathname, useSearchParams } from "next/navigation";

const CHANNEL_PARAM = "channel";

/**
 * Hook that syncs Growth Studio channel sidebar state with URL search params.
 *
 * - `urlChannel`: currently selected channel slug from `?channel=` param (null if none)
 * - `openChannel(slug)`: sets `?channel=slug` via `router.replace` (no history stack pollution)
 * - `closeChannel()`: removes `?channel=` param via `router.replace`
 */
export function useGrowthStudioUrl() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const urlChannel = searchParams.get(CHANNEL_PARAM);

  const openChannel = useCallback(
    (slug: string) => {
      const params = new URLSearchParams(searchParams.toString());
      params.set(CHANNEL_PARAM, slug);
      router.replace(`${pathname}?${params.toString()}`);
    },
    [router, pathname, searchParams],
  );

  const closeChannel = useCallback(() => {
    const params = new URLSearchParams(searchParams.toString());
    params.delete(CHANNEL_PARAM);
    const qs = params.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname);
  }, [router, pathname, searchParams]);

  return { urlChannel, openChannel, closeChannel };
}
