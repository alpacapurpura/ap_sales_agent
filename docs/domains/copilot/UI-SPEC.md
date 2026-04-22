# UI Spec: Copilot Sidebar Refactor

## 1. Overview

The Copilot sidebar is a persistent AI assistant panel anchored to the right
edge of every authenticated page. It has three visible states — collapsed
(60 px rail only), rail (chat 380 px + rail 60 px), and full (history 280 px +
chat 400 px + rail 60 px) — driven by a Zustand store slice and persisted to
`localStorage`. The rail is always visible; layout is a CSS grid that expands
the history and chat columns without reflowing page content.

---

## 2. Component Tree

```
CopilotSidebar  (Client — features/copilot/components/copilot-sidebar.tsx)
├── CopilotHistoryPanel  (Client — features/copilot/components/copilot-history-panel.tsx)
│   │  [visible only when sidebarState === "full"]
│   ├── Button "Nueva conversación"  (Shadcn Button)
│   ├── ScrollArea  (Shadcn — conversation list)
│   │   ├── ConversationGroup "Hoy"
│   │   │   └── ConversationItem × N
│   │   │       ├── title (truncate, inline-rename on dblclick)
│   │   │       ├── meta row: tiempo relativo · TierChip · msg count
│   │   │       └── DropdownMenu kebab: Renombrar / Archivar  (Shadcn DropdownMenu)
│   │   ├── ConversationGroup "Ayer"
│   │   ├── ConversationGroup "Últimos 7 días"
│   │   └── ConversationGroup "Anterior"
│   └── Button "Cargar 6 más"  (Shadcn Button variant="ghost")
│
├── CopilotChatPanel  (Client — features/copilot/components/copilot-chat-panel.tsx)
│   │  [visible when sidebarState === "rail" | "full"]
│   ├── ChatPanelHeader
│   │   ├── title (click-to-edit inline)
│   │   ├── meta: tier chips history
│   │   ├── ProcedureProgress badge (if procedure_state active)
│   │   └── MutationUndoButton  (features/copilot/components/mutation-undo-button.tsx)
│   ├── ScrollArea  (Shadcn — message list)
│   │   ├── CopilotMessage × N
│   │   │   ├── TierChip  (features/copilot/components/tier-chip.tsx)
│   │   │   ├── message text (streaming)
│   │   │   ├── PlanCard  (features/copilot/components/plan-card.tsx)
│   │   │   └── existing UIAction cards (proposal, interview, etc.)
│   │   └── StreamingIndicator (typing dots)
│   ├── ContextRotBanner  (features/copilot/components/context-rot-banner.tsx)
│   │   [visible when total_tokens >= 8000 and not dismissed]
│   └── ChatInputArea
│       ├── Textarea  (Shadcn)
│       ├── SlashCommandAutocomplete  (features/copilot/components/slash-command-autocomplete.tsx)
│       └── Button "Enviar"  (Shadcn Button)
│
└── CopilotRail  (Client — features/copilot/components/copilot-rail.tsx)
    │  [always 60 px, right edge]
    ├── Button toggle chevron  (Shadcn Button variant="ghost")
    ├── Separator  (Shadcn)
    ├── Button "+" nueva conversación  (Shadcn Button variant="ghost")
    ├── ConversationAvatars × ≤6  [collapsed only]
    │   └── Avatar 40×40 (initials, active = purple halo)
    └── Button "más" text  [collapsed only] → opens "full"
```

---

## 3. Store — New Slices (Zustand)

**File:** `frontend/src/features/copilot/store/copilot-store.ts`

### 3.1 Replace existing `SidebarState`

Current: `"collapsed" | "open"` (2 states).
New: `"collapsed" | "rail" | "full"` (3 states).

```typescript
// NEW type — replaces existing SidebarState
type SidebarState = "collapsed" | "rail" | "full";
```

Backward-compat: `isOpen` is derived as `sidebarState !== "collapsed"`.
`openPanel()` sets `"rail"`. `closePanel()` sets `"collapsed"`.

### 3.2 New slices to add

```typescript
// Sidebar 3-state
sidebarState: "collapsed" | "rail" | "full";
setSidebarState: (s: SidebarState) => void;
cycleSidebarState: () => void;  // collapsed → rail → full → collapsed

// Slash command overlay
slashCommandOpen: boolean;
setSlashCommandOpen: (open: boolean) => void;

// Context-rot dismissed banners (per-conversation)
dismissedRotBanners: Set<string>;   // keyed by conversationId
dismissRotBanner: (convId: string) => void;

// Last tier per message (updated by SSE tier_decision)
setLastMessageTier: (msgId: string, tier: ModelTier) => void;
lastMessageTiers: Record<string, ModelTier>;
```

### 3.3 Slices to remove

- `focusEntity` — eliminated with Focus mode
- `focusSnapshot` — eliminated with Focus mode
- `interviewSessionId` — merged into `session.sessionId`
- `previewData` — eliminated (no preview pane)

### 3.4 Persistence

```typescript
// On sidebarState change:
localStorage.setItem("copilot.sidebarState", newState);

// On mount (init):
const saved = localStorage.getItem("copilot.sidebarState");
if (saved === "rail" || saved === "full") {
  store.setSidebarState(saved);
}
// Mobile guard applied after init (see §7)
```

---

## 4. React Query Hooks

**Location:** `frontend/src/features/copilot/hooks/`

| Hook | File | API Endpoint | Trigger | Notes |
|------|------|--------------|---------|-------|
| `useConversationList` | `use-conversation-list.ts` | `GET /api/v1/copilot/conversations?limit=6&cursor=` | Mount + "Cargar más" | Infinite query via `useInfiniteQuery`; staleTime 30s |
| `useCreateConversation` | `use-create-conversation.ts` | `POST /api/v1/copilot/conversations` | Click "+" / "N" shortcut | Optimistic: prepend to list; on success setConversationId |
| `usePatchConversation` | `use-patch-conversation.ts` | `PATCH /api/v1/copilot/conversations/{id}` | Inline rename / archive | Optimistic update item in list; rollback on error |
| `useDeleteConversation` | `use-delete-conversation.ts` | `DELETE /api/v1/copilot/conversations/{id}` | Kebab "Archivar" | Optimistic remove; invalidate list on settle |
| `useRevertMutations` | `use-revert-mutations.ts` | `POST /api/v1/copilot/conversations/{id}/revert` | MutationUndoButton confirm | Toast with `reverted_count` on success |
| `useSlashCommands` | `use-slash-commands.ts` | `GET /api/v1/copilot/commands` | Slash "/" keypress | staleTime 5min; cached aggressively |
| `useMutationJournal` | `use-mutation-journal.ts` | `GET /api/v1/copilot/conversations/{id}/mutations` (TBD) | Chat header mount | Determine if undo button visible |

**fetchClient** must be used in all `api/` functions (injects `X-Tenant-ID`).

---

## 5. Components

### 5.1 CopilotSidebar

**Path:** `frontend/src/features/copilot/components/CopilotSidebar.tsx`
**Type:** Client Component (`"use client"`)
**Props:** none — reads `useCopilotStore`

**Layout (CSS grid, right-anchored):**

```css
.copilot-root {
  display: grid;
  grid-template-columns:
    var(--history-w, 0px)   /* 0 | 280px */
    var(--chat-w, 0px)      /* 0 | 380px | 400px */
    60px;                   /* rail — always */
  transition: grid-template-columns 220ms cubic-bezier(.2,.8,.2,1);
}
```

State → CSS variable values:

| State | `--history-w` | `--chat-w` |
|-------|--------------|-----------|
| `collapsed` | 0px | 0px |
| `rail` | 0px | 380px |
| `full` | 280px | 400px |

**Keyboard shortcut handler** (document-level `keydown`, skip if focus in input/textarea):

| Key | Action |
|-----|--------|
| `C` | `setSidebarState("collapsed")` |
| `R` | `setSidebarState("rail")` |
| `F` | `setSidebarState("full")` |
| `N` | `useCreateConversation().mutate()` |
| `Ctrl+K` / `Cmd+K` | Focus `#copilot-input` |
| `Esc` (in textarea) | `setSidebarState("rail")` |

**A11y:** `aria-expanded={sidebarState !== "collapsed"}` on root. `aria-live="polite"` region announces state changes.

---

### 5.2 CopilotRail

**Path:** `frontend/src/features/copilot/components/CopilotRail.tsx`
**Type:** Client Component
**Props:** none

**Contents by state:**

`collapsed`:
1. Toggle button — icon `ChevronLeft` → sets `"rail"` — `aria-label="Abrir copilot"`
2. Button `+` — icon `Plus` → `useCreateConversation` — `aria-label="Nueva conversación"`
3. `Separator` (Shadcn)
4. Up to 6 conversation avatars (40×40 px, 2-letter initials from title)
   - Active avatar: `box-shadow: 0 0 0 2px white, 0 0 0 3.5px var(--color-accent)`
   - Hover: `Tooltip` (Shadcn, side="left") shows title
5. Text "más" → `setSidebarState("full")` — `aria-label="Ver todas las conversaciones"`

`rail`:
1. Toggle button — icon `ChevronRight` → sets `"full"` — `aria-label="Expandir historial"`
2. Button `+` — icon `Plus`
3. `Separator`

`full`:
1. Toggle button — icon `ChevronLeft` (double) → sets `"collapsed"` — `aria-label="Cerrar copilot"`
2. Button `+`
3. `Separator`

**Tailwind classes (rail column):**
```
flex flex-col items-center gap-2 w-[60px] border-l border-border bg-background px-2 py-3
```

**Shadcn:** `Button variant="ghost" size="icon"`, `Tooltip`, `Separator`

---

### 5.3 CopilotHistoryPanel

**Path:** `frontend/src/features/copilot/components/CopilotHistoryPanel.tsx`
**Type:** Client Component
**Props:** none — reads store + `useConversationList`

**Layout:**

```
┌─────────────────────────┐
│ Conversaciones      [X] │  ← h2 title + close hint
├─────────────────────────┤
│ [+ Nueva conversación ] │  ← Button full-width accent
├─────────────────────────┤
│ Hoy                     │  ← section label (text-xs uppercase text-muted)
│  ■ Mi estrategia de...  │  ← active item (bg-accent/10 border-l-2 border-accent)
│    hace 5 min · mini ·3 │
│  ○ Buyer persona...     │
│    hace 2 h · nano ·7   │
├─────────────────────────┤
│ Ayer                    │
│  ○ Oferta webinar...    │
├─────────────────────────┤
│ [  Cargar 6 más  ]      │  ← ghost button, centered
└─────────────────────────┘
```

**Conversation item states:**
- Default: `hover:bg-muted/60 cursor-pointer rounded-md px-2 py-1.5`
- Active: `bg-accent/10 border-l-2 border-accent rounded-r-md pl-[6px]`
- Procedure active: prepend `target` icon (Lucide `Target`, 12px) + `{coverage}%` badge

**Inline rename:**
- Double-click title → replace `<span>` with `<Input>` (Shadcn Input)
- `Enter` → `usePatchConversation(id).mutate({ title })` → revert to span
- `Esc` → cancel, revert to original
- Input: `max-length="120"`, `autoFocus`

**Kebab menu (DropdownMenu):** appears on item hover (icon `MoreHorizontal`):
- "Renombrar" → triggers inline rename
- "Archivar" → `useDeleteConversation(id).mutate()`

**Sections grouping logic** (computed in hook `use-conversation-groups.ts`):

| Section label | Condition |
|---------------|-----------|
| Hoy | `updatedAt` = today |
| Ayer | `updatedAt` = yesterday |
| Últimos 7 días | `updatedAt` within last 7 days |
| Anterior | older |

Only non-empty sections render. Empty history → empty state (see §8).

**Shadcn:** `ScrollArea`, `DropdownMenu`, `Button`, `Input`, `Tooltip`

---

### 5.4 CopilotChatPanel

**Path:** `frontend/src/features/copilot/components/CopilotChatPanel.tsx`
**Type:** Client Component
**Props:** none — reads store

**Sub-sections:**

#### Header
```
┌─────────────────────────────────┐
│ [Mi estrategia de marca]  [↩ 3] │
│ mini · hace 5 min               │
│ [Buyer persona · bloque 3 de 5] │  ← ProcedureProgress (if active)
└─────────────────────────────────┘
```

- Title: click to edit inline (same pattern as history panel rename)
- `[↩ 3]`: `MutationUndoButton` — shows count of reversible mutations; hidden if 0
- Meta line: last tier chip + relative timestamp
- `ProcedureProgress` (existing component) shows when `session.procedure === "interview"`

#### Message list

- `ScrollArea` wrapping message stack
- Each assistant message:
  - `TierChip` top-right corner of bubble (appears after `tier_decision` SSE)
  - Text rendered with markdown (existing pattern)
  - UI action cards below text (existing)
  - `PlanCard` when SSE `plan_proposed` received (new)
- Streaming: typing indicator (3-dot animation, `aria-label="El copilot está escribiendo"`)
- Auto-scroll to bottom on new message

#### ContextRotBanner

Rendered between message list and input (see §5.8).

#### Input area

```
┌──────────────────────────────────┐
│ Escribe un mensaje...            │
│                             [→]  │
└──────────────────────────────────┘
```

- `Textarea` (Shadcn, `id="copilot-input"`, `rows={1}`, auto-grow to max 5 rows)
- `/` at start of input triggers `SlashCommandAutocomplete`
- Send button: `aria-label="Enviar"`, disabled while `status === "thinking" | "streaming"`
- `Enter` sends (without modifier); `Shift+Enter` newline
- `Esc` collapses sidebar to `"rail"`

**Shadcn:** `ScrollArea`, `Textarea`, `Button`

---

### 5.5 SlashCommandAutocomplete

**Path:** `frontend/src/features/copilot/components/SlashCommandAutocomplete.tsx`
**Type:** Client Component
**Props:** `{ query: string; onSelect: (command: SlashCommand) => void; onDismiss: () => void }`

- Triggered when input value starts with `/`
- Fetches commands via `useSlashCommands()` (staleTime 5min)
- Filters by `query` (the text after `/`)
- Renders as `Popover` anchored above the input (side="top")
- Inner content: `Command` (Shadcn) with `CommandList` + `CommandItem` per command

```
┌────────────────────────┐
│ /llena                 │  ← CommandInput (mirrors textarea value)
├────────────────────────┤
│ /llena-identidad       │
│  Completa identidad de marca
│ /llena-oferta          │
│  Completa sección de oferta
└────────────────────────┘
```

- Arrow keys navigate, `Enter` selects, `Esc` calls `onDismiss`
- On select: replaces `/...` with command text in textarea
- Loading: `Skeleton` rows while fetching
- Empty: "No hay comandos para '{query}'"

**Shadcn:** `Popover`, `Command`, `CommandInput`, `CommandList`, `CommandItem`, `Skeleton`

---

### 5.6 PlanCard

**Path:** `frontend/src/features/copilot/components/PlanCard.tsx`
**Type:** Client Component
**Props:**
```typescript
interface PlanCardProps {
  msgId: string;
  steps: PlanStep[];
  estimatedCostUsd: number;
  status: "pending" | "approved" | "rejected";
  onApprove: () => void;
  onReject: () => void;
}

interface PlanStep {
  order: number;
  label: string;
  toolName: string;
  estimatedTokens: number;
}
```

**Layout:**

```
┌─────────────────────────────────┐
│ Plan propuesto          [heavy] │
├─────────────────────────────────┤
│  1. Analizar identidad de marca │
│  2. Revisar métricas de funnel  │
│  3. Proponer estrategia         │
├─────────────────────────────────┤
│ Costo estimado: ~$0.02          │
│                                 │
│ [Rechazar]        [Aplicar]     │
└─────────────────────────────────┘
```

- Appears when SSE event `plan_proposed` arrives
- Status `approved`: buttons hidden, green checkmark + "Aplicado"
- Status `rejected`: buttons hidden, muted "Rechazado"
- "Aplicar" → `POST /api/v1/copilot/plan/{msgId}/approve` (stub endpoint, deferred)
- "Rechazar" → `POST /api/v1/copilot/plan/{msgId}/reject` (stub, deferred)

**Shadcn:** `Card`, `CardHeader`, `CardContent`, `CardFooter`, `Button`

---

### 5.7 MutationUndoButton

**Path:** `frontend/src/features/copilot/components/MutationUndoButton.tsx`
**Type:** Client Component
**Props:** `{ conversationId: string; mutationCount: number }`

- Renders only when `mutationCount > 0`
- Icon `RotateCcw` + count badge
- Click → opens `AlertDialog` (Shadcn)
- Dialog copy:
  - Title: "¿Seguro que quieres deshacer los cambios?"
  - Body: "Se revertirán {N} cambios aplicados en esta conversación. Esta acción no se puede deshacer."
  - Buttons: "Cancelar" (ghost) / "Deshacer todo" (destructive)
- Confirm → `useRevertMutations(conversationId).mutate()`
- On success → `toast.success("Se revirtieron {reverted_count} cambios.")` via `sonner`
- On error → `toast.error("No se pudieron deshacer los cambios. Intenta de nuevo.")`
- Loading: button shows `Loader2` spinner, disabled

**Shadcn:** `AlertDialog`, `AlertDialogContent`, `AlertDialogHeader`, `AlertDialogFooter`, `Button`

---

### 5.8 ContextRotBanner

**Path:** `frontend/src/features/copilot/components/ContextRotBanner.tsx`
**Type:** Client Component
**Props:** `{ conversationId: string; totalTokens: number; messageCount: number }`

**Trigger logic:**
- Yellow: `totalTokens >= 8000` OR `messageCount >= 12`
- Red: `totalTokens >= 16000`
- Hidden: dismissed via `store.dismissRotBanner(conversationId)`

**Yellow banner:**

```
┌──────────────────────────────────────────── [×] ┐
│ Esta conversación ya está larga. Para que el    │
│ copilot te entienda mejor, empieza una nueva.   │
└─────────────────────────────────────────────────┘
```

**Tailwind:**
- Yellow: `bg-yellow-50 border border-yellow-300 text-yellow-900 text-sm px-3 py-2 rounded-md`
- Red: `bg-red-50 border border-red-300 text-red-900 text-sm px-3 py-2 rounded-md`

- "empieza una nueva" → inline `<button>` styled as link → `useCreateConversation().mutate()`
- Dismiss `[×]` → `store.dismissRotBanner(conversationId)` (in-memory, not persisted)

**A11y:** `role="alert"` on banner div. Dismiss button `aria-label="Cerrar aviso"`.

---

### 5.9 TierChip

**Path:** `frontend/src/features/copilot/components/TierChip.tsx`
**Type:** Server-compatible (no hooks, pure display)
**Props:** `{ tier: ModelTier; size?: "sm" | "xs" }`

| Tier | Color tokens | Label |
|------|-------------|-------|
| `nano` | `bg-green-100 text-green-800` | nano |
| `mini` | `bg-blue-100 text-blue-800` | mini |
| `reasoning` | `bg-amber-100 text-amber-800` | o4 |
| `heavy` | `bg-red-100 text-red-800` | o3 |

**Tailwind (xs size, default):**
```
font-mono text-[10px] px-1.5 py-0.5 rounded-full font-medium tracking-tight
```

No Shadcn primitive needed — pure Tailwind badge.

---

## 6. TypeScript Types

**File:** `frontend/src/features/copilot/types/conversations.ts`

Direct mirror of CONTRACT.md §5:

```typescript
export type ModelTier = "nano" | "mini" | "reasoning" | "heavy";

export interface ConversationSummary {
  id: string;
  title: string | null;
  titleAutoGenerated: boolean;
  updatedAt: string;              // ISO 8601
  messageCount: number;
  totalTokens: number;
  lastTierUsed: ModelTier | null;
  hasProcedure: boolean;
  procedureProgress: number | null;
  archivedAt: string | null;
}

export interface ConversationListResponse {
  items: ConversationSummary[];
  nextCursor: string | null;
}

export interface PatchConversationRequest {
  title?: string;
  archived?: boolean;
}

export interface RevertResponse {
  revertedCount: number;
  failed: Array<{ id: string; error: string }>;
}

export interface SlashCommand {
  name: string;         // e.g. "llena-identidad"
  description: string;
  skillId: string;
}
```

---

## 7. API Integration

| Component | Hook | API Call | Trigger |
|-----------|------|----------|---------|
| CopilotHistoryPanel | `useConversationList` | `GET /conversations?limit=6` | Mount + "Cargar 6 más" |
| CopilotRail | `useConversationList` | same | Mount (rail avatars) |
| CopilotRail (new conv) | `useCreateConversation` | `POST /conversations` | Click `+` or `N` key |
| CopilotHistoryPanel (new conv) | `useCreateConversation` | `POST /conversations` | Click "Nueva conversación" |
| ConversationItem rename | `usePatchConversation` | `PATCH /conversations/{id}` | Enter after inline edit |
| ConversationItem archive | `useDeleteConversation` | `DELETE /conversations/{id}` | Kebab "Archivar" |
| MutationUndoButton | `useRevertMutations` | `POST /conversations/{id}/revert` | AlertDialog confirm |
| SlashCommandAutocomplete | `useSlashCommands` | `GET /commands` | `/` keypress |
| TierChip (per message) | store SSE handler | SSE `tier_decision` event | Auto on stream start |

---

## 8. Loading, Error & Empty States

| Component | Loading | Error | Empty |
|-----------|---------|-------|-------|
| CopilotHistoryPanel | 5 `Skeleton` rows (`h-10 rounded-md`) | `Alert` with "No se pudo cargar el historial." + Retry button | Illustration + "Aún no hay conversaciones. Empieza una nueva." |
| SlashCommandAutocomplete | 3 `Skeleton` items | (silently hide — non-blocking) | "No hay comandos para '{query}'" text inside `Command` |
| CopilotChatPanel (messages) | N/A (new conv starts empty) | `Alert` inline if SSE errors | Empty state: "Escribe tu primera pregunta." |
| MutationUndoButton | `Loader2` spinner in button, disabled | Toast error | Button hidden (count === 0) |
| ConversationItem (rename) | Optimistic instant update | Rollback + `toast.error` | N/A |

---

## 9. Responsive Behavior

| Breakpoint | Behavior |
|------------|----------|
| `< 640px` (mobile) | Sidebar forces `"collapsed"`. Rail/full states render as overlay (`position: fixed, inset-y-0 right-0`) with translucent backdrop. Tap outside → collapse. `cycleSidebarState` skips `"full"` on mobile. |
| `640px – 1023px` (tablet) | Normal rail/full. History panel overlaps page content if needed (not inline). |
| `>= 1024px` (desktop) | Full inline grid. History + chat columns push page content left. `--history-w` and `--chat-w` are inline-grid, not overlay. |

**Mobile overlay implementation note:** Wrap rail/chat/history in `Sheet` (Shadcn) on `< 640px` rather than grid layout.

---

## 10. Data Flow

### New Conversation

```
User clicks "+" in rail or history
  → useCreateConversation.mutate()
  → Optimistic: prepend ConversationSummary to list (title=null, 0 msgs)
  → POST /api/v1/copilot/conversations → 201 { id }
  → store.setConversationId(id)
  → store.clearMessages()
  → setSidebarState("rail")   [if collapsed]
  → focus #copilot-input
  → Invalidate conversation list on settle
```

### Switch Conversation

```
User clicks item in CopilotHistoryPanel
  → store.setConversationId(id)
  → store.clearMessages()
  → fetch messages for id (existing GET /messages endpoint)
  → store.addMessage(…) for each
  → focus #copilot-input
  → active item style applied
```

### Tier Chip Update

```
POST /chat SSE stream starts
  → First non-status event: "tier_decision" { tier, reason, classifier_used }
  → store.setLastMessageTier(incomingMsgId, tier)
  → TierChip re-renders with correct color
  → Subsequent text_chunk events fill message content
```

### Mutation Undo

```
User clicks MutationUndoButton → AlertDialog opens
  → Confirm → useRevertMutations(convId).mutate()
  → POST /conversations/{id}/revert
  → 200 { reverted_count, failed }
  → toast.success("Se revirtieron N cambios.")
  → store.clearMessages() + refetch messages (form fields reverted server-side)
  → activeBridge?.refreshAll()   [if bridge mounted]
```

---

## 11. FSD File Structure

```
frontend/src/features/copilot/
├── components/
│   ├── CopilotSidebar.tsx           (Client — root grid + keyboard shortcuts)
│   ├── CopilotRail.tsx              (Client — always-visible 60px strip)
│   ├── CopilotHistoryPanel.tsx      (Client — history list, groups, pagination)
│   ├── CopilotChatPanel.tsx         (Client — messages + input)
│   ├── SlashCommandAutocomplete.tsx (Client — Command popover)
│   ├── PlanCard.tsx                 (Client — plan_proposed SSE card)
│   ├── MutationUndoButton.tsx       (Client — AlertDialog + revert)
│   ├── ContextRotBanner.tsx         (Client — token rot nudge)
│   ├── TierChip.tsx                 (displayonly — no hooks)
│   ├── cards/                       (existing cards unchanged)
│   ├── messages/                    (existing message components unchanged)
│   └── shared/                      (existing shared components unchanged)
├── hooks/
│   ├── use-conversation-list.ts     (useInfiniteQuery)
│   ├── use-create-conversation.ts   (useMutation)
│   ├── use-patch-conversation.ts    (useMutation)
│   ├── use-delete-conversation.ts   (useMutation)
│   ├── use-revert-mutations.ts      (useMutation)
│   ├── use-slash-commands.ts        (useQuery, staleTime 5min)
│   ├── use-mutation-journal.ts      (useQuery)
│   └── use-conversation-groups.ts   (pure util hook — groups by date)
├── api/
│   ├── conversations.ts             (fetchClient calls)
│   └── slash-commands.ts            (fetchClient calls)
├── store/
│   └── copilot-store.ts             (update SidebarState + new slices)
├── types/
│   ├── conversations.ts             (TS mirror of CONTRACT §5)
│   └── index.ts                     (re-export)
└── index.ts                         (public barrel)
```

---

## 12. Copy (Español Neutro LatAm)

All user-facing strings. No voseo. Verified against `.claude/rules/spanish-text.md`.

| Element | String |
|---------|--------|
| History panel title | "Conversaciones" |
| New conv button | "Nueva conversación" |
| Load more button | "Cargar 6 más" |
| Kebab rename | "Renombrar" |
| Kebab archive | "Archivar" |
| Section: today | "Hoy" |
| Section: yesterday | "Ayer" |
| Section: last 7 days | "Últimos 7 días" |
| Section: older | "Anterior" |
| Rot banner yellow | "Esta conversación ya está larga. Para que el copilot te entienda mejor, [empieza una nueva]." |
| Rot banner CTA | "empieza una nueva" |
| Undo button label | "Deshacer cambios ({N})" |
| Undo dialog title | "¿Seguro que quieres deshacer los cambios?" |
| Undo dialog body | "Se revertirán {N} cambios aplicados en esta conversación. Esta acción no se puede deshacer." |
| Undo confirm button | "Deshacer todo" |
| Cancel button | "Cancelar" |
| Plan card title | "Plan propuesto" |
| Plan apply button | "Aplicar" |
| Plan applied state | "Aplicado" |
| Plan reject button | "Rechazar" |
| Plan rejected state | "Rechazado" |
| Estimated cost label | "Costo estimado:" |
| Send button aria | "Enviar" |
| Rail open aria | "Abrir copilot" |
| Rail expand aria | "Expandir historial" |
| Rail close aria | "Cerrar copilot" |
| New conv rail aria | "Nueva conversación" |
| Slash empty state | "No hay comandos para '{query}'" |
| History empty state | "Aún no hay conversaciones. Empieza una nueva." |
| Chat empty state | "Escribe tu primera pregunta." |
| Streaming aria | "El copilot está escribiendo" |

---

## 13. Shadcn Components Used

| Component | Import path | Usage |
|-----------|------------|-------|
| `Button` | `@/components/ui/button` | All action buttons |
| `Textarea` | `@/components/ui/textarea` (needs install check) | Chat input |
| `Input` | `@/components/ui/input` | Inline rename |
| `ScrollArea` | `@/components/ui/scroll-area` | Message list, history list |
| `Separator` | `@/components/ui/separator` | Rail divider |
| `Tooltip` | `@/components/ui/tooltip` (via existing popover) | Avatar hover titles |
| `DropdownMenu` | `@/components/ui/dropdown-menu` | Conversation kebab |
| `AlertDialog` | `@/components/ui/alert-dialog` | Undo confirm |
| `Dialog` | `@/components/ui/dialog` | (not needed — AlertDialog covers undo) |
| `Popover` | `@/components/ui/popover` | Slash command anchor |
| `Command` | `@/components/ui/command` | Slash command list |
| `Skeleton` | `@/components/ui/skeleton` | Loading states |
| `Card` | `@/components/ui/card` | PlanCard |
| `Badge` | Not in ui/ — use TierChip (custom Tailwind) | Tier labels |
| `Sonner` | `@/components/ui/sonner` | Toast notifications |

---

## 14. A11y Checklist

- Every `Button` has `aria-label` or visible text.
- Root sidebar has `aria-expanded={sidebarState !== "collapsed"}` and `aria-label="Panel copilot"`.
- Sidebar state transitions announced via `role="status" aria-live="polite"` hidden span.
- `AlertDialog` traps focus; `Esc` closes.
- Slash autocomplete uses `role="listbox"` + `aria-activedescendant` (via Shadcn `Command`).
- TierChip has `title` attribute for screen readers (e.g., `title="Modelo: mini"`).
- Context rot banner uses `role="alert"` for immediate announcement.
- Keyboard shortcut `Ctrl+K` targets `document.getElementById("copilot-input")?.focus()`.
- Tab order: rail toggle → rail `+` → history items (if full) → chat input → send button.
- High-contrast: all color decisions use semantic tokens (`border-border`, `bg-accent`, etc.), not raw hex.

---

## 15. Deferred (This Sprint: Spec Only, No Implementation)

| Item | Reason deferred |
|------|----------------|
| `POST /plan/{msgId}/approve|reject` endpoints | Stub only — plan execution is S5 scope |
| `GET /conversations/{id}/mutations` endpoint | TBD backend endpoint path |
| Slash command icons per skill | UX polish, post-S4 |
| Mobile overlay slide animation | Complex gesture handling, post-S4 |
| Plan step cost breakdown tooltip | Nice-to-have |
| Procedure coverage % in history items | Needs `procedure_progress` from list endpoint — field exists in DTO |

---

## 16. Architecture Fitness Tests Applicable

| Test | Constraint enforced |
|------|---------------------|
| `test-component-naming` | All `.tsx` in `components/` must be PascalCase |
| `test-file-naming` | All `.ts` in `hooks/` and `api/` must be kebab-case |
| `test-folder-naming` | `copilot/` subdirs must be kebab-case |
| `test-hook-location` | `export function use*` only in `hooks/` or `api/` |
| `test-no-default-exports` | No `export default` in `features/copilot/` |
| `test-no-duplicate-names` | Component names must not duplicate existing features |
| `test-api-location` | `fetchClient` calls only in `api/` |
