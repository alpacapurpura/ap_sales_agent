"use client";

import { useAuth } from "@clerk/nextjs";
import { Save, Loader2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { analyzeVoiceStyle } from "@/features/brand/api/voice-api";
import { useBrandSettings } from "@/features/brand/hooks/use-brand-settings";

import { VoiceForm } from "./voice-form";

import type { VoiceAnalysisResult } from "./voice-form";

export function VoiceManager() {
  const { getToken } = useAuth();
  const { settings, loading: settingsLoading, updateIdentity } = useBrandSettings();

  const [analyzing, setAnalyzing] = useState(false);
  const [step, setStep] = useState<"upload" | "result">("upload");
  const [result, setResult] = useState<VoiceAnalysisResult | undefined>(undefined);
  const [error, setError] = useState("");
  const [voiceTone, setVoiceTone] = useState<string | null>(null);
  const [savingTone, setSavingTone] = useState(false);

  // Derive current voice_tone from settings or local state
  const currentVoiceTone = voiceTone ?? settings?.identity?.voice_tone ?? "";

  const handleAnalyze = async (text?: string, file?: File) => {
    setAnalyzing(true);
    setError("");

    try {
      const token = await getToken();
      const formData = new FormData();
      if (text) formData.append("text_input", text);
      if (file) formData.append("file", file);

      const data = (await analyzeVoiceStyle(token, formData)) as VoiceAnalysisResult;
      setResult(data);
      setStep("result");

      // Auto-update voice_tone with detected tone
      if (data.style_profile?.tone) {
        setVoiceTone(data.style_profile.tone);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleReset = () => {
    setStep("upload");
    setResult(undefined);
    setError("");
  };

  const handleSaveVoiceTone = async () => {
    setSavingTone(true);
    try {
      await updateIdentity({
        ...settings?.identity,
        voice_tone: currentVoiceTone,
      });
    } finally {
      setSavingTone(false);
    }
  };

  if (settingsLoading) return null;

  return (
    <div className="space-y-8">
      {/* Voice Tone Field */}
      <div className="space-y-3">
        <Label htmlFor="voice_tone" className="text-base font-semibold">
          Tono de Voz
        </Label>
        <Textarea
          id="voice_tone"
          value={currentVoiceTone}
          onChange={(e) => setVoiceTone(e.target.value)}
          placeholder="Ej: Conversacional, aspiracional, directo con toques de humor"
          className="min-h-[80px]"
        />
        <p className="text-xs text-muted-foreground">
          Describe como habla tu marca. El SDR usara este tono en todas sus conversaciones. Si
          ejecutas la Clonacion de Estilo abajo, este campo se actualiza automaticamente.
        </p>
        {voiceTone !== null && voiceTone !== (settings?.identity?.voice_tone ?? "") && (
          <Button onClick={handleSaveVoiceTone} disabled={savingTone} size="sm">
            {savingTone ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Save className="mr-2 h-4 w-4" />
            )}
            Guardar Tono
          </Button>
        )}
      </div>

      {/* Voice Cloning */}
      <div className="border-t pt-6">
        <VoiceForm
          onAnalyze={handleAnalyze}
          onReset={handleReset}
          loading={analyzing}
          error={error}
          result={result}
          step={step}
        />
      </div>
    </div>
  );
}
