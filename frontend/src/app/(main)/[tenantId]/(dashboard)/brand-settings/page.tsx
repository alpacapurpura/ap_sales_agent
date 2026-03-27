import { redirect } from "next/navigation";

/**
 * Legacy route — redirects to the new Brand Studio structure.
 * Kept for backwards compatibility (bookmarks, copilot navigation, external links).
 */
export default async function BrandSettingsPage({
  params,
}: {
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = await params;
  redirect(`/${tenantId}/brand-studio/esencia`);
}
