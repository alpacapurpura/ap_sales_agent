---
module: "Landing Page Builder"
status: "active"
core_files:
  # BACKEND
  - "backend/src/modules/landing/domain/landing_page.py"
  - "backend/src/modules/landing/domain/content.py"
  - "backend/src/modules/landing/application/landing_service.py"
  # FRONTEND
  - "frontend/src/features/offer-studio/components/landing/components/editor/landing-editor.tsx"
  - "frontend/src/features/offer-studio/components/landing/utils/adapter.ts"
  - "frontend/src/app/(landing)/layout.tsx"
api_routes:
  - "GET /api/v1/landing/offer/{offer_id}"
  - "POST /api/v1/landing/{offer_id}/generate"
  - "PUT /api/v1/landing/{offer_id}"
  - "POST /api/v1/landing/{offer_id}/ai/regenerate-block"
---

## 1. Propósito del Negocio (El "Por Qué")
Este módulo permite a los usuarios transformar sus Ofertas estructuradas en Landing Pages de alta conversión (Squeeze, VSL, Eventos, etc.) sin conocimientos de código. Resuelve la desconexión entre la "definición de la oferta" y su "presentación visual" mediante un editor visual (Puck) que se pre-popula inteligentemente con datos de marketing, manteniendo una sincronización bidireccional entre el contenido persuasivo y el diseño.

## 2. Reglas de Negocio Estrictas (Business Rules)
- **Regla 1 (Acoplamiento de Arquetipo):** La configuración de contenido (`LandingPageConfig`) DEBE coincidir estrictamente con el `archetype` seleccionado (ej. un arquetipo `THE_SQUEEZE` rechaza estructuras de datos de `THE_EVENT`).
- **Regla 2 (Dependencia de Oferta):** Toda Landing Page nace obligatoriamente de una Oferta (`offer_id`). No existen landing pages "huerfanas"; su contenido inicial se deriva de la promesa y los dolores de la oferta.
- **Regla 3 (Aislamiento del Editor):** La experiencia de edición DEBE ocurrir en una ruta aislada (`/editor/...`) que utiliza un layout dedicado (`(landing)/layout.tsx`) para eliminar la barra lateral y maximizar el espacio de trabajo (canvas).
- **Regla 4 (Inmutabilidad del Slug):** El `slug` se genera automáticamente a partir del título de la oferta para garantizar URLs amigables, pero debe ser único dentro del contexto del `tenant_id`.

## 3. Mapa de Código (The "Where")
- **Backend (Dominio):** `backend/src/modules/landing/domain/landing_page.py` (Entidad Raíz y Lógica de Negocio)
- **Backend (Modelos de Contenido):** `backend/src/modules/landing/domain/content.py` (Estructuras Polimórficas Pydantic)
- **Backend (API):** `backend/src/modules/landing/api/landing.py` (Endpoints REST)
- **Frontend (Layout Editor):** `frontend/src/app/(landing)/layout.tsx` (Entorno visual aislado, sin sidebar)
- **Frontend (Página Editor):** `frontend/src/app/(landing)/[tenantId]/editor/[offerId]/page.tsx` (Punto de entrada Next.js)
- **Frontend (UI Principal):** `frontend/src/features/offer-studio/components/landing/components/editor/landing-editor.tsx` (Orquestador del Editor Puck)
- **Frontend (Adaptador de Datos):** `frontend/src/features/offer-studio/components/landing/utils/adapter.ts` (Transformador Crítico: Dominio <-> Puck JSON)

## 4. Casos Borde Conocidos (Edge Cases)
- **Transformación de Datos (Adapter Pattern):** El editor visual (Puck) espera una estructura JSON plana, mientras que el backend usa modelos anidados estrictos. El archivo `adapter.ts` maneja esta traducción compleja; errores aquí causan que el editor cargue en blanco.
- **Regeneración Parcial con IA:** El endpoint `regenerate-block` permite reescribir solo una sección (ej. "Hero") sin alterar el resto de la página. El frontend debe manejar el estado de "loading" por bloque para evitar conflictos de edición.
- **Sincronización de Tema Global:** Los estilos globales (colores, fuentes) definidos en el Tenant deben inyectarse en el iframe del editor mediante `LandingThemeProvider` para que la previsualización sea fidedigna ("What You See Is What You Get").
- Desfase de Estado: Modificar el título de la Oferta en el offer-studio pero que el JSON de la landing siga mostrando el título viejo estático.
- Renderizado SSR: Problemas de hidratación (Hydration Mismatch) al renderizar bloques complejos de Puck en Next.js App Router.