"use client";

import { useCallback, type ReactNode } from "react";
import { Link2 } from "lucide-react";
import { toast } from "sonner";

interface ChartSectionProps {
  /** Unique slug within the current tab — becomes the DOM id and hash anchor */
  slug: string;
  children: ReactNode;
}

/**
 * Wrapper that gives a chart/metric section a deep-linkable id.
 * On hover, shows a link icon that copies the full URL with #slug to clipboard.
 */
export function ChartSection({ slug, children }: ChartSectionProps) {
  const handleCopyLink = useCallback(() => {
    const url = new URL(window.location.href);
    url.hash = slug;
    void navigator.clipboard.writeText(url.toString());
    toast.success("Enlace copiado");
  }, [slug]);

  return (
    <section id={slug} data-section={slug} className="group/section relative scroll-mt-28">
      {children}
      <button
        type="button"
        onClick={handleCopyLink}
        className="absolute top-0 right-0 p-1.5 rounded-md opacity-0 group-hover/section:opacity-100 transition-opacity text-muted-foreground hover:text-foreground hover:bg-muted"
        title="Copiar enlace a esta sección"
      >
        <Link2 className="h-3.5 w-3.5" />
      </button>
    </section>
  );
}
