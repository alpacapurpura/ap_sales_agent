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
  isLoading?: boolean;
  saveMode?: SaveMode;
  onStartInterview?: () => void;
  className?: string;
}

/**
 * Top-level consumer API. Wraps FormRuntimeProvider + variant-C layout
 * (list + detail pane). Mobile collapses detail into a full-screen view.
 * This is the only component feature pages import.
 */
export function UniversalEditableSection<TValues extends object>({
  schema,
  values,
  onSave,
  isLoading,
  saveMode,
  onStartInterview,
  className,
}: UniversalEditableSectionProps<TValues>) {
  const [activeFieldId, setActiveFieldId] = useState<string | null>(schema.fields[0]?.id ?? null);
  const [isMobile, setIsMobile] = useState(false);
  const [mobileDetailOpen, setMobileDetailOpen] = useState(false);

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

  return (
    <FormRuntimeProvider schema={schema} initialValues={values} onSave={onSave} saveMode={saveMode}>
      <div className={cn("flex flex-col", className)}>
        <SessionHeader onStartInterview={onStartInterview} />
        <div className="flex flex-1 flex-col md:flex-row">
          <div className="w-full border-r md:w-80">
            <FieldList
              activeFieldId={activeFieldId}
              onFieldSelect={(id) => {
                setActiveFieldId(id);
                if (isMobile) setMobileDetailOpen(true);
              }}
            />
          </div>
          {(!isMobile || mobileDetailOpen) && (
            <div className="flex-1">
              <FieldDetail
                activeFieldId={activeFieldId}
                fullScreen={isMobile}
                onBack={() => setMobileDetailOpen(false)}
              />
            </div>
          )}
        </div>
      </div>
    </FormRuntimeProvider>
  );
}
