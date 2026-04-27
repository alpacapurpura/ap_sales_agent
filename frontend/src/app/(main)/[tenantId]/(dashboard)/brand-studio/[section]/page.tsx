import { notFound, redirect } from "next/navigation";

import { isBrandStudioSection } from "@/features/brand-studio/pages/section-slugs";
import { SectionDispatcher } from "@/features/brand-studio/pages/SectionDispatcher";

interface PageProps {
  params: Promise<{
    tenantId: string;
    section: string;
  }>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}

/**
 * Dispatcher de brand-studio (Server Component).
 *
 *   /{tenantId}/brand-studio/{section}                   → list view
 *   /{tenantId}/brand-studio/{section}?field={fieldId}   → detail view
 *
 * Valida el slug contra `section-slugs.ts` (server-safe, sin imports
 * client) y delega el render al `SectionDispatcher` client, que hace
 * lazy-load del chunk per-section via `next/dynamic`.
 *
 * Legacy redirect: `?field=voice_tone` o `?field=voice_tone_clone` en
 * /identity redirige a /estilo — preserva bookmarks y emails viejos
 * post-migración de esos fields.
 */
export default async function BrandStudioSectionPage({ params, searchParams }: PageProps) {
  const { tenantId, section } = await params;
  const sp: Record<string, string | string[] | undefined> = searchParams ? await searchParams : {};
  const field = Array.isArray(sp.field) ? sp.field[0] : sp.field;

  if (section === "identity" && (field === "voice_tone" || field === "voice_tone_clone")) {
    redirect(`/${tenantId}/brand-studio/estilo`);
  }

  if (!isBrandStudioSection(section)) notFound();

  return <SectionDispatcher slug={section} />;
}
