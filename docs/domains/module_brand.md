---
module: "Módulo de Marca (Brand Studio)"
status: "active"
core_files:
  # BACKEND
  - "backend/src/modules/brand/domain/aggregates.py"
  - "backend/src/modules/brand/infrastructure/repositories/brand_repository.py"
  - "backend/src/modules/brand/api/router.py"
  # FRONTEND
  - "frontend/src/features/brand/hooks/useBrandSettings.ts"
  - "frontend/src/features/brand/utils/brand-validation.ts"
  - "frontend/src/features/brand/types/index.ts"
api_routes:
  - "GET /api/v1/brand"
  - "PATCH /api/v1/brand"
  - "POST /api/v1/brand/extract"
---

## 1. Propósito del Negocio (El "Por Qué")
Centralizar y gestionar la identidad corporativa del usuario (misión, visión, colores, tono de voz) para alimentar a los agentes de IA. Este módulo actúa como la fuente de verdad para la personalidad de la marca, asegurando que todos los contenidos generados (emails, posts, mensajes) sean coherentes y alineados con la estrategia de negocio definida.

## 2. Reglas de Negocio Estrictas (Business Rules)
- **Persistencia Embebida**: La configuración global de marca NO tiene su propia tabla SQL; se almacena como un documento JSON estructurado dentro de la columna `config_json` de la tabla `tenants`.
- **Identidad Obligatoria**: El campo `brand_name` es mandatorio para considerar válida la identidad base. Sin él, el sistema no puede operar correctamente.
- **Validación de Salud (Health Score)**: El sistema calcula un puntaje de completitud (0-100%). Secciones críticas vacías pueden bloquear la generación de contenido por parte de los agentes.
- **Migración Automática**: Los modelos de Pydantic implementan validadores `before` para transformar datos legacy automáticamente al leerlos, evitando errores por cambios de esquema.
- **Avatares Separados**: Los "Buyer Personas" (Avatares) son entidades independientes con su propia tabla SQL (`avatars`) para permitir búsquedas complejas, a diferencia del resto de la configuración que es un documento único.

## 3. Mapa de Código (The "Where")
- **Backend (Dominio):** `backend/src/modules/brand/domain/aggregates.py` (Modelo Raíz BrandSettings)
- **Backend (API):** `backend/src/modules/brand/api/router.py` (Endpoints CRUD y Extracción)
- **Frontend (Estado/Hooks):** `frontend/src/features/brand/hooks/useBrandSettings.ts` (Gestión global con React Query)
- **Frontend (UI Principal):** `frontend/src/features/brand/components/container/brand-studio-layout.tsx` (Layout y Navegación)
- **Base de Datos (Modelos):** `backend/src/modules/brand/infrastructure/repositories/brand_repository.py` (Lógica de acceso a JSON en Tenant)

## 4. Casos Borde Conocidos (Edge Cases)
- **Timeouts en Extracción**: El proceso de scraping y análisis con IA puede exceder los tiempos de respuesta estándar; el frontend implementa un `AbortController` con límite de 8 minutos y feedback de progreso para evitar bloqueos.
- **Datos Incompletos/Corruptos**: Si la migración falla o los datos JSON están corruptos, el frontend inyecta valores por defecto (fallbacks seguros) para evitar que la aplicación crashee (Pantalla Blanca).
- **Sincronización Visual en Tiempo Real**: Los cambios en la paleta de colores (`BrandVisuals`) se inyectan dinámicamente como variables CSS en el DOM, permitiendo previsualización inmediata sin recargar la página.
