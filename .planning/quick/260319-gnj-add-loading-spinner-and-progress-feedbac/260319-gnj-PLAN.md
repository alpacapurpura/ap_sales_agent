---
phase: quick
plan: 260319-gnj
type: execute
wave: 1
depends_on: []
files_modified:
  - frontend/src/features/brand/sections/visuals/brand-visuals-wizard.tsx
autonomous: true
requirements: [UX-VISUAL-SCAN-FEEDBACK]
must_haves:
  truths:
    - "When user clicks 'Escanear Web', the dialog shows a full-screen processing state with spinner, progress bar, and stage messages"
    - "User sees estimated time and current analysis stage to prevent premature cancellation"
    - "Dialog cannot be dismissed while processing is in progress"
    - "On error, user sees clear error message with retry option"
  artifacts:
    - path: "frontend/src/features/brand/sections/visuals/brand-visuals-wizard.tsx"
      provides: "Processing state UI with spinner, progress bar, stage messages"
  key_links:
    - from: "brand-visuals-wizard.tsx handleAnalyzeWeb"
      to: "Processing state UI"
      via: "isProcessing/progress/stage state variables"
      pattern: "isProcessing.*setProgress.*setStage"
---

<objective>
Add loading spinner and progress feedback to the Visual DNA web scan dialog (BrandVisualsWizard).

Purpose: When users click "Escanear Web" for visual identity extraction, the dialog currently only shows a tiny spinner on the button with a toast. The actual API call takes 30-60 seconds (web crawl + LLM analysis). Users think the app is frozen and cancel, wasting AI tokens. The SmartFillDialog already has an excellent processing state pattern (animated spinner, progress bar, stage messages, time estimate) that should be replicated here.

Output: Updated brand-visuals-wizard.tsx with full processing feedback matching SmartFillDialog's UX pattern.
</objective>

<execution_context>
@/home/chris/AISALESHT/.claude/get-shit-done/workflows/execute-plan.md
@/home/chris/AISALESHT/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@frontend/src/features/brand/sections/visuals/brand-visuals-wizard.tsx
@frontend/src/features/brand/components/smart-fill/smart-fill-dialog.tsx
</context>

<interfaces>
<!-- The processing state pattern from SmartFillDialog (lines 206-218) to replicate: -->

```tsx
// State variables needed (from smart-fill-dialog.tsx):
const [isProcessing, setIsProcessing] = useState(false);
const [progress, setProgress] = useState(0);
const [stage, setStage] = useState<string>("");
const [errorState, setErrorState] = useState<{ type: "timeout" | "generic", message: string } | null>(null);

// Processing UI pattern (spinner + progress + stage):
// - Animated circular spinner (border-4 border-primary border-t-transparent animate-spin)
// - Wand2 icon pulsing in center
// - Stage text (h3)
// - Progress bar (shadcn Progress component)
// - Time estimate text
```

<!-- Existing imports already in brand-visuals-wizard.tsx: -->
```tsx
import { Loader2, Sparkles } from "lucide-react";
// Need to add: Progress from @/components/ui/progress, Wand2 from lucide-react, Alert components
```

<!-- brandApi.extractBrandVisuals signature: -->
```tsx
extractBrandVisuals: async (url: string, token: string): Promise<ExtractedVisuals>
```
</interfaces>

<tasks>

<task type="auto">
  <name>Task 1: Add processing state with spinner, progress bar, and stage messages to BrandVisualsWizard</name>
  <files>frontend/src/features/brand/sections/visuals/brand-visuals-wizard.tsx</files>
  <action>
Modify `brand-visuals-wizard.tsx` to add a full processing feedback state, following the same pattern as SmartFillDialog (lines 46-49, 68-97, 206-218 of smart-fill-dialog.tsx):

1. **Add imports:** `Progress` from `@/components/ui/progress`, `Wand2` and `AlertTriangle` and `WifiOff` from `lucide-react`, `Alert`, `AlertDescription`, `AlertTitle` from `@/components/ui/alert`.

2. **Add state variables** (after existing `analyzing` state):
   - `progress: number` (0-100)
   - `stage: string` (current step label)
   - `errorState: { type: "timeout" | "generic", message: string } | null`

3. **Update `handleAnalyzeWeb`** to mirror SmartFillDialog's approach:
   - Set `progress(5)`, `stage("Iniciando escaneo visual...")` at start
   - Add `progressInterval` with `setInterval` every 800ms that asymptotically approaches 90 (same formula: `Math.min(prev + Math.max(0.5, (90 - prev) / 50), 90)`)
   - Add `setTimeout` stage messages specific to visual extraction:
     - 2s: "Escaneando sitio web..."
     - 6s: "Analizando paleta de colores..."
     - 12s: "Detectando tipografias..."
     - 18s: "Extrayendo estilo de diseno..."
     - 24s: "Generando reglas de uso..."
   - On success: clear interval, set progress 100, stage "Identidad visual detectada!", then proceed to preview step after 800ms delay
   - On error: clear interval, set errorState with timeout detection (same logic as SmartFillDialog: check for "Failed to fetch", "Network request failed", or "TIMEOUT:" in error message), set stage "Proceso interrumpido", progress 0

4. **Add processing UI** in the `step === "select-source"` branch. When `analyzing` is true, replace the 3-card grid with a centered processing state:
   ```
   <div className="py-8 space-y-6 text-center">
     <!-- Animated circular spinner (same as SmartFillDialog) -->
     <div className="relative mx-auto w-24 h-24 flex items-center justify-center">
       <div className="absolute inset-0 border-4 border-primary/20 rounded-full" />
       <div className="absolute inset-0 border-4 border-primary border-t-transparent rounded-full animate-spin" />
       <Palette className="w-8 h-8 text-primary animate-pulse" />  <!-- Use Palette icon instead of Wand2 to match visual theme -->
     </div>
     <div className="space-y-2">
       <h3 className="text-lg font-medium">{stage}</h3>
       <Progress value={progress} className="h-2 w-full max-w-xs mx-auto" />
       <p className="text-sm text-muted-foreground">Esto puede tomar hasta 1 minuto...</p>
     </div>
   </div>
   ```

5. **Add error state UI** above the card grid (same pattern as SmartFillDialog lines 181-203): Alert with destructive variant, timeout vs generic message, retry button that calls `setErrorState(null)`.

6. **Prevent dialog dismissal during processing:** Add `onInteractOutside` handler (already present) and update `onOpenChange` to be a no-op when `analyzing` is true:
   ```tsx
   onOpenChange={(val) => { if (!analyzing) onOpenChange(val); }}
   ```

Do NOT change the logo extraction or kit selection flows -- only the web scan flow needs the processing state.
  </action>
  <verify>
    <automated>docker exec -t visionarias_client_dev npx tsc --noEmit --pretty 2>&1 | head -30</automated>
  </verify>
  <done>
    - Clicking "Escanear Web" shows full-screen processing state with animated spinner, progress bar, stage messages, and time estimate
    - Error states show clear message with retry button
    - Dialog cannot be dismissed during processing
    - TypeScript compiles without errors
    - After successful extraction, transitions to preview step as before
  </done>
</task>

</tasks>

<verification>
- TypeScript compilation passes (`tsc --noEmit`)
- Visual inspection: clicking "Escanear Web" in Brand Studio > Visual DNA shows processing state
- Processing state matches SmartFillDialog's visual pattern (spinner, progress, stages)
- Dialog blocks dismissal during scan
- Error state renders with retry option
</verification>

<success_criteria>
User sees clear progress feedback during visual DNA web scan that prevents premature cancellation and wasted AI tokens.
</success_criteria>

<output>
After completion, create `.planning/quick/260319-gnj-add-loading-spinner-and-progress-feedbac/260319-gnj-SUMMARY.md`
</output>
