---
phase: quick-260319-mqz
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - frontend/src/features/brand/sections/visuals/single-image-picker.tsx
  - frontend/src/features/brand/sections/visuals/visuals-preview.tsx
autonomous: true
requirements: [fix-logo-display]

must_haves:
  truths:
    - "After uploading an image via LogoKit slot, the uploaded image is auto-selected for that slot (no extra gallery click needed)"
    - "Logo Kit preview section shows assigned logos under Visual Identity with label Kit de Logos"
    - "Gallery manager correctly filters out logo URLs (already works once logos data is populated)"
  artifacts:
    - path: "frontend/src/features/brand/sections/visuals/single-image-picker.tsx"
      provides: "Auto-select uploaded image after upload success"
    - path: "frontend/src/features/brand/sections/visuals/visuals-preview.tsx"
      provides: "Renamed section label from Activos de Marca to Kit de Logos"
  key_links:
    - from: "SingleImagePicker.uploadMutation.onSuccess"
      to: "onChange(public_url)"
      via: "Auto-select after upload completes"
      pattern: "onChange.*public_url"
---

<objective>
Fix logo display in Brand Studio Visual Identity: after uploading a logo via LogoKit slots, the image goes to the gallery but is never auto-assigned to the logo slot. This means `visuals.logos` stays empty, the preview shows no logos, and the gallery filter has nothing to exclude.

Purpose: Logos uploaded via LogoKit slots should auto-select for the slot, persisting to `visuals.logos` so preview and gallery filtering work correctly.
Output: Working logo upload-and-assign flow, renamed preview label.
</objective>

<execution_context>
@/home/chris/AISALESHT/.claude/get-shit-done/workflows/execute-plan.md
@/home/chris/AISALESHT/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@frontend/src/features/brand/sections/visuals/single-image-picker.tsx
@frontend/src/features/brand/sections/visuals/visuals-preview.tsx
@frontend/src/features/brand/sections/visuals/logo-kit.tsx
@frontend/src/features/brand/sections/visuals/visuals-form.tsx
@frontend/src/features/brand/api/index.ts
@frontend/src/features/brand/types/index.ts

<interfaces>
<!-- Data flow: SingleImagePicker -> LogoKit -> VisualsForm -> useBrandSettings -> PATCH API -->

From frontend/src/features/brand/types/index.ts:
```typescript
export interface BrandLogos {
    primary?: string;
    secondary?: string;
    dark_mode?: string;
    light_mode?: string;
    main?: string;
    inverted?: string;
    favicon?: string;
}

export interface BrandVisuals {
    // ... colors, typography, etc.
    logos?: BrandLogos;
}
```

From single-image-picker.tsx (current upload flow):
```typescript
// uploadMutation.onSuccess ONLY invalidates queries and shows toast
// It does NOT call onChange(uploaded_url) — THIS IS THE BUG
onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ["assets"] });
    setUploadFile(null);
    setUploadDesc("");
    toast.success("Imagen subida a la galeria");
}
```

From single-image-picker.tsx (gallery select — works correctly):
```typescript
const handleSelect = (url: string) => {
    onChange(url);
    setIsPickerOpen(false);
};
```

From logo-kit.tsx:
```typescript
const updateLogo = (key: keyof BrandLogos, url: string) => {
    onChange({ ...logos, [key]: url });
};
// SingleImagePicker onChange calls updateLogo(slot.key, url)
```

From assets API response shape:
```typescript
// assetsApi.upload returns the created asset object with public_url
// assetsApi.list returns array of assets with { id, public_url, ai_description, ... }
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Auto-select uploaded image in SingleImagePicker and rename preview label</name>
  <files>
    frontend/src/features/brand/sections/visuals/single-image-picker.tsx
    frontend/src/features/brand/sections/visuals/visuals-preview.tsx
  </files>
  <action>
**Root cause:** `SingleImagePicker.uploadMutation.onSuccess` only invalidates the gallery query and resets state. It never calls `onChange(uploaded_url)` to assign the uploaded image to the slot. As a result, `visuals.logos` stays empty after upload, the preview renders nothing, and gallery filter has nothing to exclude.

**Fix 1 — single-image-picker.tsx:**
Modify the `uploadMutation` to auto-select the uploaded image after successful upload:

1. The `assetsApi.upload()` returns the created asset object. Change `mutationFn` return type to capture this.
2. In `onSuccess(data)`, after invalidating queries, call `handleSelect(data.public_url)` to:
   - Set the uploaded URL as the selected value via `onChange(url)`
   - Close the dialog via `setIsPickerOpen(false)`
3. Keep the existing gallery invalidation and toast.

The mutation should look like:
```typescript
const uploadMutation = useMutation({
    mutationFn: async () => {
        const token = await getToken();
        if (!token || !uploadFile) return null;
        return assetsApi.upload(token, uploadFile, uploadDesc);
    },
    onSuccess: (data) => {
        queryClient.invalidateQueries({ queryKey: ["assets"] });
        setUploadFile(null);
        setUploadDesc("");
        if (data?.public_url) {
            handleSelect(data.public_url);
            toast.success("Imagen subida y seleccionada");
        } else {
            toast.success("Imagen subida a la galeria");
        }
    },
    onError: () => toast.error("Error al subir imagen")
});
```

Before implementing, verify `assetsApi.upload` return type by reading `frontend/src/lib/api/assets.ts` to confirm it returns an object with `public_url`.

**Fix 2 — visuals-preview.tsx line 113:**
Change the label from "Activos de Marca" to "Kit de Logos":
```
<ImageIcon className="w-4 h-4" /> Kit de Logos
```
  </action>
  <verify>
    <automated>cd /home/chris/AISALESHT && docker exec -t visionarias_client_dev npx tsc --noEmit --pretty 2>&1 | head -30</automated>
  </verify>
  <done>
    - SingleImagePicker auto-selects uploaded image by calling onChange(public_url) on upload success
    - Dialog closes after upload (same as gallery select behavior)
    - Preview label reads "Kit de Logos" instead of "Activos de Marca"
    - TypeScript compiles without errors
  </done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>Fixed logo upload flow: uploading via LogoKit slot now auto-assigns the image to the slot. Renamed preview label to "Kit de Logos".</what-built>
  <how-to-verify>
    1. Go to Brand Studio -> Visual Identity (edit mode)
    2. Click any empty LogoKit slot (e.g., "Logo Principal")
    3. In the dialog, go to "Subir Nueva" tab and upload an image
    4. Verify: dialog closes automatically and the uploaded image appears in the slot
    5. Click "Guardar Identidad Visual" at the bottom
    6. Verify: the preview section shows logos under "Kit de Logos" label (not "Activos de Marca")
    7. Verify: the uploaded logo does NOT appear in the Gallery grid (it should be filtered out)
    8. Refresh the page and confirm logos persist
  </how-to-verify>
  <resume-signal>Type "approved" or describe issues</resume-signal>
</task>

</tasks>

<verification>
- TypeScript compilation passes without errors
- Logo upload via LogoKit auto-selects and closes dialog
- Preview shows logos under "Kit de Logos" label
- Gallery correctly excludes assigned logo URLs
</verification>

<success_criteria>
- Uploading a logo via LogoKit slot auto-assigns it (no extra gallery click needed)
- Saving the form persists logos to backend
- Preview displays logos with "Kit de Logos" label
- Gallery filters out assigned logo URLs
</success_criteria>

<output>
After completion, create `.planning/quick/260319-mqz-fix-logo-display-show-logos-in-logo-kit-/260319-mqz-SUMMARY.md`
</output>
