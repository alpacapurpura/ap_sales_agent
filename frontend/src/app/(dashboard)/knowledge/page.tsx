import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { SafetyLayerManager } from "@/components/knowledge/safety-layer"
import { FileText, Shield, Settings, Palette } from "lucide-react"

export default function KnowledgePage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h2 className="text-3xl font-bold tracking-tight">Centro de Conocimiento</h2>
        <p className="text-muted-foreground">
          Gestiona la inteligencia, seguridad y personalidad de tu agente de ventas.
        </p>
      </div>

      <Tabs defaultValue="documents" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 lg:w-[600px]">
          <TabsTrigger value="documents" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            <span>Documentos</span>
          </TabsTrigger>
          <TabsTrigger value="safety" className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            <span>Safety Layer</span>
          </TabsTrigger>
          <TabsTrigger value="rules" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            <span>Reglas</span>
          </TabsTrigger>
          <TabsTrigger value="brand" className="flex items-center gap-2">
            <Palette className="h-4 w-4" />
            <span>Marca</span>
          </TabsTrigger>
        </TabsList>

        {/* --- DOCUMENTS TAB --- */}
        <TabsContent value="documents" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Biblioteca de Documentos</CardTitle>
              <CardDescription>
                Sube PDFs, TXT o Markdown para alimentar el cerebro RAG del agente.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Placeholder for Document Manager Component */}
              <div className="flex flex-col items-center justify-center py-12 text-center border-2 border-dashed rounded-lg">
                <div className="rounded-full bg-muted p-4 mb-4">
                  <FileText className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="text-lg font-semibold">Gestor de Documentos</h3>
                <p className="text-sm text-muted-foreground max-w-sm mt-2">
                  Aquí podrás subir, categorizar y gestionar los archivos de conocimiento.
                  (Funcionalidad en migración desde Admin Panel)
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* --- SAFETY LAYER TAB --- */}
        <TabsContent value="safety" className="space-y-4">
          <SafetyLayerManager />
        </TabsContent>

        {/* --- RULES TAB --- */}
        <TabsContent value="rules">
          <Card>
            <CardHeader>
              <CardTitle>Reglas de Negocio</CardTitle>
              <CardDescription>Configura horarios, restricciones y lógica operativa.</CardDescription>
            </CardHeader>
            <CardContent className="h-[300px] flex items-center justify-center text-muted-foreground">
              🚧 Próximamente
            </CardContent>
          </Card>
        </TabsContent>

        {/* --- BRAND TAB --- */}
        <TabsContent value="brand">
          <Card>
            <CardHeader>
              <CardTitle>Identidad de Marca</CardTitle>
              <CardDescription>Define el tono, voz y filosofía del agente.</CardDescription>
            </CardHeader>
            <CardContent className="h-[300px] flex items-center justify-center text-muted-foreground">
              🚧 Próximamente
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
