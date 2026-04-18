"use client";

import {
  FileText,
  Fingerprint,
  Flag,
  Headphones,
  Landmark,
  Layers,
  Megaphone,
  Palette,
  ScrollText,
  Sparkles,
  Target,
  Users,
} from "lucide-react";
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

interface SectionNav {
  slug: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

/**
 * Fixed list of brand-studio sections. Order matches the SDR-facing
 * narrative: identity → positioning → voice/personality → story → audience
 * → assets. Keep in sync with SECTION_PAGE_MAP (factory-generated pages)
 * plus the few special routes (buyer personas).
 */
const SECTIONS: readonly SectionNav[] = [
  { slug: "identity", label: "Identidad", icon: Fingerprint },
  { slug: "positioning", label: "Posicionamiento", icon: Target },
  { slug: "narrative", label: "Narrativa", icon: ScrollText },
  { slug: "methodology", label: "Metodología", icon: Flag },
  { slug: "story", label: "Historia", icon: FileText },
  { slug: "team", label: "Equipo", icon: Users },
  { slug: "authority", label: "Autoridad", icon: Landmark },
  { slug: "testimonials", label: "Testimonios", icon: Headphones },
  { slug: "visuals", label: "Visuales", icon: Palette },
  { slug: "communication-assets", label: "Assets", icon: Layers },
  { slug: "contact", label: "Contacto", icon: Megaphone },
] as const;

const PERSONAS_SECTION: SectionNav = {
  slug: "publico",
  label: "Buyer personas",
  icon: Sparkles,
};

/**
 * Left-hand navigation rail listing every brand-studio section. The active
 * segment is derived from the URL — the first path segment after
 * `/brand-studio/` wins. Uses next/link for SPA navigation; no client-side
 * routing state required.
 */
export function BrandStudioNavRail() {
  const params = useParams<{ tenantId?: string }>();
  const tenantId = params?.tenantId ?? "";
  const pathname = usePathname();
  const activeSlug = pathname.split("/brand-studio/")[1]?.split("/")[0] ?? null;

  return (
    <nav
      aria-label="Secciones de Brand Studio"
      className="flex w-60 shrink-0 flex-col gap-0.5 border-r bg-muted/10 p-3"
    >
      <SectionLink tenantId={tenantId} section={PERSONAS_SECTION} activeSlug={activeSlug} />
      <div className="my-2 h-px bg-border" aria-hidden />
      {SECTIONS.map((section) => (
        <SectionLink
          key={section.slug}
          tenantId={tenantId}
          section={section}
          activeSlug={activeSlug}
        />
      ))}
    </nav>
  );
}

interface SectionLinkProps {
  tenantId: string;
  section: SectionNav;
  activeSlug: string | null;
}

function SectionLink({ tenantId, section, activeSlug }: SectionLinkProps) {
  const Icon = section.icon;
  const isActive = section.slug === activeSlug;

  return (
    <Link
      href={`/${tenantId}/brand-studio/${section.slug}`}
      aria-current={isActive ? "page" : undefined}
      className={cn(
        "flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
        isActive ? "bg-primary/10 font-medium text-primary" : "hover:bg-muted/50",
      )}
    >
      <Icon className="h-4 w-4" aria-hidden />
      {section.label}
    </Link>
  );
}
