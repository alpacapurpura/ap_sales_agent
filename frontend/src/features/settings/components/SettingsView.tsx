"use client"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { AIKeysForm } from "@/features/settings/components/ai-keys-form"
import { ProfileView } from "@/features/settings/components/profile-view"
import { WebhookView } from "@/features/settings/components/webhook-view"
import { GeneralSettingsForm } from "@/features/settings/components/general-settings-form"
import { TeamView } from "@/features/settings/components/team-view"
import { TelegramView } from "@/features/connections/components/telegram-view"
import { GoogleWorkspaceView } from "@/features/connections/components/google-workspace-view"
import { ShopifyView } from "@/features/connections/components/shopify-view"
import { MailerLiteView } from "@/features/connections/components/mailerlite-view"
import { ManyChatView } from "@/features/connections/components/manychat-view"
import { MetaView } from "@/features/connections/components/meta-view"
import WhatsAppView from "@/features/connections/components/whatsapp-view"
import {
  Key,
  Settings as SettingsIcon,
  User,
  Webhook,
  Users,
  MessageCircle,
  Video,
  Facebook,
  Send,
  MessageSquareCode,
  CreditCard,
  Mail,
  ShoppingBag,
  Bot,
} from "lucide-react"
import { useSearchParams, useRouter, useParams } from "next/navigation"
import { useEffect, useState, Suspense } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

function PlaceholderContent({ title, icon: Icon }: { title: string, icon: any }) {
  return (
    <Card className="w-full min-h-[600px]">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Icon className="h-6 w-6" />
          {title}
        </CardTitle>
        <CardDescription>Esta funcionalidad estará disponible próximamente.</CardDescription>
      </CardHeader>
      <CardContent className="h-[400px] flex items-center justify-center text-muted-foreground bg-muted/10 rounded-md border border-dashed m-6">
        <div className="text-center">
          <Icon className="h-12 w-12 mx-auto mb-4 opacity-20" />
          <p>Próximamente</p>
        </div>
      </CardContent>
    </Card>
  );
}

function SettingsContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const params = useParams()
  const tenantId = params.tenantId as string
  const tabParam = searchParams.get("tab")
  
  const [activeTab, setActiveTab] = useState(tabParam || "general")

  useEffect(() => {
    if (tabParam) {
      setActiveTab(tabParam)
    }
  }, [tabParam])

  const handleTabChange = (value: string) => {
    setActiveTab(value)
    router.push(`/${tenantId}/settings?tab=${value}`)
  }

  return (
    <div className="flex flex-col space-y-8 lg:flex-row lg:space-x-12 lg:space-y-0">
        <Tabs value={activeTab} onValueChange={handleTabChange} className="flex flex-col lg:flex-row w-full space-y-6 lg:space-y-0 lg:space-x-12">
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

                    {/* Grupo: Canales de Venta */}
                    <div className="w-full px-4 mb-2 mt-6">
                      <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        Canales de Venta
                      </h3>
                    </div>

                    <TabsTrigger 
                      value="whatsapp" 
                      className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                    >
                      <MessageCircle className="mr-2 h-4 w-4" />
                      WhatsApp
                    </TabsTrigger>
                    <TabsTrigger 
                      value="meta" 
                      className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                    >
                      <Facebook className="mr-2 h-4 w-4" />
                      Meta Business Suite
                    </TabsTrigger>
                    <TabsTrigger 
                      value="manychat" 
                      className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                    >
                      <Bot className="mr-2 h-4 w-4" />
                      ManyChat
                    </TabsTrigger>
                    <TabsTrigger 
                      value="shopify" 
                      className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                    >
                      <ShoppingBag className="mr-2 h-4 w-4" />
                      Shopify
                    </TabsTrigger>
                    <TabsTrigger
                      value="google-workspace"
                      className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                    >
                      <Mail className="mr-2 h-4 w-4" />
                      Google Workspace
                    </TabsTrigger>
                    <TabsTrigger 
                      value="tiktok" 
                      className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                    >
                      <Video className="mr-2 h-4 w-4" />
                      TikTok
                    </TabsTrigger>
                    <TabsTrigger
                      value="telegram" 
                      className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                    >
                      <Send className="mr-2 h-4 w-4" />
                      Telegram
                    </TabsTrigger>
                    <TabsTrigger 
                      value="webwidget" 
                      className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                    >
                      <MessageSquareCode className="mr-2 h-4 w-4" />
                      Web Widget
                    </TabsTrigger>

                    {/* Grupo: Marketing */}
                    <div className="w-full px-4 mb-2 mt-6">
                      <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        Marketing
                      </h3>
                    </div>

                    <TabsTrigger 
                      value="mailerlite" 
                      className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                    >
                      <Mail className="mr-2 h-4 w-4" />
                      MailerLite
                    </TabsTrigger>

                    {/* Grupo: Cierre de ventas */}
                    <div className="w-full px-4 mb-2 mt-6">
                      <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                        Cierre de ventas 
                      </h3>
                    </div>

                    <TabsTrigger 
                      value="crm" 
                      className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                    >
                      <Users className="mr-2 h-4 w-4" />
                      CRM
                    </TabsTrigger>
                    <TabsTrigger 
                      value="payments" 
                      className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                    >
                      <CreditCard className="mr-2 h-4 w-4" />
                      Payments
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

                {/* Canales de Venta */}
                <TabsContent value="whatsapp" className="mt-0">
                  <WhatsAppView key={tenantId} />
                </TabsContent>
                <TabsContent value="meta" className="mt-0">
                  <MetaView key={tenantId} />
                </TabsContent>
                <TabsContent value="manychat" className="mt-0">
                  <ManyChatView key={tenantId} />
                </TabsContent>
                <TabsContent value="shopify" className="mt-0">
                  <ShopifyView key={tenantId} />
                </TabsContent>
                <TabsContent value="google-workspace" className="mt-0">
                  <GoogleWorkspaceView key={tenantId} />
                </TabsContent>
                <TabsContent value="tiktok" className="mt-0">
                   <PlaceholderContent key={tenantId} title="TikTok" icon={Video} />
                </TabsContent>
<TabsContent value="telegram" className="mt-0">
                   <TelegramView key={tenantId} />
                </TabsContent>
                <TabsContent value="webwidget" className="mt-0">
                   <PlaceholderContent key={tenantId} title="Web Widget" icon={MessageSquareCode} />
                </TabsContent>

                {/* Marketing */}
                <TabsContent value="mailerlite" className="mt-0">
                   <MailerLiteView key={tenantId} />
                </TabsContent>
                <TabsContent value="crm" className="mt-0">
                   <PlaceholderContent key={tenantId} title="CRM" icon={Users} />
                </TabsContent>
                <TabsContent value="payments" className="mt-0">
                   <PlaceholderContent key={tenantId} title="Payments" icon={CreditCard} />
                </TabsContent>

                {/* Desarrolladores */}
                <TabsContent value="webhooks" className="mt-0">
                   <WebhookView key={tenantId} />
                </TabsContent>
            </div>
        </Tabs>
      </div>
  )
}

function SettingsViewInner() {
  const searchParams = useSearchParams()
  const [isPopupCallback, setIsPopupCallback] = useState(false)

  useEffect(() => {
    // Check if we are in a popup and have a code/error from Google or Meta
    if (window.opener && (searchParams.get("code") || searchParams.get("error"))) {
        setIsPopupCallback(true);
        const code = searchParams.get("code");
        const error = searchParams.get("error");
        const state = searchParams.get("state");

        if (code) {
            if (state && state.startsWith("meta")) {
                window.opener.postMessage({ type: "META_OAUTH_SUCCESS", code }, window.location.origin);
            } else {
                window.opener.postMessage({ type: "GOOGLE_OAUTH_SUCCESS", code }, window.location.origin);
            }
        } else if (error) {
            if (state && state.startsWith("meta")) {
                window.opener.postMessage({ type: "META_OAUTH_ERROR", error }, window.location.origin);
            } else {
                window.opener.postMessage({ type: "GOOGLE_OAUTH_ERROR", error }, window.location.origin);
            }
        }

        // Close after a brief delay
        setTimeout(() => window.close(), 1000);
    }
  }, [searchParams]);

  if (isPopupCallback) {
      return (
          <div className="h-screen w-full flex flex-col items-center justify-center bg-background">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-4"></div>
              <p className="text-muted-foreground">Autenticando...</p>
          </div>
      );
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
  )
}

export function SettingsView() {
  return (
    <Suspense fallback={<div>Cargando configuración...</div>}>
      <SettingsViewInner />
    </Suspense>
  )
}
