'use client';

import { Skeleton } from '@/components/ui/skeleton';
import { useAttractionDetail } from '../../../hooks/useAttractionDetail';
import { ChannelGroup } from '../channel-widgets/ChannelGroup';

function formatLastUpdated(isoDate: string): string {
  const d = new Date(isoDate);
  return d.toLocaleDateString('es-ES', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }) + ', ' + d.toLocaleTimeString('es-ES', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

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
      {data.lastUpdated && (
        <p className="text-xs text-muted-foreground px-3 pb-1">
          Ultima actualizacion: {formatLastUpdated(data.lastUpdated)}
        </p>
      )}

      <ChannelGroup
        title="Redes Sociales"
        totals={data.organicSocial.totals}
        channels={data.organicSocial.channels}
        groupType="organic_social"
        defaultOpen
      />
      <ChannelGroup
        title="Busqueda"
        totals={data.ga4Search.totals}
        channels={data.ga4Search.channels}
        groupType="ga4_search"
        defaultOpen
      />
      <ChannelGroup
        title="Publicidad Pagada"
        totals={data.paid.totals}
        channels={data.paid.channels}
        groupType="paid"
        defaultOpen
      />
      <ChannelGroup
        title="Contacto Directo"
        totals={data.outbound.totals}
        channels={data.outbound.channels}
        groupType="outbound"
        defaultOpen
      />
      {data.available && data.available.channels.length > 0 && (
        <ChannelGroup
          title="Canales Disponibles"
          totals={{}}
          channels={data.available.channels}
          groupType="available"
          defaultOpen={false}
        />
      )}
    </div>
  );
}
