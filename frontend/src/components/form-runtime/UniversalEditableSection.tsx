"use client";

import { useEffect, useState } from "react";

import { cn } from "@/lib/utils";

import { FieldDetail } from "./FieldDetail";
import { FieldList } from "./FieldList";
import { FormRuntimeProvider } from "./FormRuntimeProvider";
import { SessionHeader } from "./SessionHeader";

import type { SaveMode, SectionSchema } from "@/lib/form-runtime/schema";

const MOBILE_BREAKPOINT_PX = 768;

export interface UniversalEditableSectionProps<TValues extends object> {
  schema: SectionSchema;
  values: TValues | null | undefined;
  onSave: (next: TValues) => Promise<void>;
  /**
   * Currently-active field id. Driven by the URL — the consumer page reads
   * it from route params and passes it down.
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
  onStartInterview?: () => void;
  className?: string;
}

/**
 * Top-level consumer API. Wraps FormRuntimeProvider + variant-C layout
 * (list + detail pane). Mobile collapses detail into a full-screen view
 * when a field is active in the URL.
 *
 * URL contract: routing is the single source of truth for which field is
 * active. This component owns no `activeFieldId` state; the page above
 * extracts it from route params and passes it via props.
 */
export function UniversalEditableSection<TValues extends object>({
  schema,
  values,
  onSave,
  activeFieldId,
  getFieldHref,
  isLoading,
  saveMode,
  onStartInterview,
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
        className={cn(
          "flex items-center justify-center p-8 text-sm text-muted-foreground",
          className,
        )}
      >
        Cargando…
      </div>
    );
  }

  // Mobile: show list view when no field is selected; full-screen detail when one is.
  const showDetail = !isMobile || activeFieldId !== null;
  const showList = !isMobile || activeFieldId === null;

  return (
    <FormRuntimeProvider schema={schema} initialValues={values} onSave={onSave} saveMode={saveMode}>
      <div className={cn("flex flex-col", className)}>
        <SessionHeader onStartInterview={onStartInterview} />
        <div className="flex flex-1 flex-col md:flex-row">
          {showList && (
            <div className="w-full border-r md:w-80">
              <FieldList activeFieldId={activeFieldId} getFieldHref={getFieldHref} />
            </div>
          )}
          {showDetail && (
            <div className="flex-1">
              <FieldDetail
                activeFieldId={activeFieldId}
                fullScreen={isMobile}
                backHref={isMobile ? getFieldHref(null) : undefined}
              />
            </div>
          )}
        </div>
      </div>
    </FormRuntimeProvider>
  );
}
