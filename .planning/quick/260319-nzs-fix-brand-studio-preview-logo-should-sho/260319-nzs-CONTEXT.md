# Quick Task 260319-nzs: Fix brand studio preview logo display - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Task Boundary

Fix bug in Brand Studio preview: logo uploaded should display in Visual Identity section (below palette and typography), but currently doesn't show. Meanwhile, the same logo appears in Brand Gallery where it shouldn't (since it's already supposed to be in Visual Identity above).

</domain>

<decisions>
## Implementation Decisions

### Logo position in preview
- Logos should render BELOW palette and typography in the Visual Identity preview section (currently renders above — move it)

### Root cause investigation scope
- Investigate all paths: LogoKit sidebar form save, AI extraction wizard, Gallery upload
- Check if `visuals.logos` is being properly persisted and returned from backend
- Check URL format consistency between assets `public_url` and `visuals.logos` values

### Gallery filtering logic
- When a logo is properly saved in `visuals.logos`, it should be completely hidden from Brand Gallery (no duplicate display)
- The current filtering logic (`logoUrls` Set comparison) is the right approach but may be failing due to URL format mismatch or empty `visuals.logos`

### Claude's Discretion
- Implementation details for fixing the root cause once identified

</decisions>

<specifics>
## Specific Ideas

- Key files: `visuals-preview.tsx` (preview rendering), `gallery-manager.tsx` (gallery filtering), `logo-kit.tsx` (logo upload), `visuals-form.tsx` (save flow)
- Backend: `identity.py` (BrandVisuals domain model), `extraction_service.py` (AI extraction)
- The `GalleryManager` already has filtering logic (lines 96-101) creating `logoUrls` Set from `visuals.logos` — this is correct in principle
- The `VisualsSection` preview checks `visuals.logos?.primary` etc. — also correct in principle
- Focus on preview only, NOT the sidebar edit form

</specifics>
