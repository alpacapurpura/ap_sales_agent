'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { RefreshCw, Megaphone, Target } from 'lucide-react';
import { fetchCampaignOverview, triggerCampaignSync } from '../../api/campaigns-api';
import { CampaignCard } from './CampaignCard';
import { RecommendationsList } from './RecommendationsList';
import type { CampaignOverview } from '../../types/campaigns';

export function CampaignPanel() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery<CampaignOverview>({
    queryKey: ['campaigns', 'overview'],
    queryFn: async () => {
      const token = (await getToken()) ?? '';
      return fetchCampaignOverview(token);
    },
    staleTime: 5 * 60 * 1000,
  });

  const syncMutation = useMutation({
    mutationFn: async () => {
      const token = (await getToken()) ?? '';
      return triggerCampaignSync(token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-16 w-full" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-24 w-full" />
            ))}
          </div>
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          Error al cargar campañas. Intenta de nuevo.
        </CardContent>
      </Card>
    );
  }

  const overview = data!;

  return (
    <div className="space-y-4">
      {/* Summary bar */}
      <Card>
        <CardContent className="flex items-center justify-between py-4">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <Megaphone className="h-5 w-5 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Total:</span>
              <span className="font-semibold">{overview.total_campaigns}</span>
            </div>
            <div className="flex items-center gap-2">
              <Target className="h-5 w-5 text-green-500" />
              <span className="text-sm text-muted-foreground">Activas:</span>
              <span className="font-semibold text-green-600">{overview.active_campaigns}</span>
            </div>
            {overview.last_synced && (
              <span className="text-xs text-muted-foreground">
                Último sync: {new Date(overview.last_synced).toLocaleString('es-MX')}
              </span>
            )}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
            {syncMutation.isPending ? 'Sincronizando...' : 'Sincronizar'}
          </Button>
        </CardContent>
      </Card>

      {/* Main content: campaigns + recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-3">
          {overview.campaigns.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No hay campañas sincronizadas. Conecta Meta Ads y sincroniza.
              </CardContent>
            </Card>
          ) : (
            overview.campaigns.map((campaign) => (
              <CampaignCard key={campaign.external_id} campaign={campaign} />
            ))
          )}
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Recomendaciones</CardTitle>
            </CardHeader>
            <CardContent>
              <RecommendationsList recommendations={overview.recommendations} />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
