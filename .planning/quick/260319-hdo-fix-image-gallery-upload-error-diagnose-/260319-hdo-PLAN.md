---
phase: quick-260319-hdo
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/alembic/versions/011_make_assets_file_path_nullable.py
  - frontend/src/lib/api/assets.ts
autonomous: true
must_haves:
  truths:
    - "Image upload via gallery succeeds without NOT NULL violation on file_path"
    - "Frontend shows server error detail when upload fails instead of generic message"
  artifacts:
    - path: "backend/alembic/versions/011_make_assets_file_path_nullable.py"
      provides: "Alembic migration making file_path nullable"
      contains: "ALTER TABLE assets ALTER COLUMN file_path"
    - path: "frontend/src/lib/api/assets.ts"
      provides: "Improved error handling with server response detail"
      contains: "res.text"
  key_links:
    - from: "backend/alembic/versions/011_make_assets_file_path_nullable.py"
      to: "assets table"
      via: "ALTER COLUMN file_path DROP NOT NULL"
      pattern: "DROP NOT NULL"
---

<objective>
Fix image gallery upload 500 error caused by NOT NULL constraint on legacy `file_path` column in `assets` table, and improve frontend error reporting.

Purpose: Users cannot upload images to the gallery — every upload fails silently with a generic "Upload failed" message. The root cause is a legacy DB column (`file_path`) that the refactored model no longer populates.
Output: Working image uploads + descriptive error messages on failure.
</objective>

<execution_context>
@/home/chris/AISALESHT/.claude/get-shit-done/workflows/execute-plan.md
@/home/chris/AISALESHT/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@backend/src/modules/assets/infrastructure/models/asset_model.py
@backend/src/modules/assets/api/router.py
@frontend/src/lib/api/assets.ts
@backend/alembic/versions/010_referral_nps_tables.py

Root cause: The `assets` DB table has `file_path VARCHAR NOT NULL` but `AssetModel` was refactored to use `storage_path` instead. INSERTs omit `file_path` causing NOT NULL violation.

Current Alembic head: `010_referral_nps` (revision ID: `010_referral_nps`, down_revision: `ab8346fd2c09`).
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create idempotent migration to make file_path nullable and backfill</name>
  <files>backend/alembic/versions/011_make_assets_file_path_nullable.py</files>
  <action>
Create Alembic migration file `011_make_assets_file_path_nullable.py` with:
- revision = "011_file_path_nullable"
- down_revision = "010_referral_nps"
- Use raw SQL (idempotent, per project conventions — NO op.alter_column):
  1. `ALTER TABLE assets ALTER COLUMN file_path DROP NOT NULL;`
  2. `UPDATE assets SET file_path = storage_path WHERE file_path IS NULL AND storage_path IS NOT NULL;` (backfill any existing rows)
  3. `ALTER TABLE assets ALTER COLUMN file_path SET DEFAULT '';` (prevent future issues if any legacy code touches it)
- Downgrade: `ALTER TABLE assets ALTER COLUMN file_path SET NOT NULL;` (with guard: `UPDATE assets SET file_path = COALESCE(file_path, storage_path, '') WHERE file_path IS NULL;` first)

Run the migration inside docker: `docker exec -t visionarias_brain_dev alembic upgrade head`
  </action>
  <verify>
    <automated>docker exec -t visionarias_brain_dev alembic upgrade head 2>&1 | tail -5</automated>
  </verify>
  <done>Migration runs successfully. `file_path` column is now nullable in `assets` table. Existing NULL file_path rows backfilled from storage_path.</done>
</task>

<task type="auto">
  <name>Task 2: Improve frontend upload error message to include server detail</name>
  <files>frontend/src/lib/api/assets.ts</files>
  <action>
In `frontend/src/lib/api/assets.ts`, update the `upload` method error handling (line 37):

Replace:
```typescript
if (!res.ok) throw new Error("Upload failed");
```

With:
```typescript
if (!res.ok) {
  let detail = "Upload failed";
  try {
    const body = await res.json();
    if (body.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
  } catch {
    // Response wasn't JSON, try text
    try {
      const text = await res.text();
      if (text) detail = text;
    } catch { /* ignore */ }
  }
  throw new Error(detail);
}
```

This ensures the FastAPI error detail (which already returns `str(e)` in the 500 handler at router.py:40) propagates to the UI toast/error display instead of the generic "Upload failed".

Also apply the same pattern to the `list` method (line 55) and `delete` method (line 67) for consistency — extract a helper function:

```typescript
async function throwWithDetail(res: Response, fallback: string): Promise<never> {
  let detail = fallback;
  try {
    const body = await res.json();
    if (body.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
  } catch {
    try { const t = await res.text(); if (t) detail = t; } catch { /* ignore */ }
  }
  throw new Error(detail);
}
```

Then use `if (!res.ok) await throwWithDetail(res, "Upload failed");` in all three methods.
  </action>
  <verify>
    <automated>docker exec -t visionarias_client_dev npx tsc --noEmit 2>&1 | grep -E "assets|error" | head -10; echo "EXIT: $?"</automated>
  </verify>
  <done>Frontend compiles without errors. Upload/list/delete failures now surface server-provided error details instead of generic messages.</done>
</task>

</tasks>

<verification>
1. Migration applied: `docker exec -t visionarias_brain_dev alembic current` shows `011_file_path_nullable`
2. Upload test: Upload an image via the gallery UI — should succeed (no 500 error)
3. Error display: If a future upload fails for other reasons, the error message shows the actual server detail
</verification>

<success_criteria>
- Image gallery upload completes successfully (no NOT NULL violation)
- Frontend error messages include server-provided details
- Migration is idempotent and follows project conventions (raw SQL)
</success_criteria>

<output>
After completion, create `.planning/quick/260319-hdo-fix-image-gallery-upload-error-diagnose-/260319-hdo-SUMMARY.md`
</output>
