import { notFound } from "next/navigation";

import {
  SETTINGS_SECTION_MAP,
  type SettingsSectionSlug,
} from "@/features/settings/pages/section-page-map";

interface PageProps {
  params: Promise<{
    tenantId: string;
    section: string;
  }>;
}

function isKnownSection(slug: string): slug is SettingsSectionSlug {
  return slug in SETTINGS_SECTION_MAP;
}

/**
 * Catch-all dispatcher for settings sections.
 *
 *   /{tenantId}/settings/{section}   → section page (dispatched via SETTINGS_SECTION_MAP)
 *
 * Section slug is validated against SETTINGS_SECTION_MAP; unknown slugs
 * return the Next.js not-found page.
 */
export default async function SettingsSectionPage({ params }: PageProps) {
  const { section } = await params;
  if (!isKnownSection(section)) notFound();
  const Page = SETTINGS_SECTION_MAP[section];
  return <Page />;
}
