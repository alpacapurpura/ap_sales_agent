"use client";

import { OfferDashboard } from "@/components/offer-studio/offer-dashboard";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Package, Briefcase, GraduationCap, Repeat } from "lucide-react";

function PlaceholderContent({ title, icon: Icon }: { title: string, icon: any }) {
  return (
    <Card className="w-full min-h-[400px]">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Icon className="h-6 w-6" />
          {title}
        </CardTitle>
        <CardDescription>Esta funcionalidad estará disponible próximamente.</CardDescription>
      </CardHeader>
      <CardContent className="h-[200px] flex items-center justify-center text-muted-foreground bg-muted/10 rounded-md border border-dashed m-6">
        Próximamente
      </CardContent>
    </Card>
  );
}

export default function OfferStudioPage() {
  return (
    <div className="hidden space-y-6 p-10 pb-16 md:block">
      <div className="space-y-0.5">
        <h2 className="text-2xl font-bold tracking-tight">Ecosistema de Ofertas</h2>
        <p className="text-muted-foreground">
          Gestiona tus productos y personaliza la IA para cada nicho.
        </p>
      </div>
      <div className="border-t my-6" />

      <div className="flex flex-col space-y-8 lg:flex-row lg:space-x-12 lg:space-y-0">
        <Tabs defaultValue="services" className="flex flex-col lg:flex-row w-full space-y-6 lg:space-y-0 lg:space-x-12">
          <aside className="-mx-4 lg:w-1/5">
            <TabsList className="flex flex-col h-auto items-start justify-start bg-transparent p-0 space-y-1">
              
              {/* Grupo: Offer */}
              <div className="w-full px-4 mb-2 mt-2">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Offer
                </h3>
              </div>
              
              <TabsTrigger 
                value="products" 
                className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
              >
                <Package className="mr-2 h-4 w-4" />
                Productos
              </TabsTrigger>
              <TabsTrigger 
                value="services" 
                className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
              >
                <Briefcase className="mr-2 h-4 w-4" />
                Servicios
              </TabsTrigger>
              <TabsTrigger 
                value="programs" 
                className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
              >
                <GraduationCap className="mr-2 h-4 w-4" />
                Programas
              </TabsTrigger>
              <TabsTrigger 
                value="subscriptions" 
                className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
              >
                <Repeat className="mr-2 h-4 w-4" />
                Suscripciones
              </TabsTrigger>

            </TabsList>
          </aside>

          <div className="flex-1 lg:max-w-4xl">
            <TabsContent value="products" className="mt-0">
              <PlaceholderContent title="Productos" icon={Package} />
            </TabsContent>
            
            <TabsContent value="services" className="mt-0">
              <PlaceholderContent title="Servicios" icon={Briefcase} />
            </TabsContent>

            <TabsContent value="programs" className="mt-0">
              <Card className="w-full min-h-[600px]">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <GraduationCap className="h-6 w-6" />
                    Programas
                  </CardTitle>
                  <CardDescription>Gestiona tus programas educativos y formaciones.</CardDescription>
                </CardHeader>
                <CardContent>
                  <OfferDashboard />
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="subscriptions" className="mt-0">
              <PlaceholderContent title="Suscripciones" icon={Repeat} />
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </div>
  );
}
