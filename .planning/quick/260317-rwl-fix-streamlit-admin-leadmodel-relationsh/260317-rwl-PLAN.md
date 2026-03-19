---
phase: quick-260317-rwl
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/src/admin/app.py
autonomous: true
requirements: [QUICK-FIX]
must_haves:
  truths:
    - "Streamlit admin loads tenant list without SQLAlchemy relationship resolution errors"
    - "Streamlit admin loads user list without errors"
    - "No LeadModel or CustomerProfileModel import errors at runtime"
  artifacts:
    - path: "backend/src/admin/app.py"
      provides: "Model bootstrap imports for SQLAlchemy registry"
      contains: "from src.modules.crm.infrastructure.models.lead_model import LeadModel"
  key_links:
    - from: "backend/src/admin/app.py"
      to: "backend/src/modules/crm/infrastructure/models/lead_model.py"
      via: "bootstrap import before any DB query"
      pattern: "import LeadModel"
---

<objective>
Fix the Streamlit admin panel crashing with `sqlalchemy.exc.InvalidRequestError: expression 'LeadModel' failed to locate a name` when querying TenantModel.

Purpose: The admin app only imports IAM models, but TenantModel has `leads = relationship("LeadModel", ...)` which SQLAlchemy tries to resolve at query time. Since LeadModel (and its dependency CustomerProfileModel) are never imported, the mapper registry is incomplete.

Output: Working admin panel that can list/create/edit tenants and users without relationship resolution errors.
</objective>

<execution_context>
@/home/chris/AISALESHT/.claude/get-shit-done/workflows/execute-plan.md
@/home/chris/AISALESHT/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@backend/src/admin/app.py
@backend/src/modules/iam/infrastructure/models/tenant_model.py
@backend/src/modules/crm/infrastructure/models/lead_model.py
@backend/src/modules/crm/infrastructure/models/customer_model.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add model bootstrap imports to admin app.py</name>
  <files>backend/src/admin/app.py</files>
  <action>
In `backend/src/admin/app.py`, under the existing `# --- BOOTSTRAP MODELS (CRITICAL) ---` comment, add imports for ALL models referenced by string relationships from TenantModel and their transitive dependencies. The full chain is:

1. `TenantModel.leads` references `"LeadModel"` (string) -> needs LeadModel imported
2. `LeadModel.customer` references `"CustomerProfileModel"` (string) -> needs CustomerProfileModel imported
3. `CustomerProfileModel.identities` references `"CustomerIdentityModel"` and `CustomerProfileModel.journey_events` references `"JourneyEventModel"` -> both in same file as CustomerProfileModel, so importing that file covers them

Add these imports BEFORE the admin module imports (before the `from src.admin.modules.tenants import` lines):

```python
# --- BOOTSTRAP MODELS (CRITICAL) ---
# Import all models to ensure SQLAlchemy Registry is fully populated before any query.
# TenantModel.leads -> LeadModel -> CustomerProfileModel (+ Identity, JourneyEvent in same file)
# Without these, SQLAlchemy cannot resolve string-based relationship() references.
from src.modules.crm.infrastructure.models.lead_model import LeadModel  # noqa: F401
from src.modules.crm.infrastructure.models.customer_model import CustomerProfileModel  # noqa: F401
```

The `# noqa: F401` suppresses "imported but unused" linter warnings since these are side-effect imports for SQLAlchemy registry population.

Do NOT remove any existing imports. Keep all other code unchanged.
  </action>
  <verify>
    <automated>docker exec -t visionarias_brain_dev python -c "from src.admin.app import main; print('Admin app imports OK')"</automated>
  </verify>
  <done>Admin app.py imports LeadModel and CustomerProfileModel before any DB queries. The SQLAlchemy mapper registry is fully populated when TenantModel relationships are resolved. Import succeeds without errors.</done>
</task>

</tasks>

<verification>
1. `docker exec -t visionarias_brain_dev python -c "from src.admin.app import main; print('OK')"` exits 0
2. If Streamlit is running: navigate to admin panel, verify tenant list loads without errors
</verification>

<success_criteria>
- Admin app starts without SQLAlchemy InvalidRequestError
- Tenant listing, creation, and editing work (no LeadModel resolution failure)
- User listing works (queries TenantModel without error)
</success_criteria>

<output>
After completion, create `.planning/quick/260317-rwl-fix-streamlit-admin-leadmodel-relationsh/260317-rwl-SUMMARY.md`
</output>
