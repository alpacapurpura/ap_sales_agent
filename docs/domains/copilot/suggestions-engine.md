# Suggestions Engine — Stub and Future

Smart chips under the chat input. This iteration ships a **stub** only; the
hook surface is frozen so the real engine can land later with zero FE change.

Authoritative spec: [CONTRACT-MULTIMODAL.md §11](./CONTRACT-MULTIMODAL.md#11-smart-chips-contract-stub).
Anchor: `[COPILOT-SUGGESTIONS-ENGINE]`.

---

## Current state (this iteration)

- `Suggestion` TS interface locked.
- `useSuggestions(conversationId)` hook locked.
- Stub implementation returns 3 hardcoded chips based on `currentRoute`.
- No backend endpoint exists.

---

## Contract (stable across stub → real engine)

```typescript
export interface Suggestion {
  id: string;                           // stable; stubs use "stub-<hash>"
  label: string;                        // user-visible, Spanish neutro LatAm
  prompt: string;                       // filled into input on click
  confidence?: number;                  // 0..1; undefined in stub
  category?: "followup" | "action" | "clarify" | "nav";
}

export function useSuggestions(conversationId: string | null): {
  suggestions: Suggestion[];
  isLoading: boolean;
  refresh: () => void;
};
```

The hook MUST:
- Return ≤5 suggestions (FE renders max 5 chips).
- Be idempotent on repeated calls with the same `conversationId`.
- Expose `refresh()` to force re-compute (e.g., after a message send).

---

## Real-engine options (not built)

When the first real use case arrives, implementer picks one. Each fits the
locked hook surface.

### Option A — heuristic backend (rule-based)

```
GET /api/v1/copilot/conversations/{conversation_id}/suggestions
Response: SuggestionsPayload
```

Backend logic:
- Read last N messages.
- Apply a small rule set: if last assistant message ended with a question → surface "Sí / No / Explícame más". If `procedure_state.current_block` is set → surface "Continuar", "Saltar", "Revisar". If route is `brand-studio` → surface 2–3 brand-specific prompts.
- No LLM call. Cheap, fast.

**Pros:** deterministic, free, testable.
**Cons:** limited sophistication.

### Option B — tool-driven (LLM emits suggestions)

The LLM is instructed (via skill) to emit up to 5 `Suggestion` objects as part
of its response metadata. Surfaced in `message_end.metadata.suggestions`.

FE reads from the last message's metadata:

```ts
function useSuggestions(conversationId) {
  const lastMessage = useLastMessage(conversationId);
  return lastMessage?.metadata?.suggestions ?? [];
}
```

**Pros:** context-aware, zero extra call.
**Cons:** tokens cost per message; LLM might forget; less predictable latency
(FE must wait for `message_end`).

### Option C — new SSE event

After `done`, orchestrator emits `suggestions_ready` with a `SuggestionsPayload`.
Computed by a fast heuristic post-hoc.

**Pros:** doesn't block `done`; can be computed async.
**Cons:** new event to maintain; adds SSE surface.

### Hybrid (most likely final state)

- Heuristic (A) as default and fallback.
- LLM-driven (B) for routes where conversation quality matters (brand audit,
  offer design).
- SSE event (C) if latency of B becomes a user-visible issue.

---

## Stub implementation spec

```ts
// frontend/src/features/copilot/hooks/use-suggestions.ts
// [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md

import { useMemo, useState } from "react";
import type { Suggestion } from "../types/suggestions";
import { usePathname } from "next/navigation";

const STUBS_BY_ROUTE: Record<string, Suggestion[]> = {
  "brand-studio": [
    { id: "stub-brand-audit", label: "Audita mi identidad", prompt: "Audita mi identidad actual y dime qué mejorar." },
    { id: "stub-brand-tagline", label: "Mejora mi tagline", prompt: "Propón 3 alternativas para mi tagline actual." },
    { id: "stub-brand-voice", label: "Revisa mi tono de voz", prompt: "Revisa mi tono de voz y sugiéreme ajustes." },
  ],
  "offer-studio": [
    { id: "stub-offer-ladder", label: "Arma mi escalera de oferta", prompt: "Ayúdame a armar mi escalera de oferta completa." },
    { id: "stub-offer-price", label: "Revisa mis precios", prompt: "Revisa mis precios y dime si tiene sentido el salto entre tiers." },
    { id: "stub-offer-copy", label: "Propón copy para mi oferta flagship", prompt: "Propón copy para la oferta principal del catálogo." },
  ],
  // ... other routes
  default: [
    { id: "stub-default-help", label: "¿Qué puedes hacer?", prompt: "¿Qué tareas puedes ayudarme a resolver?" },
    { id: "stub-default-start", label: "¿Por dónde empiezo?", prompt: "Soy nuevo. Sugiéreme por dónde empezar." },
  ],
};

export function useSuggestions(conversationId: string | null) {
  const pathname = usePathname();
  const [refreshKey, setRefreshKey] = useState(0);

  const suggestions = useMemo(() => {
    const routeKey = pathname?.split("/")[2] ?? "default";
    return STUBS_BY_ROUTE[routeKey] ?? STUBS_BY_ROUTE.default;
  }, [pathname, refreshKey, conversationId]);

  return {
    suggestions,
    isLoading: false,
    refresh: () => setRefreshKey((k) => k + 1),
  };
}
```

---

## Migration from stub → real

When real engine lands:

1. Replace `useSuggestions` implementation to fetch from BE (option A) or read
   message metadata (option B) or subscribe to SSE (option C).
2. Keep the hook signature unchanged.
3. Keep `Suggestion` interface unchanged.
4. Components using `useSuggestions` (SlashCommandAutocomplete,
   SuggestedActions) require zero edits.

---

## Testing

### Stub testing

- Snapshot test: given route X, returns the expected chips.
- `refresh()` triggers a re-compute (useState invalidation).

### Real engine testing

- Contract test: response shape conforms to `SuggestionsPayload`.
- Integration: after N messages, the hook returns 3–5 chips.
- E2E smoke: clicking a chip fills the input with its `prompt`.

---

## See also

- [CONTRACT-MULTIMODAL.md §11](./CONTRACT-MULTIMODAL.md#11-smart-chips-contract-stub).
- `frontend/src/features/copilot/components/SlashCommandAutocomplete.tsx` —
  consumer today (slash commands).
- `frontend/src/features/copilot/components/SuggestedActions.tsx` — future
  consumer.
