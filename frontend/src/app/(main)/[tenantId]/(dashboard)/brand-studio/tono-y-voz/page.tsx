import { redirect } from "next/navigation";

export default async function TonoVozRedirect({
  params,
}: {
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = await params;
  redirect(`/${tenantId}/brand-studio/esencia#voice-personality`);
}
