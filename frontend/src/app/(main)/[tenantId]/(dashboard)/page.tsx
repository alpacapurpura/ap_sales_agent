import { redirect } from "next/navigation";

export default async function DashboardPage({ params }: { params: Promise<{ tenantId: string }> }) {
  const { tenantId } = await params;
  redirect(`/${tenantId}/brand-studio/esencia`);
}
