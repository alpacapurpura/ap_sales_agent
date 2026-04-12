"use client";

import { OnboardingWizard } from "../onboarding/onboarding-wizard";

interface BrandEmptyStateProps {
  onStartAI: () => void;
  onStartManual: () => void;
}

export function BrandEmptyState({ onStartAI, onStartManual }: BrandEmptyStateProps) {
  return (
    <OnboardingWizard
      onComplete={onStartAI}
      onManual={onStartManual}
    />
  );
}
