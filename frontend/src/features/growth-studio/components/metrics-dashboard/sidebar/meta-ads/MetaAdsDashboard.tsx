'use client';

import { useState } from 'react';
import { createPortal } from 'react-dom';
import { ArrowLeft, BarChart3, RefreshCw } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useChannelDashboard } from '../../../../hooks/useChannelDashboard';
import { useCampaignPerformance } from '../../../../api/campaigns-api';
import type { MetaAdsPeriod, MetaAdsDashboardTab } from '../../../../types/metrics';
import { MetaAdsPeriodSelector } from './MetaAdsPeriodSelector';
import { ResumenTab } from './tabs/ResumenTab';
import { CampaignsTab } from './tabs/CampaignsTab';
import { CreativosTab } from './tabs/CreativosTab';
import { AudienciaTab } from './tabs/AudienciaTab';
import { CostosTab } from './tabs/CostosTab';

interface MetaAdsDashboardProps {
  onClose: () => void;
}

export function MetaAdsDashboard({ onClose }: MetaAdsDashboardProps) {
  const [period, setPeriod] = useState<MetaAdsPeriod>('30d');
  const [activeTab, setActiveTab] = useState<MetaAdsDashboardTab>('resumen');
  const { data: dashboardData, isLoading: isDashboardLoading } = useChannelDashboard('meta-ads', period);
  const { data: campaignData, isLoading: isCampaignLoading } = useCampaignPerformance(period);

  const content = (
    <div className="fixed inset-0 z-50 flex flex-col bg-background">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-6 py-3">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={onClose} className="gap-1.5">
            <ArrowLeft className="h-4 w-4" />
            Volver
          </Button>
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-blue-500" />
            <h1 className="text-lg font-semibold">Meta Ads &middot; Dashboard</h1>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <MetaAdsPeriodSelector value={period} onChange={setPeriod} />
        </div>
      </div>

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={v => setActiveTab(v as MetaAdsDashboardTab)}
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
            <ResumenTab data={dashboardData} isLoading={isDashboardLoading} />
          </TabsContent>
          <TabsContent value="campanas" className="m-0 p-6">
            <CampaignsTab
              data={campaignData}
              isLoading={isCampaignLoading}
              currency={campaignData?.currency ?? dashboardData?.kpis.find(k => k.currency)?.currency}
            />
          </TabsContent>
          <TabsContent value="creativos" className="m-0 p-6">
            <CreativosTab data={dashboardData} isLoading={isDashboardLoading} />
          </TabsContent>
          <TabsContent value="audiencia" className="m-0 p-6">
            <AudienciaTab data={dashboardData} isLoading={isDashboardLoading} />
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

  if (typeof document === 'undefined') return null;
  return createPortal(content, document.body);
}
