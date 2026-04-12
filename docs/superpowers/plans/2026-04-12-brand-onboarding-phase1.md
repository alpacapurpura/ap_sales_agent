# Brand Studio Onboarding Phase 1 — Wizard + Docs + Tabs

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rediseñar el onboarding de Brand Studio con un wizard adaptativo (website/documentos/manual), upload de documentos mejorado, review de gaps, y tabs permanentes de navegación.

**Architecture:** Frontend-only phase. El backend ya soporta website extraction + file upload via `POST /api/v1/brand/extract-full-brand` con FormData. Esta fase reemplaza el `BrandEmptyState` + `SmartFillDialog` con un wizard de pasos, agrega tabs permanentes al Brand Studio (como Growth Studio), y muestra un review de gaps después de la extracción.

**Tech Stack:** Next.js 15 (App Router), React 18, TypeScript, Tailwind CSS, Shadcn UI (Tabs, Card, Button, Progress, Badge), React Query, Zod.

**Spec:** `docs/superpowers/specs/2026-04-12-brand-onboarding-interview-engine-design.md`

---

## File Structure

### New Files

| File | Responsibility |
|---|---|
| `frontend/src/features/brand/components/tabs/brand-studio-tabs.tsx` | Tab bar permanente con health % por vista (Esencia, Estrategia, Público, Identidad Creativa) |
| `frontend/src/features/brand/components/onboarding/onboarding-wizard.tsx` | Orchestrator del wizard: maneja steps, routing condicional, estado global del wizard |
| `frontend/src/features/brand/components/onboarding/step-source-picker.tsx` | Paso 0: "¿Qué tienes disponible?" — multi-select de fuentes |
| `frontend/src/features/brand/components/onboarding/step-website.tsx` | Paso 1: Input de URL + trigger de extracción |
| `frontend/src/features/brand/components/onboarding/step-documents.tsx` | Paso 2: Upload zone drag & drop + file list |
| `frontend/src/features/brand/components/onboarding/step-processing.tsx` | Paso 3a: Progreso de extracción en tiempo real |
| `frontend/src/features/brand/components/onboarding/step-gap-review.tsx` | Paso 3b: Review de gaps con previews + health scoring |
| `frontend/src/features/brand/components/onboarding/wizard-progress-bar.tsx` | Barra de progreso del wizard (step indicators) |
| `frontend/src/features/brand/hooks/useOnboardingWizard.ts` | Estado del wizard: step actual, fuentes seleccionadas, jobId, archivos |
| `frontend/src/features/brand/components/onboarding/__tests__/onboarding-wizard.test.tsx` | Tests del wizard |
| `frontend/src/features/brand/components/tabs/__tests__/brand-studio-tabs.test.tsx` | Tests de tabs |

### Modified Files

| File | Changes |
|---|---|
| `frontend/src/features/brand/context/brand-studio-context.tsx` | Agregar `wizardState` y `setWizardState` al context |
| `frontend/src/features/brand/components/empty-state/brand-empty-state.tsx` | Reemplazar contenido con `OnboardingWizard` |
| `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/layout.tsx` | Integrar `BrandStudioTabs` en el layout |
| `frontend/src/features/brand/components/layout/brand-section-shell.tsx` | Hacer nav rail compatible con tabs (opcional, el scroll-to sigue funcionando) |
| `frontend/src/features/brand/config/sections.ts` | Exportar `BRAND_SECTION_ORDER` con metadata para tabs |

---

## Task 1: Brand Studio Tabs Component

**Files:**
- Create: `frontend/src/features/brand/components/tabs/brand-studio-tabs.tsx`
- Create: `frontend/src/features/brand/components/tabs/__tests__/brand-studio-tabs.test.tsx`
- Modify: `frontend/src/features/brand/config/sections.ts`

- [ ] **Step 1: Write the failing test for BrandStudioTabs**

```tsx
// frontend/src/features/brand/components/tabs/__tests__/brand-studio-tabs.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrandStudioTabs } from "../brand-studio-tabs";

const mockSettings = {
  identity: { brand_name: "Test Brand", industry: "Tech" },
  story: { origin_story: "Founded in 2020" },
  strategy: { methodology_pillars: [] },
  positioning: {},
  narrative: {},
  visuals: {},
  team: [],
  contact: {},
  authority_vault: [],
  communication_assets: undefined,
};

describe("BrandStudioTabs", () => {
  it("renders all 4 section tabs", () => {
    render(
      <BrandStudioTabs
        activeTab="esencia"
        onTabChange={vi.fn()}
        settings={mockSettings}
      />
    );

    expect(screen.getByRole("tab", { name: /esencia/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /estrategia/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /público/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /identidad creativa/i })).toBeInTheDocument();
  });

  it("shows health percentage on each tab", () => {
    render(
      <BrandStudioTabs
        activeTab="esencia"
        onTabChange={vi.fn()}
        settings={mockSettings}
      />
    );

    const esenciaTab = screen.getByRole("tab", { name: /esencia/i });
    expect(esenciaTab).toHaveTextContent("%");
  });

  it("calls onTabChange when clicking a tab", async () => {
    const onTabChange = vi.fn();
    render(
      <BrandStudioTabs
        activeTab="esencia"
        onTabChange={onTabChange}
        settings={mockSettings}
      />
    );

    await userEvent.click(screen.getByRole("tab", { name: /estrategia/i }));
    expect(onTabChange).toHaveBeenCalledWith("estrategia");
  });

  it("marks active tab visually", () => {
    render(
      <BrandStudioTabs
        activeTab="estrategia"
        onTabChange={vi.fn()}
        settings={mockSettings}
      />
    );

    const activeTab = screen.getByRole("tab", { name: /estrategia/i });
    expect(activeTab).toHaveAttribute("data-state", "active");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/brand/components/tabs/__tests__/brand-studio-tabs.test.tsx`
Expected: FAIL — module not found

- [ ] **Step 3: Implement BrandStudioTabs**

```tsx
// frontend/src/features/brand/components/tabs/brand-studio-tabs.tsx
"use client";

import { useMemo } from "react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  BRAND_SECTIONS,
  BRAND_SECTION_ORDER,
  type BrandSectionId,
  buildSectionNavItems,
} from "../../config/sections";
import type { BrandSettings } from "../../types";

interface BrandStudioTabsProps {
  activeTab: BrandSectionId;
  onTabChange: (tab: BrandSectionId) => void;
  settings: BrandSettings;
}

function computeSectionHealth(sectionId: BrandSectionId, settings: BrandSettings): number {
  const items = buildSectionNavItems(sectionId, settings);
  if (items.length === 0) return 0;
  return Math.round(items.reduce((sum, item) => sum + item.score, 0) / items.length);
}

function healthColor(score: number): string {
  if (score >= 80) return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
  if (score > 0) return "bg-amber-500/15 text-amber-400 border-amber-500/30";
  return "bg-muted text-muted-foreground border-border";
}

export function BrandStudioTabs({ activeTab, onTabChange, settings }: BrandStudioTabsProps) {
  const sectionHealths = useMemo(
    () =>
      BRAND_SECTION_ORDER.reduce(
        (acc, id) => {
          acc[id] = computeSectionHealth(id, settings);
          return acc;
        },
        {} as Record<BrandSectionId, number>
      ),
    [settings]
  );

  return (
    <Tabs
      value={activeTab}
      onValueChange={(v) => onTabChange(v as BrandSectionId)}
    >
      <div className="border-b px-6">
        <TabsList className="h-10 bg-transparent">
          {BRAND_SECTION_ORDER.map((id) => {
            const section = BRAND_SECTIONS[id];
            const health = sectionHealths[id];
            return (
              <TabsTrigger
                key={id}
                value={id}
                className="gap-2 data-[state=active]:bg-transparent data-[state=active]:shadow-none"
              >
                {section.label}
                <Badge
                  variant="outline"
                  className={cn("text-[10px] px-1.5 py-0 h-4 font-semibold", healthColor(health))}
                >
                  {health}%
                </Badge>
              </TabsTrigger>
            );
          })}
        </TabsList>
      </div>
    </Tabs>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/features/brand/components/tabs/__tests__/brand-studio-tabs.test.tsx`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/brand/components/tabs/brand-studio-tabs.tsx frontend/src/features/brand/components/tabs/__tests__/brand-studio-tabs.test.tsx
git commit -m "feat(brand): add BrandStudioTabs component with health scoring"
```

---

## Task 2: Integrate Tabs into Brand Studio Layout

**Files:**
- Modify: `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/layout.tsx`
- Modify: `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/esencia/page.tsx` (and other 3 pages)

- [ ] **Step 1: Read current layout and page files**

Read:
- `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/layout.tsx`
- `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/esencia/page.tsx`
- `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/estrategia/page.tsx`
- `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/publico/page.tsx`
- `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/identidad-creativa/page.tsx`

Understand the routing pattern and how children are rendered.

- [ ] **Step 2: Add tab state and BrandStudioTabs to the layout**

In `layout.tsx`, inside `BrandStudioInner`:
- Derive `activeTab` from the current pathname (e.g., `/brand-studio/estrategia` → `"estrategia"`, `/brand-studio` → `"esencia"`)
- Add `useRouter()` for tab navigation
- Render `BrandStudioTabs` between the empty-state check and `{children}`
- On tab change, navigate to `/${tenantId}/brand-studio/${slug}`

```tsx
// Add these imports
import { usePathname, useRouter } from "next/navigation";
import { useParams } from "next/navigation";
import { BrandStudioTabs } from "@/features/brand/components/tabs/brand-studio-tabs";
import { BRAND_SECTIONS, type BrandSectionId } from "@/features/brand/config/sections";

// Inside BrandStudioInner, after the empty state check, before children:
const pathname = usePathname();
const router = useRouter();
const params = useParams();
const tenantId = params.tenantId as string;

const activeTab = useMemo<BrandSectionId>(() => {
  const segment = pathname.split("/brand-studio/")[1]?.split("/")[0];
  if (segment && segment in BRAND_SECTIONS) return segment as BrandSectionId;
  return "esencia";
}, [pathname]);

const handleTabChange = useCallback(
  (tab: BrandSectionId) => {
    router.push(`/${tenantId}/brand-studio/${BRAND_SECTIONS[tab].slug}`);
  },
  [tenantId, router]
);

// Render tabs (only when hasExistingData):
{hasExistingData && (
  <BrandStudioTabs
    activeTab={activeTab}
    onTabChange={handleTabChange}
    settings={settings}
  />
)}
```

- [ ] **Step 3: Verify type-check passes**

Run: `cd frontend && npx tsc --noEmit`
Expected: PASS (no new type errors)

- [ ] **Step 4: Verify lint passes**

Run: `cd frontend && npx eslint src/features/brand/components/tabs/ src/app/\(main\)/\[tenantId\]/\(dashboard\)/brand-studio/layout.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/\(main\)/\[tenantId\]/\(dashboard\)/brand-studio/layout.tsx frontend/src/features/brand/components/tabs/
git commit -m "feat(brand): integrate permanent tabs into Brand Studio layout"
```

---

## Task 3: Onboarding Wizard Hook

**Files:**
- Create: `frontend/src/features/brand/hooks/useOnboardingWizard.ts`
- Create: `frontend/src/features/brand/hooks/__tests__/useOnboardingWizard.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// frontend/src/features/brand/hooks/__tests__/useOnboardingWizard.test.ts
import { describe, it, expect } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useOnboardingWizard } from "../useOnboardingWizard";

describe("useOnboardingWizard", () => {
  it("starts at source-picker step", () => {
    const { result } = renderHook(() => useOnboardingWizard());
    expect(result.current.currentStep).toBe("source-picker");
  });

  it("toggles source selection", () => {
    const { result } = renderHook(() => useOnboardingWizard());

    act(() => result.current.toggleSource("website"));
    expect(result.current.selectedSources).toContain("website");

    act(() => result.current.toggleSource("website"));
    expect(result.current.selectedSources).not.toContain("website");
  });

  it("routes to website step when website selected", () => {
    const { result } = renderHook(() => useOnboardingWizard());

    act(() => result.current.toggleSource("website"));
    act(() => result.current.next());

    expect(result.current.currentStep).toBe("website");
  });

  it("routes to documents step when only documents selected", () => {
    const { result } = renderHook(() => useOnboardingWizard());

    act(() => result.current.toggleSource("documents"));
    act(() => result.current.next());

    expect(result.current.currentStep).toBe("documents");
  });

  it("routes to processing after last source step", () => {
    const { result } = renderHook(() => useOnboardingWizard());

    act(() => result.current.toggleSource("website"));
    act(() => result.current.next()); // → website
    act(() => result.current.next()); // → processing

    expect(result.current.currentStep).toBe("processing");
  });

  it("routes website → documents when both selected", () => {
    const { result } = renderHook(() => useOnboardingWizard());

    act(() => result.current.toggleSource("website"));
    act(() => result.current.toggleSource("documents"));
    act(() => result.current.next()); // → website
    act(() => result.current.next()); // → documents

    expect(result.current.currentStep).toBe("documents");
  });

  it("can go back", () => {
    const { result } = renderHook(() => useOnboardingWizard());

    act(() => result.current.toggleSource("website"));
    act(() => result.current.next()); // → website
    act(() => result.current.back()); // → source-picker

    expect(result.current.currentStep).toBe("source-picker");
  });

  it("computes step indices for progress bar", () => {
    const { result } = renderHook(() => useOnboardingWizard());

    act(() => result.current.toggleSource("website"));
    act(() => result.current.toggleSource("documents"));

    // source-picker → website → documents → processing → gap-review
    expect(result.current.totalSteps).toBe(5);
    expect(result.current.currentStepIndex).toBe(0);

    act(() => result.current.next());
    expect(result.current.currentStepIndex).toBe(1);
  });

  it("manages files state", () => {
    const { result } = renderHook(() => useOnboardingWizard());
    const file = new File(["content"], "test.pdf", { type: "application/pdf" });

    act(() => result.current.addFiles([file]));
    expect(result.current.files).toHaveLength(1);

    act(() => result.current.removeFile(0));
    expect(result.current.files).toHaveLength(0);
  });

  it("manages url state", () => {
    const { result } = renderHook(() => useOnboardingWizard());

    act(() => result.current.setUrl("https://example.com"));
    expect(result.current.url).toBe("https://example.com");
  });

  it("routes directly to interview-placeholder when only interview selected", () => {
    const { result } = renderHook(() => useOnboardingWizard());

    act(() => result.current.toggleSource("interview"));
    act(() => result.current.next());

    expect(result.current.currentStep).toBe("interview-placeholder");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/brand/hooks/__tests__/useOnboardingWizard.test.ts`
Expected: FAIL — module not found

- [ ] **Step 3: Implement useOnboardingWizard**

```ts
// frontend/src/features/brand/hooks/useOnboardingWizard.ts
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

  // Build the ordered step sequence based on selected sources
  const stepSequence = useMemo<WizardStep[]>(() => {
    const hasWebsite = selectedSources.includes("website");
    const hasDocs = selectedSources.includes("documents");
    const hasInterview = selectedSources.includes("interview");
    const hasExtraction = hasWebsite || hasDocs;

    // Only interview selected → short path
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/features/brand/hooks/__tests__/useOnboardingWizard.test.ts`
Expected: PASS (all 10 tests)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/brand/hooks/useOnboardingWizard.ts frontend/src/features/brand/hooks/__tests__/useOnboardingWizard.test.ts
git commit -m "feat(brand): add useOnboardingWizard hook with adaptive routing"
```

---

## Task 4: Wizard Progress Bar

**Files:**
- Create: `frontend/src/features/brand/components/onboarding/wizard-progress-bar.tsx`

- [ ] **Step 1: Implement WizardProgressBar**

```tsx
// frontend/src/features/brand/components/onboarding/wizard-progress-bar.tsx
"use client";

import { cn } from "@/lib/utils";

interface WizardProgressBarProps {
  currentIndex: number;
  totalSteps: number;
  labels?: string[];
}

export function WizardProgressBar({ currentIndex, totalSteps, labels }: WizardProgressBarProps) {
  return (
    <div className="flex items-center justify-center gap-2 py-4">
      {Array.from({ length: totalSteps }).map((_, i) => (
        <div key={i} className="flex items-center gap-2">
          <div
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold transition-all",
              i < currentIndex && "bg-primary text-primary-foreground",
              i === currentIndex && "bg-primary text-primary-foreground ring-4 ring-primary/20",
              i > currentIndex && "border-2 border-muted-foreground/30 text-muted-foreground"
            )}
          >
            {i < currentIndex ? "✓" : i + 1}
          </div>
          {labels?.[i] && (
            <span
              className={cn(
                "hidden text-xs font-medium sm:inline",
                i <= currentIndex ? "text-foreground" : "text-muted-foreground"
              )}
            >
              {labels[i]}
            </span>
          )}
          {i < totalSteps - 1 && (
            <div
              className={cn(
                "h-0.5 w-8 transition-colors",
                i < currentIndex ? "bg-primary" : "bg-muted-foreground/30"
              )}
            />
          )}
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Run type-check**

Run: `cd frontend && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/brand/components/onboarding/wizard-progress-bar.tsx
git commit -m "feat(brand): add WizardProgressBar component"
```

---

## Task 5: Step 0 — Source Picker

**Files:**
- Create: `frontend/src/features/brand/components/onboarding/step-source-picker.tsx`

- [ ] **Step 1: Implement StepSourcePicker**

```tsx
// frontend/src/features/brand/components/onboarding/step-source-picker.tsx
"use client";

import { Globe, FileText, MessageCircle, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { OnboardingSource } from "../../hooks/useOnboardingWizard";

interface StepSourcePickerProps {
  selectedSources: OnboardingSource[];
  onToggle: (source: OnboardingSource) => void;
  onNext: () => void;
  onManual: () => void;
}

const SOURCE_OPTIONS: {
  id: OnboardingSource;
  icon: typeof Globe;
  title: string;
  description: string;
}[] = [
  {
    id: "website",
    icon: Globe,
    title: "Desde tu Website",
    description: "Extraemos tu identidad, historia, equipo y más escaneando tu sitio web.",
  },
  {
    id: "documents",
    icon: FileText,
    title: "Desde tus Documentos",
    description: "Sube PDFs, presentaciones o documentos con información de tu marca.",
  },
  {
    id: "interview",
    icon: MessageCircle,
    title: "Haciéndolo Juntos",
    description: "Una entrevista guiada por IA donde nos cuentas todo sobre tu marca.",
  },
];

export function StepSourcePicker({
  selectedSources,
  onToggle,
  onNext,
  onManual,
}: StepSourcePickerProps) {
  const hasSelection = selectedSources.length > 0;

  return (
    <div className="mx-auto max-w-2xl animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="mb-10 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          Construyamos tu marca
        </h1>
        <p className="mt-3 text-muted-foreground">
          ¿Qué tienes disponible? Selecciona todo lo que aplique.
        </p>
      </div>

      <div className="grid gap-4">
        {SOURCE_OPTIONS.map(({ id, icon: Icon, title, description }) => {
          const isSelected = selectedSources.includes(id);
          const isDisabled = id === "interview";
          return (
            <button
              key={id}
              type="button"
              onClick={() => !isDisabled && onToggle(id)}
              className={cn(
                "group relative flex items-start gap-4 rounded-xl border-2 p-5 text-left transition-all",
                isSelected && !isDisabled
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50 hover:bg-muted/40",
                isDisabled && "cursor-not-allowed opacity-50"
              )}
            >
              <div
                className={cn(
                  "flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg transition-colors",
                  isSelected ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"
                )}
              >
                <Icon className="h-5 w-5" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-foreground">
                  {title}
                  {isDisabled && (
                    <span className="ml-2 text-xs font-normal text-muted-foreground">
                      Próximamente
                    </span>
                  )}
                </h3>
                <p className="mt-1 text-sm text-muted-foreground">{description}</p>
              </div>
              {isSelected && !isDisabled && (
                <div className="absolute right-4 top-4 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold">
                  ✓
                </div>
              )}
            </button>
          );
        })}
      </div>

      <div className="mt-8 flex items-center justify-between">
        <button
          type="button"
          onClick={onManual}
          className="text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
        >
          Prefiero hacerlo manualmente
        </button>
        <Button onClick={onNext} disabled={!hasSelection} className="gap-2">
          Continuar
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Run type-check**

Run: `cd frontend && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/brand/components/onboarding/step-source-picker.tsx
git commit -m "feat(brand): add StepSourcePicker — wizard step 0"
```

---

## Task 6: Step 1 — Website URL Input

**Files:**
- Create: `frontend/src/features/brand/components/onboarding/step-website.tsx`

- [ ] **Step 1: Implement StepWebsite**

```tsx
// frontend/src/features/brand/components/onboarding/step-website.tsx
"use client";

import { Globe, ArrowRight, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface StepWebsiteProps {
  url: string;
  onUrlChange: (url: string) => void;
  onNext: () => void;
  onBack: () => void;
}

export function StepWebsite({ url, onUrlChange, onNext, onBack }: StepWebsiteProps) {
  const isValidUrl = url.length > 0 && (url.startsWith("http://") || url.startsWith("https://"));

  return (
    <div className="mx-auto max-w-lg animate-in fade-in slide-in-from-right-4 duration-300">
      <div className="mb-8 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
          <Globe className="h-6 w-6 text-primary" />
        </div>
        <h2 className="text-2xl font-bold text-foreground">¿Cuál es tu sitio web?</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Escanearemos tu sitio para extraer tu identidad, historia, equipo y más.
        </p>
      </div>

      <div className="space-y-4">
        <Input
          type="url"
          placeholder="https://tumarca.com"
          value={url}
          onChange={(e) => onUrlChange(e.target.value)}
          className="h-12 text-base"
          autoFocus
        />
        <p className="text-xs text-muted-foreground">
          Incluye https:// — escanearemos las páginas principales automáticamente.
        </p>
      </div>

      <div className="mt-8 flex justify-between">
        <Button variant="ghost" onClick={onBack} className="gap-2">
          <ArrowLeft className="h-4 w-4" />
          Atrás
        </Button>
        <Button onClick={onNext} disabled={!isValidUrl} className="gap-2">
          Continuar
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Run type-check**

Run: `cd frontend && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/brand/components/onboarding/step-website.tsx
git commit -m "feat(brand): add StepWebsite — wizard step 1"
```

---

## Task 7: Step 2 — Document Upload

**Files:**
- Create: `frontend/src/features/brand/components/onboarding/step-documents.tsx`

- [ ] **Step 1: Implement StepDocuments**

```tsx
// frontend/src/features/brand/components/onboarding/step-documents.tsx
"use client";

import { useCallback } from "react";
import { FileText, Upload, X, ArrowRight, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface StepDocumentsProps {
  files: File[];
  onAddFiles: (files: File[]) => void;
  onRemoveFile: (index: number) => void;
  onNext: () => void;
  onBack: () => void;
}

const ACCEPTED_TYPES = ".pdf,.docx,.txt,.md,.pptx";

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function StepDocuments({ files, onAddFiles, onRemoveFile, onNext, onBack }: StepDocumentsProps) {
  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const droppedFiles = Array.from(e.dataTransfer.files);
      onAddFiles(droppedFiles);
    },
    [onAddFiles]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        onAddFiles(Array.from(e.target.files));
        e.target.value = "";
      }
    },
    [onAddFiles]
  );

  return (
    <div className="mx-auto max-w-lg animate-in fade-in slide-in-from-right-4 duration-300">
      <div className="mb-8 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
          <FileText className="h-6 w-6 text-primary" />
        </div>
        <h2 className="text-2xl font-bold text-foreground">Sube tus documentos</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          PDFs, presentaciones, documentos de marca — lo que tengas.
        </p>
      </div>

      {/* Drop Zone */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        className={cn(
          "relative flex min-h-[160px] flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-colors",
          "border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/30"
        )}
      >
        <Upload className="mb-3 h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">
          Arrastra archivos aquí
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          o haz click para seleccionar
        </p>
        <input
          type="file"
          accept={ACCEPTED_TYPES}
          multiple
          onChange={handleFileInput}
          className="absolute inset-0 cursor-pointer opacity-0"
        />
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="mt-4 space-y-2">
          {files.map((file, idx) => (
            <div
              key={`${file.name}-${idx}`}
              className="flex items-center justify-between rounded-lg border bg-muted/30 px-4 py-2.5"
            >
              <div className="flex items-center gap-3 overflow-hidden">
                <FileText className="h-4 w-4 flex-shrink-0 text-primary" />
                <div className="overflow-hidden">
                  <p className="truncate text-sm font-medium text-foreground">{file.name}</p>
                  <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => onRemoveFile(idx)}
                className="ml-2 flex-shrink-0 rounded-md p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      <p className="mt-3 text-xs text-muted-foreground">
        Formatos aceptados: PDF, DOCX, TXT, MD, PPTX
      </p>

      <div className="mt-8 flex justify-between">
        <Button variant="ghost" onClick={onBack} className="gap-2">
          <ArrowLeft className="h-4 w-4" />
          Atrás
        </Button>
        <Button onClick={onNext} disabled={files.length === 0} className="gap-2">
          Continuar
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Run type-check**

Run: `cd frontend && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/brand/components/onboarding/step-documents.tsx
git commit -m "feat(brand): add StepDocuments — wizard step 2 with drag and drop"
```

---

## Task 8: Step 3a — Processing (Extraction Progress)

**Files:**
- Create: `frontend/src/features/brand/components/onboarding/step-processing.tsx`

- [ ] **Step 1: Implement StepProcessing**

This reuses the polling logic from SmartFillDialog but in a full-page layout:

```tsx
// frontend/src/features/brand/components/onboarding/step-processing.tsx
"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { Loader2, AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useAuth } from "@clerk/nextjs";
import { brandApi } from "../../api/brand-api";

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
  const [isSubmitting, setIsSubmitting] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const activeJobRef = useRef<string | null>(jobId);

  // Start extraction
  const startExtraction = useCallback(async () => {
    setIsSubmitting(true);
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
    } finally {
      setIsSubmitting(false);
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

  // Auto-start extraction if no jobId yet
  useEffect(() => {
    if (!jobId && !isSubmitting) {
      startExtraction();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

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
```

- [ ] **Step 2: Verify the `brandApi` exports exist**

Read `frontend/src/features/brand/api/brand-api.ts` to confirm `extractFullBrand` and `pollExtractionStatus` exist and match the signatures used.

- [ ] **Step 3: Run type-check**

Run: `cd frontend && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/brand/components/onboarding/step-processing.tsx
git commit -m "feat(brand): add StepProcessing — extraction progress with polling"
```

---

## Task 9: Step 3b — Gap Review

**Files:**
- Create: `frontend/src/features/brand/components/onboarding/step-gap-review.tsx`

- [ ] **Step 1: Implement StepGapReview**

```tsx
// frontend/src/features/brand/components/onboarding/step-gap-review.tsx
"use client";

import { useMemo } from "react";
import { CheckCircle2, AlertCircle, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  BRAND_SECTIONS,
  BRAND_SECTION_ORDER,
  type BrandSectionId,
  buildSectionNavItems,
} from "../../config/sections";
import type { BrandSettings } from "../../types";

interface StepGapReviewProps {
  settings: BrandSettings;
  onFinish: () => void;
}

function computeSectionHealth(sectionId: BrandSectionId, settings: BrandSettings) {
  const items = buildSectionNavItems(sectionId, settings);
  if (items.length === 0) return { score: 0, items: [] };
  const score = Math.round(items.reduce((sum, item) => sum + item.score, 0) / items.length);
  return { score, items };
}

export function StepGapReview({ settings, onFinish }: StepGapReviewProps) {
  const sectionData = useMemo(
    () =>
      BRAND_SECTION_ORDER.map((id) => ({
        id,
        config: BRAND_SECTIONS[id],
        ...computeSectionHealth(id, settings),
      })),
    [settings]
  );

  const overallScore = useMemo(() => {
    const total = sectionData.reduce((sum, s) => sum + s.score, 0);
    return Math.round(total / sectionData.length);
  }, [sectionData]);

  return (
    <div className="mx-auto max-w-2xl animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="mb-8 text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
          <span className="text-2xl font-bold text-primary">{overallScore}%</span>
        </div>
        <h2 className="text-2xl font-bold text-foreground">
          {overallScore >= 80 ? "¡Excelente extracción!" : overallScore >= 40 ? "Buen inicio" : "Tenemos una base"}
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          {overallScore >= 80
            ? "Tu marca está casi completa. Puedes refinar los detalles desde el Brand Studio."
            : "Extrajimos lo que pudimos. Puedes completar el resto manualmente o esperar la entrevista IA (próximamente)."}
        </p>
      </div>

      <div className="space-y-3">
        {sectionData.map(({ id, config, score, items }) => (
          <div
            key={id}
            className={cn(
              "rounded-xl border p-4 transition-colors",
              score >= 80 ? "border-emerald-500/30 bg-emerald-500/5" : score > 0 ? "border-amber-500/30 bg-amber-500/5" : "border-border bg-muted/20"
            )}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {score >= 80 ? (
                  <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                ) : (
                  <AlertCircle className={cn("h-5 w-5", score > 0 ? "text-amber-500" : "text-muted-foreground")} />
                )}
                <div>
                  <h3 className="font-semibold text-foreground">{config.label}</h3>
                  <p className="text-xs text-muted-foreground">{config.subtitle}</p>
                </div>
              </div>
              <Badge
                variant="outline"
                className={cn(
                  "text-xs font-semibold",
                  score >= 80
                    ? "border-emerald-500/30 text-emerald-400"
                    : score > 0
                      ? "border-amber-500/30 text-amber-400"
                      : "text-muted-foreground"
                )}
              >
                {score}%
              </Badge>
            </div>

            {/* Sub-items detail */}
            {items.length > 0 && score < 100 && (
              <div className="mt-3 flex flex-wrap gap-1.5 pl-8">
                {items.map((item) => (
                  <Badge
                    key={item.id}
                    variant={item.status === "complete" ? "secondary" : "outline"}
                    className={cn(
                      "text-[10px]",
                      item.status === "complete" && "bg-emerald-500/10 text-emerald-400",
                      item.status === "partial" && "border-amber-500/30 text-amber-400",
                      item.status === "empty" && "text-muted-foreground"
                    )}
                  >
                    {item.status === "complete" ? "✓" : item.status === "partial" ? "◐" : "○"} {item.label}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-8 flex justify-center">
        <Button onClick={onFinish} size="lg" className="gap-2">
          Ir a mi Brand Studio
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Run type-check**

Run: `cd frontend && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/brand/components/onboarding/step-gap-review.tsx
git commit -m "feat(brand): add StepGapReview — extraction results with health scoring"
```

---

## Task 10: Onboarding Wizard Orchestrator

**Files:**
- Create: `frontend/src/features/brand/components/onboarding/onboarding-wizard.tsx`

- [ ] **Step 1: Implement OnboardingWizard**

```tsx
// frontend/src/features/brand/components/onboarding/onboarding-wizard.tsx
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

  const stepLabels: Record<string, string> = {
    "source-picker": "Fuentes",
    website: "Website",
    documents: "Documentos",
    processing: "Procesando",
    "gap-review": "Resultado",
    "interview-placeholder": "Entrevista",
  };

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
            labels={wizard.totalSteps <= 5 ? undefined : undefined}
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
```

- [ ] **Step 2: Run type-check**

Run: `cd frontend && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/brand/components/onboarding/onboarding-wizard.tsx
git commit -m "feat(brand): add OnboardingWizard orchestrator"
```

---

## Task 11: Integrate Wizard into Brand Studio Layout

**Files:**
- Modify: `frontend/src/features/brand/components/empty-state/brand-empty-state.tsx`
- Modify: `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/layout.tsx`

- [ ] **Step 1: Read current files**

Read:
- `frontend/src/features/brand/components/empty-state/brand-empty-state.tsx`
- `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/layout.tsx`

- [ ] **Step 2: Update BrandEmptyState to render OnboardingWizard**

Replace the contents of `brand-empty-state.tsx`:

```tsx
// frontend/src/features/brand/components/empty-state/brand-empty-state.tsx
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
```

Note: `onStartAI` here means "onboarding complete, refresh and show Brand Studio". The naming is preserved for backward compatibility with the layout that calls `openSmartFill("initial")` — but now the wizard handles extraction internally, so `onComplete` should instead refetch settings and dismiss the empty state. We need to update the layout's handler.

- [ ] **Step 3: Update layout to handle wizard completion**

In `layout.tsx`, modify the empty state rendering and handlers:

1. Replace the `onStartAI` handler: instead of opening SmartFillDialog, it should just refetch settings and dismiss empty state (the wizard already handled extraction).
2. `onStartManual` stays the same (dismiss empty state).

The key change in `BrandStudioInner`:

```tsx
// Replace the old handler:
// onStartAI={() => openSmartFill("initial")}
// With:
const handleWizardComplete = useCallback(() => {
  refetch();
  dismissEmptyState();
}, [refetch, dismissEmptyState]);

// And in the JSX:
{showEmptyState ? (
  <BrandEmptyState
    onStartAI={handleWizardComplete}
    onStartManual={dismissEmptyState}
  />
) : (
  <>
    <BrandStudioTabs
      activeTab={activeTab}
      onTabChange={handleTabChange}
      settings={settings}
    />
    {children}
    {/* Overlay layer (edit sheets, etc.) */}
  </>
)}
```

- [ ] **Step 4: Run type-check + lint**

Run: `cd frontend && npx tsc --noEmit && npx eslint src/features/brand/components/empty-state/ src/features/brand/components/onboarding/ src/app/\(main\)/\[tenantId\]/\(dashboard\)/brand-studio/layout.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/brand/components/empty-state/brand-empty-state.tsx frontend/src/app/\(main\)/\[tenantId\]/\(dashboard\)/brand-studio/layout.tsx
git commit -m "feat(brand): integrate OnboardingWizard into Brand Studio layout"
```

---

## Task 12: Integration Test

**Files:**
- Create: `frontend/src/features/brand/components/onboarding/__tests__/onboarding-wizard.test.tsx`

- [ ] **Step 1: Write integration tests for wizard flow**

```tsx
// frontend/src/features/brand/components/onboarding/__tests__/onboarding-wizard.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { OnboardingWizard } from "../onboarding-wizard";

// Mock useBrandSettings
vi.mock("../../../hooks/useBrandSettings", () => ({
  useBrandSettings: () => ({
    settings: null,
    loading: false,
    error: null,
    refetch: vi.fn(),
  }),
}));

// Mock Clerk auth
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("mock-token") }),
}));

describe("OnboardingWizard", () => {
  it("renders source picker as first step", () => {
    render(<OnboardingWizard onComplete={vi.fn()} onManual={vi.fn()} />);

    expect(screen.getByText("Construyamos tu marca")).toBeInTheDocument();
    expect(screen.getByText("Desde tu Website")).toBeInTheDocument();
    expect(screen.getByText("Desde tus Documentos")).toBeInTheDocument();
    expect(screen.getByText("Haciéndolo Juntos")).toBeInTheDocument();
  });

  it("disables continue until a source is selected", () => {
    render(<OnboardingWizard onComplete={vi.fn()} onManual={vi.fn()} />);

    const continueBtn = screen.getByRole("button", { name: /continuar/i });
    expect(continueBtn).toBeDisabled();
  });

  it("navigates to website step when website selected", async () => {
    render(<OnboardingWizard onComplete={vi.fn()} onManual={vi.fn()} />);

    await userEvent.click(screen.getByText("Desde tu Website"));
    await userEvent.click(screen.getByRole("button", { name: /continuar/i }));

    expect(screen.getByText("¿Cuál es tu sitio web?")).toBeInTheDocument();
  });

  it("navigates to documents step when documents selected", async () => {
    render(<OnboardingWizard onComplete={vi.fn()} onManual={vi.fn()} />);

    await userEvent.click(screen.getByText("Desde tus Documentos"));
    await userEvent.click(screen.getByRole("button", { name: /continuar/i }));

    expect(screen.getByText("Sube tus documentos")).toBeInTheDocument();
  });

  it("calls onManual when manual link clicked", async () => {
    const onManual = vi.fn();
    render(<OnboardingWizard onComplete={vi.fn()} onManual={onManual} />);

    await userEvent.click(screen.getByText(/prefiero hacerlo manualmente/i));
    expect(onManual).toHaveBeenCalled();
  });

  it("can navigate back from website step", async () => {
    render(<OnboardingWizard onComplete={vi.fn()} onManual={vi.fn()} />);

    await userEvent.click(screen.getByText("Desde tu Website"));
    await userEvent.click(screen.getByRole("button", { name: /continuar/i }));

    // Now on website step
    expect(screen.getByText("¿Cuál es tu sitio web?")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /atrás/i }));

    // Back to source picker
    expect(screen.getByText("Construyamos tu marca")).toBeInTheDocument();
  });

  it("shows interview placeholder for interview-only selection", async () => {
    render(<OnboardingWizard onComplete={vi.fn()} onManual={vi.fn()} />);

    // Interview option is disabled (Próximamente) in Phase 1
    const interviewOption = screen.getByText("Haciéndolo Juntos").closest("button");
    expect(interviewOption).toHaveClass("cursor-not-allowed");
  });
});
```

- [ ] **Step 2: Run tests**

Run: `cd frontend && npx vitest run src/features/brand/components/onboarding/__tests__/onboarding-wizard.test.tsx`
Expected: PASS (6 tests)

- [ ] **Step 3: Run full frontend test suite**

Run: `cd frontend && npx vitest run`
Expected: PASS (no regressions)

- [ ] **Step 4: Run full frontend lint + types**

Run: `cd frontend && npx tsc --noEmit && npx eslint src/features/brand/`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/brand/components/onboarding/__tests__/onboarding-wizard.test.tsx
git commit -m "test(brand): add integration tests for OnboardingWizard flow"
```

---

## Task 13: Final Verification

- [ ] **Step 1: Run full test suite**

Run: `cd backend && .venv/bin/ruff check src/ tests/ --no-cache && .venv/bin/pytest -x -q --tb=short`
Expected: PASS (no backend changes, just verifying no regressions)

Run: `cd frontend && npx tsc --noEmit && npx eslint src/ && npx vitest run`
Expected: PASS

- [ ] **Step 2: Verify feature visually**

Start dev: `docker compose up -d`
Navigate to Brand Studio with a tenant that has no brand data.
Verify:
1. Wizard shows step 0 (source picker) instead of old empty state
2. Selecting "Website" → shows URL input
3. Selecting "Documents" → shows upload zone
4. "Haciéndolo Juntos" shows as disabled (Próximamente)
5. Back navigation works
6. "Prefiero hacerlo manualmente" dismisses wizard
7. After extraction completes, gap review shows health scores
8. "Ir a mi Brand Studio" shows the Brand Studio with tabs
9. Tabs show health % and navigate between views

- [ ] **Step 3: Commit any fixes from visual testing**

```bash
# Only if fixes needed
git add -p  # Stage specific changes
git commit -m "fix(brand): visual adjustments from manual testing"
```
