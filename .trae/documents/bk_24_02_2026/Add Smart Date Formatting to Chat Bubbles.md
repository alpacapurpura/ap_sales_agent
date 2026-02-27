# Add Smart Date Formatting to Chat Bubbles

I will update the `ChatTimeline` component to display user-friendly dates in conversation bubbles.

## Implementation Steps

1. **Update Imports**:

   * Add `isToday`, `isYesterday` to `date-fns` imports.

   * Add `es` to `date-fns/locale` imports.

2. **Create Helper Function**:

   * Implement `formatMessageDate(dateString: string)` logic:

     * **Today**: "Hoy HH:mm:ss"

     * **Yesterday**: "Ayer HH:mm:ss"

     * **Older**: "Lunes 02 de Febrero del 2026 - HH:mm:ss" (Capitalizing the first letter).

3. **Modify Render Logic**:

   * In `ChatTimeline`, locate the message bubble rendering (lines 228-234).

   * Replace the existing `format(..., "HH:mm:ss")` call with the new `formatMessageDate` function.

## Verification

* Verify that recent messages show "Hoy".

* Verify that older messages follow the full date format.

