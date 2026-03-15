'use client';

import { Skeleton } from '@/components/ui/skeleton';
import { useAttractionDetail } from '../../../hooks/useAttractionDetail';
import { ChannelGroup } from '../channel-widgets/ChannelGroup';

export function AttractionDetail() {
  const { data, isLoading, error } = useAttractionDetail();

  if (isLoading) {
    return (
      <div className="space-y-4 p-4">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        No se pudieron cargar los datos de atracción.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <ChannelGroup
        title="Tráfico Orgánico"
        totalValue={data.organic.totalValue}
        channels={data.organic.channels}
        defaultOpen
      />
      <ChannelGroup
        title="Tráfico Pagado"
        totalValue={data.paid.totalValue}
        totalCost={data.paid.totalCost}
        channels={data.paid.channels}
        defaultOpen
      />
    </div>
  );
}
