'use client';

import {
  type ReactNode,
  type HTMLAttributes,
  useEffect,
  useRef,
  useState,
} from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useCopilotOffset } from '@/hooks/use-copilot-offset';

// ── Constants ────────────────────────────────────────────────────────
const ANIMATION_MS = 300;

// ── Hook: keep component mounted during exit animation ───────────────
function useDetailPanelTransition(open: boolean) {
  const [mounted, setMounted] = useState(open);
  const [visible, setVisible] = useState(false);

  // Sync mount/visible state with the open prop to drive enter/exit animations.
  // The effect legitimately derives transient animation state from the prop.
  useEffect(() => {
    if (open) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setMounted(true);
      // Next frame: trigger enter animation
       
      requestAnimationFrame(() => requestAnimationFrame(() => setVisible(true)));
    } else {
       
      setVisible(false);
       
      const timer = setTimeout(() => setMounted(false), ANIMATION_MS);
      return () => clearTimeout(timer);
    }
  }, [open]);

  return { mounted, visible };
}

// ── DetailPanel ──────────────────────────────────────────────────────
interface DetailPanelProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  className?: string;
}

function DetailPanel({ open, onClose, children, className }: DetailPanelProps) {
  const { mounted, visible } = useDetailPanelTransition(open);
  const copilotWidth = useCopilotOffset();
  const panelRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // Escape key closes
  useEffect(() => {
    if (!mounted) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [mounted, onClose]);

  // Focus management
  useEffect(() => {
    if (mounted && visible) {
      previousFocusRef.current = document.activeElement as HTMLElement;
      panelRef.current?.focus();
    }
    if (!mounted && previousFocusRef.current) {
      previousFocusRef.current.focus();
      previousFocusRef.current = null;
    }
  }, [mounted, visible]);

  if (!mounted) return null;

  return createPortal(
    <>
      {/* Overlay — does NOT cover the copilot */}
      <div
        className={cn(
          'fixed top-0 bottom-0 left-0 z-[45] bg-black/50 transition-opacity duration-300',
          visible ? 'opacity-100' : 'opacity-0',
        )}
        style={{ right: `${copilotWidth}px` }}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="false"
        tabIndex={-1}
        className={cn(
          'fixed top-0 bottom-0 z-[45] flex w-full flex-col overflow-y-auto border-l bg-background shadow-lg outline-none sm:w-[400px]',
          'transition-transform duration-300 ease-in-out',
          visible ? 'translate-x-0' : 'translate-x-full',
          className,
        )}
        style={{ right: `${copilotWidth}px` }}
      >
        {children}
      </div>
    </>,
    document.body,
  );
}

// ── Sub-components ───────────────────────────────────────────────────
function DetailPanelHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('flex flex-col gap-1.5 px-6 pt-6', className)}
      {...props}
    />
  );
}

function DetailPanelTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h2
      className={cn('text-lg font-semibold leading-none tracking-tight', className)}
      {...props}
    />
  );
}

interface DetailPanelCloseProps extends HTMLAttributes<HTMLButtonElement> {
  onClose: () => void;
}

function DetailPanelClose({ onClose, className, ...props }: DetailPanelCloseProps) {
  return (
    <button
      type="button"
      onClick={onClose}
      className={cn(
        'inline-flex h-7 w-7 items-center justify-center rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
        className,
      )}
      {...props}
    >
      <X className="h-4 w-4" />
      <span className="sr-only">Cerrar</span>
    </button>
  );
}

export {
  DetailPanel,
  DetailPanelHeader,
  DetailPanelTitle,
  DetailPanelClose,
};
