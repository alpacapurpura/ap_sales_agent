---
phase: quick-260319-nzs
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - frontend/src/features/brand/sections/visuals/visuals-preview.tsx
  - frontend/src/features/brand/sections/gallery/gallery-manager.tsx
autonomous: true
requirements: [QUICK-NZS-01]
must_haves:
  truths:
    - "Logo Kit section renders BELOW palette and typography in the Visual Identity preview"
    - "Logos assigned in LogoKit do NOT appear in Brand Gallery"
    - "Logos assigned in LogoKit DO appear in Visual Identity preview section"
  artifacts:
    - path: "frontend/src/features/brand/sections/visuals/visuals-preview.tsx"
      provides: "Visual Identity preview with logos below palette/typography"
    - path: "frontend/src/features/brand/sections/gallery/gallery-manager.tsx"
      provides: "Gallery filtering that excludes logo URLs with normalization"
  key_links:
    - from: "visuals-preview.tsx"
      to: "BrandVisuals.logos"
      via: "visuals.logos?.primary check"
      pattern: "visuals\\.logos"
    - from: "gallery-manager.tsx"
      to: "BrandVisuals.logos"
      via: "logoUrls Set filtering"
      pattern: "logoUrls\\.has"
---

<objective>
Fix Brand Studio preview so that logos appear in the correct position within the Visual Identity section (below palette and typography, not above), and ensure logos are properly excluded from the Brand Gallery when assigned.

Purpose: User uploaded a logo and expects to see it in the Visual Identity preview below colors/fonts, not floating above them or duplicated in the gallery.
Output: Corrected visuals-preview.tsx rendering order + robust gallery filtering.
</objective>

<execution_context>
@/home/chris/AISALESHT/.claude/get-shit-done/workflows/execute-plan.md
@/home/chris/AISALESHT/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@frontend/src/features/brand/sections/visuals/visuals-preview.tsx
@frontend/src/features/brand/sections/gallery/gallery-manager.tsx
@frontend/src/features/brand/types/index.ts

<interfaces>
From frontend/src/features/brand/types/index.ts:
```typescript
export interface BrandLogos {
    primary?: string;
    secondary?: string;
    dark_mode?: string;
    light_mode?: string;
    main?: string;      // legacy
    inverted?: string;   // legacy
    favicon?: string;    // legacy
}

export interface BrandVisuals {
    // ... colors, typography, design system fields ...
    logos?: BrandLogos;
    images?: string[];
}
```

From gallery-manager.tsx (lines 96-101):
```typescript
const logoUrls = new Set(
    Object.values(visuals.logos || {})
        .filter((url): url is string => typeof url === 'string' && url.length > 0)
);
const filteredImages = images?.filter(img => !logoUrls.has(img.public_url)) || [];
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Move logos section below palette/typography in visuals-preview.tsx</name>
  <files>frontend/src/features/brand/sections/visuals/visuals-preview.tsx</files>
  <action>
In visuals-preview.tsx, the "Kit de Logos" section (lines 109-174) currently renders ABOVE the palette/typography grid (line 176). Move the entire logos block to render AFTER the palette/typography grid and AFTER the brand mood badges section.

Specifically:
1. Cut the logos section block (lines 109-174, from `{/* Logos Section */}` through the closing `</div>` and `)}`)
2. Paste it AFTER the brand mood badges section (after line 270, before the closing `</div>` of `pl-0 md:pl-14`)
3. Keep the exact same conditional rendering: `{(visuals.logos?.primary || visuals.logos?.secondary || visuals.logos?.dark_mode) && (...)}`
4. Change the `mb-10` class on the logos wrapper div to `mt-10` since it now comes after other content instead of before
5. Also add `visuals.logos?.light_mode` to the conditional check so all 4 logo variants are considered

Do NOT change any other styling, layout, or logic in the component.
  </action>
  <verify>
    <automated>cd /home/chris/AISALESHT && grep -n "Kit de Logos" frontend/src/features/brand/sections/visuals/visuals-preview.tsx</automated>
  </verify>
  <done>The "Kit de Logos" section line number is AFTER the "Paleta Cromatica" and "Tipografia" sections, and AFTER the brand mood badges. The logos conditional also checks light_mode.</done>
</task>

<task type="auto">
  <name>Task 2: Add URL normalization to gallery logo filtering</name>
  <files>frontend/src/features/brand/sections/gallery/gallery-manager.tsx</files>
  <action>
The gallery filtering logic (lines 96-101) creates a Set of logo URLs and filters them from gallery images. This works when URLs match exactly, but can fail if one URL has a trailing slash or different path prefix.

Add URL normalization to make the comparison more robust:

1. Create a `normalizeUrl` helper function at the top of the component (or inline):
   ```typescript
   const normalizeUrl = (url: string) => {
       // Strip trailing slashes and any query params for comparison
       return url.split('?')[0].replace(/\/+$/, '');
   };
   ```

2. Update the logoUrls Set creation to normalize:
   ```typescript
   const logoUrls = new Set(
       Object.values(visuals.logos || {})
           .filter((url): url is string => typeof url === 'string' && url.length > 0)
           .map(normalizeUrl)
   );
   ```

3. Update the filter to normalize the comparison:
   ```typescript
   const filteredImages = images?.filter(img => !logoUrls.has(normalizeUrl(img.public_url))) || [];
   ```

This ensures logos are properly filtered from the gallery even with minor URL format differences.
  </action>
  <verify>
    <automated>cd /home/chris/AISALESHT && grep -n "normalizeUrl" frontend/src/features/brand/sections/gallery/gallery-manager.tsx</automated>
  </verify>
  <done>Gallery filtering uses normalized URL comparison. Logos assigned in LogoKit are excluded from gallery display regardless of trailing slash or query param differences.</done>
</task>

</tasks>

<verification>
1. In visuals-preview.tsx, the "Kit de Logos" heading appears at a higher line number than "Paleta Cromatica" and "Tipografia"
2. In gallery-manager.tsx, logoUrls Set uses normalizeUrl for robust filtering
3. No TypeScript errors in either file
</verification>

<success_criteria>
- Logo Kit section renders below palette and typography in the Visual Identity preview
- Gallery properly excludes images that are assigned as logos
- No regressions in existing visual identity display
</success_criteria>

<output>
After completion, create `.planning/quick/260319-nzs-fix-brand-studio-preview-logo-should-sho/260319-nzs-SUMMARY.md`
</output>
