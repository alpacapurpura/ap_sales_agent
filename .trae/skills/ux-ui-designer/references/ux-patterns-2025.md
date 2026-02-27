# UX Patterns 2025: Disruptive & Functional

## 1. The Bento Grid (Modular Dashboards)
Moving away from static tables to interactive, resizeable grids.

**Concept**:
- Every cell is a "micro-app".
- **Example**: In `Offer Studio`, one cell is the Pricing Editor, another is the Live Preview.
- **Key Component**: `card.tsx` + CSS Grid.

**Implementation Pattern**:
```tsx
<div className="grid grid-cols-1 md:grid-cols-3 gap-4 auto-rows-[200px]">
  <Card className="md:col-span-2 row-span-2">Main Editor</Card>
  <Card className="">Quick Stats</Card>
  <Card className="">AI Suggestions</Card>
</div>
```

## 2. AI-Native UI (Generative Interfaces)
The chat is not just text. It renders UI.

**Concept**:
- User asks: "Show me the sales trend."
- AI responds: Renders a `<ChartComponent />` directly in the chat stream.

**Implementation Pattern**:
- Use `shadcn` cards as "Artifacts" within the chat timeline.
- **Actionable**: The rendered card must be interactive (e.g., "Apply this change").

## 3. Optimistic UI & Skeleton Loading
**Problem**: AI is slow (LLM latency).
**Solution**:
1.  **Immediate Feedback**: Show the "Skeleton" of the expected response immediately.
2.  **Optimistic Updates**: If user renames a Lead, update the UI instantly, revert if API fails.
3.  **Streaming UI**: Render parts of the UI as the AI generates them.

## 4. Mode-Aware Interfaces
Beyond simple Dark Mode.
- **Depth**: Use `border-white/5` and `bg-black/40` (glassmorphism) for overlays.
- **Focus Mode**: Dim the background when a `Sheet` or `Dialog` is open to focus attention.
