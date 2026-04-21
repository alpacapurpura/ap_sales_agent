import { notFound } from "next/navigation";

import {
  SECTION_PAGE_MAP,
  type BrandStudioSectionSlug,
} from "@/features/brand-studio/pages/section-page-map";

interface PageProps {
  params: Promise<{
    tenantId: string;
    section: string;
  }>;
}

function isKnownSection(slug: string): slug is BrandStudioSectionSlug {
  return slug in SECTION_PAGE_MAP;
}

/**
 * Dispatcher for brand-studio sections.
 *
 *   /{tenantId}/brand-studio/{section}                   → list view
 *   /{tenantId}/brand-studio/{section}?field={fieldId}   → detail view
 *
 * Field selection lives in the ``?field=`` query param and is handled
 * client-side via ``useActiveField``. Unknown section slugs return 404.
 */
export default async function BrandStudioSectionPage({ params }: PageProps) {
  const { section } = await params;
  if (!isKnownSection(section)) notFound();
  const Page = SECTION_PAGE_MAP[section];
  return <Page />;
}
