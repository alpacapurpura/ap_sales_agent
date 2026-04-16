"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { useNavigation } from "./NavigationContext";

const DEBOUNCE_MS = 150;

export function NavigationOverlay() {
  const { isNavigating } = useNavigation();
  const [showOverlay, setShowOverlay] = useState(false);

  // Debounce the overlay visibility to avoid flash on fast navigations —
  // this effect legitimately syncs local UI state with external navigation state.
  useEffect(() => {
    if (isNavigating) {
      const timer = setTimeout(() => setShowOverlay(true), DEBOUNCE_MS);
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setShowOverlay(false);
  }, [isNavigating]);

  return (
    <AnimatePresence>
      {showOverlay && (
        <motion.div
          key="nav-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="fixed inset-0 z-[9998] flex flex-col items-center justify-center gap-3 bg-background/60 backdrop-blur-[2px]"
          aria-hidden="true"
        >
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="text-sm text-muted-foreground">Cargando...</span>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
