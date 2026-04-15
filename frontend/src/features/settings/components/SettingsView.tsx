"use client";

import {
  CalendarClock,
  CreditCard,
  Key,
  Settings as SettingsIcon,
  User,
  Webhook,
  Users,
} from "lucide-react";
import { useSearchParams, useParams } from "next/navigation";
import { Suspense } from "react";

import { useNavigation } from "@/components/shared/navigation";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { OAuthCallbackHandler } from "@/features/connections/components/oauth-callback-handler";
import { AIKeysForm } from "@/features/settings/components/ai-keys-form";
import { GeneralSettingsForm } from "@/features/settings/components/general-settings-form";
import { PaymentSettingsView } from "@/features/settings/components/payment-settings-view";
import { ProfileView } from "@/features/settings/components/profile-view";
import { SchedulingSettingsView } from "@/features/settings/components/scheduling-settings-view";
import { TeamView } from "@/features/settings/components/team-view";
import { WebhookView } from "@/features/settings/components/webhook-view";

function SettingsContent() {
  const searchParams = useSearchParams();
  const { navigateReplace } = useNavigation();
  const params = useParams() ?? {};
  const tenantId = params.tenantId as string;
  const tabParam = searchParams?.get("tab");

  const activeTab = tabParam || "general";

  const handleTabChange = (value: string) => {
    navigateReplace(`/${tenantId}/settings?tab=${value}`);
  };

  return (
    <div className="flex flex-col space-y-8 lg:flex-row lg:space-x-12 lg:space-y-0">
      <Tabs
        value={activeTab}
        onValueChange={handleTabChange}
        className="flex flex-col lg:flex-row w-full space-y-6 lg:space-y-0 lg:space-x-12"
      >
        <aside className="-mx-4 lg:w-1/5">
          <TabsList className="flex flex-col h-auto items-start justify-start bg-transparent p-0 space-y-1">
            {/* Grupo: Principal */}
            <div className="w-full px-4 mb-2 mt-2">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Principal
              </h3>
            </div>

            <TabsTrigger
              value="general"
              className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
            >
              <SettingsIcon className="mr-2 h-4 w-4" />
              General
            </TabsTrigger>
            <TabsTrigger
              value="profile"
              className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
            >
              <User className="mr-2 h-4 w-4" />
              Perfil
            </TabsTrigger>
            <TabsTrigger
              value="team"
              className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
            >
              <Users className="mr-2 h-4 w-4" />
              Equipo
            </TabsTrigger>
            <TabsTrigger
              value="ai-keys"
              className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
            >
              <Key className="mr-2 h-4 w-4" />
              LLM API Key&apos;s
            </TabsTrigger>

            {/* Grupo: Ventas */}
            <div className="w-full px-4 mb-2 mt-6">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Ventas
              </h3>
            </div>

            <TabsTrigger
              value="scheduling"
              className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
            >
              <CalendarClock className="mr-2 h-4 w-4" />
              Agenda
            </TabsTrigger>
            <TabsTrigger
              value="payments"
              className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
            >
              <CreditCard className="mr-2 h-4 w-4" />
              Pagos
            </TabsTrigger>

            {/* Grupo: Desarrolladores */}
            <div className="w-full px-4 mb-2 mt-6">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Desarrolladores
              </h3>
            </div>

            <TabsTrigger
              value="webhooks"
              className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
            >
              <Webhook className="mr-2 h-4 w-4" />
              Webhooks
            </TabsTrigger>
          </TabsList>
        </aside>
        <div className="flex-1 lg:max-w-3xl">
          {/* Principal */}
          <TabsContent value="general" className="mt-0">
            <GeneralSettingsForm />
          </TabsContent>
          <TabsContent value="profile" className="space-y-6 mt-0">
            <ProfileView />
          </TabsContent>
          <TabsContent value="team" className="space-y-6 mt-0">
            <TeamView />
          </TabsContent>
          <TabsContent value="ai-keys" className="space-y-6 mt-0">
            <AIKeysForm />
          </TabsContent>

          {/* Ventas */}
          <TabsContent value="scheduling" className="mt-0">
            <SchedulingSettingsView />
          </TabsContent>
          <TabsContent value="payments" className="mt-0">
            <PaymentSettingsView />
          </TabsContent>

          {/* Desarrolladores */}
          <TabsContent value="webhooks" className="mt-0">
            <WebhookView key={tenantId} />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}

function SettingsViewInner() {
  const searchParams = useSearchParams();
  const isPopupCallback =
    typeof window !== "undefined" &&
    !!window.opener &&
    !!(searchParams?.get("code") || searchParams?.get("error"));

  if (isPopupCallback) {
    return <OAuthCallbackHandler provider="auto" />;
  }

  return (
    <div className="hidden space-y-6 p-10 pb-16 md:block">
      <div className="space-y-0.5">
        <h2 className="text-2xl font-bold tracking-tight">Configuración</h2>
        <p className="text-muted-foreground">
          Administra la configuración de tu cuenta y preferencias del sistema.
        </p>
      </div>
      <div className="border-t my-6" />
      <SettingsContent />
    </div>
  );
}

export function SettingsView() {
  return (
    <Suspense fallback={<div>Cargando configuración...</div>}>
      <SettingsViewInner />
    </Suspense>
  );
}
