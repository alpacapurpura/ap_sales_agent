import { notFound, redirect } from "next/navigation";

import {
  SECTION_PAGE_MAP,
  type BrandStudioSectionSlug,
} from "@/features/brand-studio/pages/section-page-map";

interface PageProps {
  params: Promise<{
    tenantId: string;
    section: string;
  }>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
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
 *
 * Legacy redirect: ?field=voice_tone or ?field=voice_tone_clone on the
 * identity section redirects to /estilo so old emails and bookmarks don't
 * dead-end after removing those fields from identity.schema.ts.
 */
export default async function BrandStudioSectionPage({ params, searchParams }: PageProps) {
  const { tenantId, section } = await params;
  const sp: Record<string, string | string[] | undefined> = searchParams ? await searchParams : {};
  const field = Array.isArray(sp.field) ? sp.field[0] : sp.field;

  if (section === "identity" && (field === "voice_tone" || field === "voice_tone_clone")) {
    redirect(`/${tenantId}/brand-studio/estilo`);
  }

  if (!isKnownSection(section)) notFound();
  const Page = SECTION_PAGE_MAP[section];
  return <Page />;
}
