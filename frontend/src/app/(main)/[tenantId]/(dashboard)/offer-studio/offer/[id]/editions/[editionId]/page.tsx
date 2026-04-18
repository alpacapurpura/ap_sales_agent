import { redirect } from "next/navigation";

/**
 * Edition root — there is no "edition home" screen; the tab bar owns the
 * default view. We redirect to the ventas tab, which is the primary
 * per-edition dashboard (enrollments + KPIs).
 */
export default async function EditionIndexPage({
  params,
}: {
  params: Promise<{ tenantId: string; id: string; editionId: string }>;
}) {
  const { tenantId, id, editionId } = await params;
  redirect(`/${tenantId}/offer-studio/offer/${id}/editions/${editionId}/ventas`);
}
