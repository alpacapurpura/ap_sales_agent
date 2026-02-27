# Deep Data Model Review Plan

## Objective
Fix persistent "Error cargando Disponibilidad" and missing data issues in "Configuración de Agenda" by performing a deep review and correction of the data model and migration logic.

## Analysis
The previous fix attempted to rename `weekly_hours` to `schedule` and `is_active` to `is_hidden` at the top level of the JSON objects stored in `tenant.config_json`. However, it failed to address the **nested structure** of `weekly_hours` (now `schedule`).

### The Mismatch
1.  **AvailabilitySchedule**:
    *   **Current Schema**:
        ```python
        class DaySchedule(BaseModel):
            active: bool = True
            ranges: List[TimeSlot] = []
        ```
    *   **Old Data Structure (Hypothesis)**:
        ```json
        {
            "monday": {
                "is_active": true,  // <--- Mismatch: 'is_active' vs 'active'
                "slots": [...]      // <--- Mismatch: 'slots' vs 'ranges'
            }
        }
        ```
    *   **Result**: Pydantic validation fails when instantiating `AvailabilitySchedule` because the nested `DaySchedule` objects don't match the schema. The `list_schedules` method catches this or the API returns 500, leading to "Error cargando disponibilidades".

2.  **EventType**:
    *   **Current Schema**: `is_hidden`
    *   **Old Data**: `is_active`
    *   **Status**: The previous fix handled the top-level `is_active` -> `is_hidden` migration, but we need to ensure all nested fields (like `locations` or others) are also correct.

## Plan Steps

### 1. Implement Recursive Data Migration Helper
Create a robust helper function `_migrate_schedule_data` in `AvailabilityService` that:
- Takes a raw dictionary (from DB).
- Recursively traverses `weekly_hours` (or `schedule`).
- Renames nested keys:
    - `is_active` -> `active`
    - `slots` -> `ranges`
- Renames top-level key:
    - `weekly_hours` -> `schedule`
- Returns a clean dictionary ready for `AvailabilitySchedule(**data)`.

### 2. Update `AvailabilityService.list_schedules`
- Apply `_migrate_schedule_data` to every item retrieved from `tenant.config_json`.
- Ensure strict error handling: if one item fails validation, log it but don't crash the whole list (return valid ones only, or return a default if all fail).

### 3. Update `EventTypeService.list_event_types`
- Verify if `EventType` has any nested structures needing migration (e.g. `locations`).
- Ensure the `is_active` -> `is_hidden` logic is robust.

### 4. Verify Frontend Compatibility
- Double-check `frontend/src/lib/api/availability.ts` to ensure the TypeScript interfaces match the **New Schema** exactly.
    - `DaySchedule`: `active: boolean`, `ranges: TimeRange[]`.
    - `TimeRange`: `start: string`, `end: string`.

### 5. Verification
- Use `TodoWrite` to track progress.
- Once code is updated, the user should be able to reload the page and see the data correctly.

## Technical Details

### Migration Logic (Python)
```python
def _migrate_schedule_structure(self, data: dict) -> dict:
    # 1. Top level rename
    if 'weekly_hours' in data:
        data['schedule'] = data.pop('weekly_hours')
    
    # 2. Nested keys in 'schedule'
    if 'schedule' in data and isinstance(data['schedule'], dict):
        new_schedule = {}
        for day, day_data in data['schedule'].items():
            if isinstance(day_data, dict):
                # Migrate is_active -> active
                if 'is_active' in day_data:
                    day_data['active'] = day_data.pop('is_active')
                
                # Migrate slots -> ranges
                if 'slots' in day_data:
                    day_data['ranges'] = day_data.pop('slots')
            
            new_schedule[day] = day_data
        data['schedule'] = new_schedule
        
    return data
```

This approach ensures that the data passed to Pydantic is 100% compliant with the new schema.
