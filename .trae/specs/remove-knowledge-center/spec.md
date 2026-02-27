# Remove Knowledge Center Spec

## Why
The "Centro de Conocimiento" (Knowledge Center) functionality is being deprecated. The information and management capabilities previously housed there are now being consolidated into "Offer Studio" and "Brand Studio". The existing code for the Knowledge Center page and its underlying RAG infrastructure (KnowledgeService, DocumentService) is currently unused by the active modules (which use JSON config or mocks) and should be removed to clean up the codebase.

## What Changes
- **Frontend**: 
  - Remove the `/knowledge` route and page.
  - Remove the "Conocimiento" link from the sidebar.
  - Remove `KnowledgePage` components and `SafetyLayerManager` UI.
  - Remove `knowledge` API client.
- **Backend**:
  - Remove `knowledge` API router and endpoints.
  - Remove `KnowledgeService` and `DocumentService`.
  - Remove `Document` database model.
  - Remove `documents` relationship from `MarketingAsset` model.
  - Remove `sync_knowledge_base` endpoint from Admin API.
  - **KEEP** `SensitiveData` model and `SafetyLayerService` (as they are used by the Agent runtime).

## Impact
- **BREAKING**: The `/knowledge` page will 404. The `/api/v1/knowledge` endpoints will 404.
- **Data**: The `documents` table in Postgres will be orphaned (code removed, table remains until migration drops it, though migration is out of scope here unless requested, I will just remove code).
- **Agent**: The Agent will no longer be able to search for documents via `KnowledgeService` (which was unused anyway).
- **Admin**: The `sync` endpoint for RAG will be gone.

## REMOVED Requirements
### Requirement: Knowledge Center UI
**Reason**: Consolidated into Offer/Brand Studio.
**Migration**: Users should use Offer/Brand Studio for relevant settings.

### Requirement: Document Ingestion API
**Reason**: Unused by current frontend; future implementation will be domain-specific.

### Requirement: Document Management Service
**Reason**: Unused infrastructure.
