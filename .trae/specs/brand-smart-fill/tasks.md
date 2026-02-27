# Tasks

- [x] Task 1: Backend - Infraestructura de Prompts y Crawling
  - [x] SubTask 1.1: Crear carpeta `backend/src/core/prompts/brand_extraction/` y migrar/crear prompts base (Identidad, Estrategia, Historia, Equipo).
  - [x] SubTask 1.2: Actualizar `web_extractor` para implementar Deep Crawling (seguir links relevantes: About, Team, Contact).
  - [x] SubTask 1.3: Implementar lógica de extracción multi-paso (Identity -> Strategy -> Story -> Team) para mejorar calidad.

- [x] Task 2: Backend - Endpoint y Lógica de Actualización
  - [x] SubTask 2.1: Actualizar endpoint `/api/tools/extract-full-brand` para aceptar `mode` ("initial" | "update") y `update_instructions`.
  - [x] SubTask 2.2: Implementar lógica de "Merge/Update" en el backend: Comparar data existente con nueva y aplicar cambios según instrucciones.
  - [x] SubTask 2.3: Asegurar persistencia automática en DB tras la extracción inicial.
  - [x] SubTask 2.4: Validar endpoint con casos de prueba (Web sola, Web + Docs, Solo Docs, Update).

- [x] Task 3: Frontend - Componente `SmartFillCard` Avanzado
  - [x] SubTask 3.1: Implementar UI para "Modo Inicial" (Web + Docs, Advertencias de sensibilidad).
  - [x] SubTask 3.2: Implementar UI para "Modo Actualización" (Input de instrucciones, mensaje de "Refinamiento").
  - [x] SubTask 3.3: Implementar sistema de Feedback Visual (Barra de progreso / Pasos: "Analizando Home", "Buscando Equipo"...).
  - [x] SubTask 3.4: Implementar Bloqueo de UI durante el proceso.

- [x] Task 4: Frontend - Integración y Resumen
  - [x] SubTask 4.1: Integrar `SmartFillCard` en `BrandStudioLayout`.
  - [x] SubTask 4.2: Implementar Modal/Reporte de Resumen al finalizar ("X campos llenados").
  - [x] SubTask 4.3: Validar flujo completo (Extracción -> Guardado -> Visualización).

# Task Dependencies
- Task 3 depende de Task 2 (Endpoint listo).
- Task 4 depende de Task 3 (Componente listo).
