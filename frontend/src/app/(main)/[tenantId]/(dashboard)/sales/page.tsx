import { redirect } from "next/navigation";

export default async function SalesIndexPage({
  params,
}: {
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = await params;
  redirect(`/${tenantId}/sales/resumen`);
}
