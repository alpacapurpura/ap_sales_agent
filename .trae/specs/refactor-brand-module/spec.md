# Refactor Brand Module Spec

## Why
El módulo `brand` actual sufre de problemas de arquitectura que dificultan su mantenibilidad y uso por parte del Agente de IA:
1.  **God Class**: `brand.py` contiene demasiadas responsabilidades (Identidad, Estrategia, Historia, Equipo, Avatares).
2.  **Ambigüedad**: Excesivo uso de `Optional`, permitiendo estados inválidos (marcas sin nombre).
3.  **Tipado Débil**: Uso de strings para campos categóricos (e.g., `industry`).
4.  **Deuda Técnica**: Campos `_legacy` ensuciando el modelo de dominio.

## What Changes
Refactorizar el dominio del módulo `brand` (`src/modules/brand/domain/`) dividiéndolo en archivos semánticos y endureciendo las reglas de negocio.

### Estructura de Archivos Propuesta
-   `src/modules/brand/domain/identity.py`: `BrandIdentity`, `BrandVisuals` y Enums (`BrandIndustry`).
-   `src/modules/brand/domain/strategy.py`: `BrandStrategy`, `BrandCompetitor`, `BrandMethodologyPillar`.
-   `src/modules/brand/domain/story.py`: `BrandStory`, `BrandStoryMilestone`.
-   `src/modules/brand/domain/team.py`: `BrandTeam`, `KeyFigure`, `BrandContact`.
-   `src/modules/brand/domain/entities.py`: `Avatar` (Entidad con ciclo de vida propio).
-   `src/modules/brand/domain/aggregates.py`: `BrandSettings` (Agregado raíz).
-   `src/modules/brand/domain/__init__.py`: Exportar todo para minimizar impacto en imports.

### Cambios en Código
-   **Enums**: Implementar `BrandIndustry` y otros Enums relevantes.
-   **Validaciones**: Hacer obligatorios campos críticos como `brand_name`.
-   **Migración Legacy**: Usar `model_validator(mode='before')` de Pydantic para transformar datos legacy automáticamente y eliminar campos `_legacy` del modelo final.
-   **Limpieza**: Eliminar `brand.py` original tras la refactorización.

## Impact
-   **Afecta**: `src/modules/brand/domain/brand.py` (será eliminado).
-   **Requiere Actualización**:
    -   `src/modules/brand/infrastructure/repositories/brand_repository.py`
    -   `src/modules/brand/api/router.py`
    -   Cualquier otro módulo que importe desde `brand.domain.brand`.

## ADDED Requirements
### Requirement: Strong Typing
El sistema DEBE usar Enums para campos categóricos como `industry` para asegurar consistencia en los datos consumidos por la IA.

### Requirement: Legacy Migration
El sistema DEBE transformar automáticamente los datos legacy (e.g., listas de strings en `competitors_legacy`) a la nueva estructura de objetos durante la carga, sin exponer campos legacy en el modelo de dominio.

## REMOVED Requirements
### Requirement: Monolithic File
**Reason**: `brand.py` es demasiado grande y mezcla conceptos dispares.
**Migration**: Dividir en submódulos semánticos.
