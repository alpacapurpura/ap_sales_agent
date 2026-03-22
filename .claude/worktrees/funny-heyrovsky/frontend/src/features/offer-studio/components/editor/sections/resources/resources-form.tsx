"use client";

import { ChangeEvent, useState } from "react";
import { useFieldArray, UseFormReturn } from "react-hook-form";
import { SectionFormWrapper } from "../common/section-form-wrapper";
import { OfferSchema, OfferFormValues } from "../../../../types/schema";
import { AssetType } from "../../../../types";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { FormField, FormItem, FormControl, FormMessage } from "@/components/ui/form";
import { UploadCloud, FileText, Video, Image as ImageIcon, Link as LinkIcon, Trash2, Sparkles, BookOpen } from "lucide-react";

const ResourcesSchema = OfferSchema.pick({
  assets: true
});

type ResourcesFormValues = Pick<OfferFormValues, "assets">;

export interface ResourcesFormProps {
  defaultValues: Partial<OfferFormValues>;
  onSave: (data: Partial<OfferFormValues>) => Promise<void>;
  form?: any;
}

function ResourcesContent({ form }: { form: UseFormReturn<OfferFormValues> }) {
  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "assets",
  });

  const [activeTab, setActiveTab] = useState("multimedia");

  // Filtered lists (we need original indices to remove correctly)
  const multimediaFields = fields.map((f, i) => ({ ...f, index: i })).filter(f => !f.is_knowledge_base);
  const knowledgeFields = fields.map((f, i) => ({ ...f, index: i })).filter(f => f.is_knowledge_base);

  // Simulation of file upload
  const handleFileUpload = (e: ChangeEvent<HTMLInputElement>, isKnowledge: boolean) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Determine type
    let type = AssetType.URL;
    if (file.type.includes("image")) type = AssetType.IMAGE;
    else if (file.type.includes("video")) type = AssetType.VIDEO;
    else if (file.type.includes("audio")) type = AssetType.AUDIO;
    else if (file.type.includes("pdf")) type = AssetType.PDF;
    else if (file.type.includes("text") || file.name.endsWith(".md") || file.name.endsWith(".txt")) type = AssetType.TXT;

    // Create asset
    append({
        id: crypto.randomUUID(),
        type,
        name: file.name,
        url: URL.createObjectURL(file), // Temporary preview URL
        size: `${(file.size / 1024 / 1024).toFixed(2)} MB`,
        is_knowledge_base: isKnowledge,
        trigger_context: ""
    });
  };

  return (
    <div className="space-y-6">
       <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2">
             <TabsTrigger value="multimedia" className="flex items-center gap-2">
                <Video className="w-4 h-4"/> Activos de Venta
             </TabsTrigger>
             <TabsTrigger value="knowledge" className="flex items-center gap-2">
                <BookOpen className="w-4 h-4"/> Cerebro & RAG
             </TabsTrigger>
          </TabsList>

          {/* MULTIMEDIA TAB */}
          <TabsContent value="multimedia" className="space-y-4 mt-4">
             <Card className="border-dashed border-2">
                <CardContent className="pt-6 flex flex-col items-center justify-center text-center space-y-4">
                    <div className="p-3 bg-primary/10 rounded-full">
                        <Sparkles className="w-6 h-6 text-primary"/>
                    </div>
                    <div>
                        <h3 className="font-medium">Sube evidencia visual</h3>
                        <p className="text-sm text-muted-foreground">Fotos, Videos o Audios que el agente mostrará.</p>
                    </div>
                    <div className="flex gap-2">
                         <div className="relative">
                            <Button variant="outline" size="sm">Subir Archivo</Button>
                            <Input type="file" className="absolute inset-0 opacity-0 cursor-pointer" onChange={(e) => handleFileUpload(e, false)} accept="image/*,video/*,audio/*" />
                         </div>
                    </div>
                </CardContent>
             </Card>

             <div className="space-y-4">
                {multimediaFields.map((field) => (
                    <Card key={field.id} className="overflow-hidden">
                        <CardContent className="p-4 flex gap-4 items-start">
                            {/* Icon/Preview */}
                            <div className="h-16 w-16 bg-muted rounded-md flex-shrink-0 flex items-center justify-center border">
                                {field.type === AssetType.IMAGE && <ImageIcon className="w-6 h-6 text-blue-500"/>}
                                {field.type === AssetType.VIDEO && <Video className="w-6 h-6 text-red-500"/>}
                                {field.type === AssetType.AUDIO && <Sparkles className="w-6 h-6 text-purple-500"/>}
                                {field.type === AssetType.URL && <LinkIcon className="w-6 h-6 text-green-500"/>}
                            </div>
                            
                            {/* Inputs */}
                            <div className="flex-1 space-y-3">
                                <div className="flex justify-between items-start">
                                    <div>
                                        <h4 className="font-medium text-sm truncate max-w-[300px]">{field.name}</h4>
                                        <p className="text-xs text-muted-foreground">{field.type} • {field.size || "Link"}</p>
                                    </div>
                                    <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-destructive" onClick={() => remove(field.index)}>
                                        <Trash2 className="w-4 h-4"/>
                                    </Button>
                                </div>
                                
                                <FormField
                                    control={form.control}
                                    name={`assets.${field.index}.trigger_context`}
                                    render={({ field: inputField }) => (
                                        <FormItem>
                                            <FormControl>
                                                <Textarea 
                                                    placeholder="¿Cuándo debe el agente mostrar esto? Ej: 'Si preguntan por resultados...'" 
                                                    className="min-h-[60px] text-xs resize-none bg-muted/30"
                                                    {...inputField}
                                                />
                                            </FormControl>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                            </div>
                        </CardContent>
                    </Card>
                ))}
             </div>
          </TabsContent>

          {/* KNOWLEDGE TAB */}
          <TabsContent value="knowledge" className="space-y-4 mt-4">
              <Card className="bg-slate-50 dark:bg-slate-900/50">
                  <CardHeader>
                      <CardTitle className="text-base">Base de Conocimiento (RAG)</CardTitle>
                      <CardDescription>Documentos técnicos que el agente leerá para responder preguntas específicas.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                      <div className="border-2 border-dashed rounded-lg p-8 flex flex-col items-center justify-center text-center hover:bg-muted/50 transition-colors relative">
                          <UploadCloud className="w-10 h-10 text-muted-foreground mb-2"/>
                          <p className="font-medium text-sm">Arrastra PDFs o TXTs aquí</p>
                          <p className="text-xs text-muted-foreground mb-4">Máx 10MB por archivo</p>
                          <Input type="file" className="absolute inset-0 opacity-0 cursor-pointer" onChange={(e) => handleFileUpload(e, true)} accept=".pdf,.txt,.md" />
                          <Button size="sm" variant="secondary">Seleccionar Documentos</Button>
                      </div>

                      <div className="space-y-2">
                          {knowledgeFields.map((field) => (
                              <div key={field.id} className="flex items-center justify-between p-3 bg-background border rounded-md shadow-sm">
                                  <div className="flex items-center gap-3">
                                      <FileText className="w-5 h-5 text-amber-500"/>
                                      <div>
                                          <p className="text-sm font-medium">{field.name}</p>
                                          <p className="text-xs text-muted-foreground">{field.size}</p>
                                      </div>
                                  </div>
                                  <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => remove(field.index)}>
                                      <Trash2 className="w-4 h-4"/>
                                  </Button>
                              </div>
                          ))}
                          {knowledgeFields.length === 0 && (
                              <p className="text-xs text-center text-muted-foreground italic py-2">No hay documentos cargados. El agente usará solo su conocimiento general.</p>
                          )}
                      </div>
                  </CardContent>
              </Card>
          </TabsContent>
       </Tabs>
    </div>
  );
}

export function ResourcesForm({ defaultValues: propValues, onSave }: ResourcesFormProps) {
  const defaultValues: ResourcesFormValues = {
    assets: propValues?.assets || []
  };

  const handleSave = async (data: ResourcesFormValues) => {
    await onSave(data);
  };

  return (
    <SectionFormWrapper<ResourcesFormValues>
      schema={ResourcesSchema}
      defaultValues={defaultValues}
      onSubmit={handleSave}
    >
      {(form) => (
        <ResourcesContent form={form as unknown as UseFormReturn<OfferFormValues>} />
      )}
    </SectionFormWrapper>
  );
}
