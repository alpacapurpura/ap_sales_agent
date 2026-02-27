---
name: backend-expert
description: Experto en desarrollo backend (FastAPI, Monolito Modular, DDD) para Visionarias Brain. Usar para implementación de endpoints, lógica de negocio, base de datos y corrección de bugs bajo la arquitectura de módulos.
---

# Backend Functional Expert

Guía definitiva para el desarrollo y mantenimiento del backend de Visionarias Brain bajo arquitectura **Modular Monolith (DDD)**.

## 🌟 Principios Fundamentales (DDD)

La arquitectura se basa en la **separación estricta** entre Dominio e Infraestructura.

1.  **Dominio Puro**: La capa `domain/` contiene la lógica de negocio y las entidades. **JAMÁS** debe depender de frameworks externos (SQLAlchemy, FastAPI, etc.).
2.  **Infraestructura Aislada**: La capa `infrastructure/` contiene la implementación técnica (Base de Datos, APIs externas).
3.  **Repositorios como Traductores**: Los repositorios convierten entre Modelos de Dominio (Pydantic) y Modelos de Persistencia (SQLAlchemy).

Para detalles completos sobre las reglas de DDD, consulta: [DDD_RULES.md](references/DDD_RULES.md).

---

## 🏗️ Estructura del Proyecto (Modular Monolith)

El backend se organiza en un **Núcleo Compartido** y **Módulos Independientes**.

### 1. Núcleo Compartido (`src/shared/`)
Contiene utilidades transversales, configuración de base de datos y lógica base.

### 2. Módulos de Negocio (`src/modules/`)
Cada módulo es un Bounded Context autónomo:

- `iam`: Identidad y Gestión de Accesos y Autenticación  (Usuarios, Tenants, Auth).
- `sales`: Gestión de Ventas, CRM y Pipelines.
- `communication`: Orquestación de mensajería (WhatsApp, Telegram, Email).
- `offer`: Gestión del catálogo de productos y servicios.
- `marketing`: CDP, Segmentación y Gestión de Campañas.
- `brand`: Configuración de marca y personalización por tenant.
- `landing`: Generador de landing pages.
- `gallery`: Gestión de activos digitales (imágenes, archivos, audios, etc.).
- `integration`: Conectores con herramientas externas (Whatsapp, ManyChat, Google Calendar, etc.).
- `onboarding`: Flujos de bienvenida y configuración inicial.

Para ver la estructura detallada de carpetas y archivos por módulo, consulta: [ARCHITECTURE.md](references/ARCHITECTURE.md).

---

## 🚀 Guía de Desarrollo

### Flujo de Trabajo Típico

1.  **Definir Entidad de Dominio**: Crear la clase Pydantic en `domain/entities.py`.
2.  **Definir Modelo de Persistencia**: Crear la clase SQLAlchemy en `infrastructure/models/`.
3.  **Implementar Repositorio**: Crear la clase en `infrastructure/repositories/` que use el modelo SQLAlchemy y devuelva la entidad de Dominio.
4.  **Crear Servicio de Aplicación**: Implementar la lógica de negocio en `application/services/` usando el repositorio (Inyección de Dependencias).
5.  **Exponer API**: Crear el Router en `api/routers.py` que llame al servicio.

### Comandos Esenciales

**Validación de Código (Ruff)**
```bash
ruff check backend/src --fix
```

**Tests**
```bash
# Ejecutar tests dentro del contenedor
docker exec -t visionarias_brain_dev pytest src/modules/{modulo}/tests
```
Consulta [testing.md](references/testing.md) para más detalles.

**Migraciones de Base de Datos**
```bash
cd backend && alembic revision --autogenerate -m "feat: description" && alembic upgrade head
```
Consulta [database.md](references/database.md) para más detalles.

---

## 🛑 Reglas de Oro (MANDATORIAS)

### 1. Naming Conventions (ESTRICTO)
-   **Archivos/Carpetas**: `snake_case` (e.g., `user_service.py`).
-   **Clases**: `PascalCase` (e.g., `UserRepository`).
-   **Variables/Funciones**: `snake_case` (e.g., `calculate_total`).
-   **Constantes**: `UPPER_CASE` (e.g., `MAX_RETRIES`).

### 2. Aislamiento de Módulos
-   **Prohibido**: Importar modelos de DB de otro módulo.
-   **Prohibido**: Joins SQL entre módulos.
-   **Permitido**: Comunicación vía Servicios (Síncrono) o Eventos (Asíncrono).

### 3. Capas Limpias
-   **Dominio**: Solo Python/Pydantic.
-   **Aplicación**: Orquestación y lógica de negocio.
-   **Infraestructura**: Detalles técnicos (DB, API, File System).
-   **API**: Entrada/Salida (HTTP).
