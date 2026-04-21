# UI-SPEC — Brand Studio Nav Rail change

**Status:** mechanical.
**Scope:** inserción de 1 entrada + ajuste de icono.
**Files affected:**
- `frontend/src/features/brand-studio/lib/section-catalog.ts`
- `frontend/src/features/brand-studio/pages/section-page-map.ts`

---

## Cambio en `BRAND_SECTIONS`

**Before** (13 entries):
```ts
export const BRAND_SECTIONS: readonly BrandSectionMeta[] = [
  { slug: "publico", label: "Buyer personas", icon: Sparkles, kind: "collection" },
  { slug: "identity", label: "Identidad", icon: Fingerprint, kind: "singleton" },
  { slug: "positioning", label: "Posicionamiento", icon: Target, kind: "singleton" },
  { slug: "narrative", label: "Narrativa", icon: ScrollText, kind: "singleton" },
  // ... resto
];
```

**After** (14 entries):
```ts
import { MessageCircle } from "lucide-react";  // añadir al import

export const BRAND_SECTIONS: readonly BrandSectionMeta[] = [
  { slug: "publico", label: "Buyer personas", icon: Sparkles, kind: "collection" },
  { slug: "identity", label: "Identidad", icon: Fingerprint, kind: "singleton" },
  { slug: "estilo", label: "Estilo Comunicacional", icon: MessageCircle, kind: "singleton" },  // NEW
  { slug: "positioning", label: "Posicionamiento", icon: Target, kind: "singleton" },
  { slug: "narrative", label: "Narrativa", icon: ScrollText, kind: "singleton" },
  // ... resto igual
];
```

---

## Cambio en `SECTION_PAGE_MAP`

**Before:**
```ts
export const SECTION_PAGE_MAP = {
  identity: IdentityPage,
  legal: LegalPage,
  visuals: VisualsPage,
  contact: ContactPage,
  methodology: MethodologyPage,
  story: StoryPage,
  positioning: PositioningPage,
  narrative: NarrativePage,
  "communication-assets": CommunicationAssetsPage,
} as const satisfies Readonly<Record<string, () => React.JSX.Element>>;
```

**After:**
```ts
import { CommunicationStylePage, /* ... */ } from "./section-pages";

export const SECTION_PAGE_MAP = {
  identity: IdentityPage,
  estilo: CommunicationStylePage,  // NEW
  legal: LegalPage,
  // ... resto igual
} as const satisfies Readonly<Record<string, () => React.JSX.Element>>;
```

Actualizar también el docstring comment — reemplazar:
```
*   - personality  → own API via usePersonalityHooks (Sprint 2 deferred).
*   - voice        → subset of identity (voice_tone); renders under identity page.
```
por:
```
*   - avatars      → sub-entity, covered by PersonaDetailPage.
```
(el estilo deja de ser subset de identity porque ahora tiene su propia ruta).

---

## Opcional: redirect legacy links

Si hay enlaces externos (emails, bookmarks) a `?field=voice_tone` o `?field=voice_tone_clone`, considerar redirect en:

`frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/[section]/page.tsx`:

```ts
// Si section === "identity" y field es legacy, redirect a /estilo
const legacyVoiceFields = new Set(["voice_tone", "voice_tone_clone"]);
const field = searchParams?.field;
if (section === "identity" && typeof field === "string" && legacyVoiceFields.has(field)) {
  redirect(`/${tenantId}/brand-studio/estilo`);
}
```

No es bloqueante; la query `?field=voice_tone` simplemente no hace nada (no matchea field existente) después de remover los campos del schema — el page renderiza identity normal sin scroll target. Incluir redirect solo si hay tráfico medible a esos deep links.
