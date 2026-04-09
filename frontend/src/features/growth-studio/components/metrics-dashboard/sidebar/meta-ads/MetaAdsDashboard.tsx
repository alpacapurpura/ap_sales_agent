'use client';

import { useState, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { ArrowLeft, BarChart3, RefreshCw } from 'lucide-react';
import { useRouter, useSearchParams, useParams } from 'next/navigation';

import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import { useChannelDashboard } from '../../../../hooks/useChannelDashboard';
import { useHashScroll } from '../../../../hooks/useHashScroll';
import { useConnectionHealth } from '../../../../hooks/useConnectionHealth';
import { useSyncAllSources } from '../../../../hooks/useSyncAllSources';
import { useCampaignPerformance } from '../../../../api/campaigns-api';
import type { MetaAdsPeriod, MetaAdsDashboardTab } from '../../../../types/metrics';
import { ConnectionHealthBanner } from '../../../connection-health-banner';
import { MetaAdsPeriodSelector } from './MetaAdsPeriodSelector';
import { ResumenTab } from './tabs/ResumenTab';
import { CampaignsTab } from './tabs/CampaignsTab';
import { CreativosTab } from './tabs/CreativosTab';
import { AudienciaTab } from './tabs/AudienciaTab';
import { CostosTab } from './tabs/CostosTab';
import { useTenantLocale } from '@/features/tenant/context/tenant-locale-context';
import { formatTenantDateTime } from '@/lib/format-date';

interface MetaAdsDashboardProps {
  onClose?: () => void;
  initialTab?: MetaAdsDashboardTab;
  isRouteBased?: boolean;
}

const VALID_TABS: MetaAdsDashboardTab[] = ['resumen', 'campanas', 'creativos', 'audiencia', 'costos'];

export function MetaAdsDashboard({ onClose, initialTab, isRouteBased }: MetaAdsDashboardProps) {
  const { timezone } = useTenantLocale();
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const tenantId = params?.tenantId as string;

  const tabFromUrl = searchParams?.get('tab') ?? initialTab ?? 'resumen';
  const periodFromUrl = (searchParams?.get('period') ?? '30d') as MetaAdsPeriod;
  const [period, setPeriod] = useState<MetaAdsPeriod>(periodFromUrl);
  const [activeTab, setActiveTab] = useState<MetaAdsDashboardTab>(
    VALID_TABS.includes(tabFromUrl as MetaAdsDashboardTab)
      ? (tabFromUrl as MetaAdsDashboardTab)
      : 'resumen',
  );
  const { data: dashboardData, isLoading: isDashboardLoading } = useChannelDashboard('meta-ads', period);
  const { data: campaignData, isLoading: isCampaignLoading } = useCampaignPerformance(period);
  const { data: health } = useConnectionHealth('meta-ads');
  const { trigger: syncAll, isLoading: isSyncing } = useSyncAllSources();
  useHashScroll();

  const handlePeriodChange = useCallback((p: MetaAdsPeriod) => {
    setPeriod(p);
    const url = new URL(window.location.href);
    if (p === '30d') { url.searchParams.delete('period'); } else { url.searchParams.set('period', p); }
    window.history.replaceState(null, '', url.toString());
  }, []);

  const handleTabChange = useCallback(
    (value: string) => {
      const tab = value as MetaAdsDashboardTab;
      setActiveTab(tab);
      const url = new URL(window.location.href);
      if (tab === 'resumen') {
        url.searchParams.delete('tab');
      } else {
        url.searchParams.set('tab', tab);
      }
      window.history.replaceState(null, '', url.toString());
    },
    [],
  );

  const handleBack = useCallback(() => {
    if (onClose) {
      onClose();
      return;
    }
    router.push(`/${tenantId}/growth-studio/atraccion-captura?channel=meta-ads`);
  }, [onClose, router, tenantId]);

  const content = (
    <div className={isRouteBased ? 'flex flex-col min-h-screen bg-background' : 'fixed inset-0 z-50 flex flex-col bg-background'}>
      {/* Header */}
      <div className="flex items-center justify-between border-b px-6 py-3">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={handleBack} className="gap-1.5">
            <ArrowLeft className="h-4 w-4" />
            Volver
          </Button>
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-blue-500" />
            <h1 className="text-lg font-semibold">Meta Ads &middot; Dashboard</h1>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <MetaAdsPeriodSelector value={period} onChange={handlePeriodChange} />
          {campaignData?.lastSynced && (
            <span className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Última sync: {formatTenantDateTime(campaignData.lastSynced, timezone)}
            </span>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => syncAll(30)}
            disabled={isSyncing}
            className="gap-1.5 text-xs"
          >
            <RefreshCw className={cn('h-3 w-3', isSyncing && 'animate-spin')} />
            {isSyncing ? 'Sincronizando…' : 'Sincronizar'}
          </Button>
        </div>
      </div>

      {/* Connection Health Banner */}
      {health && health.status !== 'healthy' && (
        <div className="px-6 pt-4">
          <ConnectionHealthBanner
            status={health.status}
            channelSlug={health.channelSlug}
            message={health.message}
            expiresAt={health.expiresAt}
          />
        </div>
      )}

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={handleTabChange}
        className="flex flex-1 flex-col overflow-hidden"
      >
        <div className="border-b px-6">
          <TabsList className="h-10">
            <TabsTrigger value="resumen">Resumen</TabsTrigger>
            <TabsTrigger value="campanas">Campañas</TabsTrigger>
            <TabsTrigger value="creativos">Creativos</TabsTrigger>
            <TabsTrigger value="audiencia">Audiencia</TabsTrigger>
            <TabsTrigger value="costos">Costos</TabsTrigger>
          </TabsList>
        </div>

        <div className="flex-1 overflow-y-auto">
          <TabsContent value="resumen" className="m-0 p-6">
            <ResumenTab
              data={dashboardData}
              isLoading={isDashboardLoading}
              campaignData={campaignData}
              onNavigateToTab={setActiveTab}
            />
          </TabsContent>
          <TabsContent value="campanas" className="m-0 p-6">
            <CampaignsTab
              data={campaignData}
              isLoading={isCampaignLoading}
              currency={campaignData?.currency ?? dashboardData?.kpis.find(k => k.currency)?.currency}
            />
          </TabsContent>
          <TabsContent value="creativos" className="m-0 p-6">
            <CreativosTab data={dashboardData} isLoading={isDashboardLoading} period={period} />
          </TabsContent>
          <TabsContent value="audiencia" className="m-0 p-6">
            <AudienciaTab data={dashboardData} isLoading={isDashboardLoading} period={period} />
          </TabsContent>
          <TabsContent value="costos" className="m-0 p-6">
            <CostosTab
              data={dashboardData}
              campaignData={campaignData}
              isLoading={isDashboardLoading}
            />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );

  if (isRouteBased) return content;
  if (typeof document === 'undefined') return null;
  return createPortal(content, document.body);
}
