# UI-SPEC — CommunicationStylePage

**Status:** requires-design (hand off ready; para mockups pixel-perfect invocar `ux-disruptivo`).
**Section slug:** `estilo`.
**Route:** `/{tenantId}/brand-studio/estilo`.
**Server component:** `CommunicationStylePage.tsx`.

---

## 1. Component Tree

```
CommunicationStylePage  [Server]
├─ SectionHeader  [shared]  — title, subtitle, optional actions
├─ if !activeProfile:
│   ├─ VoiceToneMigrationCard  [Client, optional]  — if BrandIdentity.voice_tone exists and not dismissed
│   └─ EmptyState  [Client]
│       ├─ PresetCtaCard  — abre PresetPickerDrawer
│       └─ CloneCtaCard  — abre CloneWizardDrawer
└─ else:
    └─ ActiveState  [Client]
        ├─ ProfileHeader  — activo: nombre + badge (preset|cloned|custom) + updated_at + menu "Cambiar estilo"
        ├─ DimensionsPanel  — 6 sliders + boton Editar
        ├─ LinguisticFingerprintPanel  — saludo, despedida, emojis, muletillas + boton Editar
        ├─ SampleExchangesPanel  — 3-6 ejemplos + boton Regenerar
        └─ ActionsFooter  — [Probar en conversación] [Ver instrucción compilada]

[Overlays globales activados desde CTAs / header menu]
├─ PresetPickerDrawer  [Client]
│   └─ PresetCard × 6  — de GET /personality/presets
├─ CloneWizardDrawer  [Client]
│   ├─ CloneStep1Material  — pegado/upload
│   ├─ CloneStep2Analyzing  — progress
│   └─ CloneStep3Preview  — previa + activar
└─ SimulateDrawer  [Client]
    └─ Conversation simulator
```

---

## 2. Data Flow

**Server-side on load:**
```ts
// CommunicationStylePage.tsx (Server Component)
const [activeProfile, legacyVoiceTone] = await Promise.all([
  fetchPersonalityActive(token),  // GET /api/v1/brand/personality/active
  fetchLegacyVoiceTone(token),    // GET /api/v1/brand/identity (voice_tone field si existe)
]);
```

**Client-side mutations via React Query:**
- `useActivePersonality()` — SWR-style, key `["personality", "active"]`.
- `usePresets()` — cacheable 24h (datos estáticos del backend).
- `useSelectPreset()` — POST /select-preset → invalida `["personality", "active"]`.
- `useClonePersonality()` — POST /clone, retorna profile con `is_active=false`.
- `useActivateProfile()` — POST /{id}/activate → invalida active.
- `useUpdateDimensions()` — PUT /{id}/dimensions, debounced 500ms.
- `useSimulate()` — POST /{id}/simulate.
- `useFromVoiceTone()` — POST /from-voice-tone.

---

## 3. Responsive Behavior

| Breakpoint | Layout |
|---|---|
| `< 640px` (mobile) | EmptyState cards stackean vertical. PresetPicker = fullscreen drawer. DimensionsPanel colapsa labels a una sola línea ("Calma ↔ Eléctrica" en hint). CloneWizard = fullscreen drawer. |
| `640–1024px` (tablet) | EmptyState 2-col grid. PresetPicker drawer right 480px. Dimensions sliders full width. |
| `> 1024px` (desktop) | EmptyState 2-col grid centrado max-w-4xl. PresetPicker drawer right 560px con 6 cards en grid 2×3. Clone wizard drawer right 720px. |

Todos los drawers = `Sheet` de shadcn; modales = `Dialog`.

---

## 4. Interaction Patterns

### EmptyState
- Click "Ver los 6 presets" → open `PresetPickerDrawer`.
- Click "Empezar a clonar" → open `CloneWizardDrawer`.
- `VoiceToneMigrationCard` (si aplica):
  - "Convertir en estilo inicial" → POST /from-voice-tone → loader → ActiveState.
  - "Empezar de cero" → dismiss card (persiste flag), card desaparece, sigue EmptyState.

### ActiveState
- Header "Cambiar estilo ▾" → dropdown con 3 opciones:
  - "Elegir otro preset" → abre PresetPickerDrawer.
  - "Clonar un estilo nuevo" → abre CloneWizardDrawer.
  - "Perfil desde cero" (futuro, oculto v1).
- DimensionsPanel:
  - Modo read-only inicial. Click "Editar" → habilita sliders.
  - Al mover slider: PUT debounced 500ms. Indicador "Guardando..." → "Guardado hace 1 s".
  - Preset activo + dimensiones modificadas → badge cambia a "preset (modificado)".
- SampleExchangesPanel:
  - "Regenerar" → POST /simulate → reemplaza los 3 ejemplos visibles.
- "Probar en conversación" → abre SimulateDrawer.
- "Ver instrucción compilada" → abre modal con `system_instruction` en textarea read-only (útil para debugging / tenants curiosos).

### PresetPickerDrawer
- Grid 2×3 de PresetCard.
- Card interacciones:
  - "Previa" → modal con 6 SampleExchange completos + dimensiones read-only.
  - "Activar" → POST /select-preset → cierra drawer → ActiveState refrescado. Toast "Estilo Cálida y Cercana activado".

### CloneWizardDrawer
- Drawer full con stepper superior (● / ○ / ○).
- Paso 1 (Material): radio (pegar / subir) + textarea grande o dropzone. Validación: mínimo 10 mensajes (split por newline). Botón Analizar habilitado cuando válido.
- Paso 2 (Análisis): checklist con progresión real del graph (si BE no emite progress SSE, usar polling cada 3 s a `GET /personality/{job_id}/status`). Mensaje "puedes cerrar y te avisamos".
- Paso 3 (Previa): dimensiones + fingerprint + ejemplos. Botón "Regenerar ejemplos" → POST /simulate. Botón "Ajustar dimensiones" → abre DimensionsPanel inline editable. "Activar este estilo" → POST /{id}/activate → cierra drawer → ActiveState.

### SimulateDrawer
- Quick pills ([Saludo] [Precio] [Objeción] [Interés] [Cierre]) precargan un mensaje típico en el textarea.
- "Generar respuesta" → POST /simulate → muestra agent_response.
- Otra simulación: limpia + reset.

---

## 5. Accessibility

- Todos los botones de CTA tienen `aria-label` explícito cuando el texto es ambiguo.
- Sliders: `role="slider"`, `aria-valuemin=0`, `aria-valuemax=1`, `aria-valuenow`, `aria-label="Energía"`, `aria-valuetext="Calma"` (texto semántico del bucket).
- Drawer: foco autoatrapado (shadcn por default), cerrable con Escape.
- Stepper del wizard: `aria-current="step"` en el paso activo.
- Cards de preset: `role="button"`, `tabIndex=0`, enter/space dispara Activar (o Previa según default).
- Live region para toast "Guardando..." → "Guardado".

---

## 6. Copy (Spanish Neutro LatAm, sin voseo)

- Title: **Estilo Comunicacional**.
- Subtitle: "Cómo habla tu marca en cada conversación. El SDR y las piezas auto-generadas usan este estilo."
- Empty CTAs: "Empezar con un preset" / "Clonar mi estilo".
- Hint empty: "Empieza con un preset; puedes clonar tu estilo después sin perder la configuración."
- Migration card: "Tienes un tono de voz cargado desde antes: [...]. ¿Quieres que lo convirtamos en un estilo inicial?"
- Dim slider ejemplo: "Energía · Calma ↔ Eléctrica".
- Clone wizard paso 1 hint: "Pega 10 o más mensajes tuyos reales. Variedad importa: saludos, objeciones, cierres, follow-ups."
- Clone paso 2 wait: "Esto suele tardar 2-4 minutos. Puedes cerrar esta ventana; te avisamos cuando termine."
- Toasts: "Estilo activado.", "Guardado.", "Error al guardar. Reintenta."

**Prohibido:** `elegí`, `dale`, `mirá`, `podés`. Usar imperativos neutros: `elige`, `activa`, `mira`, `puedes`.

---

## 7. Design Tokens

- Usar tokens de `frontend/src/app/globals.css`.
- Colores: default Shadcn + `--primary` Nicolify.
- Iconos: lucide-react. Preset icons son emojis (del backend `PresetDefinition.icon`).
- Spacing: rejilla de 4px (tailwind). Secciones separadas por `gap-6`.
- Cards: `rounded-lg border border-border bg-card p-6`.

---

## 8. Empty / Error / Loading States

| State | UI |
|---|---|
| Loading initial | Skeleton del ActiveState (bloques gris con `animate-pulse`). |
| Error fetching active | Banner rojo "No pudimos cargar tu estilo. Reintentar." + botón. |
| Clone pipeline fail | Paso 2 cambia a error: "No pudimos analizar tu material. Revisa el formato y reintenta." + botón Reintentar. |
| Simulate fail | Respuesta fallback: "(no pudimos generar una respuesta — revisa tu configuración)". |
| Slider PUT fail | Badge rojo "No guardado. Reintenta." junto al slider que falló. |
