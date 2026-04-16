"use client";

import { useAuth } from "@clerk/nextjs";
import { Loader2, AlertCircle, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

import { brandApi } from "../../api";

interface StepProcessingProps {
  url: string;
  files: File[];
  jobId: string | null;
  onJobStarted: (jobId: string) => void;
  onComplete: () => void;
  onBack: () => void;
}

export function StepProcessing({
  url,
  files,
  jobId,
  onJobStarted,
  onComplete,
  onBack,
}: StepProcessingProps) {
  const { getToken } = useAuth();
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState("Preparando extracción...");
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const activeJobRef = useRef<string | null>(jobId);

  const startExtraction = useCallback(async () => {
    setError(null);

    try {
      const token = await getToken();
      if (!token) throw new Error("No auth token");

      const formData = new FormData();
      formData.append("mode", "initial");

      if (url) formData.append("url", url);
      for (const file of files) {
        formData.append("files", file);
      }

      const result = await brandApi.extractFullBrand(formData, token);
      activeJobRef.current = result.job_id;
      onJobStarted(result.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al iniciar extracción");
    }
  }, [url, files, getToken, onJobStarted]);

  // Poll for status
  useEffect(() => {
    const currentJobId = activeJobRef.current;
    if (!currentJobId) return;

    pollRef.current = setInterval(async () => {
      try {
        const token = await getToken();
        if (!token) return;

        const status = await brandApi.pollExtractionStatus(currentJobId, token);
        setProgress(status.progress);
        if (status.stage) setStage(status.stage);

        if (status.status === "completed") {
          if (pollRef.current) clearInterval(pollRef.current);
          setProgress(100);
          setStage("¡Extracción completada!");
          setTimeout(onComplete, 800);
        }

        if (status.status === "failed") {
          if (pollRef.current) clearInterval(pollRef.current);
          setError(status.error || "La extracción falló");
        }
      } catch {
        // Token refresh may fail temporarily, keep polling
      }
    }, 3000);

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [jobId, getToken, onComplete]);

  // Auto-start extraction once on mount if no jobId
  const hasStartedRef = useRef(false);
  useEffect(() => {
    if (!jobId && !hasStartedRef.current) {
      hasStartedRef.current = true;
      void startExtraction();
    }
  }, [jobId, startExtraction]);

  return (
    <div className="mx-auto max-w-md animate-in fade-in duration-300">
      <div className="mb-10 text-center">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
        <h2 className="text-2xl font-bold text-foreground">Analizando tu marca</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Esto puede tomar un par de minutos. No cierres esta ventana.
        </p>
      </div>

      <div className="space-y-3">
        <Progress value={progress} className="h-2" />
        <p className="text-center text-sm text-muted-foreground">{stage}</p>
      </div>

      {error && (
        <Alert variant="destructive" className="mt-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="mt-8 flex justify-center gap-3">
        {error && (
          <>
            <Button variant="ghost" onClick={onBack}>
              Atrás
            </Button>
            <Button onClick={startExtraction} className="gap-2">
              <RefreshCw className="h-4 w-4" />
              Reintentar
            </Button>
          </>
        )}
      </div>
    </div>
  );
}
