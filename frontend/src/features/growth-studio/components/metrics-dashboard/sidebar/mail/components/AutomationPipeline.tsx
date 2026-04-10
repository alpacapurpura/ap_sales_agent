'use client';

import { Clock, Sparkles, AlertTriangle, TrendingDown } from 'lucide-react';

import { cn } from '@/lib/utils';
import {
  computeDropoff,
  diagnoseStep,
  findBestStep,
  findAttentionStep,
} from '../../../../../utils/automation-health';
import { AUTOMATION_METRIC_INFO } from '../../../../../utils/automation-metric-info';
import type { AutomationStep } from '../../../../../types/mail-types';
import { MetricInfoTooltip } from './MetricInfoTooltip';

interface AutomationPipelineProps {
  steps: AutomationStep[];
  onStepClick: (step: AutomationStep) => void;
}

/**
 * Horizontal visual pipeline of an automation's email sequence.
 *
 * Renders each email as a card with key metrics, connectors between steps
 * showing delay and drop-off, best/attention badges, and an AI insight
 * summary computed from the deterministic diagnosis rules.
 */
export function AutomationPipeline({
  steps,
  onStepClick,
}: AutomationPipelineProps) {
  const emailSteps = steps.filter((s) => s.type === 'email');

  if (emailSteps.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border/40 bg-muted/10 py-8 text-center">
        <p className="text-xs text-muted-foreground">
          Sin pasos registrados para esta automatización.
        </p>
      </div>
    );
  }

  const bestStep = findBestStep(emailSteps);
  const attentionStep = findAttentionStep(emailSteps);
  const insights = computeSequenceInsights(emailSteps);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold text-muted-foreground">
          Secuencia de emails — {emailSteps.length} paso
          {emailSteps.length === 1 ? '' : 's'}
        </h4>
        {insights.headline && (
          <span className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
            {insights.headlineIcon}
            {insights.headline}
          </span>
        )}
      </div>

      {/* Horizontal pipeline */}
      <div className="flex items-stretch gap-0 overflow-x-auto pb-2">
        {steps.map((step, idx) => {
          if (step.type === 'delay') {
            return <DelayConnector key={step.stepId} step={step} />;
          }

          // Email step
          const prevEmailStep = findPreviousEmail(steps, idx);
          const dropoff = prevEmailStep
            ? computeDropoff(prevEmailStep.emailsSent, step.emailsSent)
            : null;

          return (
            <div key={step.stepId} className="flex items-stretch">
              {prevEmailStep && !hasDelayBefore(steps, idx) && (
                <StepConnector dropoff={dropoff} />
              )}
              <EmailNode
                step={step}
                isBest={bestStep?.stepId === step.stepId}
                isAttention={attentionStep?.stepId === step.stepId}
                onClick={() => onStepClick(step)}
              />
            </div>
          );
        })}
      </div>

      {/* Funnel bar */}
      <FunnelBar steps={emailSteps} />

      {/* AI insight */}
      {insights.messages.length > 0 && (
        <div
          data-testid="automation-ai-insight"
          className="rounded-lg border border-primary/20 bg-primary/5 px-4 py-3 flex gap-2.5"
        >
          <Sparkles className="h-4 w-4 text-primary mt-0.5 shrink-0" />
          <div className="text-[12px] text-muted-foreground leading-relaxed space-y-1">
            {insights.messages.map((msg, i) => (
              <p key={i}>{msg}</p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Sub-components ─────────────────────────────────────────────────

interface EmailNodeProps {
  step: AutomationStep;
  isBest: boolean;
  isAttention: boolean;
  onClick: () => void;
}

function EmailNode({ step, isBest, isAttention, onClick }: EmailNodeProps) {
  const openClass =
    step.openRate >= 50
      ? 'text-emerald-500'
      : step.openRate >= 30
        ? 'text-amber-500'
        : 'text-red-500';
  const clickClass =
    step.clickRate >= 5
      ? 'text-emerald-500'
      : step.clickRate >= 2
        ? 'text-amber-500'
        : 'text-red-500';

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'relative w-[190px] shrink-0 rounded-lg border bg-card p-3.5 text-left transition-all cursor-pointer',
        'hover:border-primary hover:shadow-[0_0_0_1px_hsl(var(--primary)),0_4px_20px_rgba(99,102,241,0.15)]',
        isBest && 'border-emerald-500 shadow-[0_0_0_1px_rgba(16,185,129,0.3)]',
        isAttention &&
          !isBest &&
          'border-red-500 shadow-[0_0_0_1px_rgba(239,68,68,0.2)]',
      )}
    >
      {isBest && (
        <span className="absolute -top-2 right-3 rounded-full bg-emerald-500 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide text-black">
          ★ Mejor
        </span>
      )}
      {isAttention && !isBest && (
        <span className="absolute -top-2 right-3 rounded-full bg-red-500 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide text-white">
          ⚡ Atención
        </span>
      )}

      <div className="flex items-center justify-between text-[9px] uppercase tracking-wide text-muted-foreground">
        <span>Email {step.stepNumber}</span>
        <span>{step.emailsSent} enviados</span>
      </div>
      <p className="mt-1 truncate text-xs font-medium">
        {step.subject || '(sin asunto)'}
      </p>

      <div className="mt-2.5 grid grid-cols-2 gap-1.5">
        <div className="rounded bg-muted/20 py-1 text-center">
          <p className={cn('text-sm font-bold tabular-nums', openClass)}>
            {step.openRate.toFixed(1)}%
          </p>
          <div className="flex items-center justify-center gap-0.5 text-[9px] uppercase text-muted-foreground">
            Open
            <MetricInfoTooltip
              info={AUTOMATION_METRIC_INFO.stepOpen}
              iconSize="xs"
            />
          </div>
        </div>
        <div className="rounded bg-muted/20 py-1 text-center">
          <p className={cn('text-sm font-bold tabular-nums', clickClass)}>
            {step.clickRate.toFixed(1)}%
          </p>
          <div className="flex items-center justify-center gap-0.5 text-[9px] uppercase text-muted-foreground">
            Click
            <MetricInfoTooltip
              info={AUTOMATION_METRIC_INFO.stepClick}
              iconSize="xs"
            />
          </div>
        </div>
      </div>
    </button>
  );
}

interface StepConnectorProps {
  dropoff: number | null;
}

function StepConnector({ dropoff }: StepConnectorProps) {
  const dropoffClass =
    dropoff === null
      ? 'text-muted-foreground'
      : dropoff < 10
        ? 'text-emerald-500'
        : dropoff < 30
          ? 'text-amber-500'
          : 'text-red-500';

  return (
    <div className="flex min-w-[72px] flex-col items-center justify-center px-2">
      <div className="relative h-0.5 w-full bg-border">
        <span className="absolute -right-1 -top-1 h-0 w-0 border-y-[4px] border-l-[6px] border-y-transparent border-l-border" />
      </div>
      <div className="mt-1.5 text-center space-y-0.5">
        {dropoff !== null && (
          <p
            className={cn(
              'flex items-center justify-center gap-0.5 text-[10px] font-semibold whitespace-nowrap',
              dropoffClass,
            )}
          >
            −{dropoff}%
            <MetricInfoTooltip info={AUTOMATION_METRIC_INFO.dropoff} iconSize="xs" />
          </p>
        )}
      </div>
    </div>
  );
}

const DELAY_UNIT_LABELS: Record<string, [string, string]> = {
  minutes: ['minuto', 'minutos'],
  hours: ['hora', 'horas'],
  days: ['día', 'días'],
  weeks: ['semana', 'semanas'],
};

function formatDelayLabel(value: number | null, unit: string | null): string {
  const n = value ?? 0;
  if (!unit) return `${n}`;
  const labels = DELAY_UNIT_LABELS[unit];
  if (!labels) return `${n} ${unit}`;
  return `${n} ${n === 1 ? labels[0] : labels[1]}`;
}

function DelayConnector({ step }: { step: AutomationStep }) {
  return (
    <div className="flex min-w-[72px] flex-col items-center justify-center px-2">
      <div className="relative h-0.5 w-full bg-border">
        <span className="absolute -right-1 -top-1 h-0 w-0 border-y-[4px] border-l-[6px] border-y-transparent border-l-border" />
      </div>
      <p className="mt-1.5 flex items-center gap-1 text-[10px] text-muted-foreground whitespace-nowrap">
        <Clock className="h-2.5 w-2.5" />
        {formatDelayLabel(step.delayValue, step.delayUnit)}
      </p>
    </div>
  );
}

interface FunnelBarProps {
  steps: AutomationStep[];
}

function FunnelBar({ steps }: FunnelBarProps) {
  if (steps.length === 0) return null;
  const maxSent = Math.max(...steps.map((s) => s.emailsSent), 1);

  return (
    <div>
      <div className="flex h-1.5 overflow-hidden rounded bg-muted/20">
        {steps.map((s) => {
          const width = (s.emailsSent / maxSent) * 100;
          const color =
            s.openRate >= 50
              ? 'bg-emerald-500/70'
              : s.openRate >= 30
                ? 'bg-amber-500/70'
                : 'bg-red-500/70';
          return (
            <div
              key={s.stepId}
              className={cn('h-full transition-all', color)}
              style={{ width: `${width}%` }}
            />
          );
        })}
      </div>
      <div className="mt-1 flex justify-between text-[10px] text-muted-foreground">
        <span>{steps[0].emailsSent} enviaron primer email</span>
        <span>{steps[steps.length - 1].emailsSent} recibieron último</span>
      </div>
    </div>
  );
}

// ─── Helpers ────────────────────────────────────────────────────────

function findPreviousEmail(
  steps: AutomationStep[],
  currentIdx: number,
): AutomationStep | null {
  for (let i = currentIdx - 1; i >= 0; i--) {
    if (steps[i].type === 'email') return steps[i];
  }
  return null;
}

function hasDelayBefore(steps: AutomationStep[], currentIdx: number): boolean {
  if (currentIdx === 0) return false;
  return steps[currentIdx - 1].type === 'delay';
}

interface SequenceInsights {
  headline: string | null;
  headlineIcon: React.ReactNode;
  messages: string[];
}

function computeSequenceInsights(emailSteps: AutomationStep[]): SequenceInsights {
  const messages: string[] = [];
  let headline: string | null = null;
  let headlineIcon: React.ReactNode = null;

  if (emailSteps.length === 0) {
    return { headline: null, headlineIcon: null, messages: [] };
  }

  // Aggregate per-step diagnosis
  for (let i = 0; i < emailSteps.length; i++) {
    const prev = i > 0 ? emailSteps[i - 1] : undefined;
    const stepInsights = diagnoseStep(emailSteps[i], prev);
    for (const insight of stepInsights) {
      const prefix = `Email ${emailSteps[i].stepNumber}:`;
      messages.push(`${prefix} ${insight}`);
    }
  }

  // Compute headline
  const totalEmailSent = emailSteps.reduce((sum, s) => sum + s.emailsSent, 0);
  if (totalEmailSent > 0) {
    const firstSent = emailSteps[0].emailsSent;
    const lastSent = emailSteps[emailSteps.length - 1].emailsSent;
    if (firstSent > 0 && lastSent / firstSent < 0.5 && emailSteps.length > 1) {
      const dropPct = Math.round((1 - lastSent / firstSent) * 100);
      headline = `Engagement cae ${dropPct}% a lo largo de la secuencia`;
      headlineIcon = <TrendingDown className="h-3 w-3 text-red-500" />;
    } else if (messages.length === 0) {
      headline = 'Secuencia saludable — replica este formato';
      headlineIcon = <Sparkles className="h-3 w-3 text-emerald-500" />;
    } else {
      headline = `${messages.length} oportunidad${messages.length === 1 ? '' : 'es'} de mejora`;
      headlineIcon = <AlertTriangle className="h-3 w-3 text-amber-500" />;
    }
  }

  return { headline, headlineIcon, messages };
}
