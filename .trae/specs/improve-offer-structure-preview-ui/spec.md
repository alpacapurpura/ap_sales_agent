# Offer Structure Preview UI Improvement Spec

## Why
The current "Offer Structure" preview is too technical, cluttered with duplicate titles and nested cards, and lacks the visual appeal needed for non-technical users. The goal is to transform it into a "Live Preview" experience similar to the **Brand Studio**, where the user sees a visual summary of their offer rather than a form dump.

## What Changes
- **Creative & Visual "Identity" Section**:
    - **Inspiration**: `Brand Studio > HeaderSection`.
    - **Design**: Create a visual header for the offer.
        - Use a subtle gradient background or a clean, modern layout.
        - Display the **Offer Name** with large, elegant typography.
        - Show **Offer Type** and **Delivery Model** as styled badges/pills, not just text fields.
        - **Remove**: Duplicate "Identidad" title and internal card borders.
- **Visual "Strategy" Summary**:
    - **Inspiration**: `Brand Studio > StrategySection`.
    - **Design**:
        - **Avatar Persona**: Display the Target Avatar as a "User Profile" (Avatar + Name + Key trait).
        - **Pain Points/Desires**: Use a "Tag Cloud" or "Key Highlights" list with checkmarks/icons, limiting to top 3 items to keep it clean.
        - **Remove**: Duplicate "Estrategia" title and card wrappers.
- **Consistent "Brand Studio" Aesthetics**:
    - **Layout**: Remove all `Card` components. Use the `OfferSectionWrapper`'s natural flow (Icon on left, content on right).
    - **Typography**: Use hierarchy (H1 for offer name, distinct styles for labels vs content).
    - **Interactivity**: Add subtle hover effects (like Brand Studio) to indicate editability.
- **Refactor Other Previews**:
    - Apply the same "No Card / No Duplicate Title" rule to `PricingPreview`, `InstructorsPreview`, etc.
    - Ensure `PlaceholderPreview` fits this new clean style.

## Impact
- **Affected specs**: Offer Studio (Editor & Preview).
- **Affected code**:
    - `frontend/src/features/offer-studio/components/editor/preview/IdentityPreview.tsx`
    - `frontend/src/features/offer-studio/components/editor/preview/StrategyPreview.tsx`
    - `frontend/src/features/offer-studio/components/editor/preview/PricingPreview.tsx` (and others)
    - `frontend/src/features/offer-studio/components/editor/OfferSectionWrapper.tsx`

## ADDED Requirements
### Requirement: Brand-Studio-Like Visuals
The preview system SHALL use a "Live Document" aesthetic (clean, spacious, visual) instead of a "Form Summary" aesthetic (boxed, dense, textual).

#### Scenario: Viewing Offer Identity
- **WHEN** the user views the Identity section.
- **THEN** they see a "Hero" style header with the Offer Name and styled metadata, resembling a landing page header.

### Requirement: Creative Data Summarization
The system SHALL creatively summarize complex data points.
- **Avatar**: Show as a persona card.
- **Lists**: Show as visual tags or bullet points with icons.
- **Pricing**: Show as a price tag or clean number display.

## MODIFIED Requirements
### Requirement: Section Layout
**Old**: Nested Cards with internal titles.
**New**: Flat, seamless sections relying on `OfferSectionWrapper` for structure and headers, preventing visual redundancy.
