"use client";

import { useEffect, useState } from "react";

import { cn } from "@/lib/utils";

import { FieldContextPanel } from "./FieldContextPanel";
import { FieldDetail } from "./FieldDetail";
import { FieldList } from "./FieldList";
import { FinderColumn } from "./FinderColumn";
import { FormRuntimeProvider } from "./FormRuntimeProvider";
import { NextEmptyFieldCta } from "./NextEmptyFieldCta";

import type { SaveMode, SectionSchema } from "@/lib/form-runtime/schema";

const MOBILE_BREAKPOINT_PX = 768;

export interface UniversalEditableSectionProps<TValues extends object> {
  schema: SectionSchema;
  values: TValues | null | undefined;
  onSave: (next: TValues) => Promise<void>;
  /**
   * Currently-active field id. Driven by the URL — the consumer page reads
   * it from route params and passes it down. Used for scroll-into-view +
   * focus. When null, the editor falls back to the first field.
   */
  activeFieldId: string | null;
  /**
   * URL builder. Given a field id, returns the href to navigate to when the
   * user selects that row. Passing `null` in the consumer (e.g. for the
   * mobile "back" link) is expected to return the section-level URL.
   */
  getFieldHref: (fieldId: string | null) => string;
  isLoading?: boolean;
  saveMode?: SaveMode;
  /**
   * Section title resolved from backend catalog. Preferred over
   * ``schema.title`` so the copy stays in a single source of truth.
   * Falls back to ``schema.title`` when omitted.
   */
  titleOverride?: string;
  /** Section description resolved from backend catalog. Same contract. */
  descriptionOverride?: string;
  /**
   * Optional leading node rendered between the sections rail and the fields
   * column — used by collection sections (buyer personas, team, …) to slot
   * in the 280px instance picker.
   */
  instanceColumn?: React.ReactNode;
  className?: string;
}

/**
 * Finder-style section editor: fields column + editor grid + collapsible
 * recommendations panel. Mobile (<768px) collapses to list-or-editor view
 * based on ``activeFieldId``. Dimensions locked by
 * docs/ux-sessions/2026-04-20-brand-studio-finder-nav/UI-SPEC-locked-dimensions.md.
 */
export function UniversalEditableSection<TValues extends object>({
  schema,
  values,
  onSave,
  activeFieldId,
  getFieldHref,
  isLoading,
  saveMode,
  titleOverride,
  descriptionOverride,
  instanceColumn,
  className,
}: UniversalEditableSectionProps<TValues>) {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    function check() {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT_PX);
    }
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  if (isLoading || !values) {
    return (
      <div
        aria-busy
        aria-label={titleOverride ?? schema.title ?? "Cargando"}
        className={cn(
          "flex items-center justify-center p-8 text-sm text-muted-foreground",
          className,
        )}
      >
        Cargando…
      </div>
    );
  }

  const fieldsTitle = titleOverride ?? schema.title ?? "Campos";
  const showDetail = !isMobile || activeFieldId !== null;
  const showList = !isMobile || activeFieldId === null;
  const firstField = schema.fields[0];
  const resolvedActiveId = activeFieldId ?? firstField?.id ?? null;
  const effectiveDescription = descriptionOverride ?? schema.description;
  void effectiveDescription; // surfaced via FieldContextPanel metadata later

  return (
    <FormRuntimeProvider schema={schema} initialValues={values} onSave={onSave} saveMode={saveMode}>
      <div className={cn("flex min-h-0 min-w-0 flex-1", className)}>
        {instanceColumn}

        {showList && (
          <FinderColumn
            title={fieldsTitle}
            count={schema.fields.length}
            widthClass="w-[var(--brand-col-fields)]"
            bgClass="bg-muted/10"
            ariaLabel={`Campos de ${fieldsTitle}`}
          >
            <FieldList activeFieldId={resolvedActiveId} getFieldHref={getFieldHref} />
          </FinderColumn>
        )}

        {showDetail && (
          <div className="flex min-w-0 flex-1 flex-col">
            <div className="flex min-h-0 flex-1 flex-col bg-card">
              <FieldDetail
                activeFieldId={resolvedActiveId}
                fullScreen={isMobile}
                backHref={isMobile ? getFieldHref(null) : undefined}
              />
              <NextEmptyFieldCta getFieldHref={getFieldHref} />
            </div>
            <FieldContextPanel activeFieldId={resolvedActiveId} />
          </div>
        )}
      </div>
    </FormRuntimeProvider>
  );
}
