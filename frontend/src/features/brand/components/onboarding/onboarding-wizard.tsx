"use client";

import { useOnboardingWizard } from "../../hooks/useOnboardingWizard";
import { useBrandSettings } from "../../hooks/useBrandSettings";
import { WizardProgressBar } from "./wizard-progress-bar";
import { StepSourcePicker } from "./step-source-picker";
import { StepWebsite } from "./step-website";
import { StepDocuments } from "./step-documents";
import { StepProcessing } from "./step-processing";
import { StepGapReview } from "./step-gap-review";

interface OnboardingWizardProps {
  onComplete: () => void;
  onManual: () => void;
}

export function OnboardingWizard({ onComplete, onManual }: OnboardingWizardProps) {
  const wizard = useOnboardingWizard();
  const { settings, refetch } = useBrandSettings();

  const handleProcessingComplete = async () => {
    await refetch();
    wizard.next(); // → gap-review
  };

  return (
    <div className="flex min-h-[calc(100vh-8rem)] flex-col items-center justify-center px-6 py-12">
      {wizard.currentStep !== "source-picker" && (
        <div className="mb-8 w-full max-w-md">
          <WizardProgressBar
            currentIndex={wizard.currentStepIndex}
            totalSteps={wizard.totalSteps}
          />
        </div>
      )}

      {wizard.currentStep === "source-picker" && (
        <StepSourcePicker
          selectedSources={wizard.selectedSources}
          onToggle={wizard.toggleSource}
          onNext={wizard.next}
          onManual={onManual}
        />
      )}

      {wizard.currentStep === "website" && (
        <StepWebsite
          url={wizard.url}
          onUrlChange={wizard.setUrl}
          onNext={wizard.next}
          onBack={wizard.back}
        />
      )}

      {wizard.currentStep === "documents" && (
        <StepDocuments
          files={wizard.files}
          onAddFiles={wizard.addFiles}
          onRemoveFile={wizard.removeFile}
          onNext={wizard.next}
          onBack={wizard.back}
        />
      )}

      {wizard.currentStep === "processing" && (
        <StepProcessing
          url={wizard.url}
          files={wizard.files}
          jobId={wizard.jobId}
          onJobStarted={wizard.setJobId}
          onComplete={handleProcessingComplete}
          onBack={wizard.back}
        />
      )}

      {wizard.currentStep === "gap-review" && settings && (
        <StepGapReview settings={settings} onFinish={onComplete} />
      )}

      {wizard.currentStep === "interview-placeholder" && (
        <div className="mx-auto max-w-md animate-in fade-in text-center">
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 text-3xl">
            💬
          </div>
          <h2 className="text-2xl font-bold text-foreground">Entrevista IA</h2>
          <p className="mt-3 text-muted-foreground">
            Próximamente podrás completar tu marca conversando con nuestra IA.
            Por ahora, usa la configuración manual.
          </p>
          <button
            type="button"
            onClick={onManual}
            className="mt-6 text-sm text-primary underline-offset-4 hover:underline"
          >
            Ir a configuración manual →
          </button>
        </div>
      )}
    </div>
  );
}
