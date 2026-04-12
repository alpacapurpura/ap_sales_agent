import { useState, useCallback, useMemo } from "react";

export type OnboardingSource = "website" | "documents" | "interview";

export type WizardStep =
  | "source-picker"
  | "website"
  | "documents"
  | "processing"
  | "gap-review"
  | "interview-placeholder";

export function useOnboardingWizard() {
  const [currentStep, setCurrentStep] = useState<WizardStep>("source-picker");
  const [selectedSources, setSelectedSources] = useState<OnboardingSource[]>([]);
  const [url, setUrl] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);

  const toggleSource = useCallback((source: OnboardingSource) => {
    setSelectedSources((prev) =>
      prev.includes(source) ? prev.filter((s) => s !== source) : [...prev, source]
    );
  }, []);

  const addFiles = useCallback((newFiles: File[]) => {
    setFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const removeFile = useCallback((index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const stepSequence = useMemo<WizardStep[]>(() => {
    const hasWebsite = selectedSources.includes("website");
    const hasDocs = selectedSources.includes("documents");
    const hasInterview = selectedSources.includes("interview");
    const hasExtraction = hasWebsite || hasDocs;

    if (hasInterview && !hasExtraction) {
      return ["source-picker", "interview-placeholder"];
    }

    const steps: WizardStep[] = ["source-picker"];
    if (hasWebsite) steps.push("website");
    if (hasDocs) steps.push("documents");
    if (hasExtraction) {
      steps.push("processing");
      steps.push("gap-review");
    }
    return steps;
  }, [selectedSources]);

  const currentStepIndex = stepSequence.indexOf(currentStep);
  const totalSteps = stepSequence.length;

  const next = useCallback(() => {
    const idx = stepSequence.indexOf(currentStep);
    if (idx < stepSequence.length - 1) {
      setCurrentStep(stepSequence[idx + 1]);
    }
  }, [currentStep, stepSequence]);

  const back = useCallback(() => {
    const idx = stepSequence.indexOf(currentStep);
    if (idx > 0) {
      setCurrentStep(stepSequence[idx - 1]);
    }
  }, [currentStep, stepSequence]);

  const reset = useCallback(() => {
    setCurrentStep("source-picker");
    setSelectedSources([]);
    setUrl("");
    setFiles([]);
    setJobId(null);
  }, []);

  return {
    currentStep,
    selectedSources,
    url,
    files,
    jobId,
    totalSteps,
    currentStepIndex,
    toggleSource,
    setUrl,
    addFiles,
    removeFile,
    setJobId,
    next,
    back,
    reset,
  };
}
