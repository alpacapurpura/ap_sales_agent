# Tasks

- [x] Task 1: Remove Frontend Knowledge Center
  - [x] SubTask 1.1: Delete `frontend/src/app/(main)/(dashboard)/knowledge/` folder.
  - [x] SubTask 1.2: Delete `frontend/src/features/knowledge/` folder.
  - [x] SubTask 1.3: Delete `frontend/src/lib/api/knowledge.ts` file.
  - [x] SubTask 1.4: Update `frontend/src/components/shared/layout/app-sidebar.tsx` to remove "Conocimiento" link.

- [x] Task 2: Remove Backend Knowledge API & Service
  - [x] SubTask 2.1: Delete `backend/src/api/routers/knowledge.py` file.
  - [x] SubTask 2.2: Delete `backend/src/services/knowledge_service.py` file.
  - [x] SubTask 2.3: Delete `backend/src/services/document_service.py` file.
  - [x] SubTask 2.4: Delete `backend/scripts/test_rag_raw.py` and `backend/scripts/test_category_logic.py`.

- [x] Task 3: Update Backend Configuration & Models
  - [x] SubTask 3.1: Modify `backend/src/main.py` to remove `knowledge` router include.
  - [x] SubTask 3.2: Modify `backend/src/api/routers/admin.py` to remove `KnowledgeService` import and `sync_knowledge_base` endpoint.
  - [x] SubTask 3.3: Modify `backend/src/services/db/models/business.py` to remove `Document` class and `documents` relationship in `MarketingAsset`.
  - [x] SubTask 3.4: Modify `backend/src/services/db/models/__init__.py` to remove `Document` export.
  - [ ] SubTask 3.5: Create database migration to remove `documents` table and relationship (Optional but recommended for consistency).

# Task Dependencies
- Task 3 depends on Task 2 (Files must be gone or modified before removing references).
