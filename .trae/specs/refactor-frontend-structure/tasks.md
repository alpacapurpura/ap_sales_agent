# Tasks

- [x] Task 1: Move Marketing Studio to Tenant Scope
  - [x] SubTask 1.1: Create target directory `src/app/(main)/[tenantId]/(dashboard)/marketing-studio` if it doesn't exist.
  - [x] SubTask 1.2: Move `src/app/(dashboard)/marketing-studio/page.tsx` to the new location.
  - [x] SubTask 1.3: Verify and update imports in the moved file if necessary.
  - [x] SubTask 1.4: Remove the empty `src/app/(dashboard)` directory.

- [x] Task 2: Verify and Fix Links
  - [x] SubTask 2.1: Search for any internal links to `/marketing-studio` in the codebase (e.g., sidebar navigation).
  - [x] SubTask 2.2: Update them to point to `/${tenantId}/marketing-studio`.

- [x] Task 3: Refactor Tenants Client (Bonus/Cleanup)
  - [x] SubTask 3.1: Move logic from `src/app/(main)/[tenantId]/(dashboard)/admin/tenants/tenants-client.tsx` to `src/features/admin/components/tenants-list.tsx`.
  - [x] SubTask 3.2: Update import in `page.tsx`.
