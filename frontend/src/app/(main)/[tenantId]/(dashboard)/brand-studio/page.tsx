import { redirect } from "next/navigation";

/**
 * Brand Studio landing. Sends the user to the identity section, which is
 * both the most common entry point and the most information-dense. The
 * left nav rail is rendered by the layout regardless of the section.
 */
export default async function BrandStudioIndexPage({
  params,
}: {
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = await params;
  redirect(`/${tenantId}/brand-studio/identity`);
}
