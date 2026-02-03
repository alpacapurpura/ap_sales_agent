"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { SafetyLayerManager } from "@/features/knowledge/components/safety-layer"
import { FileText, Shield, Settings, Palette } from "lucide-react"

function PlaceholderContent({ title, icon: Icon, description, content }: { title: string, icon: any, description?: string, content?: React.ReactNode }) {
  return (
    <Card className="w-full min-h-[400px]">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Icon className="h-6 w-6" />
          {title}
        </CardTitle>
        <CardDescription>{description || "Esta funcionalidad estará disponible próximamente."}</CardDescription>
      </CardHeader>
      <CardContent className="h-[200px] flex items-center justify-center text-muted-foreground bg-muted/10 rounded-md border border-dashed m-6">
        {content || "Próximamente"}
      </CardContent>
    </Card>
  );
}

export default function KnowledgePage() {
  return (
    <div className="hidden space-y-6 p-10 pb-16 md:block">
      <div className="space-y-0.5">
        <h2 className="text-2xl font-bold tracking-tight">Centro de Conocimiento</h2>
        <p className="text-muted-foreground">
          Gestiona la inteligencia, seguridad y personalidad de tu agente de ventas.
        </p>
      </div>
      <div className="border-t my-6" />

      <div className="flex flex-col space-y-8 lg:flex-row lg:space-x-12 lg:space-y-0">
        <Tabs defaultValue="documents" className="flex flex-col lg:flex-row w-full space-y-6 lg:space-y-0 lg:space-x-12">
          <aside className="-mx-4 lg:w-1/5">
            <TabsList className="flex flex-col h-auto items-start justify-start bg-transparent p-0 space-y-1">
              
              {/* Grupo: Knowledge */}
              <div className="w-full px-4 mb-2 mt-2">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Knowledge
                </h3>
              </div>
              
              <TabsTrigger 
                value="documents" 
                className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
              >
                <FileText className="mr-2 h-4 w-4" />
                Documentos
              </TabsTrigger>
              <TabsTrigger 
                value="safety" 
                className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
              >
                <Shield className="mr-2 h-4 w-4" />
                Safety Layer
              </TabsTrigger>
              <TabsTrigger 
                value="rules" 
                className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
              >
                <Settings className="mr-2 h-4 w-4" />
                Reglas
              </TabsTrigger>
              <TabsTrigger 
                value="brand" 
                className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
              >
                <Palette className="mr-2 h-4 w-4" />
                Marca
              </TabsTrigger>

            </TabsList>
          </aside>

          <div className="flex-1 lg:max-w-4xl">
            {/* --- DOCUMENTS TAB --- */}
            <TabsContent value="documents" className="mt-0">
              <PlaceholderContent 
                title="Biblioteca de Documentos" 
                icon={FileText} 
                description="Sube PDFs, TXT o Markdown para alimentar el cerebro RAG del agente."
                content={
                  <div className="flex flex-col items-center justify-center text-center">
                    <div className="rounded-full bg-muted p-4 mb-4">
                      <FileText className="h-8 w-8 text-muted-foreground" />
                    </div>
                    <h3 className="text-lg font-semibold">Gestor de Documentos</h3>
                    <p className="text-sm text-muted-foreground max-w-sm mt-2">
                      Aquí podrás subir, categorizar y gestionar los archivos de conocimiento.
                      (Funcionalidad en migración desde Admin Panel)
                    </p>
                  </div>
                }
              />
            </TabsContent>
            
            {/* --- SAFETY LAYER TAB --- */}
            <TabsContent value="safety" className="mt-0">
              <SafetyLayerManager />
            </TabsContent>

            {/* --- RULES TAB --- */}
            <TabsContent value="rules" className="mt-0">
              <PlaceholderContent 
                title="Reglas de Negocio" 
                icon={Settings} 
                description="Configura horarios, restricciones y lógica operativa."
                content="🚧 Próximamente"
              />
            </TabsContent>

            {/* --- BRAND TAB --- */}
            <TabsContent value="brand" className="mt-0">
              <PlaceholderContent 
                title="Identidad de Marca" 
                icon={Palette} 
                description="Define el tono, voz y filosofía del agente."
                content="🚧 Próximamente"
              />
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </div>
  )
}
