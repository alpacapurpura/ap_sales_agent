# UI Spec: Copilot Chat Redesign — Rich Multimodal Surface

**Version:** 2.0
**Date:** 2026-04-21
**Status:** Ready for implementation
**Replaces:** `docs/domains/copilot/UI-SPEC.md` v1 (sidebar-v2 rail/history layout)

---

## Overview

El chat del Copilot Nicolify pasa de un input de texto plano a una superficie de comunicación rica y multimodal. El usuario puede enviar texto con Markdown, adjuntar archivos (imagen, audio, video, documento), grabar voz que se convierte en audio+transcripción reproducible, citar mensajes previos, y recibir respuestas del asistente compuestas de bloques heterogéneos (texto Markdown, tablas, código, imágenes, audios, citas RAG, cards interactivas).

El sidebar mantiene los 3 estados existentes (`collapsed / rail / full`) pero los controles pasan de un botón de ciclo a botones explícitos por estado. La columna `[rail-or-history]` es una sola columna CSS que cambia de 60px a 280px.

---

## §1 Sidebar Layout + States

### Grid CSS

```
CopilotSidebar → display: grid; gridTemplateColumns: <history> <chat> 60px
```

| Estado | `<history>` | `<chat>` | Rail |
|--------|-------------|----------|------|
| `collapsed` | 0px | 0px | 60px visible |
| `rail` | 0px | 380px | 60px visible |
| `full` | 280px | 400px | 60px visible |

Transición: `grid-template-columns 220ms cubic-bezier(.2,.8,.2,1)` (ya implementada — preservar).

### Mockup: Estado COLLAPSED

```
┌──────────────────────────────────────────────────────────────────┬──────────┐
│                    PAGE CONTENT                                  │   RAIL   │
│                                                                  │  [→]     │
│                                                                  │  ──────  │
│                                                                  │  [+]     │
│                                                                  │          │
│                                                                  │  (AB)    │
│                                                                  │  (CD)    │
│                                                                  │  (EF)    │
│                                                                  │  ···     │
│                                                                  │  más     │
└──────────────────────────────────────────────────────────────────┴──────────┘

Rail 60px: [→ Abrir chat] | [+ Nueva] | avatares recientes | "más"
```

### Mockup: Estado RAIL

```
┌──────────────────────────────────┬──────────────────────┬──────────┐
│           PAGE CONTENT           │      CHAT PANEL      │   RAIL   │
│                                  │  ┌────────────────┐  │  [←]     │
│                                  │  │ Chat · o4-mini │  │  ──────  │
│                                  │  ├────────────────┤  │  [≫]     │
│                                  │  │  mensajes...   │  │  ──────  │
│                                  │  │                │  │  [+]     │
│                                  │  ├────────────────┤  │          │
│                                  │  │  [composer]    │  │          │
│                                  │  └────────────────┘  │          │
└──────────────────────────────────┴──────────────────────┴──────────┘

Rail 60px: [← Cerrar chat] | [≫ Ver historial] | [+ Nueva]
```

### Mockup: Estado FULL

```
┌──────────┬──────────────────────┬──────────────────────┬──────────┐
│  PAGE    │     HISTORY 280px    │    CHAT PANEL 400px  │   RAIL   │
│          │  ┌──────────────────┐│  ┌────────────────┐  │  [←]     │
│          │  │ Conversaciones   ││  │ Chat · o4-mini │  │  ──────  │
│          │  │ [+ Nueva]        ││  ├────────────────┤  │  [«]     │
│          │  ├──────────────────┤│  │  mensajes...   │  │  ──────  │
│          │  │ Hoy              ││  │                │  │  [+]     │
│          │  │  • Mi brand [●]  ││  │                │  │          │
│          │  │  • Oferta XYZ    ││  ├────────────────┤  │          │
│          │  │ Ayer             ││  │  [composer]    │  │          │
│          │  │  • Growth Q1     ││  └────────────────┘  │          │
│          │  └──────────────────┘│                      │          │
└──────────┴──────────────────────┴──────────────────────┴──────────┘

Rail 60px: [← Cerrar chat] | [« Ocultar historial] | [+ Nueva]
```

### Mobile Behavior (< 768px)

- El sidebar no usa CSS grid de escritorio.
- En `collapsed`: solo el rail flota como FAB en esquina inferior derecha (botón circular 44px, `position: fixed; bottom: 1rem; right: 1rem`).
- En `rail` o `full`: un `Sheet` (Shadcn) ocupa pantalla completa desde la derecha con backdrop.
- El `Sheet` muestra el chat panel. Si `full`, muestra un switcher "Historial" / "Chat" con `Tabs` en el header del Sheet.
- Teclado virtual (keyboard) → el composer sube (`padding-bottom: env(keyboard-inset-height)`).

### Keyboard Shortcuts (sin cambios respecto a v1)

| Shortcut | Acción |
|----------|--------|
| `Ctrl+K` | Focus input copilot |
| `C` (fuera de input) | `setSidebarState("collapsed")` |
| `R` (fuera de input) | `setSidebarState("rail")` |
| `F` (fuera de input) | `setSidebarState("full")` |
| `N` (fuera de input) | Nueva conversación |
| `Escape` (en chat, sin slash open) | `setSidebarState("rail")` si en full; `setSidebarState("collapsed")` si en rail |

### Accesibilidad

- `<aside aria-label="Panel copilot" aria-expanded={isExpanded}>` — ya implementado, preservar.
- `<span role="status" aria-live="polite">` para anunciar cambios de estado — ya implementado.
- Rail: todos los botones con `aria-label` explícito (ver §2).
- Focus trap: cuando el Sheet mobile está abierto, el foco debe quedar dentro del Sheet.

---

## §2 Sidebar Rail & History Controls — Botones Explícitos

**Problema actual:** Un solo botón cicla `collapsed→rail→full→collapsed`. En rail, click va a `full`, pero si el usuario quiere cerrar el chat, hace click y expande el historial en vez de cerrar. El BUG que señala el prompt.

**Solución:** Cada estado tiene sus propios botones con intención inequívoca.

### Tabla de botones por estado

| Estado | Botón 1 | Botón 2 | Botón 3 | Botón 4 |
|--------|---------|---------|---------|---------|
| `collapsed` | `ChevronLeft` → rail ("Abrir chat") | — | — | — |
| `rail` | `ChevronLeft` → collapsed ("Cerrar chat") | `PanelRightOpen` → full ("Ver historial") | `Plus` ("Nueva conversación") | — |
| `full` | `ChevronLeft` → collapsed ("Cerrar chat") | `PanelRightClose` → rail ("Ocultar historial") | `Plus` ("Nueva conversación") | — |

**Notas:**
- En `collapsed`: el botón de abrir es el único CTA principal del rail. Icono `ChevronLeft` (la flecha apunta hacia el panel, indicando "abrir hacia aquí").
- En `rail` y `full`: los dos primeros botones cubren las dos intenciones (cerrar vs historial). El `Plus` para nueva conversación queda en tercer lugar.
- Todos los botones son `variant="ghost" size="icon"` con `Tooltip` side="left".

### ARIA labels

| Botón | aria-label |
|-------|-----------|
| ChevronLeft → rail | "Abrir chat" |
| ChevronLeft → collapsed | "Cerrar chat" |
| PanelRightOpen → full | "Ver historial" |
| PanelRightClose → rail | "Ocultar historial" |
| Plus | "Nueva conversación" |

### Avatares en collapsed

- Mostrar hasta 6 avatares de conversaciones recientes (ya implementado en `CopilotRail`).
- Click en avatar → `setConversationId(id)` + `setSidebarState("rail")`.
- "más" link → `setSidebarState("full")`.
- Preservar el tooltip con título de conversación.

### Historia en full: botón "Nueva conversación"

En `full`, el botón `Plus` en el rail duplica al que existe en `CopilotHistoryPanel`. Se puede mantener en ambos lugares — no hay conflicto. El del rail es más accesible (siempre visible).

---

## §3 ChatComposer — Compound Component

`ChatComposer` es el reemplazo de `CopilotChatPanel`'s input area + `CopilotInput.tsx`. Es un compound component con sub-componentes estáticos que se ensamblan en el panel.

### Jerarquía

```
ChatComposer ("use client" — features/copilot/components/composer/ChatComposer.tsx)
├── ChatComposer.SuggestedChips    (chips horizontales scroll — §9)
├── ChatComposer.ReplyPreview      (preview de mensaje citado — §8)
├── ChatComposer.ContextChips      (campos seleccionados — §10)
├── ChatComposer.AttachmentTray    (chips de archivos adjuntos — §5)
├── ChatComposer.Toolbar           (barra principal)
│   ├── ChatComposer.AttachmentButton  (paperclip)
│   ├── ChatComposer.VoiceButton       (micrófono)
│   ├── ChatComposer.TextArea          (textarea auto-grow)
│   └── ChatComposer.SendButton        (enviar / stop)
├── ChatComposer.VoiceOverlay      (grabación en progreso, reemplaza Toolbar)
└── ChatComposer.SlashAutocomplete (overlay arriba del Toolbar)
```

### Props del ChatComposer raíz

```typescript
interface ChatComposerProps {
  onSend: (payload: ComposerPayload) => void;
  onStop?: () => void;           // abortar streaming en curso
  disabled?: boolean;
  isStreaming?: boolean;
  placeholder?: string;
}

interface ComposerPayload {
  text: string;
  attachments: UploadedAttachment[];  // solo refs a uploads completados
  replyToMessageId: string | null;
  replyToPreview: string | null;      // texto truncado del mensaje citado
}
```

### Estado interno del ChatComposer

El ChatComposer gestiona su propio estado local. NO usa el store Zustand para estado de composición (excepto `selectedFields` que viene del store como read-only).

```typescript
// Estado local del ChatComposer
const [draft, setDraft] = useState("");
const [attachments, setAttachments] = useState<AttachmentItem[]>([]);
const [replyTo, setReplyTo] = useState<ReplyRef | null>(null);
const [voiceState, setVoiceState] = useState<VoiceState>("idle");
```

Ver §13 para extensiones del store global.

### Mockup: ChatComposer idle

```
┌─────────────────────────────────────────────────────────────────┐
│  💡 ¿Qué me falta?  📊 Mis métricas  ✍️ Mejora mi UVP          │  ← SuggestedChips (scroll-x)
├─────────────────────────────────────────────────────────────────┤
│  📎 doc.pdf [×]  🖼 foto.jpg [×]                               │  ← AttachmentTray (si hay archivos)
├─────────────────────────────────────────────────────────────────┤
│  Contexto: [Tagline ×] [UVP ×]                                 │  ← ContextChips (si hay campos)
├─────────────────────────────────────────────────────────────────┤
│  [📎] [🎙]  Escribe un mensaje...                    [→]       │  ← Toolbar
└─────────────────────────────────────────────────────────────────┘
```

### Mockup: ChatComposer con reply preview

```
┌─────────────────────────────────────────────────────────────────┐
│  💬 Respondiendo a: "El funnel de captación tiene..."  [×]      │  ← ReplyPreview
├─────────────────────────────────────────────────────────────────┤
│  [📎] [🎙]  Escribe tu respuesta...                   [→]       │  ← Toolbar
└─────────────────────────────────────────────────────────────────┘
```

### Mockup: ChatComposer grabando voz

```
┌─────────────────────────────────────────────────────────────────┐
│  [●] 00:14  Grabando...          ▐▌▐▐▌▐▌▐▌   [□ Cancelar] [■] │  ← VoiceOverlay
└─────────────────────────────────────────────────────────────────┘
```

### Mockup: ChatComposer slash open

```
┌─────────────────────────────────────────────────────────────────┐
│  ┌────────────────────────────────────────────────────────┐     │
│  │ / Buscar comando...                                    │     │
│  │ ─────────────────────────────────────────────────────  │     │  ← SlashAutocomplete overlay
│  │  /brand    Analiza tu Brand Studio                     │     │
│  │  /oferta   Revisa tus ofertas                          │     │
│  │  /funnel   Explica tu funnel                           │     │
│  └────────────────────────────────────────────────────────┘     │
│  [📎] [🎙]  /bra_                                     [→]       │  ← Toolbar (con texto parcial)
└─────────────────────────────────────────────────────────────────┘
```

### Sub-componente: ChatComposer.TextArea

- `Textarea` (Shadcn) con `resize: none`, `rows={1}`, auto-grow hasta `max-h-[140px]`.
- `id="copilot-input"` — para el shortcut `Ctrl+K`.
- `Enter` → enviar (si no hay slash open y no es recording).
- `Shift+Enter` → newline.
- `Escape` → si slash open: cerrar slash. Si reply preview: cancelar reply. Si ninguno: colapsar sidebar a estado anterior.
- `disabled` cuando `isStreaming` o `voiceState !== "idle"`.

### Sub-componente: ChatComposer.SendButton

- Icono `Send` (Lucide) cuando `!isStreaming`.
- Icono `Square` (Lucide, rojo) cuando `isStreaming` → click llama `onStop()`.
- `disabled` cuando `!canSend && !isStreaming`.
- `canSend = draft.trim().length > 0 || attachments.some(a => a.status === "uploaded")`.
- aria-label: "Enviar" / "Detener respuesta".

### Sub-componente: ChatComposer.AttachmentButton

Reutiliza `AttachmentButton` existente con `accept` expandido:

```typescript
accept="image/*,audio/*,video/*,.pdf,.docx,.txt,.md,.pptx,.csv,.xlsx"
```

Drag-and-drop en el área del composer: el textarea acepta drop de archivos (evento `onDrop`). Paste de imagen desde clipboard (`onPaste` → detectar `items[i].type.startsWith("image/")`).

### Sub-componente: ChatComposer.VoiceButton

Reutiliza `VoiceButton` existente. Al hacer click cuando `idle`:
1. Llama `startRecording()`.
2. El `ChatComposer` reemplaza visualmente el `Toolbar` con `VoiceOverlay`.

Al click cuando `recording` (o desde VoiceOverlay):
- "Stop" → `stopRecording()` → obtiene transcript + blob.
- Genera un `UploadedAttachment` de tipo `audio` (upload en paralelo al obtener transcript).
- El transcript se inyecta en el draft del textarea.
- El audio chip aparece en `AttachmentTray`.

### Disabled states

| Condición | Componentes deshabilitados |
|-----------|---------------------------|
| `isStreaming` | Textarea, SendButton (cambia a Stop), AttachmentButton, VoiceButton |
| `voiceState === "recording"` | TextArea, AttachmentButton, SendButton |
| `voiceState === "transcribing"` | TextArea, AttachmentButton, VoiceButton, SendButton |
| Uploads pendientes al enviar | SendButton muestra spinner, texto "Esperando uploads..." |

---

## §4 Voice Recording UX

### Estados del VoiceButton

```
idle  →  [click]  →  requesting-permission  →  recording  →  [stop]  →  transcribing  →  done
                              ↓                     ↓
                        denied (error)        [cancel]
                                                    ↓
                                                  idle
```

### Estados visuales del VoiceButton

| Estado | Visual del botón | Componente de overlay |
|--------|------------------|-----------------------|
| `idle` | `Mic` icon, ghost border | ninguno |
| `recording` | `Mic` icon rojo, pulsante, `border-red-500/50 bg-red-500/20` | `VoiceOverlay` reemplaza Toolbar |
| `transcribing` | `Loader2` spin, `border-purple-500/30` | `VoiceOverlay` con "Transcribiendo..." |
| `done` | vuelve a idle | ninguno |

### VoiceOverlay

```
┌─────────────────────────────────────────────────────────────────┐
│  [●] 00:14  ▐▌▐▌▐▐▌▐▌▐▌ (waveform bars animados css)  [X] [■]  │
└─────────────────────────────────────────────────────────────────┘
```

- `[●]` dot rojo pulsante.
- Timer en `font-mono` (formato `mm:ss`).
- Waveform: 8-12 barras `<div>` con alturas aleatorias animadas via CSS `@keyframes`. No requiere Web Audio API — es decorativo.
- `[X]` Cancelar → `cancelRecording()` → descarta audio y transcript.
- `[■]` Detener → `stopRecording()` → sigue al transcribing state.

### Flujo post-stop

```
stopRecording() → Promise<string>  (transcript)
     ↓ en paralelo
uploadAudio(blob) → POST /copilot/media/upload → { asset_id, public_url, mime, size_bytes }
     ↓ ambos resueltos
setDraft(transcript)                    // prefill textarea con texto
appendAttachment({                      // chip en AttachmentTray
  kind: "audio",
  file: audioBlob as File,
  status: "uploaded",
  assetId: asset_id,
  publicUrl: public_url,
  mimeType: mime,
  transcript: transcript
})
```

### Error handling

| Error | UI feedback |
|-------|-------------|
| Permiso denegado (`NotAllowedError`) | `Alert` inline debajo del composer: "No se pudo acceder al micrófono. Verifica los permisos del navegador." |
| Error de red al transcribir | `Alert` inline: "Error al transcribir. Intenta de nuevo." Botón "Reintentar" llama `stopRecording()` otra vez con el mismo blob (guardado en ref). |
| Error de red al subir audio | Chip en estado `error` con botón "Reintentar upload". El mensaje puede enviarse solo con transcript (sin audio). |

---

## §5 Attachment Flow

### Tipos aceptados y MIME validation

| kind | MIMEs aceptados | Icono Lucide |
|------|----------------|--------------|
| `image` | `image/jpeg, image/png, image/gif, image/webp, image/svg+xml` | `Image` |
| `audio` | `audio/webm, audio/mp4, audio/ogg, audio/mpeg, audio/wav` | `Mic` |
| `video` | `video/mp4, video/webm, video/ogg` | `Video` |
| `document` | `application/pdf, application/vnd.openxmlformats-officedocument.*,  text/plain, text/markdown, text/csv, application/vnd.ms-excel` | `FileText` |

Validación en el cliente: si el MIME no encaja, mostrar `toast` error "Tipo de archivo no soportado: {name}". No añadir al tray.

### Tamaño máximo

- Imagen: 10MB. Audio: 25MB. Video: 100MB. Documento: 20MB.
- Si excede: toast "El archivo {name} supera el límite de {N}MB."

### Chip de attachment (AttachmentChip)

Reemplaza `DocumentChip` con soporte multi-tipo:

```typescript
type AttachmentStatus = "pending" | "uploading" | "uploaded" | "error";

interface AttachmentItem {
  id: string;                   // uuid local
  kind: "image" | "audio" | "video" | "document";
  file: File;
  status: AttachmentStatus;
  progress: number;             // 0-100 durante uploading
  assetId?: string;             // del server tras upload
  publicUrl?: string;
  mimeType?: string;
  transcript?: string;          // solo para audio
  error?: string;
}
```

### Visual del chip por estado

| Status | Visual |
|--------|--------|
| `pending` | Icono gris, nombre truncado, `[×]` para cancelar |
| `uploading` | Progress bar debajo del nombre (usa `Progress` Shadcn), porcentaje |
| `uploaded` | `CheckCircle2` verde, nombre, `[×]` para quitar |
| `error` | `XCircle` rojo, "Error" label, botón "Reintentar" |

Para imágenes en `uploaded`: thumbnail 32×32px con `object-fit: cover` antes del nombre.

### Tray layout

```
┌──────────────────────────────────────────────────────────────────┐
│  🖼 foto.jpg ████████░░ 80%    📄 brief.pdf ✓  [×]             │
└──────────────────────────────────────────────────────────────────┘
```

- `flex-wrap gap-1.5` dentro de `AttachmentTray`.
- Visible solo cuando `attachments.length > 0`.

### Upload API

```typescript
// POST /copilot/media/upload (multipart/form-data)
// Retorna: { asset_id: string, public_url: string, mime: string, size_bytes: number, kind: string }

// La mutación React Query usa onUploadProgress para actualizar progress:
const uploadMutation = useMutation({
  mutationFn: (file: File) => uploadCopilotMedia(file, {
    onProgress: (pct) => updateAttachmentProgress(id, pct)
  }),
  onSuccess: (data, _, id) => markAttachmentUploaded(id, data),
  onError: (_, __, id) => markAttachmentError(id),
});
```

### Envío con attachments pendientes

Si hay uploads en `uploading` al click de Enviar:
- El botón de Send muestra `Loader2` + "Esperando..." y está deshabilitado.
- Cuando todos los uploads resuelven (success o error), el send se habilita.
- Si alguno quedó en `error`, el usuario puede quitar el chip o reintentar antes de enviar.

---

## §6 Message Rendering — BlockDispatcher

### Tipo canónico de bloque

```typescript
type BlockKind =
  | "text" | "image" | "audio" | "video" | "document"
  | "table" | "code" | "citation" | "card" | "tool_result" | "quote_reply";

interface MessageBlock {
  id: string;
  kind: BlockKind;
  // text
  markdown?: string;
  // image
  url?: string;
  alt?: string;
  width?: number;
  height?: number;
  // audio
  audioUrl?: string;
  audioMime?: string;
  duration?: number;
  transcript?: string;
  // video
  videoUrl?: string;
  poster?: string;
  // document
  docUrl?: string;
  filename?: string;
  sizeBytes?: number;
  // table
  columns?: string[];
  rows?: Record<string, string>[];
  caption?: string;
  recommended?: string;
  // code
  code?: string;
  language?: string;
  // citation
  source?: string;
  snippet?: string;
  citationUrl?: string;
  citationIndex?: number;
  // card
  cardType?: string;         // mapea al UIAction.type existente
  cardData?: UIAction;
  // tool_result
  toolName?: string;
  toolResult?: string;
  isError?: boolean;
  // quote_reply
  quotedMessageId?: string;
  quotedText?: string;       // preview truncado
  quotedRole?: "user" | "assistant";
  quotedTimestamp?: number;
}
```

### BlockDispatcher

```
BlockDispatcher ("use client" — features/copilot/components/blocks/BlockDispatcher.tsx)
  Recibe: block: MessageBlock
  Despacha a:

  "text"        → TextBlock
  "image"       → ImageBlock
  "audio"       → AudioBlock
  "video"       → VideoBlock
  "document"    → DocumentBlock
  "table"       → TableBlock
  "code"        → CodeBlock
  "citation"    → CitationBlock
  "card"        → CardBlock  →  dispatch por cardType al componente existente
  "tool_result" → ToolResultBlock
  "quote_reply" → QuoteReplyBlock
```

### TextBlock

- **Librería:** `react-markdown` + `remark-gfm` + `rehype-sanitize`.
- Soporte: tablas GFM, task lists, strikethrough, autolinks, code fences.
- Code fences inline: `CodeBlock` anidado con Shiki (language highlight + copy button).
- Streaming: `markdown` se concatena via `appendToLastAssistant` (ya implementado). El TextBlock re-renderiza con el string completo actualizado. El cursor pulsante `animate-pulse` se muestra mientras `isStreaming`.
- Estilos via `prose prose-sm dark:prose-invert` de Tailwind Typography (o clases semánticas equivalentes si Tailwind Typography no está instalado — verificar en `globals.css`).
- `rehype-sanitize` desactiva scripts, iframes, onclick. Preserva: links (con `rel="noopener noreferrer" target="_blank"`), imágenes (remoto permitido), tables, code.

```
TextBlock ARIA:
  <div role="region" aria-label="Mensaje del asistente">
    <div aria-live="polite" aria-atomic="false">
      {markdown rendered}
    </div>
  </div>
```

### ImageBlock

```
┌────────────────────────────────────────┐
│  [thumbnail 200px max-width, rounded]  │
│  Alt text debajo en text-xs            │
└────────────────────────────────────────┘
```

- Thumbnail clicable → lightbox (Dialog Shadcn, imagen a pantalla completa).
- Loading: `Skeleton` mientras la imagen carga (usa `onLoad` + `useState(false)`).
- Error fallback: placeholder gris con `ImageOff` (Lucide) icon.
- `<img alt={alt ?? "Imagen adjunta"} loading="lazy">`.

### AudioBlock

```
┌──────────────────────────────────────────────────────────────────┐
│  🎙 Audio (00:14)                                                │
│  ▶  [────────●────────────────────────]  0:14 / 0:45            │
│  ↓ Ver transcripción                                             │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ "El funnel de captación tiene tres etapas principales..."  │  │  ← collapsed por defecto
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

- HTML5 `<audio>` con controles custom (play/pause, scrubber `<input type="range">`).
- No se usa `<audio controls>` nativo — los controles nativos tienen estilos inconsistentes.
- Velocidad: botón `1x / 1.5x / 2x` (cicla).
- Transcripción: `Collapsible` (Shadcn), cerrado por defecto. Click "Ver transcripción" / "Ocultar".
- ARIA: `role="region" aria-label="Reproductor de audio"`, `aria-label="Reproducir"` / `"Pausar"` en el botón.

### VideoBlock

- Thumbnail clickable (usa `poster` URL si disponible, o frame extraído del server).
- Click → reproduce inline usando `<video>` con controles nativos.
- No se usa un player custom para video (complejidad alta, controles nativos suficientes).
- Loading skeleton mientras el video buffer.

### DocumentBlock

```
┌──────────────────────────────────────────────────────────────────┐
│  📄  brief-proyecto.pdf          256 KB                         │
│      [Abrir ↗]  [Descargar ↓]                                   │
└──────────────────────────────────────────────────────────────────┘
```

- Icono varía por extensión: `FileText` (PDF/TXT/MD), `Table2` (CSV/XLSX), `FileSpreadsheet` (XLSX), `Presentation` (PPTX), `File` (fallback).
- `sizeBytes` formateado: `formatFileSize(bytes)` → "256 KB", "1.2 MB".
- "Abrir" → `window.open(docUrl, "_blank", "noopener")`.
- "Descargar" → `<a href={docUrl} download={filename}>`.

### TableBlock

- Usa `Table, TableHeader, TableBody, TableRow, TableHead, TableCell` de Shadcn.
- `overflow-x-auto` en contenedor para scroll horizontal.
- Caption opcional arriba de la tabla.
- Mobile: las tablas largas (>4 columnas) colapsan a vista de cards (cada fila = card vertical). Implementado con CSS `@media (max-width: 640px)` en el componente.
- Fila `recommended` highlight como en `ComparisonTable` existente (preservar comportamiento).

### CodeBlock

```
┌──────────────────────────────────────────────────────────────────┐
│ python                                           [Copiar ✓]     │
│ ─────────────────────────────────────────────────────────────── │
│  def calcular_cac(spend, nuevos_clientes):                       │
│      return spend / nuevos_clientes                              │
└──────────────────────────────────────────────────────────────────┘
```

- Shiki para syntax highlighting. Tema: `github-dark` en dark mode, `github-light` en light mode.
- Si Shiki no está instalado aún: usar `<pre><code>` con clases de Tailwind (`bg-muted`, `font-mono text-xs`).
- Botón "Copiar": `navigator.clipboard.writeText(code)` → estado "Copiado ✓" por 2s.
- Label de lenguaje en `text-xs text-muted-foreground`.

### CitationBlock

```
┌──────────────────────────────────────────────────────────────────┐
│  [1] Brand Studio — Identidad de marca                          │
│      "Los pilares de metodología definen cómo..."  ▼ Ver más    │
└──────────────────────────────────────────────────────────────────┘
```

- Aparece debajo del `TextBlock` del mensaje assistant cuando el backend emite citas RAG.
- `citationIndex` muestra el número `[1]`, `[2]`, etc.
- `source` es el nombre del documento/sección.
- `snippet` truncado a ~120 chars. `Collapsible` para ver completo.
- `citationUrl` si disponible → link externo.
- ARIA: `<aside aria-label="Fuente [N]">`.

### CardBlock

El `CardBlock` es el adaptador entre el nuevo modelo de bloques y los componentes de cards existentes. Usa el mismo dispatch que `AssistantMessage.renderUIAction`:

```typescript
// features/copilot/components/blocks/CardBlock.tsx
function CardBlock({ block }: { block: MessageBlock }) {
  if (!block.cardData) return null;
  return renderUIAction(block.cardData, 0, block.id, sendCardAction);
}
```

Todos los componentes existentes (`ProposalCard`, `AlternativesCard`, `CheckpointCard`, `ClarifyCard`, `InterviewCompleteCard`, `MetricSummaryCard`, `ComparisonTable`, `ProgressChecklist`, `MultiOptionSelector`, `NavigationCard`) se preservan sin cambios. Solo cambia el mecanismo de invocación.

### ToolResultBlock

```
┌──────────────────────────────────────────────────────────────────┐
│  🔧 brand_health_check  ▼                                        │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  { "health_score": 72, "missing": ["methodology"] }       │  │  ← Collapsible, cerrado
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

- `Collapsible` cerrado por defecto.
- Si `isError`: borde rojo, icono `AlertCircle`.
- El result se renderiza como JSON formateado en `<pre>` si es parseable, texto plano si no.

### QuoteReplyBlock

```
┌──────────────────────────────────────────────────────────────────┐
│  ┊  Tú · hace 5 min                                              │
│  ┊  "¿Cómo está mi funnel de captación?"                        │
└──────────────────────────────────────────────────────────────────┘
```

- Borde izquierdo `border-l-2 border-muted-foreground/40`.
- `quotedRole`: "Tú" si `user`, nombre del asistente si `assistant`.
- `quotedText` truncado a 100 chars + "..." si más largo.
- Click → scroll al mensaje original (usa `document.getElementById(quotedMessageId)?.scrollIntoView`).
- ARIA: `aria-label="Mensaje citado de {role}"`.

### Message wrapper por rol

```
AssistantMessageV2 ("use client"):
  <div class="flex gap-2.5 animate-in slide-in-from-bottom-2">
    <SparklesAvatar />   ← avatar circular 28px, purple-100/purple-900
    <div class="max-w-[85%] space-y-2">
      {blocks.map(block => <BlockDispatcher key={block.id} block={block} />)}
    </div>
  </div>

UserMessageV2 ("use client"):
  <div class="flex justify-end animate-in slide-in-from-bottom-2">
    <div class="max-w-[85%] space-y-1.5">
      {blocks.map(block => <BlockDispatcher key={block.id} block={block} />)}
    </div>
  </div>
```

User messages: el bloque de texto tiene `bg-purple-600 text-white rounded-2xl rounded-br-sm`. Los attachments del usuario se muestran como `DocumentBlock`/`ImageBlock`/`AudioBlock` con estilo invertido (sobre fondo morado).

### Adapter: CopilotMessage legacy → MessageBlock[]

Para compatibilidad con el store actual (donde `content: string` y `uiActions: UIAction[]`):

```typescript
// features/copilot/utils/message-adapter.ts
function adaptLegacyMessage(msg: CopilotMessage): MessageBlock[] {
  const blocks: MessageBlock[] = [];
  if (msg.content) {
    blocks.push({ id: `${msg.id}-text`, kind: "text", markdown: msg.content });
  }
  msg.uiActions?.forEach((action, idx) => {
    blocks.push({
      id: `${msg.id}-card-${idx}`,
      kind: "card",
      cardType: action.type,
      cardData: action,
    });
  });
  return blocks;
}
```

Esta función se usa en `AssistantMessageV2` y `UserMessageV2`. El store puede opcionalmente migrar a `blocks[]` en una fase posterior.

---

## §7 Streaming UX

### Estados del mensaje en streaming

```
status: "thinking" + NO placeholder en messages → mostrar TypingIndicator
status: "streaming" + placeholder en messages  → mostrar TextBlock con cursor
status: "done"                                  → TextBlock finalizado, quitar cursor
```

El cursor pulsante es `<span class="inline-block h-4 w-0.5 animate-pulse bg-purple-500">` (ya implementado, preservar).

### Block streaming

El backend puede emitir eventos:
- `block_append`: nuevo bloque añadido al mensaje en curso → `store.addBlock(msgId, block)`
- `block_update`: actualización del último bloque (text concat) → `store.updateLastBlock(msgId, chunk)`
- `text_chunk` (legacy): concatenar al último `TextBlock` (compatibilidad hacia atrás)

El `TextBlock` re-renderiza de forma eficiente. Dado que `react-markdown` re-parsea en cada render, para mensajes largos en streaming se puede mostrar texto plano (sin MD) durante el streaming y cambiar a MD al finalizar. Decisión: implementar ambos y elegir en `ChatPanelV2` según `isStreaming`.

### Stop button

Cuando `status === "streaming"` o `status === "thinking"`, el `ChatComposer.SendButton` muestra `Square` rojo con aria-label "Detener respuesta". Click → `onStop()` → el hook `useCopilotChat` llama al `AbortController.abort()`.

Tras el abort: el mensaje queda con los bloques ya recibidos. El store pone `status: "done"`. No se muestra error — es una acción voluntaria del usuario.

### scroll-to-bottom inteligente

El scroll auto-sticks al fondo mientras el usuario no haya hecho scroll manual hacia arriba. Si el usuario scrolleó up durante streaming (para releer), NO se fuerza scroll al fondo con cada chunk. Se muestra un botón flotante "↓ Ir al final" que re-activa el stick.

El virtualizer `@tanstack/react-virtual` se mantiene. Para bloques con altura variable (imágenes, audio), `estimateSize` se ajusta:
- `text`: 60px base + ~20px por línea estimada.
- `image`: 240px.
- `audio`: 120px.
- `video`: 200px.
- `card`: 180px.
- `document`: 72px.
- `code`: 100px.
- Default: 80px.

`measureElement` corrige las estimaciones una vez el DOM renderiza.

---

## §8 Reply-Quote Interaction

### Trigger

- **Desktop hover:** hover sobre un mensaje → menú contextual aparece a la derecha del bubble con botón `Reply` (icono `CornerUpLeft` Lucide).
- **Mobile long-press:** `onContextMenu` o `onTouchStart` con timer 500ms → bottom sheet con opciones.
- **Solo opción por ahora:** "Responder". (Copiar y "Compartir" son futuras.)

### Flujo

```
1. Usuario hover/long-press sobre mensaje M
2. Click "Responder"
3. ChatComposer.ReplyPreview aparece con:
   - role label ("Tú" / asistente)
   - quotedText primeros 100 chars
   - botón [×] para cancelar
4. setReplyTo({ messageId: M.id, preview: M.text.slice(0, 100), role: M.role })
5. Focus al textarea automáticamente
6. Usuario escribe y envía
7. ComposerPayload incluye replyToMessageId + replyToPreview
8. Backend recibe reply context
9. Mensaje user generado incluye QuoteReplyBlock como primer bloque
10. setReplyTo(null) tras envío
```

### ReplyPreview visual

```
┌──────────────────────────────────────────────────────────────────┐
│  ┊  Respondiendo a:  Tú · hace 3 min                            │
│  ┊  "¿Cuándo debo lanzar mi oferta premium?"                    │
│                                              [× Cancelar reply] │
└──────────────────────────────────────────────────────────────────┘
```

- `border-l-2 border-accent` + `bg-accent/5` + `rounded-r-md`.
- Botón `[×]` con `aria-label="Cancelar respuesta"`.

---

## §9 Suggested Chips (Smart)

### Componente: SuggestedChips

```
// [COPILOT-SUGGESTIONS-ENGINE]
// Anchor para el motor de sugerencias dinámicas.
// Hoy: array estático por ruta (ver SuggestedActions.tsx existente).
// Futuro: POST /copilot/suggestions → { chips: { label, prompt }[] }
//         con contexto de ruta + historial reciente + campos incompletos.
// El contrato de datos del hook useSuggestions() debe mantenerse estable.
```

```typescript
// hooks/use-suggestions.ts
interface SuggestionChip {
  id: string;
  label: string;
  prompt: string;
  icon?: string;    // nombre de icono Lucide, futuro
}

function useSuggestions(): { chips: SuggestionChip[]; isLoading: boolean } {
  // [COPILOT-SUGGESTIONS-ENGINE] stub: return from ROUTE_SUGGESTIONS map
  const currentRoute = useCopilotStore(s => s.currentRoute);
  return { chips: getSuggestionsForRoute(currentRoute), isLoading: false };
}
```

### Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ ←fade  [💡 ¿Qué me falta?] [📊 Mis métricas] [✍️ UVP] [...]  fade→ │
└──────────────────────────────────────────────────────────────────┘
```

- `flex overflow-x-auto gap-2 px-1 py-1` sin scrollbar visible (`scrollbar-hide` class).
- Fade edges: `mask-image: linear-gradient(to right, transparent, black 8px, black calc(100% - 8px), transparent)`.
- Cada chip: `Button variant="outline" size="sm"` con `rounded-full`, `text-xs`, `whitespace-nowrap`.
- Click en chip → `setDraft(chip.prompt)` + foco en textarea (el usuario puede editar antes de enviar).
- `SuggestedChips` se oculta cuando `messages.length > 0` (hay conversación activa). Solo visible al inicio.

---

## §10 Context Chips

Integración del `ContextChips.tsx` existente en el `ChatComposer`:

- Se posiciona entre `AttachmentTray` y la `Toolbar` (o entre ReplyPreview y Toolbar si hay reply).
- Misma lógica existente: lee `selectedFields` del store, permite remover por campo.
- **Cambio:** límite visual de 3 chips visibles + "+N más" expandible (evitar que el composer crezca mucho con contexto largo).
  - Si `selectedFields.length <= 3`: mostrar todos.
  - Si `selectedFields.length > 3`: mostrar 3 + badge `+N más` clicable → expande a lista completa inline.
- Botón "Limpiar todo" solo visible cuando `selectedFields.length > 1`.
- Se mantiene el `Badge variant="secondary"` purple existente.

---

## §11 Interaction Matrix

| Acción del usuario | Componente | Resultado | Edge cases |
|--------------------|-----------|-----------|-----------|
| Typing en textarea | `ChatComposer.TextArea` | `setDraft(value)`, auto-grow hasta 140px | `/` al inicio → abrir SlashAutocomplete |
| `Enter` (sin Shift) | `ChatComposer.TextArea` | `handleSend()` si `canSend` | Ignorado si slash open; ignorado si `isStreaming` |
| `Shift+Enter` | `ChatComposer.TextArea` | Newline en textarea | — |
| `Escape` | `ChatComposer.TextArea` | 1) Cerrar slash si open; 2) Cancelar reply si reply; 3) Colapsar sidebar | Prioridad en orden |
| Click `/` chip del slash | `SlashAutocomplete` | `setDraft("/${cmd.name} ")` + foco textarea | — |
| Click paperclip | `ChatComposer.AttachmentButton` | Abrir file picker (multi, todos los tipos) | Si `isStreaming` → deshabilitado |
| Drag-drop archivo en textarea | `ChatComposer.TextArea` | `onDrop` → añadir al AttachmentTray | Solo archivos (no texto) |
| Paste imagen del clipboard | `ChatComposer.TextArea` | `onPaste` → detectar imagen → añadir attachment | Solo si items[i].type es imagen |
| Click micrófono (idle) | `ChatComposer.VoiceButton` | `startRecording()` → VoiceOverlay | Si permiso denegado → Alert error |
| Click Stop (VoiceOverlay) | `VoiceOverlay` | `stopRecording()` → transcript en draft + audio chip | Si red falla → Alert retry |
| Click Cancelar (VoiceOverlay) | `VoiceOverlay` | `cancelRecording()` → descarta todo | — |
| Click Enviar (canSend) | `ChatComposer.SendButton` | `onSend(payload)` → clear composer | Si uploads pendientes → spinner |
| Click Stop (isStreaming) | `ChatComposer.SendButton` | `onStop()` → AbortController.abort() | Mensaje queda con bloques parciales |
| Hover mensaje | `AssistantMessageV2 / UserMessageV2` | Mostrar menú contextual con "Responder" | Solo si no en streaming |
| Click "Responder" | Menú contextual | `setReplyTo(...)` + foco textarea | — |
| Click `[×]` en ReplyPreview | `ChatComposer.ReplyPreview` | `setReplyTo(null)` | — |
| Click chip sugerencia | `SuggestedChips` | `setDraft(chip.prompt)` + foco | — |
| Click `[×]` en ContextChip | `ChatComposer.ContextChips` | `removeSelectedField(fieldId)` | — |
| Click `[×]` en AttachmentChip | `AttachmentTray` | Remover de attachments | Si `uploading` → cancelar upload |
| "Reintentar" upload error | `AttachmentChip` | Re-lanzar `uploadMutation.mutate(file)` | — |
| Click thumbnail imagen | `ImageBlock` | Abrir lightbox `Dialog` | Escape cierra lightbox |
| Click "Ver transcripción" | `AudioBlock` | `Collapsible` se abre | — |
| Click cita | `QuoteReplyBlock` | scroll al mensaje original | Si no está en DOM (virtualizer) → scroll to index |
| Long-press mobile (500ms) | Mensaje | Bottom Sheet con "Responder" | cancelar si touch move > 10px |
| Draft preservado al cerrar chat | `ChatComposer` | `localStorage.setItem("copilot.draft", draft)` + restaurar en mount | Solo si draft no vacío |
| Nueva conversación | `CopilotRail` `Plus` | `createConversation()` + `clearDraft()` | — |
| Abrir conversación del historial | `ConversationItem` | `clearDraft()` + load messages | — |

---

## §12 Data Flow

### Flujo completo de envío

```
User types → ChatComposer local state (draft)
     ↓
Click Enviar
     ↓
ChatComposer.handleSend()
  → await pending uploads
  → build ComposerPayload { text, attachments, replyToMessageId }
  → onSend(payload)
     ↓
CopilotChatPanel.handleSend(payload)
  → addMessage({ role: "user", blocks: buildUserBlocks(payload) })  // store
  → addMessage({ role: "assistant", blocks: [], status: "thinking" }) // placeholder
  → setStatus("thinking")
  → useCopilotChat.sendMessage(payload)
     ↓
streamCopilotChat(chatPayload, callbacks, token)
  → POST /api/v1/copilot/chat (SSE stream)
     ↓
SSE eventos:
  "text_chunk" → store.appendToLastTextBlock(chunk)
  "block_append" → store.addBlockToLastAssistant(block)
  "tool_result" → store.addBlockToLastAssistant(toolResultBlock)
  "ui_action"  → store.addBlockToLastAssistant(cardBlock)  [adapter]
  "status"     → store.setStatus(state)
  "done"       → store.setStatus("done"), setConversationId(id)
  "error"      → store.setStatus("done"), addErrorBlock
     ↓
BlockDispatcher renders blocks in AssistantMessageV2
```

### Dónde vive cada estado

| Estado | Ubicación |
|--------|-----------|
| `draft` (texto en composición) | `ChatComposer` local state + `localStorage` |
| `attachments[]` | `ChatComposer` local state |
| `replyTo` | `ChatComposer` local state |
| `voiceState` | `ChatComposer` local state |
| `messages[]` | `copilot-store` (Zustand) |
| `status` | `copilot-store` |
| `sidebarState` | `copilot-store` + `localStorage` |
| `selectedFields[]` | `copilot-store` |
| `conversationId` | `copilot-store` |
| `uploadProgress` por archivo | `ChatComposer` local state (via attachments[].progress) |
| `suggestions[]` | `useSuggestions` hook (stub → React Query futuro) |

---

## §13 Store Extensions Required

El `copilot-store.ts` actual requiere las siguientes extensiones:

### 1. Migrar CopilotMessage a soporte de blocks

```typescript
// Extensión backward-compatible — preservar `content` y `uiActions` para compatibilidad
interface CopilotMessage {
  id: string;
  role: MessageRole;
  content: string;         // PRESERVAR — usado por legacy adapter
  timestamp: number;
  toolCalls?: { ... };     // PRESERVAR
  uiActions?: UIAction[];  // PRESERVAR
  blocks?: MessageBlock[]; // NUEVO — si presente, BlockDispatcher lo usa; si null, adapter corre
  status?: "thinking" | "streaming" | "done" | "error"; // NUEVO — por mensaje
}
```

### 2. Nuevas acciones del store

```typescript
// Agregar al CopilotState:
addBlockToLastAssistant: (block: MessageBlock) => void;
updateLastTextBlock: (chunk: string) => void;  // reemplaza appendToLastAssistant internamente
setMessageStatus: (msgId: string, status: CopilotMessage["status"]) => void;
```

### 3. NO agregar al store Zustand

- `draft` — local de ChatComposer.
- `attachments` — local de ChatComposer.
- `uploadProgress` — local de ChatComposer.
- `replyTo` — local de ChatComposer.
- `voiceState` — local de ChatComposer (derivado de `useVoiceRecorder`).

### 4. Suggestions placeholder

```typescript
// En el store: no agregar nada.
// El stub vive en hooks/use-suggestions.ts como hook independiente.
// Cuando el motor real esté listo, el hook cambia internamente sin tocar el store.
```

---

## §14 Accessibility

### ARIA completo por componente

| Componente | ARIA |
|-----------|------|
| `ChatComposer` | `role="form" aria-label="Compositor de mensaje"` |
| `ChatComposer.TextArea` | `id="copilot-input"`, `aria-label="Mensaje"`, `aria-multiline="true"` |
| `ChatComposer.SendButton` | `aria-label="Enviar"` / `"Detener respuesta"` |
| `ChatComposer.AttachmentButton` | `aria-label="Adjuntar archivo"` |
| `ChatComposer.VoiceButton` | `aria-label="Grabar audio"` / `"Detener grabación"` |
| `ChatComposer.ReplyPreview` | `aria-label="Respondiendo a {role}"` |
| `ChatComposer.SlashAutocomplete` | `role="listbox"`, items `role="option"` |
| `VoiceOverlay` | `role="status" aria-live="assertive"` con duración |
| `AssistantMessageV2` | `role="region" aria-label="Respuesta del asistente"` |
| `UserMessageV2` | `role="region" aria-label="Tu mensaje"` |
| `ImageBlock lightbox` | `Dialog` Shadcn → focus trap automático |
| `AudioBlock player` | `role="group" aria-label="Reproductor de audio"` |
| `ToolResultBlock` | `aria-label="Resultado de herramienta: {toolName}"` |
| `QuoteReplyBlock` | `aria-label="Mensaje citado"` |
| Streaming indicator | `aria-live="polite" aria-atomic="false"` en el contenedor del TextBlock |
| Upload progress | `aria-label="{filename}: {pct}% subido"`, `role="progressbar" aria-valuenow={pct}` |

### Keyboard navigation

- Tab navega: rail buttons → composer buttons → textarea → send.
- En SlashAutocomplete: Arrow Up/Down navega items, Enter selecciona, Escape cierra.
- En Lightbox: Escape cierra, Arrow Left/Right para galería (futuro).
- AudioBlock: Space = play/pause, Arrow Left/Right ±5s.
- `ChatComposer.ContextChips`: cada chip tiene `tabIndex={0}`, Enter/Space remueve.

### Screen reader streaming

```html
<!-- Región de mensajes con aria-live -->
<div role="log" aria-live="polite" aria-label="Conversación">
  {messages.map(msg => <MessageWrapper key={msg.id} ... />)}
</div>
```

El `role="log"` es el correcto para conversaciones (anuncia adiciones automáticamente). `aria-live="polite"` no interrumpe al usuario.

### Reduced motion

```css
@media (prefers-reduced-motion: reduce) {
  /* Quitar animaciones de entrada de mensajes */
  .animate-in { animation: none; }
  /* Quitar cursor pulsante */
  .animate-pulse { animation: none; }
  /* Mantener waveform como barras estáticas */
  [data-waveform] > div { animation: none; height: 4px; }
}
```

---

## §15 Performance

### Virtualizer con block heights variables

El virtualizer `@tanstack/react-virtual` se mantiene con `measureElement` para corrección de altura post-render.

`estimateSize` por tipo de bloque:

```typescript
function estimateBlockHeight(block: MessageBlock): number {
  switch (block.kind) {
    case "text":     return 72 + Math.ceil((block.markdown?.length ?? 0) / 80) * 20;
    case "image":    return 260;
    case "audio":    return 128;
    case "video":    return 220;
    case "document": return 72;
    case "table":    return 160 + (block.rows?.length ?? 0) * 36;
    case "code":     return 96 + (block.code?.split("\n").length ?? 0) * 18;
    case "card":     return 200;
    case "citation": return 80;
    case "tool_result": return 100;
    case "quote_reply": return 72;
    default:         return 80;
  }
}

// Un mensaje puede tener múltiples bloques — el estimateSize del mensaje es la suma:
function estimateMsgHeight(msg: CopilotMessage): number {
  const blocks = msg.blocks ?? adaptLegacyMessage(msg);
  return blocks.reduce((acc, b) => acc + estimateBlockHeight(b), 24); // 24px padding
}
```

### Lazy loading

- Imágenes: `loading="lazy"` nativo.
- Audio/Video: `preload="none"` — el browser no pre-descarga media no visible.
- `IntersectionObserver` en `AudioBlock` para pausar si sale del viewport.

### Scroll anchor

```typescript
// En CopilotChatPanel:
const [isUserScrolled, setIsUserScrolled] = useState(false);

const handleScroll = () => {
  const el = scrollRef.current;
  if (!el) return;
  const isAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
  setIsUserScrolled(!isAtBottom);
};

useEffect(() => {
  if (!isUserScrolled) {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }
}, [messages, isUserScrolled]);
```

El botón "↓ Ir al final" aparece como badge flotante sobre el composer cuando `isUserScrolled && isStreaming`.

---

## §16 Mobile Adaptations

### Layout mobile (<768px)

```
┌──────────────────────────────────┐
│         PAGE CONTENT             │
│                                  │
│                          [●]     │  ← FAB circular 44px, bottom-right, collapsed
└──────────────────────────────────┘

Al expandir → Sheet (Shadcn) fullscreen desde derecha:

┌──────────────────────────────────┐
│  ╔══════════════════════════════╗ │
│  ║  [← Cerrar]    Chat · o4   ║ │  ← Sheet header
│  ╠══════════════════════════════╣ │
│  ║  mensajes...                ║ │
│  ║                             ║ │
│  ╠══════════════════════════════╣ │
│  ║  [composer]                 ║ │  ← sticky bottom
│  ╚══════════════════════════════╝ │
└──────────────────────────────────┘
```

- FAB: `position: fixed; bottom: 1rem; right: 1rem; z-index: 50`. Icono `Sparkles` (Lucide). Muestra badge rojo con cuenta de mensajes no leídos si hay.
- `Sheet side="right"` fullscreen: `w-screen h-screen` en mobile.
- En `full` mobile: `Tabs` "Chat" / "Historial" en el header del Sheet.
- Composer en mobile: `position: sticky; bottom: 0`. `padding-bottom: env(safe-area-inset-bottom)`. Cuando el teclado virtual aparece, el CSS `height: 100dvh` garantiza que el composer sube.

### Attachment picker mobile

```typescript
// En mobile, el input acepta capture="camera" como fallback:
<input
  type="file"
  accept="image/*"
  capture="camera"  // solo en mobile si el mime es imagen
  multiple
/>
```

Detectar mobile con `navigator.maxTouchPoints > 0` o CSS `@media (pointer: coarse)`.

### Touch gestures

- Long-press (500ms) en mensaje → mostrar bottom `Sheet` con opción "Responder".
- Swipe en attachment chip → animar salida + eliminar.
- Pull-to-refresh en la lista de mensajes: NO implementar (el scroll del virtualizer lo haría complejo).

---

## §17 Error / Empty / Loading States

### Por componente

| Componente | Loading | Empty | Error |
|-----------|---------|-------|-------|
| `CopilotHistoryPanel` | 5 `Skeleton` de h-10 | "Aún no hay conversaciones. Empieza una nueva." + Button "Nueva conversación" | `Alert` + "No se pudo cargar el historial." + link "Reintentar" |
| `MessageList` | `TypingIndicator` (dots animados) mientras `status === "thinking"` | Empty state con `SuggestedChips` + "Escribe tu primera pregunta." | Inline message de error con `AlertCircle` icon |
| `SlashAutocomplete` | 3 `Skeleton` h-8 en CommandList | `CommandEmpty`: 'No hay comandos para "{query}"' | — |
| `ImageBlock` | `Skeleton` con mismo aspect ratio | — | Placeholder gris + `ImageOff` icon |
| `AudioBlock` | `Skeleton` h-16 | — | "No se pudo cargar el audio." |
| `VideoBlock` | `Skeleton` con aspect 16:9 | — | "No se pudo cargar el video." |
| `AttachmentChip` (uploading) | Progress bar animada | — | Estado `error` con "Reintentar" |
| `SuggestedChips` | No loading state (stub síncrono) | Oculto si vacío | — |
| Streaming text | Cursor pulsante | — | Toast "Error de conexión. Reintentando..." |
| `ToolResultBlock` | — | — | Borde rojo + `AlertCircle` + texto de error |

### Error de streaming

Si el SSE falla (tras 3 reintentos), el mensaje placeholder del asistente se convierte en mensaje de error:

```
┌──────────────────────────────────────────────────────────────────┐
│  ✦  ⚠️ No se pudo obtener respuesta. Verifica tu conexión.      │
│     [Reintentar]                                                 │
└──────────────────────────────────────────────────────────────────┘
```

"Reintentar" re-envía el mismo `ComposerPayload` usando el `useRetryLastMessage()` hook (lee el último payload de user del store).

---

## §18 Component Inventory

### Componentes nuevos a crear

| Componente | Path | Shadcn primitives |
|-----------|------|------------------|
| `ChatComposer` | `features/copilot/components/composer/ChatComposer.tsx` | `Textarea`, `Button`, `Tooltip`, `TooltipProvider` |
| `ChatComposer.SuggestedChips` | `features/copilot/components/composer/SuggestedChips.tsx` | `Button` |
| `ChatComposer.ReplyPreview` | `features/copilot/components/composer/ReplyPreview.tsx` | `Button` |
| `ChatComposer.ContextChips` | Migrar de `ContextChips.tsx` → `composer/ContextChips.tsx` | `Badge`, `Button` |
| `ChatComposer.AttachmentTray` | `features/copilot/components/composer/AttachmentTray.tsx` | `Progress`, `Button` |
| `ChatComposer.VoiceOverlay` | `features/copilot/components/composer/VoiceOverlay.tsx` | `Button` |
| `AttachmentChip` | `features/copilot/components/composer/AttachmentChip.tsx` | `Progress`, `Button` |
| `BlockDispatcher` | `features/copilot/components/blocks/BlockDispatcher.tsx` | — |
| `TextBlock` | `features/copilot/components/blocks/TextBlock.tsx` | — |
| `ImageBlock` | `features/copilot/components/blocks/ImageBlock.tsx` | `Dialog`, `DialogContent`, `Skeleton` |
| `AudioBlock` | `features/copilot/components/blocks/AudioBlock.tsx` | `Collapsible`, `CollapsibleContent`, `CollapsibleTrigger`, `Slider` |
| `VideoBlock` | `features/copilot/components/blocks/VideoBlock.tsx` | `Skeleton` |
| `DocumentBlock` | `features/copilot/components/blocks/DocumentBlock.tsx` | `Button` |
| `TableBlock` | `features/copilot/components/blocks/TableBlock.tsx` | `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableHead`, `TableCell` |
| `CodeBlock` | `features/copilot/components/blocks/CodeBlock.tsx` | `Button` |
| `CitationBlock` | `features/copilot/components/blocks/CitationBlock.tsx` | `Collapsible`, `CollapsibleContent`, `CollapsibleTrigger` |
| `CardBlock` | `features/copilot/components/blocks/CardBlock.tsx` | — (delega a cards existentes) |
| `ToolResultBlock` | `features/copilot/components/blocks/ToolResultBlock.tsx` | `Collapsible`, `CollapsibleContent`, `CollapsibleTrigger` |
| `QuoteReplyBlock` | `features/copilot/components/blocks/QuoteReplyBlock.tsx` | — |
| `AssistantMessageV2` | `features/copilot/components/messages/AssistantMessageV2.tsx` | — |
| `UserMessageV2` | `features/copilot/components/messages/UserMessageV2.tsx` | — |
| `MessageContextMenu` | `features/copilot/components/messages/MessageContextMenu.tsx` | `DropdownMenu`, `DropdownMenuContent`, `DropdownMenuItem` |
| `useSuggestions` | `features/copilot/hooks/use-suggestions.ts` | — |
| `useMediaUpload` | `features/copilot/hooks/use-media-upload.ts` | — |
| `message-adapter` | `features/copilot/utils/message-adapter.ts` | — |
| `media-api` | `features/copilot/api/media-api.ts` | — |

### Componentes existentes a modificar

| Componente | Cambios |
|-----------|---------|
| `CopilotRail.tsx` | Reemplazar botón de ciclo por 3 botones explícitos por estado (§2). Quitar `handleToggle`. |
| `CopilotSidebar.tsx` | Sin cambios estructurales. Keyboard shortcuts preservados. |
| `CopilotChatPanel.tsx` | Reemplazar sección input por `<ChatComposer>`. Reemplazar `AssistantMessage`/`UserMessage` por `AssistantMessageV2`/`UserMessageV2`. Agregar scroll-anchor inteligente. Agregar Stop button logic. |
| `copilot-store.ts` | Agregar `blocks?: MessageBlock[]` a `CopilotMessage`. Agregar `addBlockToLastAssistant`, `updateLastTextBlock`, `setMessageStatus`. |
| `AttachmentButton.tsx` | Extender `accept` para incluir imagen, audio, video. |
| `DocumentChip.tsx` | Deprecar — reemplazado por `AttachmentChip` multi-tipo. |

### Componentes existentes a deprecar

| Componente | Reemplazo | Cuándo |
|-----------|-----------|--------|
| `CopilotInput.tsx` | `ChatComposer` | Tras implementar ChatComposer |
| `CopilotChat.tsx` | Funcionalidad integrada en `CopilotChatPanel` | Tras consolidar |
| `DocumentChip.tsx` | `AttachmentChip` | Tras implementar AttachmentChip |
| `ContextChips.tsx` (raíz) | `ChatComposer.ContextChips` (sub-componente) | Mover, no eliminar |
| `SuggestedActions.tsx` | `SuggestedChips` | Refactor con misma lógica de `ROUTE_SUGGESTIONS` |
| `AssistantMessage.tsx` | `AssistantMessageV2` | Después de migrar y validar el adapter |
| `UserMessage.tsx` | `UserMessageV2` | Ídem |

---

## §19 Anchor Comments

| Anchor | Componente | Propósito |
|--------|-----------|-----------|
| `[COPILOT-SUGGESTIONS-ENGINE]` | `hooks/use-suggestions.ts` | Marcar el punto de integración con el futuro motor de sugerencias dinámicas |
| `[COPILOT-BLOCK-REGISTRY]` | `blocks/BlockDispatcher.tsx` | Punto de extensión para registrar nuevos tipos de bloque sin tocar el dispatcher |
| `[COPILOT-VOICE-UPLOAD]` | `hooks/use-media-upload.ts` | Lógica de upload paralelo audio+transcript — crítico para el flujo de voz |
| `[COPILOT-SCROLL-ANCHOR]` | `CopilotChatPanel.tsx` | Lógica de scroll-to-bottom inteligente — no regresionar en PR |
| `[COPILOT-STREAMING-BLOCKS]` | `copilot-store.ts` | Acciones del store para streaming de bloques heterogéneos |
| `[COPILOT-LEGACY-ADAPTER]` | `utils/message-adapter.ts` | Conversión de mensajes legacy (content+uiActions) a blocks[] |
| `[COPILOT-MOBILE-FAB]` | `CopilotSidebar.tsx` | FAB mobile — requiere `position: fixed` fuera del sidebar grid |
| `[COPILOT-CONTEXT-MENU]` | `MessageContextMenu.tsx` | Hover/long-press para reply — diferente UX en desktop vs mobile |

---

## §20 Open Questions

1. **Shiki disponible?** Verificar si `shiki` está en `package.json`. Si no, el `CodeBlock` arranca con `<pre>` plain y se migra en un PR separado.

2. **`react-markdown` + `remark-gfm` + `rehype-sanitize` disponibles?** Verificar en `package.json`. Si no, el `TextBlock` usa `whitespace-pre-wrap` temporalmente (como hoy) y se agrega en el mismo PR que el bloque de texto.

3. **Tailwind Typography (`@tailwindcss/typography`)?** Verificar si está instalado. Si no, los estilos del markdown se implementan manualmente con clases semánticas en el `TextBlock`.

4. **`collapsible` en `components/ui/`?** No aparece en el `ls` de componentes ui. Si no está, instalar via `npx shadcn-ui@latest add collapsible` o usar implementación con `useState + max-height` CSS.

5. **`avatar.tsx` en `components/ui/`?** Sí está en el `ls`. Considerar usarlo para el avatar del asistente en lugar del `div` circular actual.

6. **SSE de blocks:** El backend actual emite `text_chunk` (texto plano, no blocks). La migración a `block_append / block_update` requiere coordinación con el backend team. El `message-adapter.ts` mantiene compatibilidad mientras se hace la transición.

7. **Video lightbox vs inline:** Los videos inline pueden consumir ancho en el sidebar angosto (380px). En `rail` state, los videos deberían abrir en un Dialog (como imágenes) en vez de reproducir inline. Confirmar.

8. **Limite de archivos simultáneos:** No hay límite especificado. Propuesta: máximo 5 attachments por mensaje. Confirmar con producto.

9. **Draft persistence en `localStorage`:** El draft del composer se persiste para "reabrir el chat con el borrador guardado". ¿Persiste por conversación (key por `conversationId`) o global? Propuesta: por `conversationId` (`copilot.draft.${conversationId}`).

10. **Audio playback múltiple:** Si hay múltiples `AudioBlock` en la misma conversación, ¿se pausa el anterior al reproducir otro? Propuesta: sí, usando un contexto o store local de `playingAudioId`.

---

## FSD File Structure

```
frontend/src/features/copilot/
├── api/
│   ├── copilot-api.ts          (existente — preservar)
│   ├── document-api.ts         (existente — preservar)
│   ├── media-api.ts            (NUEVO — upload de media)
│   └── voice-api.ts            (existente — preservar)
├── components/
│   ├── blocks/                 (NUEVO directorio)
│   │   ├── BlockDispatcher.tsx
│   │   ├── TextBlock.tsx
│   │   ├── ImageBlock.tsx
│   │   ├── AudioBlock.tsx
│   │   ├── VideoBlock.tsx
│   │   ├── DocumentBlock.tsx
│   │   ├── TableBlock.tsx
│   │   ├── CodeBlock.tsx
│   │   ├── CitationBlock.tsx
│   │   ├── CardBlock.tsx
│   │   ├── ToolResultBlock.tsx
│   │   └── QuoteReplyBlock.tsx
│   ├── cards/                  (existente — sin cambios)
│   │   ├── AlternativesCard.tsx
│   │   ├── CheckpointCard.tsx
│   │   ├── ClarifyCard.tsx
│   │   └── InterviewCompleteCard.tsx
│   ├── composer/               (NUEVO directorio)
│   │   ├── ChatComposer.tsx    (componente raíz + sub-componentes estáticos)
│   │   ├── SuggestedChips.tsx
│   │   ├── ReplyPreview.tsx
│   │   ├── ContextChips.tsx    (migrado desde raíz)
│   │   ├── AttachmentTray.tsx
│   │   ├── AttachmentChip.tsx  (reemplaza DocumentChip para multi-tipo)
│   │   └── VoiceOverlay.tsx
│   ├── messages/               (existente — agregar V2)
│   │   ├── AssistantMessage.tsx     (existente — mantener para compat)
│   │   ├── AssistantMessageV2.tsx   (NUEVO)
│   │   ├── UserMessage.tsx          (existente — mantener para compat)
│   │   ├── UserMessageV2.tsx        (NUEVO)
│   │   ├── MessageContextMenu.tsx   (NUEVO)
│   │   ├── ComparisonTable.tsx      (existente — sin cambios)
│   │   ├── MetricSummaryCard.tsx    (existente — sin cambios)
│   │   ├── MultiOptionSelector.tsx  (existente — sin cambios)
│   │   ├── NavigationCard.tsx       (existente — sin cambios)
│   │   ├── ProposalCard.tsx         (existente — sin cambios)
│   │   ├── ProgressChecklist.tsx    (existente — sin cambios)
│   │   └── TypingIndicator.tsx      (existente — sin cambios)
│   ├── shared/                 (existente)
│   │   ├── AttachmentButton.tsx     (existente — ampliar accept)
│   │   ├── DocumentChip.tsx         (existente — deprecar gradual)
│   │   └── VoiceButton.tsx          (existente — preservar)
│   ├── ContextChips.tsx        (existente — mantener re-export hasta migración)
│   ├── ContextRotBanner.tsx    (existente — sin cambios)
│   ├── CopilotChatHeader.tsx   (existente — sin cambios)
│   ├── CopilotChatPanel.tsx    (existente — modificar para usar ChatComposer + V2)
│   ├── CopilotHistoryPanel.tsx (existente — sin cambios)
│   ├── CopilotRail.tsx         (existente — modificar botones explícitos)
│   ├── CopilotSidebar.tsx      (existente — sin cambios estructurales)
│   ├── MutationUndoButton.tsx  (existente — sin cambios)
│   ├── SlashCommandAutocomplete.tsx (existente — integrar en ChatComposer)
│   ├── SuggestedActions.tsx    (existente — deprecar, lógica migra a SuggestedChips)
│   └── TierChip.tsx            (existente — sin cambios)
├── hooks/
│   ├── use-conversation-groups.ts   (existente)
│   ├── use-conversation-list.ts     (existente)
│   ├── use-copilot-chat.ts          (existente)
│   ├── use-copilot-navigator.ts     (existente)
│   ├── use-create-conversation.ts   (existente)
│   ├── use-delete-conversation.ts   (existente)
│   ├── use-media-upload.ts          (NUEVO)
│   ├── use-mutation-journal.ts      (existente)
│   ├── use-patch-conversation.ts    (existente)
│   ├── use-route-tracker.ts         (existente)
│   ├── use-slash-commands.ts        (existente)
│   ├── use-suggestions.ts           (NUEVO)
│   └── use-voice-recorder.ts        (existente — sin cambios)
├── store/
│   └── copilot-store.ts        (existente — extensiones §13)
├── types/
│   └── conversations.ts        (existente — agregar MessageBlock)
└── utils/
    └── message-adapter.ts      (NUEVO)
```

---

## Responsive Behavior Summary

| Breakpoint | Layout |
|------------|--------|
| Desktop (≥1024px) | CSS grid 3 columnas, todos los estados del sidebar |
| Tablet (768-1023px) | CSS grid 3 columnas, `rail` como estado por defecto (280px chat 0px history) |
| Mobile (<768px) | FAB circular + Sheet fullscreen. Chat ocupa pantalla completa. Tabs para historial. |

