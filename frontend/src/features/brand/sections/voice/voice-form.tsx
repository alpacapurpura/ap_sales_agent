"use client";

import { useState } from "react";
import { Upload, FileText, CheckCircle, Loader2, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export interface VoiceAnalysisResult {
  style_profile?: {
    tone?: string;
    signature_phrases?: string[];
    response_structure?: string;
  };
  simulation_examples?: string[];
}

interface VoiceFormProps {
  onAnalyze: (text?: string, file?: File) => Promise<void>;
  onReset: () => void;
  loading: boolean;
  error?: string;
  result?: VoiceAnalysisResult;
  step: "upload" | "result";
}

export function VoiceForm({ onAnalyze, onReset, loading, error, result, step }: VoiceFormProps) {
  const [textInput, setTextInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [localError, setLocalError] = useState("");

  const handleAnalyzeClick = () => {
    if (!textInput && !file) {
      setLocalError("Por favor, proporciona texto o un archivo.");
      return;
    }
    setLocalError("");
    onAnalyze(textInput || undefined, file || undefined);
  };

  return (
    <div className="space-y-6">
      {step === "upload" && (
        <Card className="border-none shadow-none">
          <CardHeader className="px-0 pt-0">
            <CardTitle>Clonación de Estilo</CardTitle>
            <CardDescription>
              Sube tus mejores chats para que Visionaria aprenda a hablar exactamente como tú. Pega
              un historial de chat (WhatsApp/Email) o sube un archivo .txt exportado.
            </CardDescription>
          </CardHeader>
          <CardContent className="px-0 space-y-6">
            {(error || localError) && (
              <Alert variant="destructive">
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error || localError}</AlertDescription>
              </Alert>
            )}

            <Tabs defaultValue="paste" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="paste">Pegar Texto</TabsTrigger>
                <TabsTrigger value="file">Subir Archivo</TabsTrigger>
              </TabsList>

              <TabsContent value="paste" className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>Historial de Chat</Label>
                  <Textarea
                    placeholder="[10:00] Yo: Hola cliente... [10:01] Cliente: Hola..."
                    className="min-h-[200px] font-mono text-sm"
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Recomendado: 20-50 mensajes tuyos para capturar tu esencia.
                  </p>
                </div>
              </TabsContent>

              <TabsContent value="file" className="space-y-4 py-4">
                <div className="flex items-center justify-center w-full">
                  <label className="flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-lg cursor-pointer hover:bg-muted/50">
                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                      <Upload className="w-8 h-8 mb-4 text-muted-foreground" />
                      <p className="mb-2 text-sm text-muted-foreground">
                        <span className="font-semibold">Click para subir</span> o arrastra
                      </p>
                      <p className="text-xs text-muted-foreground">TXT, PDF (Max 5MB)</p>
                    </div>
                    <Input
                      type="file"
                      className="hidden"
                      onChange={(e) => setFile(e.target.files?.[0] || null)}
                    />
                  </label>
                </div>
                {file && (
                  <div className="flex items-center gap-2 p-2 border rounded bg-muted/20">
                    <FileText className="w-4 h-4" />
                    <span className="text-sm font-medium">{file.name}</span>
                  </div>
                )}
              </TabsContent>
            </Tabs>

            <Button onClick={handleAnalyzeClick} disabled={loading} className="w-full">
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {loading
                ? "Analizando (The Janitor -> Psychologist -> Architect)..."
                : "Analizar Estilo"}
            </Button>
          </CardContent>
        </Card>
      )}

      {step === "result" && result && (
        <div className="space-y-6">
          <Alert className="bg-green-50 border-green-200">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertTitle className="text-green-800">Análisis Completado</AlertTitle>
            <AlertDescription className="text-green-700">
              Hemos creado tu perfil de estilo y configurado tu clon digital.
            </AlertDescription>
          </Alert>

          <div className="grid gap-6 md:grid-cols-2">
            {/* Style Profile Card */}
            <Card>
              <CardHeader>
                <CardTitle>Perfil Psicológico (The Psychologist)</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label className="text-xs uppercase text-muted-foreground">Tono Detectado</Label>
                  <p className="font-medium">{result.style_profile?.tone}</p>
                </div>
                <div>
                  <Label className="text-xs uppercase text-muted-foreground">
                    Muletillas (Signature Phrases)
                  </Label>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {result.style_profile?.signature_phrases?.map((p: string, i: number) => (
                      <Badge key={i} variant="secondary">
                        {p}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <Label className="text-xs uppercase text-muted-foreground">Estructura</Label>
                  <p className="text-sm text-muted-foreground">
                    {result.style_profile?.response_structure}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Simulation Card */}
            <Card className="bg-slate-50 border-slate-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="w-5 h-5" />
                  Simulación (The Simulator)
                </CardTitle>
                <CardDescription>
                  Así respondería tu clon a: &quot;Hola, me interesa pero es caro.&quot;
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {result.simulation_examples?.map((ex: string, i: number) => (
                  <div key={i} className="p-3 bg-white rounded-lg shadow-sm border text-sm">
                    &quot;{ex}&quot;
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          <Button onClick={onReset} variant="outline" className="w-full">
            Volver a intentar
          </Button>
        </div>
      )}
    </div>
  );
}
