"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { VoiceForm } from "./voice-form";
import { useBrandSettings } from "@/features/brand/hooks/useBrandSettings";

export function VoiceManager() {
  const { getToken } = useAuth();
  // Although we don't use settings directly, we might in the future.
  // The user requested usage of useBrandSettings for consistency.
  const { loading: settingsLoading } = useBrandSettings();

  const [analyzing, setAnalyzing] = useState(false);
  const [step, setStep] = useState<"upload" | "result">("upload");
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  const handleAnalyze = async (text?: string, file?: File) => {
    setAnalyzing(true);
    setError("");

    try {
      const token = await getToken();
      const formData = new FormData();
      if (text) formData.append("text_input", text);
      if (file) formData.append("file", file);

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/onboarding/analyze-style`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Analysis failed");
      }

      const data = await res.json();
      setResult(data);
      setStep("result");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleReset = () => {
    setStep("upload");
    setResult(null);
    setError("");
  };

  if (settingsLoading) return null; // Or a loader

  return (
    <VoiceForm
      onAnalyze={handleAnalyze}
      onReset={handleReset}
      loading={analyzing}
      error={error}
      result={result}
      step={step}
    />
  );
}
