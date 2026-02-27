# Plan de Ejecución: Ecosistema de Ofertas (Metodología Iterativa & Clean Code)

Entendido perfectamente. Mantendremos intactos los módulos de **Auditoría** y **Datos Sensibles**. Este plan se centrará en la **expansión** del sistema siguiendo estrictamente tu ciclo de calidad (Investigación -> Revisión -> Implementación -> Verificación).

## 1. Metodología de Trabajo (Por cada módulo)
Para cada fase (Backend, Frontend, Lógica), ejecutaré el siguiente ciclo **antes de escribir código**:
1.  **Investigación UX/UI (2025/2026):** Referencias visuales de **Cloudflare/Hostinger** (Dashboards limpios, feedback inmediato, tablas densas pero legibles).
2.  **Revisión de Código:** Escaneo profundo para identificar funciones reutilizables (ej: en `admin/app.py` o `knowledge_service.py`) y evitar duplicidad.
3.  **Diseño Clean Code:** Aplicación de patrones (Factory, Strategy, Repository) y principios SOLID.
4.  **Implementación & Verificación:** Desarrollo incremental con tests de humo.

---

## 2. Fase 1: Backend & Modelado de Datos (Cimientos)
**Objetivo:** Extender `business.py` sin tocar `observability.py` (Audit).

1.  **Revisión Previa:** Confirmar que `SensitiveData` (Safety Layer) se integra correctamente con el nuevo flujo de RAG sin conflictos.
2.  **Nuevas Tablas (SQLAlchemy):**
    *   `AvatarDefinition`: Configuración global del ICP.
    *   `MarketingAsset`: Fuente de verdad para contextos (Webinars, PDFs).
    *   `Objection`: Matriz detallada vinculada a `Product`.
3.  **Actualización de `Document`:** Añadir columnas `scope`, `product_id`, `marketing_asset_id` para habilitar la arquitectura multi-contexto.

---

## 3. Fase 2: Motor de Conocimiento (RAG Logic)
**Objetivo:** Potenciar `KnowledgeService` para soportar scopes, protegiendo la carga actual.

1.  **Patrón Strategy:** Refactorizar `ingest_file` para usar estrategias de metadatos (GlobalStrategy, OfferStrategy) sin llenar el código de `if/else`.
2.  **Integración Qdrant:** Asegurar que los payloads incluyan `scope` y `entity_id` para el filtrado, manteniendo la compatibilidad con los vectores ya indexados (defaults seguros).

---

## 4. Fase 3: Frontend "Offer Studio" (UX Referente)
**Objetivo:** Un Wizard de configuración en Next.js con la elegancia de Cloudflare.

1.  **UX/UI Research:** Buscar patrones de "Multi-step Configuration Wizards" modernos.
2.  **Componentes:**
    *   **Orquestador:** Estado global del wizard.
    *   **Objection Editor:** UI tipo hoja de cálculo (Hostinger style) para editar objeciones rápidamente.
    *   **Asset Uploader:** Reutilizar lógica de carga pero con feedback visual mejorado.
3.  **Integración API:** Conectar con los nuevos endpoints del backend.

---

## Compromiso de Seguridad
*   ❌ **NO TOCAR:** `src/services/db/models/observability.py` (Audit), `src/admin/app.py` (Lógica actual de Admin/Audit), ni la lógica core de `SensitiveData`.
*   ✅ **EXTENDER:** `business.py` y `knowledge_service.py`.

Procederé fase por fase, iniciando con la **Fase 1 (Backend)** tras tu confirmación.
