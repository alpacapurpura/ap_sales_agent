# Tasks

- [x] Task 1: Auditar y Refactorizar `src/app` y `src/lib`
  - [x] SubTask 1.1: Revisar `src/app` para asegurar que solo contenga rutas y layouts. Mover lógica encontrada a `src/features` correspondiente o crear nueva feature si es necesario.
  - [x] SubTask 1.2: Revisar `src/lib` para asegurar que contenga solo utilidades globales y configuraciones. Verificar que no haya lógica de negocio específica de una feature.
  - [x] SubTask 1.3: Verificar que no haya duplicidad de funciones utilitarias entre `src/lib` y otros directorios.

- [x] Task 2: Auditar y Refactorizar `src/features` (Parte 1: Core Features)
  - [x] SubTask 2.1: Revisar `src/features/brand` (si existe) para asegurar estructura `components`, `hooks`, `types`.
  - [x] SubTask 2.2: Revisar `src/features/connections` (si existe) para asegurar estructura `components`, `hooks`, `types`.
  - [x] SubTask 2.3: Revisar `src/features/offer-studio` (si existe) para asegurar estructura `components`, `hooks`, `types`.
  - [x] SubTask 2.4: Mover cualquier componente o hook que pertenezca a estas features desde `src/components` o `src/hooks` hacia la feature correspondiente.

- [x] Task 3: Auditar y Refactorizar `src/features` (Parte 2: Otras Features)
  - [x] SubTask 3.1: Identificar otras carpetas en `src/features` y aplicar la misma revisión estructural.
  - [x] SubTask 3.2: Verificar que `src/features` no tenga dependencias circulares entre features.
  - [x] SubTask 3.3: Asegurar que cada feature tenga un `index.ts` que exporte su API pública.

- [x] Task 4: Auditar y Refactorizar `src/components` y `src/hooks` Globales
  - [x] SubTask 4.1: Revisar `src/components/ui` para asegurar que sean componentes puros de Shadcn.
  - [x] SubTask 4.2: Revisar `src/components/shared` para asegurar que sean componentes verdaderamente reutilizables y no pertenezcan a una feature específica.
  - [x] SubTask 4.3: Revisar `src/hooks` para asegurar que sean hooks genéricos y no de negocio.

- [ ] Task 5: Verificación Final de Calidad y Duplicidad
  - [ ] SubTask 5.1: Ejecutar una búsqueda de código duplicado en todo `src`.
  - [ ] SubTask 5.2: Verificar nombres de variables y funciones para asegurar claridad y consistencia.
  - [ ] SubTask 5.3: Asegurar que todos los archivos sigan las convenciones de nombrado del proyecto.

# Task Dependencies
- Task 2 y Task 3 dependen de Task 1 parcialmente (para mover lógica extraída).
- Task 5 depende de completar todas las tareas anteriores.
