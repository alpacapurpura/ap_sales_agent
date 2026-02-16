# Documentación de Arquitectura Técnica: AISALESHT

## 1. Visión General
Este documento define la arquitectura técnica del sistema **AISALESHT**, diseñado como un **Monolito Modular** distribuido en contenedores Docker. La arquitectura prioriza la separación de responsabilidades, la escalabilidad modular y la mantenibilidad a largo plazo.

### Principios Fundamentales
*   **Desacoplamiento:** El núcleo del negocio no depende de frameworks ni bases de datos.
*   **Modularidad:** El frontend y backend están organizados por dominios de negocio (Features/Slices) en lugar de capas técnicas puras.
*   **Determinismo:** Los agentes de IA operan sobre máquinas de estado finitas (LangGraph) para garantizar flujos predecibles.

---

## 2. Backend: Arquitectura Hexagonal (Ports & Adapters)
**Ubicación:** `/backend/src`
**Stack:** Python 3.11, FastAPI, LangGraph, SQLAlchemy, Pydantic.

El backend sigue estrictamente la **Arquitectura Hexagonal (Clean Architecture)**, dividiendo el código en capas concéntricas donde las dependencias apuntan solo hacia adentro.

### 2.1. Capa de Dominio (Núcleo)
*   **Ruta:** `src/core/domain/` y `src/services/db/models/`
*   **Responsabilidad:** Contiene la lógica de negocio pura, entidades y reglas invariantes del sistema.
*   **Componentes:**
    *   **Modelos Pydantic:** Definen la estructura de datos y validación (ej. `BrandSettings`, `OfferSchema`).
    *   **Entidades SQLAlchemy:** Mapeo a base de datos (ej. `User`, `Lead`), tratados como detalles de implementación pero definidos cerca del dominio.
    *   **Interfaces (Puertos):** Definiciones abstractas de lo que el sistema necesita (ej. `BaseRepository`, `LLMProvider`).

### 2.2. Capa de Aplicación (Casos de Uso)
*   **Ruta:** `src/services/` y `src/core/agents/`
*   **Responsabilidad:** Orquesta la lógica de negocio utilizando las entidades del dominio. No conoce detalles de HTTP o UI.
*   **Componentes:**
    *   **Services:** Clases que ejecutan acciones de negocio (ej. `OfferGeneratorService`, `DashboardService`).
    *   **Agentes (LangGraph):** El "cerebro" del sistema.
        *   `Orchestrator`: Grafo principal que gestiona el estado global.
        *   `Sales Swarm`: Sub-grafo de especialistas en ventas.
        *   `Web Extractor`: Agente efímero para scraping.

### 2.3. Capa de Adaptadores (Infraestructura)
*   **Adaptadores Primarios (Driving):**
    *   **API Routers (`src/api/routers`):** Controladores FastAPI que reciben peticiones HTTP y llaman a la capa de aplicación. Actúan como la "entrada" al hexágono.
*   **Adaptadores Secundarios (Driven):**
    *   **Repositorios (`src/services/db/repositories`):** Implementación concreta del acceso a datos (Postgres).
    *   **Vector Store (`src/services/vector_store.py`):** Cliente de Qdrant para memoria semántica.
    *   **Canales (`src/channels`):** Integraciones con WhatsApp (Evolution API), Telegram, etc.

---

## 3. Frontend: Feature-Sliced Design (FSD)
**Ubicación:** `/frontend/src`
**Stack:** Next.js 14 (App Router), TypeScript, Shadcn UI, React Query, Zustand.

El frontend utiliza una adaptación de **Feature-Sliced Design**, organizando el código por valor de negocio para facilitar la escalabilidad.

### 3.1. Estructura de Capas
1.  **App (`src/app`):**
    *   Capa de Routing de Next.js.
    *   Solo contiene `page.tsx`, `layout.tsx` y configuración de proveedores.
    *   Delega la lógica inmediatamente a las Features.

2.  **Features (`src/features`):**
    *   El núcleo de la arquitectura. Cada carpeta es un módulo autónomo.
    *   **Ejemplos:**
        *   `offer-studio/`: Lógica para crear y editar ofertas (Hooks, Componentes, API).
        *   `brand/`: Configuración de identidad de marca.
        *   `sales/`: Gestión de leads y calendario.
        *   `audit/`: Visualización de trazas de IA.
    *   **Regla:** Una feature puede usar componentes de `shared`, pero debe evitar depender fuertemente de otras features hermanas (bajo acoplamiento).

3.  **Shared (`src/components/ui`, `src/lib`):**
    *   **UI Kit (Atomic Design):** Componentes base de Shadcn (Botones, Inputs, Cards). Son los "átomos" y "moléculas".
    *   **Lib:** Utilidades, clientes de API (`axios/fetch`), constantes globales.

### 3.2. Gestión de Estado
*   **Server State:** **React Query** (TanStack Query) es la fuente de verdad principal para datos que vienen del backend (Leads, Configuración).
*   **Client State:** **Zustand** o **Context API** para estados de UI efímeros (modales abiertos, filtros activos).
*   **Formularios:** **React Hook Form** + **Zod** para validación robusta alineada con los esquemas del backend.

---

## 4. Infraestructura & DevOps
El sistema se orquesta mediante **Docker Compose**, definiendo un entorno de microservicios cohesivo.

| Servicio | Contenedor | Puerto | Descripción |
| :--- | :--- | :--- | :--- |
| **API Gateway** | `visionarias_brain_dev` | 8000 | Core del Backend (FastAPI + LangGraph). |
| **Client App** | `visionarias_client_dev` | 3000 | Frontend Next.js. |
| **Admin Panel** | `visionarias_admin_dev` | 8502 | Panel interno Streamlit para gestión rápida y RAG (Dev). Prod: 8501. |
| **Vector DB** | `visionarias_qdrant` | 6333 | Base de datos vectorial para búsqueda semántica (RAG). |
| **Relational DB** | `visionarias_postgres` | 5432 | Base de datos principal (PostgreSQL 15). |
| **Cache** | `visionarias_redis` | 6379 | Cola de tareas y caché de sesiones. |
| **WhatsApp** | `visionarias_whatsapp` | 8080 | Instancia de Evolution API v2 para conexión con Meta. |

---

## 5. Patrones de Diseño Clave

### 5.1. Backend
*   **Repository Pattern:** Abstracción del acceso a datos. Permite cambiar el ORM o la DB sin tocar la lógica de negocio.
    *   *Uso:* `UserRepository`, `OfferRepository`.
*   **Factory Pattern:** Creación dinámica de objetos complejos.
    *   *Uso:* `LLMFactory` (instancia GPT-4 o Gemini según config), `WhatsAppFactory`.
*   **Strategy Pattern:** Selección de algoritmos en tiempo de ejecución.
    *   *Uso:* Nodos de LangGraph (Router decide qué nodo ejecutar siguiente).
*   **Dependency Injection:** Inyección de dependencias a través de FastAPI (`Depends`).
    *   *Uso:* Inyección de `SessionLocal` (DB) y `CurrentUser` en los endpoints.

### 5.2. Frontend
*   **Composition Pattern:** Construcción de interfaces complejas componiendo componentes pequeños (`children` props) en lugar de herencia.
*   **Custom Hooks (Facade):** Encapsulación de lógica compleja de API y estado en hooks personalizados (`useOffers`, `useBrand`).
