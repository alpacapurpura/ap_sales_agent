'use client';

import { useState, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { ArrowLeft, Mail } from 'lucide-react';
import { useRouter, useSearchParams, useParams } from 'next/navigation';

import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useChannelDashboard } from '../../../../hooks/useChannelDashboard';
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

const VALID_TABS: MailDashboardTab[] = ['overview', 'engagement', 'entregabilidad', 'lista', 'automatizacion'];

export function MailDashboard({ onClose, initialTab, isRouteBased }: MailDashboardProps) {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const tenantId = params?.tenantId as string;

  const tabFromUrl = searchParams?.get('tab') ?? initialTab ?? 'overview';
  const [activeTab, setActiveTab] = useState<MailDashboardTab>(
    VALID_TABS.includes(tabFromUrl as MailDashboardTab)
      ? (tabFromUrl as MailDashboardTab)
      : 'overview',
  );
  const [period, setPeriod] = useState<MetaAdsPeriod>('30d');
  const { data, isLoading } = useChannelDashboard('email-nurture', period);

  const handleTabChange = useCallback(
    (value: string) => {
      const tab = value as MailDashboardTab;
      setActiveTab(tab);
      const url = new URL(window.location.href);
      if (tab === 'overview') {
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
        <ChannelPeriodSelector value={period} onChange={setPeriod} />
      </div>

      <Tabs
        value={activeTab}
        onValueChange={handleTabChange}
        className="flex flex-1 flex-col overflow-hidden"
      >
        <div className="border-b px-6">
          <TabsList className="h-10">
            <TabsTrigger value="overview">Resumen</TabsTrigger>
            <TabsTrigger value="engagement">Engagement</TabsTrigger>
            <TabsTrigger value="entregabilidad">Entregabilidad</TabsTrigger>
            <TabsTrigger value="lista">Lista</TabsTrigger>
            <TabsTrigger value="automatizacion">Automatización</TabsTrigger>
          </TabsList>
        </div>

        <div className="flex-1 overflow-y-auto">
          <TabsContent value="overview" className="m-0 p-6">
            <MailOverviewTab data={data} isLoading={isLoading} />
          </TabsContent>
          <TabsContent value="engagement" className="m-0 p-6">
            <MailEngagementTab data={data} isLoading={isLoading} />
          </TabsContent>
          <TabsContent value="entregabilidad" className="m-0 p-6">
            <MailEntregabilidadTab data={data} isLoading={isLoading} />
          </TabsContent>
          <TabsContent value="lista" className="m-0 p-6">
            <MailListaTab data={data} isLoading={isLoading} />
          </TabsContent>
          <TabsContent value="automatizacion" className="m-0 p-6">
            <MailAutomatizacionTab data={data} isLoading={isLoading} />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );

  if (isRouteBased) return dashboardContent;

  if (typeof document === 'undefined') return null;
  return createPortal(dashboardContent, document.body);
}
