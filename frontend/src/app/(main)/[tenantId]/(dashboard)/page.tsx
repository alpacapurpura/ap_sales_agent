import { redirect } from "next/navigation";

export default function DashboardPage({ params }: { params: { tenantId: string } }) {
  // Redirect root tenant path to brand-settings by default
  redirect(`/${params.tenantId}/brand-settings`);
}
