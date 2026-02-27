# Brand Studio UX Refactor Spec

## Why
The current interface crowds the "Brand Studio" with large input forms that are only relevant during initial setup or specific updates. This creates visual noise for established brands and pushes the actual content (The "DNA") below the fold.

## UX Scenarios & Flow

### 1. New User (Zero State)
**Context**: A user creates a new brand and enters Brand Studio for the first time.
- **Visual**: The main content area is replaced by a **"Brand Onboarding" Hero Section**.
    - *Headline*: "Define tu Identidad de Marca"
    - *Subhead*: "¿Cómo quieres empezar?"
- **Actions**:
    - **Primary Button (Magic)**: "Autocompletar con IA" -> Opens the **Smart Fill Sheet** (Side Panel) to analyze a website/doc.
    - **Secondary Button (Manual)**: "Configurar Manualmente" -> Removes the Hero Section and reveals the standard layout with empty placeholders.

### 2. User in Progress (Partial State)
**Context**: User has defined the "Identity" but "Strategy" is missing.
- **Visual**: Standard layout.
    - *Identity Section*: Shows the defined logo/colors.
    - *Strategy Section*: Shows a "Placeholder Card" (already exists) prompting to add strategy.
- **Actions**:
    - User clicks the specific "Add Strategy" placeholder to edit manually.
    - **OR** User clicks "Refinar con IA" in the header to use the AI assistant to fill the missing gaps.

### 3. User Completed (Established State)
**Context**: Brand is fully configured.
- **Visual**: A clean, document-style view of the Brand DNA. No large forms, no clutter. Focus is on the *content*.
- **Actions**: Read-only view with subtle "Edit" buttons on hover for each section.

### 4. Returning User (Refinement/Update)
**Context**: User wants to update the brand tone or add a new product line after months.
- **Visual**: Same clean view as Scenario 3.
- **Actions**:
    - User clicks the **"Refinar con IA"** button (located in the top-right header, always accessible).
    - **Interaction**: The **Smart Fill Sheet** slides in from the right.
    - **Flow**: User types "Update our tone to be more professional" -> AI processes -> Changes are previewed -> User applies.
    - **Result**: The Sheet closes, and the main view updates instantly.

## What Changes
- **Refactor `BrandStudioLayout`**: Remove the embedded `SmartFillCard`.
- **Introduce `BrandEmptyState`**: The "Hero Section" for Scenario 1.
- **Create `SmartFillSheet`**: The Side Panel container for the AI tool.
- **Update `HeaderSection`**: Add the persistent "Refinar con IA" button.

## Impact
- **Affected Specs**: Brand Studio.
- **Affected Code**: `brand-studio-layout.tsx`, `smart-fill-card.tsx`, `header-section.tsx`.
- **UX Improvement**:
    - **Clarity**: Separation of "Editing" vs "Viewing".
    - **Focus**: Content-first approach.
    - **Consistency**: AI tools are always in the same place (Header -> Sheet), not floating in the page body.

## ADDED Requirements
### Requirement: On-Demand Smart Fill
The system SHALL provide access to "Brand Refinement" tools via a secondary action button in the header.

### Requirement: Brand Empty State
The system SHALL display a clear "Getting Started" view for brands with no data, offering "Start with AI" and "Manual Setup" paths.

## MODIFIED Requirements
### Requirement: Clean Layout
The `BrandStudioLayout` SHALL NOT render the `SmartFillCard` directly in the document flow.
