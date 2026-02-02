"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  MessageCircle, 
  Video, 
  Instagram, 
  MessageSquare, 
  Send, 
  MessageSquareCode, 
  Calendar, 
  Users, 
  CreditCard, 
  Webhook,
  Mail
} from "lucide-react";
import { useSearchParams, useRouter } from "next/navigation";
import { useEffect, useState, Suspense } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { WebhookView } from "@/components/settings/webhook-view";
import { TelegramView } from "@/components/connections/telegram-view";
import { GoogleCalendarView } from "@/components/connections/google-calendar-view";
import { GmailView } from "@/components/connections/gmail-view";

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

function ConnectionsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const tabParam = searchParams.get("tab");
  
  const [activeTab, setActiveTab] = useState(tabParam || "whatsapp");

  useEffect(() => {
    if (tabParam) {
      setActiveTab(tabParam);
    }
  }, [tabParam]);

  const handleTabChange = (value: string) => {
    setActiveTab(value);
    router.push(`/connections?tab=${value}`);
  };

  return (
    <div className="flex flex-col space-y-8 lg:flex-row lg:space-x-12 lg:space-y-0">
      <Tabs value={activeTab} onValueChange={handleTabChange} className="flex flex-col lg:flex-row w-full space-y-6 lg:space-y-0 lg:space-x-12">
        {/* Sidebar de Navegación Secundaria */}
        <aside className="-mx-4 lg:w-1/5">
          <TabsList className="flex flex-col h-auto items-start justify-start bg-transparent p-0 space-y-1">
            
            {/* Grupo: Canales de Venta */}
            <div className="w-full px-4 mb-2 mt-2">
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
              value="email" 
              className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
            >
              <Mail className="mr-2 h-4 w-4" />
              Correo Electrónico
            </TabsTrigger>
            <TabsTrigger 
              value="tiktok" 
              className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
            >
              <Video className="mr-2 h-4 w-4" />
              TikTok
            </TabsTrigger>
            <TabsTrigger 
              value="instagram" 
              className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
            >
              <Instagram className="mr-2 h-4 w-4" />
              Instagram
            </TabsTrigger>
            <TabsTrigger 
              value="messenger" 
              className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
            >
              <MessageSquare className="mr-2 h-4 w-4" />
              Messenger
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

            {/* Grupo: Herramientas */}
            <div className="w-full px-4 mb-2 mt-6">
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Cierre de ventas 
              </h3>
            </div>

            <TabsTrigger 
              value="calendar" 
              className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
            >
              <Calendar className="mr-2 h-4 w-4" />
              Calendario
            </TabsTrigger>
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
              Pasarela de Pagos
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

        {/* Área de Contenido Principal */}
        <div className="flex-1 lg:max-w-3xl">
          <TabsContent value="whatsapp" className="mt-0">
            <PlaceholderContent title="WhatsApp" icon={MessageCircle} />
          </TabsContent>
          <TabsContent value="email" className="mt-0">
             <GmailView />
          </TabsContent>
          <TabsContent value="tiktok" className="mt-0">
             <PlaceholderContent title="TikTok" icon={Video} />
          </TabsContent>
          <TabsContent value="instagram" className="mt-0">
             <PlaceholderContent title="Instagram" icon={Instagram} />
          </TabsContent>
          <TabsContent value="messenger" className="mt-0">
             <PlaceholderContent title="Messenger" icon={MessageSquare} />
          </TabsContent>
          <TabsContent value="telegram" className="mt-0">
             <TelegramView />
          </TabsContent>
          <TabsContent value="webwidget" className="mt-0">
             <PlaceholderContent title="Web Widget" icon={MessageSquareCode} />
          </TabsContent>
          
          <TabsContent value="calendar" className="mt-0">
             <GoogleCalendarView />
          </TabsContent>
          <TabsContent value="crm" className="mt-0">
             <PlaceholderContent title="CRM" icon={Users} />
          </TabsContent>
          <TabsContent value="payments" className="mt-0">
             <PlaceholderContent title="Pasarela de Pagos" icon={CreditCard} />
          </TabsContent>
          
          <TabsContent value="webhooks" className="mt-0">
             <WebhookView />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}

export default function ConnectionsPage() {
  const searchParams = useSearchParams();
  const [isPopupCallback, setIsPopupCallback] = useState(false);

  useEffect(() => {
    // Check if we are in a popup and have a code/error from Google
    if (window.opener && (searchParams.get("code") || searchParams.get("error"))) {
        setIsPopupCallback(true);
        const code = searchParams.get("code");
        const error = searchParams.get("error");

        if (code) {
            window.opener.postMessage({ type: "GOOGLE_OAUTH_SUCCESS", code }, window.location.origin);
        } else if (error) {
            window.opener.postMessage({ type: "GOOGLE_OAUTH_ERROR", error }, window.location.origin);
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
        <h2 className="text-2xl font-bold tracking-tight">Conexiones</h2>
        <p className="text-muted-foreground">
          Gestiona tus integraciones con canales de mensajería, herramientas y servicios externos.
        </p>
      </div>
      <div className="border-t my-6" />
      <Suspense fallback={<div>Cargando conexiones...</div>}>
        <ConnectionsContent />
      </Suspense>
    </div>
  );
}
