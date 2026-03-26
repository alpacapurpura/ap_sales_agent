import { redirect } from 'next/navigation';

export const metadata = {
  title: 'Growth Studio | AI Sales Agent',
  description: 'Manage your customer lifecycle, connections, and growth metrics.',
};

export default async function MarketingStudioPage({
  params,
}: {
  params: Promise<{ tenantId: string }>;
}) {
  const { tenantId } = await params;
  redirect(`/${tenantId}/marketing-studio/atraccion-captura`);
}
