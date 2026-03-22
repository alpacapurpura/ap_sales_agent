import { redirect } from "next/navigation";

export default async function DashboardPage({ params }: { params: Promise<{ tenantId: string }> }) {
  const { tenantId } = await params;
  // Redirect root tenant path to brand-settings by default
  redirect(`/${tenantId}/brand-settings`);
}
