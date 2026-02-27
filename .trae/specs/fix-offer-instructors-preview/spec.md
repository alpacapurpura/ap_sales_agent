# Fix Offer Instructors Preview & Progress Spec

## Why
Users are experiencing two issues with the "Instructors" section in the Offer Studio:
1.  The preview section appears empty even when instructors are selected (showing only IDs or nothing).
2.  The section is not marked as "Completed" in the progress sidebar, even when instructors are added.

## What Changes
- **`InstructorsPreview` Component**:
    - Will now fetch `BrandSettings` using the `useBrandSettings` hook to access the full `team` list.
    - Will map the selected `instructor_ids` to the actual `KeyFigure` objects to display names, roles, and avatars.
    - Will handle loading states gracefully.
- **`offer-health.ts` Utility**:
    - Will update the validation logic for the `instructors` section.
    - Instead of always returning `optional`, it will return `complete` if instructors are present, and `optional` if empty. This ensures it counts towards the completion progress when filled.

## Impact
- **Affected Specs**: Offer Studio (Instructors Section).
- **Affected Code**:
    - `frontend/src/features/offer-studio/components/editor/sections/instructors/instructors-preview.tsx`
    - `frontend/src/features/offer-studio/utils/offer-health.ts`

## ADDED Requirements
### Requirement: Instructor Preview
The `InstructorsPreview` component SHALL:
- Retrieve the full list of instructors from `BrandSettings`.
- Match selected IDs with available instructors.
- Display the Instructor's Name, Role, and Avatar (if available).
- Show a fallback avatar if no image is provided.

### Requirement: Progress Calculation
The `getOfferHealth` logic SHALL:
- Mark the `instructors` section as `complete` if the offer has at least one instructor assigned.
- Keep it as `optional` (not `incomplete`) if no instructors are assigned, so it doesn't prevent 100% completion if the user chooses not to add any.

## MODIFIED Requirements
### Requirement: Offer Health Logic
**Old**: `instructors` section always returns `status: "optional"`.
**New**: `instructors` section returns `status: "complete"` if `offer.instructors.length > 0`, otherwise `status: "optional"`.
