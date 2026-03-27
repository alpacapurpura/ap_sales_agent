import { redirect } from "next/navigation";

/**
 * /brand-studio → redirects to the first section (Esencia).
 */
export default async function BrandStudioIndexPage({
  params,
}: {
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = await params;
  redirect(`/${tenantId}/brand-studio/esencia`);
}
