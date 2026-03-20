# Quick Task 260319-mqz: Fix logo display — show logos in Logo Kit section under Visual Identity instead of gallery preview - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Task Boundary

After uploading a logo via LogoKit slots (SingleImagePicker), the logo appears in the Gallery but NOT in the Visual Identity preview or Logo Kit. Logos should appear below Visual Identity with their names, not in the Gallery. This was working before.

</domain>

<decisions>
## Implementation Decisions

### Upload Flow
- Bug occurs when uploading via LogoKit slots (Primary, Isotipo, Dark Mode, Light Mode)
- The SingleImagePicker uploads to assets API and returns a URL, but the URL isn't properly persisting to `visuals.logos`
- Need to trace the data flow: SingleImagePicker → LogoKit.onChange → form state → onSubmit → API save

### Logo Display Layout
- Keep current horizontal row layout in VisualsSection preview
- Rename section label from "Activos de Marca" to "Kit de Logos"
- Keep variant labels: Principal, Isotipo, Fondo Oscuro, Fondo Claro

### Gallery Behavior
- Logos assigned to a slot should be completely excluded from Gallery grid
- Current filtering code (gallery-manager.tsx lines 96-101) is correct in intent
- The issue is likely that `visuals.logos` isn't populated, so the filter has nothing to exclude

### Claude's Discretion
- Root cause debugging approach
- Fix strategy (data binding vs API vs state management)

</decisions>

<specifics>
## Specific Ideas

- User confirms this was working previously — check git history for regressions
- The existing code in visuals-preview.tsx (lines 110-174) already renders logos correctly IF the data exists
- Gallery filtering (gallery-manager.tsx lines 96-101) already works IF visuals.logos has URLs
- Most likely root cause: data persistence issue where logo URLs aren't being saved to brand settings

</specifics>
