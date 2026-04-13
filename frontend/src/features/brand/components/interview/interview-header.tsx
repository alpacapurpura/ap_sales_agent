"use client";

/**
 * Brand Interview Header — backward-compatible re-export.
 *
 * Wraps the generic InterviewHeader from copilot with brand-specific
 * block labels and title.
 */

import { InterviewHeader as GenericInterviewHeader } from "@/features/copilot/components/interview/interview-header";

const BRAND_BLOCK_LABELS: Record<string, string> = {
  identidad: "Identidad",
  posicionamiento: "Posicionamiento",
  narrativa: "Narrativa",
  publico: "Público",
  identidad_creativa: "Identidad Creativa",
};

interface InterviewHeaderProps {
  currentBlockLabel: string;
  blocksCompleted: number;
  totalBlocks: number;
}

export function InterviewHeader({
  currentBlockLabel,
  blocksCompleted,
  totalBlocks,
}: InterviewHeaderProps) {
  return (
    <GenericInterviewHeader
      currentBlockLabel={currentBlockLabel}
      blocksCompleted={blocksCompleted}
      totalBlocks={totalBlocks}
      blockLabels={BRAND_BLOCK_LABELS}
      title="Cocreando tu Marca"
    />
  );
}
