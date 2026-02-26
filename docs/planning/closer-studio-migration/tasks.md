# Plan de Tareas: Closer Studio Transformation

## Fase 1: Frontend (Mock-First)
**Objetivo:** Validar la UX/UI con datos simulados antes de tocar el backend.

- [ ] **Task 1.1: Definir Tipos e Interfaces**
  - Actualizar `frontend/src/features/sales/types/index.ts`.
  - Definir `Lead` unificado con `Customer`.
  - Definir `MockData` estática para los 5 escenarios (Empty, Partial, Full, Extreme Content, Error).

- [ ] **Task 1.2: Componentes Atómicos (Atomic Design)**
  - Crear `components/molecules/CustomerAvatar.tsx` (Muestra avatar o iniciales).
  - Crear `components/organisms/LeadCard.tsx` (Composición de Customer info + Sales status).
  - Crear `components/templates/PipelineView.tsx` (Kanban board).

- [ ] **Task 1.3: Vista Principal Closer Studio**
  - Implementar página `/closer-studio` (o ruta equivalente).
  - Integrar los componentes con el Mock Data.
  - Validar interactividad (Drag & Drop visual, apertura de detalles).

## Fase 2: Backend (Core & Migration)
**Objetivo:** Refactorizar el modelo de datos y migrar información existente.

- [ ] **Task 2.1: Migración de Base de Datos (Alembic)**
  - Crear revisión `alembic` para añadir `customer_id` a `leads`.
  - Escribir script de migración de datos (Python) para poblar `CustomerProfile` desde `LeadModel`.
  - Crear revisión `alembic` para eliminar columnas redundantes en `leads`.

- [ ] **Task 2.2: Actualización de Modelos SQLAlchemy**
  - Modificar `LeadModel` en `backend/src/modules/sales`.
  - Establecer relaciones ORM (`lead.customer`).
  - Actualizar `LeadRepository` para manejar la creación dual (Customer + Lead) transaccional.

- [ ] **Task 2.3: Endpoints API**
  - Actualizar `GET /leads` para incluir datos del cliente (Eager loading).
  - Actualizar `POST /leads` para manejar la lógica de "Buscar o Crear Cliente".

## Fase 3: Integración
**Objetivo:** Conectar Frontend con Backend real.

- [ ] **Task 3.1: Cliente HTTP**
  - Actualizar `leadsApi` en frontend para consumir la nueva estructura.
  - Mapear respuesta del backend a las interfaces de UI.

- [ ] **Task 3.2: E2E Testing Manual**
  - Verificar flujo: Crear Lead -> Verifica que aparezca en Marketing -> Mover en Pipeline.

## Fase 4: Auditoría y Limpieza
- [ ] **Task 4.1:** Ejecutar `front-arch-auditor` para validar estructura de componentes.
- [ ] **Task 4.2:** Ejecutar `back-arch-auditor` para validar Clean Architecture.
