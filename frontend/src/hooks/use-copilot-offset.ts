'use client';

import { useEffect, useState } from 'react';
import { useCopilotStore } from '@/features/copilot/store/copilot-store';

export const COPILOT_OPEN_WIDTH = 380;
export const COPILOT_RAIL_WIDTH = 60;
const SM_BREAKPOINT = 640;

/**
 * Returns the current copilot column width in pixels.
 * - Desktop + open  → 380
 * - Desktop + closed → 60
 * - Mobile           → 0
 */
export function useCopilotOffset() {
  const isOpen = useCopilotStore((s) => s.isOpen);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < SM_BREAKPOINT);
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, []);

  if (isMobile) return 0;
  return isOpen ? COPILOT_OPEN_WIDTH : COPILOT_RAIL_WIDTH;
}
