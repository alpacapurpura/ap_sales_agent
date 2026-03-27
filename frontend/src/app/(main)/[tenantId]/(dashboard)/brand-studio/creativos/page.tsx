import { redirect } from "next/navigation";

export default async function CreativosRedirect({ params }: { params: Promise<{ tenantId: string }> }) {
  const { tenantId } = await params;
  redirect(`/${tenantId}/brand-studio/identidad-creativa`);
}
