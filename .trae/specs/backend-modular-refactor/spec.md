# Backend Modular Monolith Refactoring Spec

## Why
El backend actual presenta acoplamiento entre la capa de dominio y la infraestructura (SQLAlchemy), violando los principios de DDD. Esto dificulta el mantenimiento, las pruebas y la escalabilidad. Se requiere una refactorización completa hacia un Monolito Modular estricto para asegurar la separación de responsabilidades y la pureza del dominio.

## What Changes
Implementación de una arquitectura de Monolito Modular estricta con las siguientes características:

-   **Separación Estricta de Capas**:
    -   **Domain**: Puro Python/Pydantic. Prohibido SQLAlchemy o dependencias de infraestructura.
    -   **Application**: Casos de uso y orquestación.
    -   **Infrastructure**: Implementación técnica (BD, Modelos SQLAlchemy, Adaptadores).
    -   **API**: Controladores/Routers.
-   **Repositorios**: Actúan como traductores entre Modelos de Dominio y Modelos de Persistencia.
-   **Núcleo Compartido (Shared Kernel)**: Lógica transversal sin reglas de negocio específicas.
-   **Módulos Independientes**:
    -   IAM (Identidad y Acceso)
    -   Sales (Ventas y CRM)
    -   Communication (Mensajería y Agenda)
    -   Offer (Gestión de Ofertas)
    -   Marketing (CDP y Analytics)
    -   Brand (Identidad de Marca)
    -   Landing (Generador de Páginas)
    -   Gallery (Gestión de Activos)

## Execution Strategy (CRITICAL)
Dado el riesgo de pérdida de información y la complejidad del cambio:
1.  **Plan Maestro**: Este documento define la arquitectura global.
2.  **Especificaciones por Módulo**: Para CADA módulo a refactorizar, se **DEBE** crear un nuevo documento de especificaciones (`/spec`) específico antes de tocar código. Esto asegurará un análisis detallado de la migración de datos y lógica para ese módulo en particular.
3.  **Orden de Ejecución**:
    1.  **Shared Kernel**: Base del sistema.
    2.  **IAM**: Dependencia crítica para autenticación/tenants.
    3.  Resto de módulos (orden secuencial recomendado: Brand -> Offer -> Sales -> Communication -> Marketing -> Gallery -> Landing).

## ADDED Requirements

### Requirement: Shared Kernel Structure
El núcleo compartido (`src/shared/`) DEBE contener:
-   `domain/`: Entidades base, excepciones, eventos.
-   `application/`: Event Bus.
-   `infrastructure/`: Configuración DB, Base Model SQLAlchemy, Modelos técnicos (Log, Trace).
-   `utils/`: Logger, Crypto.

### Requirement: Module Structure (Standard)
Cada módulo (`src/modules/<name>/`) DEBE seguir estrictamente:
-   `domain/`: Modelos Pydantic (Pure Python).
-   `application/`: Servicios de aplicación.
-   `infrastructure/`:
    -   `models/`: Modelos SQLAlchemy (Heredan de Base).
    -   `repositories/`: Implementación de persistencia y mapeo (SQLAlchemy <-> Pydantic).
-   `api/`: Routers FastAPI.

### Requirement: DDD Rules
-   **Prohibido**: Importar `sqlalchemy` en `domain/`.
-   **Prohibido**: Heredar de `Base` (SQLAlchemy) en clases de `domain/`.
-   **Obligatorio**: Usar Repositorios para persistencia.

## Impact
-   **Affected Code**: Todo el directorio `backend/src`.
-   **Breaking Changes**: La estructura de importaciones cambiará completamente. Se requiere refactorización masiva.
