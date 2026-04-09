'use client';

import { useState, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { ArrowLeft, Mail, RefreshCw } from 'lucide-react';
import { useRouter, useSearchParams, useParams } from 'next/navigation';

import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import { useChannelDashboard } from '../../../../hooks/useChannelDashboard';
import { useHashScroll } from '../../../../hooks/useHashScroll';
import { useSyncChannel } from '../../../../hooks/useSyncChannel';
import type { MetaAdsPeriod, MailDashboardTab } from '../../../../types/metrics';
import { ChannelPeriodSelector } from '../ig-organic/ChannelPeriodSelector';
import { MailOverviewTab } from './tabs/MailOverviewTab';
import { MailEngagementTab } from './tabs/MailEngagementTab';
import { MailEntregabilidadTab } from './tabs/MailEntregabilidadTab';
import { MailListaTab } from './tabs/MailListaTab';
import { MailAutomatizacionTab } from './tabs/MailAutomatizacionTab';

interface MailDashboardProps {
  onClose?: () => void;
  initialTab?: string;
  isRouteBased?: boolean;
}

const VALID_TABS: MailDashboardTab[] = ['panorama', 'campanas', 'automatizaciones', 'audiencia', 'entregabilidad', 'crecimiento'];

export function MailDashboard({ onClose, initialTab, isRouteBased }: MailDashboardProps) {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const tenantId = params?.tenantId as string;

  const tabFromUrl = searchParams?.get('tab') ?? initialTab ?? 'panorama';
  const [activeTab, setActiveTab] = useState<MailDashboardTab>(
    VALID_TABS.includes(tabFromUrl as MailDashboardTab)
      ? (tabFromUrl as MailDashboardTab)
      : 'panorama',
  );
  const periodFromUrl = (searchParams?.get('period') ?? '30d') as MetaAdsPeriod;
  const [period, setPeriod] = useState<MetaAdsPeriod>(periodFromUrl);
  const { data, isLoading } = useChannelDashboard('email-nurture', period);
  const { sync, isSyncing, cooldownMinutes } = useSyncChannel('email-nurture');
  useHashScroll();

  const handlePeriodChange = useCallback((p: MetaAdsPeriod) => {
    setPeriod(p);
    const url = new URL(window.location.href);
    if (p === '30d') { url.searchParams.delete('period'); } else { url.searchParams.set('period', p); }
    window.history.replaceState(null, '', url.toString());
  }, []);

  const handleTabChange = useCallback(
    (value: string) => {
      const tab = value as MailDashboardTab;
      setActiveTab(tab);
      const url = new URL(window.location.href);
      if (tab === 'panorama') {
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
    router.push(`/${tenantId}/growth-studio/nutricion-oportunidad?channel=email-nurture`);
  }, [onClose, router, tenantId]);

  const dashboardContent = (
    <div className={isRouteBased ? 'flex flex-col min-h-screen bg-background' : 'fixed inset-0 z-50 flex flex-col bg-background'}>
      <div className="flex items-center justify-between border-b px-6 py-3">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={handleBack} className="gap-1.5">
            <ArrowLeft className="h-4 w-4" />
            Volver
          </Button>
          <div className="flex items-center gap-2">
            <Mail className="h-5 w-5 text-amber-500" />
            <h1 className="text-lg font-semibold">Email Marketing &middot; Dashboard</h1>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <ChannelPeriodSelector value={period} onChange={handlePeriodChange} />
          <Button
            variant="outline"
            size="sm"
            onClick={() => sync()}
            disabled={isSyncing || cooldownMinutes > 0}
            className="gap-1.5 text-xs"
          >
            <RefreshCw className={cn('h-3 w-3', isSyncing && 'animate-spin')} />
            {isSyncing ? 'Sincronizando…' : 'Sincronizar'}
          </Button>
        </div>
      </div>

      <Tabs
        value={activeTab}
        onValueChange={handleTabChange}
        className="flex flex-1 flex-col overflow-hidden"
      >
        <div className="border-b px-6">
          <TabsList className="h-10">
            <TabsTrigger value="panorama">Panorama</TabsTrigger>
            <TabsTrigger value="campanas">Campañas</TabsTrigger>
            <TabsTrigger value="automatizaciones">Automatizaciones</TabsTrigger>
            <TabsTrigger value="audiencia">Audiencia</TabsTrigger>
            <TabsTrigger value="entregabilidad">Entregabilidad</TabsTrigger>
            <TabsTrigger value="crecimiento">Crecimiento</TabsTrigger>
          </TabsList>
        </div>

        <div className="flex-1 overflow-y-auto">
          <TabsContent value="panorama" className="m-0 p-6">
            <MailOverviewTab data={data} isLoading={isLoading} />
          </TabsContent>
          <TabsContent value="campanas" className="m-0 p-6">
            <MailEngagementTab data={data} isLoading={isLoading} />
          </TabsContent>
          <TabsContent value="automatizaciones" className="m-0 p-6">
            <MailAutomatizacionTab data={data} isLoading={isLoading} />
          </TabsContent>
          <TabsContent value="audiencia" className="m-0 p-6">
            <MailListaTab data={data} isLoading={isLoading} />
          </TabsContent>
          <TabsContent value="entregabilidad" className="m-0 p-6">
            <MailEntregabilidadTab data={data} isLoading={isLoading} />
          </TabsContent>
          <TabsContent value="crecimiento" className="m-0 p-6">
            {/* Growth tab placeholder - will be replaced by dedicated component */}
            <MailOverviewTab data={data} isLoading={isLoading} />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );

  if (isRouteBased) return dashboardContent;

  if (typeof document === 'undefined') return null;
  return createPortal(dashboardContent, document.body);
}
