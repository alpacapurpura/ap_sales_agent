"use client";

import { Plus } from "lucide-react";
import Link from "next/link";

import { cn } from "@/lib/utils";

import { FinderColumn } from "./FinderColumn";
import {
  avatarClassFor,
  computeCompletionTone,
  initialsOf,
  toneToFillClass,
} from "./instance-display";

export interface InstancePickerInstance {
  id: string;
  primary: string;
  secondary?: string;
  /** 0..100 completion. */
  completion: number;
  /** Optional absolute count label (e.g. "18/22"). Falls back to completion%. */
  completionLabel?: string;
}

export interface InstancePickerProps {
  title: string;
  createLabel: string;
  onCreate: () => void;
  activeInstanceId: string | null;
  instances: InstancePickerInstance[];
  getInstanceHref: (instanceId: string) => string;
  className?: string;
}

/**
 * Column 2 of the Finder layout when a section is a collection (buyer
 * personas, team, testimonials, authority). Renders the dashed "Crear nueva"
 * CTA at the top and one PersonaRow per instance below.
 *
 * Dimensions locked by UI-SPEC §6:
 *   - avatar 38×38, color-hashed
 *   - status bar 60×3px, colored by completion bucket
 *   - row height ~62px
 */
export function InstancePicker({
  title,
  createLabel,
  onCreate,
  activeInstanceId,
  instances,
  getInstanceHref,
  className,
}: InstancePickerProps) {
  return (
    <FinderColumn
      title={title}
      count={instances.length}
      widthClass="w-[var(--brand-col-instances)]"
      bgClass="bg-muted/5"
      className={className}
      ariaLabel={title}
    >
      <div className="px-[14px] pt-3">
        <button
          type="button"
          onClick={onCreate}
          className={cn(
            "flex w-full items-center gap-2 rounded-md border border-dashed border-brand/50",
            "px-3 py-2 text-[12px] font-medium text-brand",
            "transition-colors hover:bg-brand/10",
          )}
        >
          <Plus className="h-3.5 w-3.5" aria-hidden="true" />
          <span>{createLabel}</span>
        </button>
      </div>

      <ul className="flex flex-col">
        {instances.map((instance) => (
          <InstanceRow
            key={instance.id}
            instance={instance}
            isActive={instance.id === activeInstanceId}
            href={getInstanceHref(instance.id)}
          />
        ))}
      </ul>
    </FinderColumn>
  );
}

interface InstanceRowProps {
  instance: InstancePickerInstance;
  isActive: boolean;
  href: string;
}

function InstanceRow({ instance, isActive, href }: InstanceRowProps) {
  const tone = computeCompletionTone(instance.completion);
  const fillWidth = `${Math.max(Math.min(instance.completion, 100), 0)}%`;
  return (
    <li>
      <Link
        href={href}
        aria-current={isActive ? "page" : undefined}
        className={cn(
          "relative flex items-center gap-3 border-b border-border/50",
          "px-[14px] py-3 transition-colors",
          isActive ? "bg-muted/60" : "hover:bg-muted/30",
          isActive &&
            "before:absolute before:inset-y-0 before:left-0 before:w-[2px] before:bg-brand",
        )}
      >
        <span
          aria-hidden="true"
          className={cn(
            "flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-full text-[16px] font-semibold",
            avatarClassFor(instance.id),
          )}
        >
          {initialsOf(instance.primary)}
        </span>
        <div className="flex min-w-0 flex-1 flex-col">
          <span className="truncate text-[13px] font-medium text-foreground">
            {instance.primary}
          </span>
          {instance.secondary && (
            <span className="truncate text-[11px] text-muted-foreground">{instance.secondary}</span>
          )}
          <div className="mt-1.5 flex items-center gap-2">
            <span className="h-[3px] w-[60px] overflow-hidden rounded-full bg-border">
              <span
                className={cn("block h-full", toneToFillClass(tone))}
                style={{ width: fillWidth }}
              />
            </span>
            <span className="text-[10px] text-muted-foreground">
              {instance.completionLabel ?? `${Math.round(instance.completion)}%`}
            </span>
          </div>
        </div>
      </Link>
    </li>
  );
}
