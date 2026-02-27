# Tasks

- [x] Backend: Create Pydantic schemas for partial updates.
- [x] Backend: Create atomic `PATCH` endpoints in `products.py`.
- [x] Frontend: Move `Identity`, `Strategy`, `Pricing`, `Closing`, `Visuals`, `Resources`, `Instructors`, `ValueStack`, `Promise`, `Psychology` to `sections/`.
- [x] Frontend: Move complex forms to `sections/`:
    - [x] `program-form.tsx`, `curriculum-builder.tsx`, `session-schedule-builder.tsx`, `import-curriculum-dialog.tsx` -> `sections/program-details/`
    - [x] `product-form.tsx` -> `sections/product-details/`
    - [x] `service-form.tsx` -> `sections/service-details/`
    - [x] `event-form.tsx` -> `sections/event-details/`
    - [x] `subscription-form.tsx` -> `sections/subscription-details/`
- [x] Frontend: Move shared components to `sections/common/`:
    - [x] `SectionFormWrapper.tsx`
    - [x] `PlaceholderForm.tsx`
- [x] Frontend: Move `OfferEditSheetManager.tsx` to `components/editor/`.
- [x] Frontend: Update `offer-builder-config.ts` with new paths.
- [x] Frontend: Update API client (`offer-service.ts` or similar) to use new atomic endpoints.
- [x] Frontend: Integrate forms with new API calls.
