# Refactorización de Arquitectura Backend (Core & Shared)

## Why
El backend actual carece de una separación clara entre infraestructura técnica transversal y el núcleo de negocio compartido, lo que lleva a dependencias circulares y código duplicado. Para avanzar hacia un Monolito Modular estricto, es necesario establecer `src/core` (agnóstico) y `src/shared` (kernel de negocio) como cimientos sólidos.

## What Changes
- **Creación de `src/core/`**:
  - Centralización de configuración (`config.py`).
  - Centralización de infraestructura técnica (DB, Logger, Security, Exceptions).
- **Creación de `src/shared/domain/`**:
  - Definición de entidades base (`Base` de SQLAlchemy).
  - Value Objects compartidos.
- **Extracción de `src/shared/links/`**:
  - Mover lógica de URLs cortas de `communication` a `shared`.
- **Revisión Exhaustiva y Migración Módulo por Módulo**:
  - Se revisará CADA módulo (`iam`, `sales_agent`, `communication`, etc.) archivo por archivo.
  - Se extraerá CUALQUIER utilidad, configuración, o infraestructura genérica hacia `src/core`.
  - Se extraerá CUALQUIER lógica de dominio compartida o transversal hacia `src/shared`.
- **Limpieza y Reubicación**:
  - Eliminación de archivos duplicados en módulos.
  - Actualización masiva de importaciones.
- **Reglas de Dependencia**:
  - `core` NO importa de `shared` ni `modules`.
  - `shared` importa de `core`, NO de `modules`.

## Impact
- **Affected specs**: Arquitectura general del sistema.
- **Affected code**: `src/config.py`, `src/modules/*`, y múltiples archivos con importaciones de configuración o DB.

## ADDED Requirements
### Requirement: Estructura Core Completa
El sistema DEBE tener un directorio `src/core` que contenga TODA la infraestructura técnica agnóstica al negocio (Logger, Context, Security, DB, Exceptions, Config).

### Requirement: Estructura Shared Domain Completa
El sistema DEBE tener un directorio `src/shared` que contenga TODOS los elementos de dominio compartidos y utilidades de negocio transversales (Links, Value Objects, Base Entities).

### Requirement: Limpieza de Módulos
Los módulos de negocio (`src/modules/*`) NO DEBEN contener utilidades genéricas ni configuraciones de infraestructura que pertenezcan a `core` o `shared`.

## MODIFIED Requirements
### Requirement: Configuración e Inicialización
La configuración de la app y la inicialización de la DB deben importarse desde `src.core` en lugar de `src.config` o `src.shared.infrastructure.db`.

## REMOVED Requirements
### Requirement: Ubicaciones Antiguas
**Reason**: Centralización y limpieza.
**Migration**: Los archivos en `src/shared/infrastructure/db` (si existen duplicados) y `src/config.py` raíz serán eliminados tras su reubicación.
