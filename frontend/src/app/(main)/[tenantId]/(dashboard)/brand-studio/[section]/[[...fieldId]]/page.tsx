import { notFound } from "next/navigation";

import {
  SECTION_PAGE_MAP,
  type BrandStudioSectionSlug,
} from "@/features/brand-studio/pages/section-pages";

interface PageProps {
  params: Promise<{
    tenantId: string;
    section: string;
    fieldId?: string[];
  }>;
}

function isKnownSection(slug: string): slug is BrandStudioSectionSlug {
  return slug in SECTION_PAGE_MAP;
}

/**
 * Catch-all dispatcher for brand-studio sections.
 *
 *   /{tenantId}/brand-studio/{section}              → section list view
 *   /{tenantId}/brand-studio/{section}/{fieldId}    → field detail view
 *
 * Section slug is validated against `SECTION_PAGE_MAP`; unknown slugs return
 * the Next.js not-found page. Field id (when present) is read from the URL
 * by `useBrandStudioFieldRouting` inside the factory page itself — this
 * route file stays thin.
 */
export default async function BrandStudioSectionPage({ params }: PageProps) {
  const { section } = await params;
  if (!isKnownSection(section)) notFound();
  const Page = SECTION_PAGE_MAP[section];
  return <Page />;
}
