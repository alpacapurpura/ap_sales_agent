# Visionarias Brand Identity Spec

## Why
The current "Offer Identity" header is clean but generic. The user specifically requested the "Visionarias" visual identity to be applied, ensuring the interface feels like part of their specific brand ecosystem (Mystic, Abundance, Liberation).

## What Changes
- **Refactor `IdentityPreview.tsx`**:
    -   **Visual Theme**: Shift from generic "Primary/Slate" to a **"Mystic & Abundance"** theme.
    -   **Palette**:
        -   **Primary**: Deep Purple / Indigo (`violet-600` / `indigo-900`).
        -   **Accent**: Gold / Amber (`amber-400` / `yellow-500`) for "Abundance" signals.
    -   **Typography**: Use `font-serif` (if available in global fonts) or elegant `tracking-tight` styling for the Offer Title to match the "Editorial" feel.
    -   **Iconography**: Update the Icon Container to be more "Ethereal" (Glassmorphism + Glow).
    -   **Background**: Implement a rich gradient background that evokes "Fire & Water" (Purple to Amber/Rose).

## Impact
- **Affected specs**: Offer Studio > Identity.
- **Affected code**: `frontend/src/features/offer-studio/components/editor/preview/IdentityPreview.tsx`.

## Design Proposals (Alternatives)

### Option A: "The Sovereign" (Selected)
*   **Vibe**: Authority, Structure, High-Ticket.
*   **Background**: Deep dark navy/purple (almost black) with a central glowing orb.
*   **Text**: White/Cream with Gold gradients on key terms.
*   **Why**: Fits the "Empresaria" (Businesswoman) archetype of Visionarias.

### Option B: "The Alchemist"
*   **Vibe**: Transformation, Flow, Energy.
*   **Background**: Lighter, fluid gradients (Rose -> Violet).
*   **Text**: Dark purple.
*   **Why**: Fits the "Sanación" (Healing) archetype.

**Decision**: We will implement a hybrid **"Visionarias Studio"** look:
- **Light Mode**: Cream/Soft Gold background with Purple text (Warm, welcoming).
- **Dark Mode**: Deep Indigo/Violet background with Gold text (Mystic, premium).
- *Note*: We will use Tailwind's `dark:` modifiers to support both, but focus on the "Premium" feel.

## ADDED Requirements
### Requirement: Visionarias Brand Alignment
The component SHALL use the specific "Visionarias" color palette (Purple/Gold) instead of generic system defaults.

#### Scenario: Visual Feedback
- **WHEN** the user views the header
- **THEN** they see a "Gold/Purple" glow effect around the icon.
- **THEN** the badges use a custom "Brand Pill" style (Solid deep color or elegant outline).
