# Sales Module Refactoring Spec

## Why
El módulo Sales (Lead y Pipeline) es el núcleo del sistema de IA. Actualmente, `Lead` mezcla datos de perfil, estado del sistema y lógica de canales. La relación con `Customer` (Marketing) y `Tenant` (IAM) debe ser clara. Se requiere separar el modelo de dominio puro de la persistencia y limpiar dependencias cruzadas.

## What Changes
-   **Domain**:
    -   `Lead`: Entidad raíz. Contiene `UserProfile` (Value Object), Scores y Estado.
    -   `UserProfile`: Pydantic puro para datos demográficos/psicográficos.
    -   `LeadStatus` / `PipelineStage`: Enums.
-   **Infrastructure**:
    -   `LeadModel` (SQLAlchemy): Mapeo a tabla `leads`.
    -   `LeadRepository`: CRUD y búsqueda por canales (telegram_id, whatsapp_id, etc.).
-   **Application**:
    -   `PipelineService`: Lógica para mover leads por el embudo.
    -   `LeadService`: Gestión de leads (creación, actualización, fusión).
-   **API**:
    -   `leads.py`: Router actualizado.

## Impact
-   **Affected Code**: `src/modules/sales/*`.
-   **Breaking Changes**: Rutas de importación de `Lead`.

## ADDED Requirements

### Requirement: Sales Domain
-   `Lead`: Root Aggregate.
-   `UserProfile`: Value Object complejo (datos "Valeria").

### Requirement: Sales Infrastructure
-   `LeadModel`: Tabla `leads`.
-   FK a `Tenant` (Obligatorio).
-   FK a `Customer` (Opcional, Link a Marketing).

### Requirement: Sales Repository
-   `LeadRepository.get_by_channel_id(channel, id, tenant_id) -> Optional[Lead]`
-   `LeadRepository.save(lead: Lead) -> Lead`
