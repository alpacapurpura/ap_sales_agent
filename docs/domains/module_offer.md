---
module: "Módulo de Ofertas (Offer Studio)"
status: "active"
core_files:
  # BACKEND
  - "backend/src/modules/offer/domain/offer.py"
  - "backend/src/modules/offer/domain/details.py"
  - "backend/src/modules/offer/api/products.py"
  - "backend/src/modules/offer/api/dto/products.py"
  # FRONTEND
  - "frontend/src/features/offer-studio/types/schema.ts"
  - "frontend/src/features/offer-studio/hooks/use-offer.ts"
  - "frontend/src/features/offer-studio/config/offer-builder-config.ts"
api_routes:
  - "GET /api/v1/products/{id}"
  - "POST /api/v1/products"
  - "PATCH /api/v1/products/{id}/identity"
  - "PATCH /api/v1/products/{id}/strategy"
  - "GET /api/v1/products/metadata/hints"
---

## 1. Propósito del Negocio (El "Por Qué")
Este módulo permite a los usuarios diseñar, configurar y gestionar sus "Ofertas Irresistibles" (Productos, Servicios, Programas, etc.) a través de un editor visual paso a paso ("Offer Studio"). Centraliza la definición de la propuesta de valor, precios, entregables y promesas de transformación, actuando como la fuente de verdad para generar funnels de venta y contenido de marketing automatizado.

## 2. Reglas de Negocio Estrictas (Business Rules)
- **Polimorfismo Obligatorio:** Toda oferta debe tener un `offer_type` válido (product, service, program, subscription, event) y sus `specific_details` deben coincidir estrictamente con la estructura definida para ese tipo.
- **Validación de Identidad:** El nombre de la oferta es obligatorio. El slug se genera automáticamente pero debe ser único por tenant.
- **Niveles de Consciencia:** La estrategia de la oferta debe definir a qué nivel de consciencia del cliente se dirige (Problem Aware, Solution Aware, etc.), lo cual condiciona los hooks de marketing generados.
- **Precios y Garantías:** Una oferta puede tener múltiples opciones de precio (pago único, plazos) y tipos de garantía (incondicional, condicional), pero la estructura de datos para estos debe seguir el esquema estricto de `PricingModel` y `Guarantee`.
- **Integridad de Datos en Actualizaciones:** Las actualizaciones parciales (PATCH) a secciones específicas (ej. `strategy`) no deben eliminar datos de otras secciones (ej. `identity`).

## 3. Mapa de Código (The "Where")
- **Backend (Dominio):** `backend/src/modules/offer/domain/offer.py` (Entidad Raíz), `backend/src/modules/offer/domain/details.py` (Polimorfismo).
- **Backend (API):** `backend/src/modules/offer/api/products.py` (Endpoints), `backend/src/modules/offer/api/dto/products.py` (DTOs).
- **Frontend (Estado/Hooks):** `frontend/src/features/offer-studio/hooks/use-offer.ts` (Lógica de carga y guardado), `frontend/src/features/offer-studio/utils/offer-health.ts` (Cálculo de completitud).
- **Frontend (UI Principal):** `frontend/src/features/offer-studio/components/offer-builder-layout.tsx` (Layout del editor), `frontend/src/features/offer-studio/config/offer-builder-config.ts` (Configuración de secciones).
- **Base de Datos (Modelos):** `backend/src/infrastructure/models/offer.py` (Tabla SQLAlchemy).

## 4. Casos Borde Conocidos (Edge Cases)
- **Cambio de Tipo de Oferta:** El sistema no permite cambiar el `offer_type` de una oferta ya creada debido a la incompatibilidad de `specific_details`. Se debe crear una nueva.
- **Persistencia de Datos Parciales:** El "Studio" permite guardar borradores incompletos. Las validaciones estrictas de "Publicación" son distintas a las de "Guardado de Borrador".
- **Manejo de Imágenes Relativas:** Las URLs de imágenes almacenadas en el backend son relativas y requieren que el frontend las procese con el helper `getFullUrl` para su visualización.
- **Concurrencia en Edición:** No hay bloqueo optimista; la última escritura gana. El frontend mitiga esto guardando por secciones aisladas.
