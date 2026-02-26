import { Metadata } from 'next';
import MarketingStudio from '@/features/marketing-studio';

export const metadata: Metadata = {
  title: 'Growth Studio | AI Sales Agent',
  description: 'Manage your customer lifecycle, connections, and growth metrics.',
};

export default function MarketingStudioPage() {
  return <MarketingStudio />;
}
