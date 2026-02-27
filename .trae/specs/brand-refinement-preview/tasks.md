# Tasks

- [x] Task 1: Backend - Add dry_run to BrandExtractionService
  - [x] Update `BrandExtractionService.extract_all` to accept `dry_run: bool = False`.
  - [x] Update `_merge_and_save` to handle `dry_run`. If true, return merged settings without DB commit.
  - [x] Add unit test for `extract_all(dry_run=True)` to ensure no DB changes.

- [x] Task 2: Backend - Add dry_run to extract-full-brand endpoint
  - [x] Update `POST /api/v1/tools/extract-full-brand` to accept `dry_run: bool = False`.
  - [x] Pass `dry_run` to `BrandExtractionService`.
  - [x] Verify endpoint returns correct data without saving.

- [x] Task 3: Frontend - Add Preview Mode to BrandStudioLayout
  - [x] Add `previewData` state to `BrandStudioLayout`.
  - [x] Implement `handlePreview` function to update state.
  - [x] Compute `displaySettings` merging `settings` and `previewData`.
  - [x] Pass `displaySettings` to all child components (`StrategySection`, `StorySection`, etc.).
  - [x] Add `PreviewBanner` component to indicate preview mode.

- [x] Task 4: Frontend - Implement Preview in SmartFillCard
  - [x] Add `onPreview` prop to `SmartFillCard`.
  - [x] Update `handleExtract` to call API with `dry_run=true` when in "update" mode.
  - [x] Call `onPreview(data)` on success.
  - [x] Update "Apply Changes" logic to commit the preview data (either by calling save API or using existing `onSuccess` flow).

- [x] Task 5: Frontend - Audit and Verify Field Mappings
  - [x] Verify that all fields mentioned by the user (UVP, Methodology, Story, etc.) are correctly mapped from `BrandSettings` to UI components.
  - [x] Specifically check `AvatarsSection` (Wait, Avatars are separate entity, need special handling or note limitation).
  - [x] Ensure `TeamSection` uses `team` from `displaySettings`.
  - [x] Ensure `TrustSection` uses `authority_vault` from `displaySettings`.

- [x] Task 6: Frontend - Integration Test
  - [x] Verify the full flow: Refine -> Preview -> Apply -> Save.
  - [x] Verify data persistence after reload.

# Task Dependencies
- Task 3 depends on Task 2 (API update).
- Task 4 depends on Task 3 (Layout support).
- Task 5 depends on Task 3.
