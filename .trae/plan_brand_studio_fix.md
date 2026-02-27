# Plan: Fix Brand Studio Methodology Error and Data Mismatch

## Context

The user is experiencing a `Runtime TypeError: Cannot read properties of undefined (reading 'map')` in `MethodologyForm` because `strategy.methodology_pillars` is undefined.
Investigation revealed a significant mismatch between the Database data (JSON) and the Backend Pydantic Model (`BrandStrategy`).

* **Database (`tenants.config_json['brand_settings']['strategy']`)**: Contains `methodology_name`, `methodology_pillars`, `methodology_description`, `unique_value_proposition`, `competitors`.

* **Backend Model (`BrandStrategy`)**: Contains `value_proposition`, `target_audience`, `differentiation`, `offerings`. It lacks the methodology fields and uses different names (e.g., `value_proposition` vs `unique_value_proposition`).

* **Frontend (`BrandStrategy`** **interface)**: Expects `unique_value_proposition`, `competitors`, and `methodology_pillars` (based on usage), but the type definition is likely missing them or inconsistent.

The strict Pydantic validation in the backend is stripping the existing DB fields because they are not in the model.

## Objectives

1. **Sync Backend Model with DB**: Update `BrandStrategy` Pydantic model to include the fields present in the database (`methodology_*`, `competitors`, `unique_value_proposition`).
2. **Sync Frontend Types**: Ensure `BrandStrategy` interface in frontend matches the backend model and usage.
3. **Fix Runtime Crash**: Initialize `methodology_pillars` to `[]` in the frontend hook to prevent crashes if data is missing.

## Steps

### 1. Update Backend Data Models

* **File**: `backend/src/modules/brand/domain/models.py`

* **Action**:

  * Define `BrandMethodologyPillar` model (id, title, description).

  * Define `BrandCompetitor` model (id, name, etc. - inferred from usage or generic dict if unknown).

  * Update `BrandStrategy` model to include:

    * `unique_value_proposition: Optional[str]`

    * `methodology_name: Optional[str]`

    * `methodology_description: Optional[str]`

    * `methodology_pillars: List[BrandMethodologyPillar] = Field(default_factory=list)`

    * `competitors: List[BrandCompetitor] = Field(default_factory=list)`

  * Keep existing fields (`value_proposition`, etc.) for backward compatibility if needed, but mark as optional.

### 2. Update Frontend Type Definitions

* **File**: `frontend/src/features/brand/types/index.ts`

* **Action**:

  * Add `BrandMethodologyPillar` interface.

  * Add `BrandCompetitor` interface.

  * Update `BrandStrategy` interface to include the new fields.

### 3. Update Frontend Data Initialization

* **File**: `frontend/src/features/brand/hooks/useBrandSettings.ts`

* **Action**:

  * In `useQuery`, ensure `settings.strategy.methodology_pillars` is initialized to `[]` if undefined.

  * Ensure `competitors` is initialized to `[]`.

### 4. Verify Fix

* **Action**: Review changes. The backend will now pass the DB data through to the frontend. The frontend will have correct types and runtime safety.

