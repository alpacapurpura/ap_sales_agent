'use client';

import { useState } from 'react';
import { createPortal } from 'react-dom';
import { ArrowLeft, BarChart3 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useChannelDashboard } from '../../../../hooks/useChannelDashboard';
import type { MetaAdsPeriod, MetaAdsDashboardTab } from '../../../../types/metrics';
import { MetaAdsPeriodSelector } from './MetaAdsPeriodSelector';
import { OverviewTab } from './tabs/OverviewTab';
import { CampaignsTab } from './tabs/CampaignsTab';
import { AudienceTab } from './tabs/AudienceTab';
import { VideoTab } from './tabs/VideoTab';
import { CostsTab } from './tabs/CostsTab';

interface MetaAdsDashboardProps {
  onClose: () => void;
}

export function MetaAdsDashboard({ onClose }: MetaAdsDashboardProps) {
  const [period, setPeriod] = useState<MetaAdsPeriod>('30d');
  const [activeTab, setActiveTab] = useState<MetaAdsDashboardTab>('overview');
  const { data, isLoading } = useChannelDashboard('meta-ads', period);

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
        <MetaAdsPeriodSelector value={period} onChange={setPeriod} />
      </div>

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={v => setActiveTab(v as MetaAdsDashboardTab)}
        className="flex flex-1 flex-col overflow-hidden"
      >
        <div className="border-b px-6">
          <TabsList className="h-10">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="campaigns">Campanas</TabsTrigger>
            <TabsTrigger value="audience">Audiencia</TabsTrigger>
            <TabsTrigger value="video">Video</TabsTrigger>
            <TabsTrigger value="costs">Costos</TabsTrigger>
          </TabsList>
        </div>

        <div className="flex-1 overflow-y-auto">
          <TabsContent value="overview" className="m-0 p-6">
            <OverviewTab data={data} isLoading={isLoading} />
          </TabsContent>
          <TabsContent value="campaigns" className="m-0 p-6">
            <CampaignsTab />
          </TabsContent>
          <TabsContent value="audience" className="m-0 p-6">
            <AudienceTab />
          </TabsContent>
          <TabsContent value="video" className="m-0 p-6">
            <VideoTab />
          </TabsContent>
          <TabsContent value="costs" className="m-0 p-6">
            <CostsTab data={data} isLoading={isLoading} />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );

  if (typeof document === 'undefined') return null;
  return createPortal(content, document.body);
}
