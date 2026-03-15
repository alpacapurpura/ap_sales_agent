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
        No se pudieron cargar los datos de atraccion.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <ChannelGroup
        title="Trafico Organico"
        totalValue={data.organic.totalValue}
        channels={data.organic.channels}
        defaultOpen
      />
      <ChannelGroup
        title="Trafico Pagado"
        totalValue={data.paid.totalValue}
        totalCost={data.paid.totalCost}
        channels={data.paid.channels}
        defaultOpen
      />
      {data.available && data.available.channels.length > 0 && (
        <ChannelGroup
          title="Canales disponibles"
          totalValue={0}
          channels={data.available.channels}
          defaultOpen={false}
        />
      )}
      {data.lastUpdated && (
        <p className="text-xs text-muted-foreground text-right mt-2">
          Ultima actualizacion: {new Date(data.lastUpdated).toLocaleString()}
        </p>
      )}
    </div>
  );
}
